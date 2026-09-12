"""后台员工登录（账号密码 + 登录态管理）。

与 C 端微信登录解耦：
- 凭证 = 账号 + 密码（bcrypt 级强度用 pbkdf2_hmac 替代，零额外依赖）。
- token = HMAC 签名（`s{staff_id}.{exp}.{sig}`），namespace 用 `s` 与 C 端区分。
- 员工处于停用状态 → 拒绝登录 / 校验失败。
"""
import hashlib
import hmac
import secrets
import time

from sqlalchemy.orm import Session

from app.config import settings
from app.models.staff import Staff, StaffStatus

TOKEN_TTL_DAYS = 7


class StaffAuthError(Exception):
    """登录失败（账号密码错 / 已停用 / 配置缺失）。"""


# ---------- 密码 ----------
def hash_password(pw: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), bytes.fromhex(salt), 100_000)
    return f"pbkdf2_sha256$100000${salt}${dk.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        _, iter_s, salt, hash_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), bytes.fromhex(salt), int(iter_s))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


# ---------- token ----------
def _secret() -> str:
    # STAFF_TOKEN_SECRET 未配置时用开发兜底值（生产务必显式配置）
    return settings.STAFF_TOKEN_SECRET or "pet_xiaoman-dev-staff-secret"


def create_staff_token(staff_id: int) -> str:
    exp = int(time.time()) + TOKEN_TTL_DAYS * 86400
    payload = f"s{staff_id}.{exp}"
    sig = hmac.new(_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{payload}.{sig}"


def verify_staff_token(token: str) -> int | None:
    """无效/过期返回 None。"""
    try:
        head, exp, sig = token.split(".")
        if not head.startswith("s"):
            return None
        staff_id = int(head[1:])
        payload = f"{head}.{exp}"
        expect = hmac.new(_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, expect):
            return None
        if int(exp) < time.time():
            return None
        return staff_id
    except Exception:
        return None


# ---------- 登录 ----------
def login_staff(db: Session, username: str, password: str) -> Staff:
    staff = db.query(Staff).filter(Staff.username == username).first()
    if not staff or staff.status != StaffStatus.ACTIVE or not verify_password(password, staff.password_hash):
        raise StaffAuthError("账号或密码错误")
    return staff
