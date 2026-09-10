"""微信支付回调入口（PRD §5.2.6）：验签 fail-check，绝不带病处理。

商户号开通后（PAY_ENABLED=true）此接口才会真正落账；关闭时验签层直接拒绝。
"""
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import payment_service

router = APIRouter()


@router.post("/notify/wechat", summary="微信支付回调（验签失败拒绝处理，幂等落账）")
async def wechat_notify(request: Request,
                        signature: str = Header(default=""),
                        timestamp: str = Header(default=""),
                        nonce: str = Header(default=""),
                        db: Session = Depends(get_db)):
    body = await request.body()
    try:
        result = payment_service.handle_pay_callback(db, body, signature, timestamp, nonce)
    except PermissionError as e:
        return {"code": "FAIL", "message": str(e)}
    except ValueError as e:
        return {"code": "FAIL", "message": str(e)}
    return {"code": "SUCCESS", "message": "OK", **result}
