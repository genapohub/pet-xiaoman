"""B 端订单路由（PRD §5.1 B002/B003）：列表筛选、确认、状态流转。

角色控制（PRD §8.5）：关键危险操作走后台员工 token + RBAC 权限校验。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_perm, staff_auth
from app.models.order import Order, OrderStatus, PayType, RefundStatus
from app.models.pet import Pet
from app.models.service_item import ServiceItem
from app.models.staff import Staff, StaffRole
from app.services import media_service, order_service, payment_service
from app.services.order_service import BusinessError
from app.services.order_state import TransitionContext
from app.services.tenant import belongs, store_clause

router = APIRouter()


def _lookups(db: Session, orders: list[Order]) -> tuple[dict, dict]:
    """批量取套餐名 / 宠物名，避免列表页 N+1。

    为什么必须补：设计稿的订单列表有「服务项目」列（显示「单独火化 · 中型」），
    而订单表只存 `pkg_id`；关键词检索的占位文案是「订单号/宠物名」，
    也依赖宠物名可查。缺了这两项，前端只能显示裸 id 或假装能搜宠物名。
    """
    pkg_ids = {o.pkg_id for o in orders if o.pkg_id}
    pet_ids = {o.pet_id for o in orders if o.pet_id}
    pkg_names: dict = {}
    pet_names: dict = {}
    if pkg_ids:
        pkg_names = {r[0]: r[1] for r in db.query(ServiceItem.id, ServiceItem.name)
                     .filter(ServiceItem.id.in_(pkg_ids)).all()}
    if pet_ids:
        pet_names = {r[0]: r[1] for r in db.query(Pet.id, Pet.name)
                     .filter(Pet.id.in_(pet_ids)).all()}
    return pkg_names, pet_names


@router.get("/orders", summary="订单列表（B002：状态/日期/夜间单/关键词筛选 + 分页）")
def list_orders(status: str | None = None,
                date: str | None = None,
                is_night: bool | None = None,
                keyword: str | None = None,
                page: int = 1, size: int = 20,
                staff: Staff = Depends(staff_auth),
                db: Session = Depends(get_db)):
    query = db.query(Order)
    clause = store_clause(Order, staff.store_id)  # 多租户：仅本店
    if clause is not None:
        query = query.filter(clause)
    if status:
        query = query.filter(Order.status == OrderStatus(status))
    if date:
        query = query.filter(Order.expect_time.like(f"{date}%"))
    if is_night is not None:
        query = query.filter(Order.is_night == is_night)
    if keyword:
        # 占位文案承诺「订单号/宠物名」都能搜 → 必须真的支持宠物名，
        # 否则门店按宠物名搜不到，会以为订单丢了。用 outerjoin 保证没建档的订单仍能按单号命中。
        like = f"%{keyword}%"
        query = (query.outerjoin(Pet, Order.pet_id == Pet.id)
                 .filter((Order.order_no.like(like)) | (Pet.name.like(like))))
    total = query.count()
    rows = (query.order_by(Order.created_at.desc())
            .offset((page - 1) * size).limit(size).all())
    pkg_names, pet_names = _lookups(db, rows)
    return {
        "total": total,
        "items": [{
            "order_no": o.order_no,
            "status": o.status.value,
            "pkg_id": o.pkg_id,
            "pkg_name": pkg_names.get(o.pkg_id, ""),
            "pet_id": o.pet_id,
            "pet_name": pet_names.get(o.pet_id, ""),
            "total_amount": float(o.total_amount),
            "pay_type": o.pay_type.value,
            "paid_amount": float(o.paid_amount),
            "refund_status": o.refund_status.value,
            "is_night": bool(o.is_night),
            "expect_time": o.expect_time.isoformat(),
            "created_at": o.created_at.isoformat(),
        } for o in rows],
    }


@router.post("/orders/{order_no}/confirm", summary="确认订单（待确认→已预约，SLA 30 分钟）")
def confirm_order(order_no: str, payload: dict, staff: Staff = Depends(staff_auth), db: Session = Depends(get_db)):
    return _transition(order_no, {"target": OrderStatus.BOOKED.value}, db, staff)


@router.post("/orders/{order_no}/transition", summary="状态流转（强制影像=服务端查库校验，结清校验在状态机内）")
def transition(order_no: str, payload: dict, staff: Staff = Depends(staff_auth), db: Session = Depends(get_db)):
    return _transition(order_no, payload, db, staff)


def _transition(order_no: str, payload: dict, db: Session, staff: Staff) -> dict:
    target = payload.get("target")
    if not target:
        raise HTTPException(422, "缺少 target 状态")
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not belongs(order, staff.store_id):  # 多租户：防跨店操作
        raise HTTPException(404, "订单不存在")
    # 强制影像：服务端查 service_media 表，不信任前端 has_media 参数（PRD §5.2.2）
    # 店长判定：来自登录态 token 解析的角色，不再信任前端 payload.role（堵伪造）
    ctx = TransitionContext(
        has_media=media_service.node_media_satisfied(db, order.id, target),
        pay_type=order.pay_type.value if hasattr(order.pay_type, "value") else str(order.pay_type),
        is_owner=staff.role == StaffRole.MANAGER,
    )
    try:
        order = order_service.transition(db, order_no, target, ctx)
    except BusinessError as e:
        raise HTTPException(422, str(e))
    if target == OrderStatus.CANCELLED.value:
        reason = (payload.get("reason") or "").strip()
        order.cancel_reason = reason or "后台取消"
        if order.pay_type != PayType.UNPAID:
            order.refund_status = RefundStatus.REFUNDING
        db.commit()
        db.refresh(order)
    return {"order_no": order.order_no, "status": order.status.value,
            "message": f"已流转至「{order.status.value}」"}


@router.get("/orders/{order_no}", summary="订单详情（B003：全字段 + 影像 + 备注）")
def get_order_detail(order_no: str, staff: Staff = Depends(staff_auth),
                     db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not belongs(order, staff.store_id):
        raise HTTPException(404, "订单不存在")
    return {
        "order_no": order.order_no,
        "status": order.status.value,
        "pet_id": order.pet_id,
        "pkg_id": order.pkg_id,
        "price_version": order.price_version,
        "addons": order.addons or [],
        "expect_time": order.expect_time.isoformat(),
        "address": order.address,
        "is_night": bool(order.is_night),
        "total_amount": float(order.total_amount),
        "pay_type": order.pay_type.value,
        "paid_amount": float(order.paid_amount),
        "refund_status": order.refund_status.value,
        "cancel_reason": order.cancel_reason,
        "notes": order.notes,
        "reschedule_count": order.reschedule_count,
        "created_at": order.created_at.isoformat(),
        "media": media_service.list_order_media(db, order),
    }


@router.put("/orders/{order_no}/notes", summary="内部备注（客户不可见，自动保存）")
def save_notes(order_no: str, payload: dict, staff: Staff = Depends(staff_auth),
               db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not belongs(order, staff.store_id):
        raise HTTPException(404, "订单不存在")
    order.notes = payload.get("notes", "")
    db.commit()
    return {"order_no": order.order_no, "saved": True}


@router.post("/orders/{order_no}/reschedule", summary="改期（免费 1 次，PRD §6.2）")
def reschedule(order_no: str, payload: dict, staff: Staff = Depends(staff_auth),
               db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not belongs(order, staff.store_id):
        raise HTTPException(404, "订单不存在")
    if order.reschedule_count >= 1:
        raise HTTPException(422, "免费改期次数已用完，请联系店长")
    new_time = payload.get("expect_time")
    if not new_time:
        raise HTTPException(422, "缺少 expect_time")
    if order.status not in (OrderStatus.PENDING_CONFIRM, OrderStatus.BOOKED):
        raise HTTPException(422, "当前状态不可改期，请联系店长")
    next_time = datetime.fromisoformat(new_time)
    if next_time <= datetime.now():
        raise HTTPException(422, "改期时间必须晚于现在")
    order.expect_time = next_time
    order.reschedule_count += 1
    db.commit()
    return {"order_no": order.order_no, "expect_time": order.expect_time.isoformat(),
            "reschedule_count": order.reschedule_count}


@router.get("/refunds", summary="退款任务列表（V1.5：未接支付时人工闭环）")
def refund_tasks(status: str | None = "退款中",
                 staff: Staff = Depends(require_perm("order.refund")),
                 db: Session = Depends(get_db)):
    query = db.query(Order)
    clause = store_clause(Order, staff.store_id)
    if clause is not None:
        query = query.filter(clause)
    if status:
        query = query.filter(Order.refund_status == RefundStatus(status))
    else:
        query = query.filter(Order.refund_status != RefundStatus.NONE)
    rows = query.order_by(Order.updated_at.desc()).all()
    return [{
        "order_no": o.order_no,
        "status": o.status.value,
        "refund_status": o.refund_status.value,
        "pay_type": o.pay_type.value,
        "paid_amount": float(o.paid_amount),
        "total_amount": float(o.total_amount),
        "cancel_reason": o.cancel_reason,
        "updated_at": o.updated_at.isoformat(),
    } for o in rows]


@router.post("/orders/{order_no}/refund/mark", summary="标记退款完成/失败（人工退款任务闭环）")
def mark_refund(order_no: str, payload: dict,
                staff: Staff = Depends(require_perm("order.refund")),
                db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not belongs(order, staff.store_id):
        raise HTTPException(404, "订单不存在")
    try:
        order = payment_service.mark_refund(db, order_no, payload.get("status", ""), payload.get("note", ""))
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"order_no": order.order_no, "refund_status": order.refund_status.value,
            "notes": order.notes}


@router.post("/orders/{order_no}/media", summary="上传节点影像（强制流转证据，同步 C 端时间线）")
def upload_media(order_no: str, node: str, file: UploadFile,
                 staff: Staff = Depends(staff_auth), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not belongs(order, staff.store_id):
        raise HTTPException(404, "订单不存在")
    try:
        media = media_service.save_media(db, order, node, file.filename,
                                         file.file.read(), uploaded_by=staff.id)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"media_id": media.id, "node": media.node.value,
            "media_type": media.media_type.value, "url": media.url}


@router.post("/orders/{order_no}/settle", summary="到店付结清标记（实收金额落流水，B003）")
def settle(order_no: str, payload: dict, staff: Staff = Depends(staff_auth),
           db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not belongs(order, staff.store_id):
        raise HTTPException(404, "订单不存在")
    try:
        order = payment_service.settle_offline(db, order_no,
                                               float(payload.get("amount", 0)), staff_id=staff.id)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"order_no": order.order_no, "pay_type": order.pay_type.value,
            "paid_amount": float(order.paid_amount)}


@router.post("/media/{media_id}/revoke", summary="影像撤回（仅店长，强制原因留审计）")
def revoke_media(media_id: int, payload: dict,
                 staff: Staff = Depends(require_perm("media.revoke")),
                 db: Session = Depends(get_db)):
    try:
        media = media_service.revoke_media(db, media_id,
                                           True, payload.get("reason", ""))
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"media_id": media.id, "revoked": media.revoked}
