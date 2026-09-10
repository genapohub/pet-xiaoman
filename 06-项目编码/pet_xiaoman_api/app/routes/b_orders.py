"""B 端订单路由（PRD §5.1 B002/B003）：列表筛选、确认、状态流转。

角色控制（PRD §8.5）：当前骨架期信任 payload.role，鉴权中间件接入后从 token 解出。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order, OrderStatus
from app.services import media_service, order_service, payment_service
from app.services.order_service import BusinessError
from app.services.order_state import TransitionContext

router = APIRouter()


@router.get("/orders", summary="订单列表（B002：状态/日期/夜间单/关键词筛选 + 分页）")
def list_orders(status: str | None = None,
                date: str | None = None,
                is_night: bool | None = None,
                keyword: str | None = None,
                page: int = 1, size: int = 20,
                db: Session = Depends(get_db)):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == OrderStatus(status))
    if date:
        query = query.filter(Order.expect_time.like(f"{date}%"))
    if is_night is not None:
        query = query.filter(Order.is_night == is_night)
    if keyword:
        query = query.filter(Order.order_no.like(f"%{keyword}%"))
    total = query.count()
    rows = (query.order_by(Order.created_at.desc())
            .offset((page - 1) * size).limit(size).all())
    return {
        "total": total,
        "items": [{
            "order_no": o.order_no,
            "status": o.status.value,
            "total_amount": float(o.total_amount),
            "is_night": bool(o.is_night),
            "expect_time": o.expect_time.isoformat(),
            "created_at": o.created_at.isoformat(),
        } for o in rows],
    }


@router.post("/orders/{order_no}/confirm", summary="确认订单（待确认→已预约，SLA 30 分钟）")
def confirm_order(order_no: str, payload: dict, db: Session = Depends(get_db)):
    return _transition(order_no, {"target": OrderStatus.BOOKED.value}, db)


@router.post("/orders/{order_no}/transition", summary="状态流转（强制影像=服务端查库校验，结清校验在状态机内）")
def transition(order_no: str, payload: dict, db: Session = Depends(get_db)):
    return _transition(order_no, payload, db)


def _transition(order_no: str, payload: dict, db: Session) -> dict:
    target = payload.get("target")
    if not target:
        raise HTTPException(422, "缺少 target 状态")
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    # 强制影像：服务端查 service_media 表，不信任前端 has_media 参数（PRD §5.2.2）
    ctx = TransitionContext(
        has_media=media_service.node_media_satisfied(db, order.id, target),
        pay_type=order.pay_type.value if hasattr(order.pay_type, "value") else str(order.pay_type),
        is_owner=payload.get("role") == "店长",
    )
    try:
        order = order_service.transition(db, order_no, target, ctx)
    except BusinessError as e:
        raise HTTPException(422, str(e))
    return {"order_no": order.order_no, "status": order.status.value,
            "message": f"已流转至「{order.status.value}」"}


@router.get("/orders/{order_no}", summary="订单详情（B003：全字段 + 影像 + 备注）")
def get_order_detail(order_no: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
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
def save_notes(order_no: str, payload: dict, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    order.notes = payload.get("notes", "")
    db.commit()
    return {"order_no": order.order_no, "saved": True}


@router.post("/orders/{order_no}/reschedule", summary="改期（免费 1 次，PRD §6.2）")
def reschedule(order_no: str, payload: dict, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.reschedule_count >= 1:
        raise HTTPException(422, "免费改期次数已用完，请联系店长")
    new_time = payload.get("expect_time")
    if not new_time:
        raise HTTPException(422, "缺少 expect_time")
    order.expect_time = datetime.fromisoformat(new_time)
    order.reschedule_count += 1
    db.commit()
    return {"order_no": order.order_no, "expect_time": order.expect_time.isoformat(),
            "reschedule_count": order.reschedule_count}


@router.post("/orders/{order_no}/media", summary="上传节点影像（强制流转证据，同步 C 端时间线）")
def upload_media(order_no: str, node: str, file: UploadFile, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    try:
        media = media_service.save_media(db, order, node, file.filename,
                                         file.file.read(), uploaded_by=1)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"media_id": media.id, "node": media.node.value,
            "media_type": media.media_type.value, "url": media.url}


@router.post("/orders/{order_no}/settle", summary="到店付结清标记（实收金额落流水，B003）")
def settle(order_no: str, payload: dict, db: Session = Depends(get_db)):
    try:
        order = payment_service.settle_offline(db, order_no,
                                               float(payload.get("amount", 0)), staff_id=1)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"order_no": order.order_no, "pay_type": order.pay_type.value,
            "paid_amount": float(order.paid_amount)}


@router.post("/media/{media_id}/revoke", summary="影像撤回（仅店长，强制原因留审计）")
def revoke_media(media_id: int, payload: dict, db: Session = Depends(get_db)):
    try:
        media = media_service.revoke_media(db, media_id,
                                           payload.get("role") == "店长",
                                           payload.get("reason", ""))
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"media_id": media.id, "revoked": media.revoked}
