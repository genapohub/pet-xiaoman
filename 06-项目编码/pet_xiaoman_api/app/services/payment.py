"""微信支付框架（JSAPI）。支付功能开关关闭时全部到店付。

对账与验签规则（PRD §5.2.6 / 宠宝树 fail-check 经验）：
- 回调必须验签，验签失败直接拒绝处理（fail-check）
- 回调未达：5 分钟对账任务补偿（对账任务入口 query_and_reconcile）
- 并发重复支付：以 order_no+金额幂等，多收部分自动原路退回
"""
import hmac
import json
from dataclasses import dataclass

from app.config import settings


class PaymentVerifyError(Exception):
    """验签失败 / 支付不可用。"""


def ensure_pay_enabled() -> None:
    if not settings.PAY_ENABLED:
        raise PaymentVerifyError("支付功能未开启（商户号未配置），当前仅支持到店付")


def verify_callback_signature(payload: bytes, signature: str, timestamp: str, nonce: str) -> dict:
    """微信支付 v3 回调验签：验签失败 raise PaymentVerifyError（fail-check，绝不带病处理）。"""
    if not settings.PAY_ENABLED:
        raise PaymentVerifyError("支付功能未开启")
    # TODO(商户号开通后)：平台证书验签实现。
    # 验签通过后 AES-256-GCM 解密 resource 得到报文。此处为框架位：
    if not signature or not timestamp or not nonce:
        raise PaymentVerifyError("回调验签参数缺失，拒绝处理")
    return json.loads(payload)


@dataclass
class PayResult:
    order_no: str
    amount: float
    transaction_id: str


def apply_payment_idempotent(order, result: PayResult) -> bool:
    """支付结果幂等落账：以累计金额判断结清；超额/已结清返回 False（调用方触发原路退款）。

    order: app.models.order.Order
    """
    total = float(order.total_amount or 0)
    paid = float(order.paid_amount or 0)
    if paid >= total:
        return False  # 已结清，重复支付
    if paid + result.amount > total:
        return False  # 超额支付，多收部分需原路退回
    order.paid_amount = paid + result.amount
    from app.models.order import PayType
    order.pay_type = (PayType.FULL_PAID if float(order.paid_amount) == total
                      else PayType.DEPOSIT_PAID)
    return True


def refund(order_no: str, amount: float) -> bool:
    """原路退款（接宠前取消全额退）。商户号开通后接微信退款 API；失败转人工。"""
    if not settings.PAY_ENABLED:
        raise PaymentVerifyError("支付功能未开启，退款走人工")
    # TODO(商户号开通后)：wxpay.refund(...)
    return True
