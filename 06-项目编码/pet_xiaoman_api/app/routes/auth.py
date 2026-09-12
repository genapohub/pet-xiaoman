"""C 端登录（PRD：微信登录接入）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import customer_auth, store_context
from app.services.auth_service import AuthError, login, phone_login, verify_token

router = APIRouter()


class LoginInput(BaseModel):
    code: str | None = Field(default=None, description="wx.login code（WX_LOGIN_ENABLED=true 时必填）")
    customer_id: int | None = Field(default=None, description="dev 模式：客户 id 直换 token")


class PhoneLoginInput(BaseModel):
    phone_code: str | None = Field(default=None, description="wx.getPhoneNumber 返回的 code（WX_LOGIN_ENABLED=true 时必填）")
    dev_phone: str | None = Field(default=None, description="dev 模式：直接传手机号兜底")


@router.post("/auth/login", summary="登录（code 换 token；开关关闭时 dev 模式）")
def login_route(payload: LoginInput, db: Session = Depends(get_db)):
    try:
        return login(db, code=payload.code, dev_customer_id=payload.customer_id)
    except AuthError as e:
        raise HTTPException(422, str(e))


@router.post("/auth/phone-login", summary="手机号一键登录（运营商授权手机号 / dev 兜底）")
def phone_login_route(payload: PhoneLoginInput, db: Session = Depends(get_db),
                      store_id: int | None = Depends(store_context)):
    try:
        return phone_login(db, phone_code=payload.phone_code, dev_phone=payload.dev_phone,
                           store_id=store_id)
    except AuthError as e:
        raise HTTPException(422, str(e))


@router.get("/auth/me", summary="当前登录客户（token 校验）")
def me(customer_id: int | None = Depends(customer_auth)):
    if customer_id is None:
        return {"logged_in": False}
    return {'logged_in': True, 'customer_id': customer_id}
