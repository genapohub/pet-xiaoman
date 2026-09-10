"""C 端鉴权依赖（软校验模式，对齐 WX_LOGIN_ENABLED 开关）：

- 请求头 X-Customer-Token 存在 → 解出 customer_id（无效 401）
- WX_LOGIN_ENABLED=true 且无 token → 401（强制模式）
- 否则返回 None（legacy 放行，路由回退到请求体 user_id）
"""
from fastapi import Header, HTTPException

from app.config import settings
from app.services.auth_service import verify_token


def customer_auth(x_customer_token: str | None = Header(default=None)) -> int | None:
    if x_customer_token:
        customer_id = verify_token(x_customer_token)
        if customer_id is None:
            raise HTTPException(401, "登录态无效或已过期，请重新登录")
        return customer_id
    if settings.WX_LOGIN_ENABLED:
        raise HTTPException(401, "请先登录")
    return None


def ensure_customer_match(token_customer_id: int | None, request_user_id: int | None) -> int:
    """token 优先解析身份；请求体 user_id 仅 legacy 模式（无 token）生效。"""
    if token_customer_id is None:
        if settings.WX_LOGIN_ENABLED:
            raise HTTPException(401, "请先登录")
        if not request_user_id:
            raise HTTPException(401, "缺少客户身份")
        return request_user_id
    if request_user_id and request_user_id != token_customer_id:
        raise HTTPException(403, "身份不匹配")
    return token_customer_id
