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
