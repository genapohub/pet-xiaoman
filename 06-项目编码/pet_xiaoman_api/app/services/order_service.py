"""订单业务逻辑（PRD §5.2.1 预约下单 / §5.2.2 状态流转 / §5.2.1 取消规则）。

路由层只做参数解析，业务规则集中在这里——状态机校验委托 order_state。
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.order import Order, OrderStatus, PayType, RefundStatus
from app.models.pet import Pet, Species
from app.models.service_item import ItemStatus, ItemType, ServiceItem
from app.services import order_state
from app.services.order_state import TransitionContext, TransitionError

# 进行中状态：存在其一则禁止重复下单（PRD §5.2.1 业务规则②）
ACTIVE_STATUSES = [OrderStatus.PENDING_CONFIRM, OrderStatus.BOOKED, OrderStatus.PICKING,
                   OrderStatus.IN_SERVICE, OrderStatus.WAIT_DELIVERY]


class BusinessError(Exception):
    """业务规则不满足，路由层转 422。"""


def is_night_order(dt: datetime) -> bool:
    """夜间单判定（PRD §7.2）：下单时刻在 22:00-次日 7:00。"""
    return dt.hour >= 22 or dt.hour < 7


def gen_order_no(db: Session) -> str:
    """GD+yyyyMMdd+3 位当日序号（PRD §7.1）；unique 索引兜底并发，调用方需捕获重试。"""
    prefix = f"GD{datetime.now().strftime('%Y%m%d')}"
    count = db.query(Order).filter(Order.order_no.like(f"{prefix}%")).count()
    return f"{prefix}{count + 1:03d}"


def _get_or_create_pet(db: Session, user_id: int, name: str, species: str, weight,
                       store_id: int | None = None) -> Pet:
    """宠物档案复用：同名未删除档案直接复用，否则新建（PRD C009）。"""
    pet = (db.query(Pet)
           .filter(Pet.owner_id == user_id, Pet.name == name, Pet.deleted.is_(False))
           .first())
    if pet:
        if store_id is not None and pet.store_id is None:
            pet.store_id = store_id  # 顺手打标历史档案
        return pet
    try:
        species_enum = Species(species)
    except ValueError:
        species_enum = Species.OTHER
    pet = Pet(name=name, species=species_enum, weight=weight, owner_id=user_id, store_id=store_id)
    db.add(pet)
    db.flush()
    return pet


def create_order(db: Session, data, store_id: int | None = None) -> Order:
    """提交预约：校验 → 重复单拦截 → 锁价快照 → 落库（PRD §5.2.1）。"""
    if data.expect_time <= datetime.now():
        raise BusinessError("期望服务时间必须晚于现在")

    # ① 重复单拦截：同客户存在进行中订单
    active = (db.query(Order)
              .filter(Order.user_id == data.user_id, Order.status.in_(ACTIVE_STATUSES))
              .first())
    if active:
        raise BusinessError("您有进行中的订单，请联系门店处理")

    # ② 套餐锁价：只接受在售套餐，价格与版本快照（并限本店，防跨店下单）
    pkg = db.get(ServiceItem, data.pkg_id)
    if (not pkg or pkg.type != ItemType.PACKAGE or pkg.status != ItemStatus.ON_SALE
            or (store_id is not None and pkg.store_id not in (store_id, None))):
        raise BusinessError("套餐不存在或已下架")
    addons_snap, total = [], float(pkg.price)
    for aid in data.addon_ids or []:
        item = db.get(ServiceItem, aid)
        if (not item or item.status != ItemStatus.ON_SALE
                or (store_id is not None and item.store_id not in (store_id, None))):
            raise BusinessError("包含不可用的加购项，请刷新后重试")
        addons_snap.append({"item_id": aid, "name": item.name, "price_snapshot": float(item.price)})
        total += float(item.price)

    pet = _get_or_create_pet(db, data.user_id, data.pet_name, data.species, data.weight, store_id)
    now = datetime.now()
    order = Order(
        order_no=gen_order_no(db),
        user_id=data.user_id,
        pet_id=pet.id,
        pkg_id=pkg.id,
        price_version=pkg.version,
        addons=addons_snap,
        expect_time=data.expect_time,
        address=data.address,
        is_night=is_night_order(now),
        total_amount=round(total, 2),
        store_id=store_id,
    )
    db.add(order)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # order_no 并发竞态：重试一次
        order.order_no = gen_order_no(db)
        db.add(order)
        db.commit()
    db.refresh(order)
    return order


def cancel_by_customer(db: Session, order_no: str, reason: str) -> Order:
    """客户取消（PRD §5.2.1）：仅待确认/已预约可取消；已付金额自动转退款流程。"""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise BusinessError("订单不存在")
    if order.status not in (OrderStatus.PENDING_CONFIRM, OrderStatus.BOOKED):
        raise BusinessError("当前状态不可取消，请联系门店处理")
    if order.pay_type != PayType.UNPAID:
        # 接宠完成前取消：已付金额全额原路退（退款执行由支付模块消费 REFUNDING 状态）
        order.refund_status = RefundStatus.REFUNDING
    order.status = OrderStatus.CANCELLED
    order.cancel_reason = reason or "客户取消"
    db.commit()
    db.refresh(order)
    return order


def reschedule_by_customer(db: Session, order_no: str, new_time: datetime) -> Order:
    """客户改期（PRD §6.2）：免费 1 次，与 B 端 `/api/b/orders/{no}/reschedule` 共享配额。

    校验：
      - 仅待确认/已预约可改期（接宠之后改期要走门店人工通道）
      - 1 次免费配额已用完 → 抛 BusinessError，前端引导「请联系店长」
      - 改到过去时间 → 抛 BusinessError
    """
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise BusinessError("订单不存在")
    if order.status not in (OrderStatus.PENDING_CONFIRM, OrderStatus.BOOKED):
        raise BusinessError("当前状态不可改期，请联系门店处理")
    if order.reschedule_count >= 1:
        raise BusinessError("免费改期次数已用完，请联系店长")
    if new_time <= datetime.now():
        raise BusinessError("改期时间必须晚于现在")
    order.expect_time = new_time
    order.reschedule_count += 1
    db.commit()
    db.refresh(order)
    return order


def transition(db: Session, order_no: str, target: str, ctx: TransitionContext) -> Order:
    """B 端状态流转：校验（状态机）+ 落库。店长回退例外通道暂不实现（PRD §6.4 无逆向边）。"""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise BusinessError("订单不存在")
    try:
        order_state.validate_transition(order.status.value if isinstance(order.status, str) else order.status.value,
                                        target, ctx)
    except TransitionError as e:
        raise BusinessError(str(e))
    order.status = OrderStatus(target)
    db.commit()
    db.refresh(order)
    return order
