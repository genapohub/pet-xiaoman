"""微信支付框架（JSAPI）。支付功能开关关闭时全部到店付。

对账与验签规则（PRD §5.2.6 / 宠宝树 fail-check 经验）：
- 回调必须验签，验签失败直接拒绝处理（fail-check）
- 回调未达：5 分钟对账任务补偿（对账任务入口 query_and_reconcile）
- 并发重复支付：以 order_no+金额幂等，多收部分自动原路退回
"""
import base64
import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from cryptography.exceptions import InvalidSignature
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


class PaymentVerifyError(Exception):
    """验签失败 / 支付不可用。"""


def ensure_pay_enabled() -> None:
    if not settings.PAY_ENABLED:
        raise PaymentVerifyError("支付功能未开启（商户号未配置），当前仅支持到店付")
    missing = missing_pay_config()
    if missing:
        raise PaymentVerifyError(f"微信支付配置缺失：{', '.join(missing)}")


def _private_key_pem() -> str:
    if settings.WX_PAY_PRIVATE_KEY:
        return settings.WX_PAY_PRIVATE_KEY.replace("\\n", "\n")
    if settings.WX_PAY_PRIVATE_KEY_PATH:
        path = Path(settings.WX_PAY_PRIVATE_KEY_PATH).expanduser()
        if path.exists():
            return path.read_text(encoding="utf8")
    return ""


def missing_pay_config() -> list[str]:
    """返回启动正式支付还缺哪些配置。"""
    required = [
        ("WX_APPID", settings.WX_APPID),
        ("WX_MCH_ID", settings.WX_MCH_ID),
        ("WX_PAY_SERIAL_NO", settings.WX_PAY_SERIAL_NO),
        ("WX_PAY_NOTIFY_URL", settings.WX_PAY_NOTIFY_URL),
        ("WX_PAY_API_V3_KEY", settings.WX_PAY_API_V3_KEY),
    ]
    missing = [name for name, value in required if not value]
    if not _private_key_pem():
        missing.append("WX_PAY_PRIVATE_KEY 或 WX_PAY_PRIVATE_KEY_PATH")
    return missing


def pay_config_status() -> dict:
    missing = missing_pay_config() if settings.PAY_ENABLED else []
    return {
        "pay_enabled": settings.PAY_ENABLED,
        "ready": settings.PAY_ENABLED and not missing,
        "missing": missing,
        "mch_id": settings.WX_MCH_ID,
        "appid": settings.WX_APPID,
        "notify_url": settings.WX_PAY_NOTIFY_URL,
    }


def _load_private_key():
    try:
        return serialization.load_pem_private_key(_private_key_pem().encode(), password=None)
    except Exception as exc:
        raise PaymentVerifyError("商户私钥读取失败，请检查 WX_PAY_PRIVATE_KEY_PATH / WX_PAY_PRIVATE_KEY") from exc


def _rsa_sign(message: str) -> str:
    signature = _load_private_key().sign(
        message.encode("utf8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf8")


def _authorization(method: str, url_path: str, body: str) -> str:
    timestamp = str(int(time.time()))
    nonce = secrets.token_hex(16)
    message = f"{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n"
    signature = _rsa_sign(message)
    return (
        'WECHATPAY2-SHA256-RSA2048 '
        f'mchid="{settings.WX_MCH_ID}",'
        f'nonce_str="{nonce}",'
        f'timestamp="{timestamp}",'
        f'serial_no="{settings.WX_PAY_SERIAL_NO}",'
        f'signature="{signature}"'
    )


def _jsapi_pay_sign(prepay_id: str, timestamp: str, nonce: str) -> str:
    package_value = f"prepay_id={prepay_id}"
    message = f"{settings.WX_APPID}\n{timestamp}\n{nonce}\n{package_value}\n"
    return _rsa_sign(message)


def verify_callback_signature(payload: bytes, signature: str, timestamp: str,
                              nonce: str, serial: str = "") -> dict:
    """微信支付 v3 回调验签：验签失败 raise PaymentVerifyError（fail-check，绝不带病处理）。"""
    ensure_pay_enabled()
    if not signature or not timestamp or not nonce:
        raise PaymentVerifyError("回调验签参数缺失，拒绝处理")
    if not settings.WX_PAY_PLATFORM_CERT_PATH:
        raise PaymentVerifyError("缺少 WX_PAY_PLATFORM_CERT_PATH，无法验签微信支付回调")
    cert_path = Path(settings.WX_PAY_PLATFORM_CERT_PATH).expanduser()
    if not cert_path.exists():
        raise PaymentVerifyError("微信支付平台证书文件不存在")
    cert_bytes = cert_path.read_bytes()
    try:
        cert = x509.load_pem_x509_certificate(cert_bytes).public_key()
    except ValueError:
        cert = serialization.load_pem_public_key(cert_bytes)
    message = f"{timestamp}\n{nonce}\n{payload.decode('utf8')}\n".encode("utf8")
    try:
        cert.verify(base64.b64decode(signature), message, padding.PKCS1v15(), hashes.SHA256())
    except (InvalidSignature, ValueError) as exc:
        raise PaymentVerifyError(f"回调签名不可信 serial={serial}") from exc

    data = json.loads(payload)
    resource = data.get("resource")
    if not resource:
        return data
    decrypted = _decrypt_callback_resource(resource)
    amount = decrypted.get("amount", {}).get("total", 0)
    return {
        "order_no": decrypted.get("out_trade_no"),
        "amount": round(float(amount) / 100, 2),
        "transaction_id": decrypted.get("transaction_id"),
        "trade_state": decrypted.get("trade_state"),
    }


def _decrypt_callback_resource(resource: dict) -> dict:
    key = settings.WX_PAY_API_V3_KEY.encode("utf8")
    if len(key) != 32:
        raise PaymentVerifyError("WX_PAY_API_V3_KEY 必须为 32 位")
    aad = (resource.get("associated_data") or "").encode("utf8")
    nonce = (resource.get("nonce") or "").encode("utf8")
    ciphertext = base64.b64decode(resource.get("ciphertext") or "")
    text = AESGCM(key).decrypt(nonce, ciphertext, aad)
    return json.loads(text.decode("utf8"))


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


def create_jsapi_params(order_no: str, amount: float, openid: str | None = None,
                        description: str = "宠物善终服务") -> dict:
    """创建小程序 JSAPI 支付参数。

    走微信支付 v3 JSAPI 下单，返回 wx.requestPayment 所需参数。
    """
    ensure_pay_enabled()
    if not openid:
        raise PaymentVerifyError("缺少 openid，无法发起微信支付")
    total = int(round(float(amount) * 100))
    if total <= 0:
        raise PaymentVerifyError("支付金额必须大于 0")
    url_path = "/v3/pay/transactions/jsapi"
    body = {
        "appid": settings.WX_APPID,
        "mchid": settings.WX_MCH_ID,
        "description": description[:127],
        "out_trade_no": order_no,
        "notify_url": settings.WX_PAY_NOTIFY_URL,
        "amount": {"total": total, "currency": "CNY"},
        "payer": {"openid": openid},
    }
    body_text = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    headers = {
        "Authorization": _authorization("POST", url_path, body_text),
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "pet-xiaoman/1.0",
    }
    try:
        resp = httpx.post(f"{settings.WX_PAY_API_BASE}{url_path}", content=body_text,
                          headers=headers, timeout=10)
    except httpx.HTTPError as exc:
        raise PaymentVerifyError("微信支付下单网络异常，请稍后重试") from exc
    if resp.status_code >= 300:
        try:
            error = resp.json()
        except Exception:
            error = {"message": resp.text}
        raise PaymentVerifyError(f"微信支付下单失败：{error.get('message') or error}")
    prepay_id = resp.json().get("prepay_id")
    if not prepay_id:
        raise PaymentVerifyError("微信支付下单失败：未返回 prepay_id")
    ts = str(int(time.time()))
    nonce = secrets.token_hex(16)
    package_value = f"prepay_id={prepay_id}"
    return {
        "timeStamp": ts,
        "nonceStr": nonce,
        "package": package_value,
        "signType": "RSA",
        "paySign": _jsapi_pay_sign(prepay_id, ts, nonce),
        "amount": amount,
        "prepay_id": prepay_id,
    }
