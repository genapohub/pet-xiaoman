"""C 端登录（PRD：微信登录接入）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import customer_auth, store_context
from app.models.customer import Customer
from app.models.store_profile import StoreProfile
from app.services.auth_service import AuthError, login, phone_login, verify_token

router = APIRouter()


class LoginInput(BaseModel):
    code: str | None = Field(default=None, description="wx.login code（WX_LOGIN_ENABLED=true 时必填）")
    customer_id: int | None = Field(default=None, description="dev 模式：客户 id 直换 token")


class PhoneLoginInput(BaseModel):
    phone_code: str | None = Field(default=None, description="wx.getPhoneNumber 返回的 code（WX_LOGIN_ENABLED=true 时必填）")
    code: str | None = Field(default=None, description="wx.login code（用于绑定 openid，支付必需）")
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
        return phone_login(db, phone_code=payload.phone_code, code=payload.code,
                           dev_phone=payload.dev_phone,
                           store_id=store_id)
    except AuthError as e:
        raise HTTPException(422, str(e))


def _mask_phone(phone: str | None) -> str:
    if not phone:
        return ""
    return phone if len(phone) < 7 else f"{phone[:3]}****{phone[-4:]}"


@router.get("/auth/me", summary="当前登录客户（token 校验 + 个人中心资料）")
def me(customer_id: int | None = Depends(customer_auth),
       store_id: int | None = Depends(store_context),
       db: Session = Depends(get_db)):
    if customer_id is None:
        return {"logged_in": False}
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(401, "客户不存在，请重新登录")
    profile = None
    sid = store_id if store_id is not None else customer.store_id
    if sid is not None:
        profile = db.query(StoreProfile).filter(StoreProfile.store_id == sid).first()
    return {
        "logged_in": True,
        "customer_id": customer.id,
        "nickname": customer.nickname,
        "phone": customer.phone,
        "phone_masked": _mask_phone(customer.phone),
        "has_openid": bool(customer.openid),
        "store_id": customer.store_id,
        "current_store_id": sid,
        "store_name": profile.name if profile else "",
    }


class ProfileUpdateInput(BaseModel):
    nickname: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=20)


@router.put("/auth/me", summary="更新个人资料（昵称 / 手机号）")
def update_me(payload: ProfileUpdateInput,
              customer_id: int | None = Depends(customer_auth),
              db: Session = Depends(get_db)):
    """客户自助改昵称与手机号（C 端「资料编辑」页的数据落点）。

    只开放这两个字段：
      - `openid` 是登录凭据，改了会导致账号与微信身份脱钩；
      - `store_id` 决定门店归属，由登录/扫码流程绑定，允许客户改等于放开跨店。
    两者都必须走各自流程，不在本接口暴露。
    """
    if customer_id is None:
        raise HTTPException(401, "请先登录")
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(401, "客户不存在，请重新登录")
    if payload.nickname is not None:
        name = payload.nickname.strip()
        if not name:
            raise HTTPException(422, "昵称不能为空")
        customer.nickname = name
    if payload.phone is not None:
        # 去掉空格/短横线后再校验，避免用户按 138-0000-0000 输入被判非法
        phone = "".join(ch for ch in str(payload.phone) if ch.isdigit())
        if phone and (len(phone) != 11 or not phone.startswith("1")):
            raise HTTPException(422, "请输入 11 位手机号")
        customer.phone = phone
    db.commit()
    return {
        "customer_id": customer.id,
        "nickname": customer.nickname,
        "phone": customer.phone,
        "phone_masked": _mask_phone(customer.phone),
    }
