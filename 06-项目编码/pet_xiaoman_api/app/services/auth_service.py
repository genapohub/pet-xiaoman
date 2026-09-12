"""微信登录（PRD §10 外部依赖之一）：code2session + HMAC 签名 token。

开关模式（与 PAY_ENABLED 同设计）：
- WX_LOGIN_ENABLED=false：/auth/login 仅支持 dev 模式（customer_id 直换 token，本地联调用），
  C 端存量接口不强制 token；
- true：code 必填，走微信 code2session，openid 绑定客户，存量接口 401 强制。
"""
import hashlib
import hmac
import json
import time
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.customer import Customer

TOKEN_TTL_DAYS = 30


class AuthError(Exception):
    """登录失败（code 无效/开关关闭/配置缺失）。"""


def code_to_session(code: str) -> str:
    """wx.login code → openid。"""
    if not settings.WX_LOGIN_ENABLED:
        raise AuthError("微信登录未开启（WX_LOGIN_ENABLED=false）")
    if not (settings.WX_APPID and settings.WX_SECRET):
        raise AuthError("微信登录配置缺失（WX_APPID/WX_SECRET）")
    resp = httpx.get("https://api.weixin.qq.com/sns/jscode2session",
                     params={"appid": settings.WX_APPID, "secret": settings.WX_SECRET,
                             "js_code": code, "grant_type": "authorization_code"},
                     timeout=10)
    data = resp.json()
    if "openid" not in data:
        # fail-check：errcode/errmsg 原样带回，不带病继续
        raise AuthError(f"code2session 失败：{data.get('errcode')} {data.get('errmsg', '')}")
    return data["openid"]


def _token_secret() -> str:
    # TOKEN_SECRET 未配置时用开发兜底值（生产环境务必显式配置）
    return settings.TOKEN_SECRET or "pet_xiaoman-dev-token-secret"


def create_token(customer_id: int) -> str:
    exp = int(time.time()) + TOKEN_TTL_DAYS * 86400
    payload = f"{customer_id}.{exp}"
    sig = hmac.new(_token_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{payload}.{sig}"


def verify_token(token: str) -> int | None:
    """无效/过期返回 None。"""
    try:
        customer_id, exp, sig = token.split(".")
        payload = f"{customer_id}.{exp}"
        expect = hmac.new(_token_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, expect):
            return None
        if int(exp) < time.time():
            return None
        return int(customer_id)
    except Exception:
        return None


def login(db: Session, code: str | None = None, dev_customer_id: int | None = None) -> dict:
    """登录入口：开关开走 code，关走 dev_customer_id。返回 token + 客户信息。"""
    if settings.WX_LOGIN_ENABLED:
        if not code:
            raise AuthError("缺少 code")
        openid = code_to_session(code)
        customer = db.query(Customer).filter(Customer.openid == openid).first()
        if not customer:
            customer = Customer(nickname="微信用户", openid=openid)
            db.add(customer)
            db.commit()
            db.refresh(customer)
        else:
            customer.updated_at = datetime.now()
            db.commit()
    else:
        if not dev_customer_id:
            raise AuthError("微信登录未开启：请提供 customer_id（dev 模式）或开启 WX_LOGIN_ENABLED")
        customer = db.get(Customer, dev_customer_id)
        if not customer:
            raise AuthError("客户不存在")
    return {"token": create_token(customer.id), "customer_id": customer.id,
            "nickname": customer.nickname}


def get_access_token() -> str:
    """client_credential 换 access_token（用于手机号解密等需服务端凭证的接口）。"""
    if not (settings.WX_APPID and settings.WX_SECRET):
        raise AuthError("微信登录配置缺失（WX_APPID/WX_SECRET）")
    resp = httpx.get("https://api.weixin.qq.com/cgi-bin/token",
                     params={"grant_type": "client_credential",
                             "appid": settings.WX_APPID, "secret": settings.WX_SECRET},
                     timeout=10)
    data = resp.json()
    if "access_token" not in data:
        raise AuthError(f"获取 access_token 失败：{data.get('errcode')} {data.get('errmsg', '')}")
    return data["access_token"]


def get_phone_number(phone_code: str) -> str:
    """getPhoneNumber code → 纯手机号（需 access_token）。"""
    token = get_access_token()
    resp = httpx.post("https://api.weixin.qq.com/wxa/business/getuserphonenumber",
                      params={"access_token": token}, json={"code": phone_code}, timeout=10)
    data = resp.json()
    if data.get("errcode", 0) != 0 or "phone_info" not in data:
        raise AuthError(f"获取手机号失败：{data.get('errcode')} {data.get('errmsg', '')}")
    return data["phone_info"]["pure_phone_number"]


def phone_login(db: Session, phone_code: str | None = None, dev_phone: str | None = None,
                store_id: int | None = None) -> dict:
    """手机号一键登录：运营商授权手机号（prod）或 dev 手机号（本地）。按手机号找/建客户。

    多租户：同一手机号在不同门店各建一条客户档案（各店数据独立），故按 store_id 隔离查找。
    store_id 为空时退回 legacy 单店行为（不按店过滤）。
    """
    if settings.WX_LOGIN_ENABLED:
        if not phone_code:
            raise AuthError("缺少手机号授权 code")
        phone = get_phone_number(phone_code)
    else:
        if not dev_phone:
            raise AuthError("微信登录未开启：请提供 dev_phone（本地联调）或开启 WX_LOGIN_ENABLED")
        phone = dev_phone
    query = db.query(Customer).filter(Customer.phone == phone)
    if store_id is not None:
        query = query.filter(Customer.store_id == store_id)
    customer = query.first()
    if not customer:
        customer = Customer(nickname="微信用户", phone=phone, store_id=store_id)
        db.add(customer)
        db.commit()
        db.refresh(customer)
    else:
        customer.updated_at = datetime.now()
        db.commit()
    return {"token": create_token(customer.id), "customer_id": customer.id, "nickname": customer.nickname}
