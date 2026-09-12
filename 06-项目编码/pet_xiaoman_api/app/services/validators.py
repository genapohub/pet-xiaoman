"""门店白标入参校验（唯一事实源）。

这些值会被前端直接拿去派生整套色阶 / 拼 URL / 渲染品牌，
脏值会让整站样式失效或资源 404，所以必须在入口拦下。
"""
import re

SLUG_RE = re.compile(r"^[A-Za-z0-9_-]{2,50}$")
HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

MAX_NAME = 50
MAX_SLOGAN = 50
MAX_LOGO_URL = 255


def valid_slug(v: str) -> str:
    """门店标识会进 URL 路径与二维码 → 只允许 URL 安全字符。"""
    v = (v or "").strip()
    if not SLUG_RE.match(v):
        raise ValueError("门店标识只能包含字母、数字、下划线与短横线（2-50 位）")
    return v


def valid_hex_color(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    if not HEX_COLOR_RE.match(v):
        raise ValueError("主题色需为十六进制色值，如 #5B8C85")
    return v


def valid_logo_url(v: str | None) -> str | None:
    """Logo 只接受站内路径或 http(s) 地址；空串表示清空（前端回落中性占位）。"""
    if v is None:
        return None
    v = v.strip()
    if not v:
        return ""
    if len(v) > MAX_LOGO_URL:
        raise ValueError(f"Logo 地址过长（≤{MAX_LOGO_URL} 字符）")
    if not (v.startswith("/") or v.startswith("http://") or v.startswith("https://")):
        raise ValueError("Logo 需为站内路径（如 /uploads/logo.png）或 http(s) 地址")
    return v


def valid_slogan(v: str | None) -> str | None:
    """标语：空串表示清空（前端不展示），而不是"未提供"。"""
    if v is None:
        return None
    v = v.strip()
    if len(v) > MAX_SLOGAN:
        raise ValueError(f"标语过长（≤{MAX_SLOGAN} 字）")
    return v
