"""C 端登录（PRD：微信登录接入）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import customer_auth
from app.services.auth_service import AuthError, login, verify_token

router = APIRouter()


class LoginInput(BaseModel):
    code: str | None = Field(default=None, description="wx.login code（WX_LOGIN_ENABLED=true 时必填）")
    customer_id: int | None = Field(default=None, description="dev 模式：客户 id 直换 token")


@router.post("/auth/login", summary="登录（code 换 token；开关关闭时 dev 模式）")
def login_route(payload: LoginInput, db: Session = Depends(get_db)):
    try:
        return login(db, code=payload.code, dev_customer_id=payload.customer_id)
    except AuthError as e:
        raise HTTPException(422, str(e))


@router.get("/auth/me", summary="当前登录客户（token 校验）")
def me(customer_id: int | None = Depends(customer_auth)):
    if customer_id is None:
        return {"logged_in": False}
    return {'logged_in': True, 'customer_id': customer_id}
