"""C 端 / 后台鉴权依赖。

C 端（软校验，对齐 WX_LOGIN_ENABLED）：`customer_auth` 解 X-Customer-Token。
后台（强制）：`staff_auth` 解 Authorization: Bearer，并附带该员工的
角色、菜单（menus）、操作权限（permissions），供路由与 RBAC 校验使用。
"""
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.services.auth_service import verify_token
from app.services.staff_auth_service import verify_staff_token
from app.database import get_db
from app.models.staff import Staff, StaffStatus, StaffRole
from app.models.rbac import Role, RoleMenu


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


# ---------- 后台员工鉴权（强制）----------
def _load_staff_with_perms(db: Session, staff_id: int) -> Staff:
    staff = db.get(Staff, staff_id)
    if staff is None or staff.status != StaffStatus.ACTIVE:
        raise HTTPException(401, "账号已停用或不存在")
    role = db.query(Role).filter(Role.key == staff.role.value).first()
    # 把角色对应的菜单与操作权限挂在实例上，供路由响应与 require_perm 使用（非持久化列）
    staff.permissions = list(role.permissions) if role else []
    staff.menus = [rm.menu_key for rm in db.query(RoleMenu).filter(RoleMenu.role_id == role.id)] if role else []
    return staff


def staff_auth(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> Staff:
    """Authorization: Bearer <token> → 解出员工并附带 menus / permissions。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "未登录或登录态缺失")
    staff_id = verify_staff_token(authorization[len("Bearer "):])
    if staff_id is None:
        raise HTTPException(401, "登录态无效或已过期，请重新登录")
    return _load_staff_with_perms(db, staff_id)


def require_role(*roles: StaffRole):
    """仅允许指定角色。例：require_role(StaffRole.MANAGER)。"""
    allowed = set(roles)

    def dep(staff: Staff = Depends(staff_auth)) -> Staff:
        if staff.role not in allowed:
            raise HTTPException(403, "当前角色无此操作权限")
        return staff

    return dep


def require_perm(code: str):
    """要求具备某操作权限 code（来自角色 permissions）。"""
    def dep(staff: Staff = Depends(staff_auth)) -> Staff:
        if code not in getattr(staff, "permissions", []):
            raise HTTPException(403, "当前角色无此操作权限")
        return staff

    return dep

