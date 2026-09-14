"""支付业务落账（PRD §5.2.6）：验签 → 幂等落账 → 订单支付状态更新。

payment.py 是微信协议框架（验签/开关），本模块是业务侧。
"""
from sqlalchemy.orm import Session

from app.models.order import Order, PayType, RefundStatus
from app.models.payment_record import BizType, PayStatus, PaymentRecord
from app.services import payment as pay_framework
from app.services.payment import PaymentVerifyError, PayResult


def apply_payment(db: Session, order: Order, result: PayResult) -> dict:
    """幂等落账（业务入口，可由回调或线下补录驱动）：流水 + 订单支付状态。"""
    exists = (db.query(PaymentRecord)
              .filter(PaymentRecord.transaction_id == result.transaction_id).first())
    if exists:
        return {"order_no": order.order_no, "duplicated": True}
    applied = pay_framework.apply_payment_idempotent(order, result)
    db.add(PaymentRecord(order_id=order.id, biz_type=BizType.FULL if applied else BizType.FULL,
                         amount=result.amount, transaction_id=result.transaction_id,
                         pay_status=PayStatus.REFUNDED if not applied else PayStatus.SUCCESS))
    db.commit()
    return {"order_no": order.order_no, "pay_type": order.pay_type.value,
            "paid_amount": float(order.paid_amount), "duplicated": not applied}


def handle_pay_callback(db: Session, payload: bytes, signature: str,
                        timestamp: str, nonce: str, serial: str = "") -> dict:
    """微信回调处理：验签 fail-check → 幂等落账。"""
    try:
        data = pay_framework.verify_callback_signature(payload, signature, timestamp, nonce, serial)
    except PaymentVerifyError as e:
        # fail-check：绝不带病处理
        raise PermissionError(f"回调验签失败：{e}")
    if data.get("trade_state") and data.get("trade_state") != "SUCCESS":
        raise ValueError(f"支付状态未成功: {data.get('trade_state')}")
    order = db.query(Order).filter(Order.order_no == data["order_no"]).first()
    if not order:
        raise ValueError(f"回调订单不存在: {data['order_no']}")
    return apply_payment(db, order,
                         PayResult(order_no=order.order_no, amount=float(data["amount"]),
                                   transaction_id=data["transaction_id"]))


def settle_offline(db: Session, order_no: str, amount: float, staff_id: int) -> Order:
    """到店付结清（B 端标记）：实收金额落流水，pay_type → 到店付已结清。"""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise ValueError("订单不存在")
    if order.pay_type == PayType.FULL_PAID:
        raise ValueError("订单已全款支付，无需到店结清")
    remain = float(order.total_amount or 0) - float(order.paid_amount or 0)
    if amount < remain:
        raise ValueError(f"实收金额不足：应收尾款 {remain} 元")
    db.add(PaymentRecord(order_id=order.id, biz_type=BizType.TAIL, amount=amount,
                         transaction_id=f"OFFLINE-{order.order_no}-{int(amount)}",
                         pay_status=PayStatus.SUCCESS))
    order.pay_type = PayType.SETTLED_OFFLINE
    order.paid_amount = float(order.paid_amount or 0) + amount
    order.refund_status = RefundStatus.NONE
    db.commit()
    db.refresh(order)
    return order


def mark_refund(db: Session, order_no: str, status: str, note: str = "") -> Order:
    """人工退款闭环：商户号未接入时，由后台记录退款完成/失败。"""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise ValueError("订单不存在")
    if order.refund_status == RefundStatus.NONE:
        raise ValueError("该订单没有待处理退款")
    try:
        next_status = RefundStatus(status)
    except ValueError as exc:
        raise ValueError("退款状态只能标记为「已退款」或「退款失败」") from exc
    if next_status not in (RefundStatus.REFUNDED, RefundStatus.FAILED):
        raise ValueError("退款状态只能标记为「已退款」或「退款失败」")

    order.refund_status = next_status
    if next_status == RefundStatus.REFUNDED:
        records = (db.query(PaymentRecord)
                   .filter(PaymentRecord.order_id == order.id,
                           PaymentRecord.pay_status == PayStatus.SUCCESS)
                   .all())
        for record in records:
            record.pay_status = PayStatus.REFUNDED
    if note:
        prefix = f"{order.notes}\n" if order.notes else ""
        order.notes = f"{prefix}[退款处理] {note}"
    db.commit()
    db.refresh(order)
    return order


def query_and_reconcile(db: Session) -> dict:
    """对账任务入口（5 分钟调度，云托管定时任务触发）：支付开关关闭时空转。"""
    if not pay_framework.settings.PAY_ENABLED:
        return {"skipped": "支付未开启"}
    # TODO(商户号开通后)：拉微信账单 vs payment_records 逐笔核对，差异落告警
    return {"checked": 0}
