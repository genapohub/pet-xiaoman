"""微信支付回调入口（PRD §5.2.6）：验签 fail-check，绝不带病处理。

商户号开通后（PAY_ENABLED=true）此接口才会真正落账；关闭时验签层直接拒绝。
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import customer_auth, store_context
from app.models.customer import Customer
from app.models.order import Order
from app.services import payment as pay_framework, payment_service
from app.services.payment import PaymentVerifyError
from app.services.tenant import belongs

router = APIRouter()


@router.get("/config", summary="微信支付配置状态（只返回是否就绪，不泄露密钥）")
def pay_config():
    return pay_framework.pay_config_status()


@router.post("/jsapi", summary="C012 拉起微信支付参数（支付开关关闭时返回明确提示）")
def jsapi_prepay(payload: dict,
                 customer_id: int | None = Depends(customer_auth),
                 store_id: int | None = Depends(store_context),
                 db: Session = Depends(get_db)):
    order_no = payload.get("order_no")
    pay_type = payload.get("pay_type", "full")
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not belongs(order, store_id):
        from fastapi import HTTPException
        raise HTTPException(404, "订单不存在")
    customer = db.get(Customer, customer_id) if customer_id else None
    if not customer or customer.id != order.user_id:
        from fastapi import HTTPException
        raise HTTPException(401, "请先登录后再支付")
    total = float(order.total_amount or 0)
    paid = float(order.paid_amount or 0)
    if pay_type == "deposit":
        amount = min(max(round(total * 0.2, 2), 100 if total else 0), max(total - paid, 0))
    else:
        amount = max(total - paid, 0)
    try:
        return pay_framework.create_jsapi_params(
            order.order_no, amount, customer.openid, description=f"宠物善终服务-{order.order_no}"
        )
    except PaymentVerifyError as e:
        from fastapi import HTTPException
        raise HTTPException(422, str(e))


@router.post("/notify/wechat", summary="微信支付回调（验签失败拒绝处理，幂等落账）")
async def wechat_notify(request: Request,
                        db: Session = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("Wechatpay-Signature") or request.headers.get("signature", "")
    timestamp = request.headers.get("Wechatpay-Timestamp") or request.headers.get("timestamp", "")
    nonce = request.headers.get("Wechatpay-Nonce") or request.headers.get("nonce", "")
    serial = request.headers.get("Wechatpay-Serial") or request.headers.get("serial", "")
    try:
        result = payment_service.handle_pay_callback(db, body, signature, timestamp, nonce, serial)
    except PermissionError as e:
        return {"code": "FAIL", "message": str(e)}
    except ValueError as e:
        return {"code": "FAIL", "message": str(e)}
    return {"code": "SUCCESS", "message": "OK", **result}
