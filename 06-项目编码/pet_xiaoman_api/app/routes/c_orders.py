"""C 端订单路由（PRD §5.2.1）：提交预约 / 我的订单 / 订单详情 / 客户取消。

业务规则在 services/order_service.py；登录态由鉴权中间件注入 user_id（当前骨架期
接受请求体 user_id，微信登录接入后改为从 token 解出，路由签名不变）。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import customer_auth, ensure_customer_match, store_context
from app.models.order import Order
from app.services import media_service, order_service
from app.services.order_service import BusinessError
from app.services.tenant import belongs, store_clause

router = APIRouter()


class OrderCreateInput(BaseModel):
    user_id: int | None = Field(default=None, description="legacy 模式传；登录后由 token 解出")
    pet_name: str = Field(max_length=30, description="宠物名字（必填）")
    species: str = Field(default="犬", description="犬/猫/兔/其他")
    weight: float | None = Field(default=None, ge=0, le=200, description="kg，影响火化计价")
    pkg_id: int = Field(description="套餐 id")
    addon_ids: list[int] = Field(default_factory=list, description="加购项 id 列表")
    expect_time: datetime = Field(description="期望服务时间，精确到小时")
    address: str | None = Field(default=None, max_length=200, description="接送地址（自送可空）")


def _order_brief(o: Order) -> dict:
    return {
        "order_no": o.order_no,
        "status": o.status.value if hasattr(o.status, "value") else o.status,
        "pet_id": o.pet_id,
        "pkg_id": o.pkg_id,
        "total_amount": float(o.total_amount),
        "pay_type": o.pay_type.value if hasattr(o.pay_type, "value") else o.pay_type,
        "paid_amount": float(o.paid_amount),
        "is_night": bool(o.is_night),
        "expect_time": o.expect_time.isoformat(),
        "created_at": o.created_at.isoformat(),
    }


@router.post("/orders", summary="提交预约（价格按下单时刻版本锁定，PRD §5.2.1）")
def create_order(payload: OrderCreateInput, db: Session = Depends(get_db),
                 token_customer_id: int | None = Depends(customer_auth),
                 store_id: int | None = Depends(store_context)):
    payload.user_id = ensure_customer_match(token_customer_id, payload.user_id)
    try:
        order = order_service.create_order(db, payload, store_id=store_id)
    except BusinessError as e:
        raise HTTPException(422, str(e))
    return {
        "order_no": order.order_no,
        "status": order.status.value,
        "is_night": bool(order.is_night),
        "total_amount": float(order.total_amount),
        "price_version": order.price_version,
        "message": "已提交，门店将在 30 分钟内确认",
    }


@router.get("/orders", summary="我的订单（按创建时间倒序）")
def list_orders(user_id: int, db: Session = Depends(get_db),
                token_customer_id: int | None = Depends(customer_auth),
                store_id: int | None = Depends(store_context)):
    user_id = ensure_customer_match(token_customer_id, user_id)
    query = db.query(Order).filter(Order.user_id == user_id)
    clause = store_clause(Order, store_id)
    if clause is not None:
        query = query.filter(clause)
    orders = query.order_by(Order.created_at.desc()).all()
    return [_order_brief(o) for o in orders]


@router.get("/orders/{order_no}", summary="订单详情（C006 进度时间线数据源）")
def get_order(order_no: str, db: Session = Depends(get_db),
              store_id: int | None = Depends(store_context)):
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not belongs(order, store_id):
        raise HTTPException(404, "订单不存在")
    return {
        **_order_brief(order),
        "price_version": order.price_version,
        "addons": order.addons or [],
        "cancel_reason": order.cancel_reason,
        "reschedule_count": order.reschedule_count,
        "reschedule_quota_left": max(0, 1 - order.reschedule_count),
    }


@router.post("/orders/{order_no}/cancel", summary="客户取消（待确认/已预约可取消；已付自动转退款）")
def cancel_order(order_no: str, payload: dict, db: Session = Depends(get_db),
                 store_id: int | None = Depends(store_context)):
    existing = db.query(Order).filter(Order.order_no == order_no).first()
    if not belongs(existing, store_id):
        raise HTTPException(404, "订单不存在")
    try:
        order = order_service.cancel_by_customer(db, order_no, payload.get("reason", ""))
    except BusinessError as e:
        raise HTTPException(422, str(e))
    refunded = order.refund_status.value == "退款中"
    return {
        "order_no": order.order_no,
        "status": order.status.value,
        "refund_status": order.refund_status.value,
        "message": "已取消" + ("，已付金额将原路退回（1-3 个工作日）" if refunded else ""),
    }


@router.post("/orders/{order_no}/reschedule", summary="客户免费改期一次（PRD §6.2，仅对本店订单生效）")
def reschedule(order_no: str, payload: dict, db: Session = Depends(get_db),
               store_id: int | None = Depends(store_context)):
    """C 端改期：免费 1 次，与 B 端 `/api/b/orders/{no}/reschedule` 共享配额 `reschedule_count`。

    安全：
      - 走 store 隔离（belongs 校验），跨店改期直接 404
      - 超过 1 次返 422（前端友好提示「请联系店长」）
      - 不允许改到过去时间（业务校验在 order_service.reschedule_by_customer）
    """
    existing = db.query(Order).filter(Order.order_no == order_no).first()
    if not belongs(existing, store_id):
        raise HTTPException(404, "订单不存在")
    new_time = payload.get("expect_time")
    if not new_time:
        raise HTTPException(422, "缺少 expect_time")
    try:
        dt = datetime.fromisoformat(str(new_time).replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        order = order_service.reschedule_by_customer(db, order_no, dt)
    except BusinessError as e:
        raise HTTPException(422, str(e))
    except ValueError:
        raise HTTPException(422, "改期时间格式不正确")
    return {"order_no": order.order_no, "expect_time": order.expect_time.isoformat(),
            "reschedule_count": order.reschedule_count,
            "reschedule_quota_left": max(0, 1 - order.reschedule_count)}


@router.get("/orders/{order_no}/media", summary="订单影像（C006 时间线数据源，不含已撤回）")
def list_media(order_no: str, db: Session = Depends(get_db),
               store_id: int | None = Depends(store_context)):
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not belongs(order, store_id):
        raise HTTPException(404, "订单不存在")
    return media_service.list_order_media(db, order)
