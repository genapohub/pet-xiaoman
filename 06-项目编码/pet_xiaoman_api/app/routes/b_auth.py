"""后台登录与登录态（账号密码 + token，含首次初始化）。

门店品牌配置已收归平台超管（见 `app/routes/b_platform.py`）：
本文件只保留「读自己门店品牌」，写入恒 403。入参校验统一在 `app/services/validators.py`。
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import staff_auth
from app.models.staff import Store, Staff, StaffRole, StaffStatus, ROLE_DISPLAY
from app.models.rbac import Role, RoleMenu
from app.models.store_profile import StoreProfile, DEFAULT_PRIMARY_COLOR
from app.services.staff_auth_service import (
    StaffAuthError, create_staff_token, login_staff, hash_password,
)

router = APIRouter()


class LoginInput(BaseModel):
    username: str
    password: str


DEFAULT_DEMO_STORE_SLUG = "chongxiaoman"
DEFAULT_DEMO_STORE_NAME = "宠小满·示例门店"
DEFAULT_DEMO_STORE_SLOGAN = "爱意小满，不留遗憾"


class SetupInput(BaseModel):
    store_name: str = DEFAULT_DEMO_STORE_NAME
    username: str
    password: str
    name: str = "店长"


def _profile(staff: Staff, db: Session) -> dict:
    role = db.query(Role).filter(Role.key == staff.role.value).first()
    menus = [rm.menu_key for rm in db.query(RoleMenu).filter(RoleMenu.role_id == role.id)] if role else []
    permissions = list(role.permissions) if role else []
    return {
        "id": staff.id, "name": staff.name, "username": staff.username, "phone": staff.phone,
        "role": staff.role.value, "role_name": ROLE_DISPLAY.get(staff.role, staff.role.value),
        "store_id": staff.store_id, "menus": menus, "permissions": permissions,
    }


@router.post("/auth/login", summary="后台账号密码登录")
def login_route(payload: LoginInput, db: Session = Depends(get_db)):
    try:
        staff = login_staff(db, payload.username, payload.password)
    except StaffAuthError as e:
        raise HTTPException(401, str(e))
    return {"token": create_staff_token(staff.id), "staff": _profile(staff, db)}


@router.get("/auth/me", summary="当前登录员工（token 校验 + 角色权限）")
def me(staff: Staff = Depends(staff_auth), db: Session = Depends(get_db)):
    return {"logged_in": True, **_profile(staff, db)}


@router.post("/auth/setup", summary="首次初始化：创建门店与首位店长（同时建白标资料）")
def setup(payload: SetupInput, db: Session = Depends(get_db)):
    if db.query(Staff).count() > 0:
        raise HTTPException(409, "系统已初始化，请勿重复创建店长")
    store = Store(name=payload.store_name)
    db.add(store)
    db.commit()
    db.refresh(store)
    db.add(StoreProfile(
        store_id=store.id, slug=DEFAULT_DEMO_STORE_SLUG, name=payload.store_name,
        slogan=DEFAULT_DEMO_STORE_SLOGAN,
        miniapp_name=payload.store_name, miniapp_entry_enabled=True,
        primary_color=DEFAULT_PRIMARY_COLOR, theme_json={},
    ))
    mgr = Staff(
        username=payload.username, password_hash=hash_password(payload.password),
        name=payload.name, role=StaffRole.MANAGER, store_id=store.id,
        manager_id=None, status=StaffStatus.ACTIVE,
    )
    db.add(mgr)
    db.commit()
    db.refresh(mgr)
    return {"token": create_staff_token(mgr.id), "staff": _profile(mgr, db)}


# ---------- 白标资料（读：租户读自己那家；写：已收归平台超管）----------
PLATFORM_BRAND = {
    "store_id": None, "slug": None, "name": "平台管理台", "slogan": "多门店统一管理",
    "logo_url": None, "primary_color": DEFAULT_PRIMARY_COLOR,
    "theme": {"primary_color": DEFAULT_PRIMARY_COLOR},
    "miniapp_name": None, "miniapp_appid": None, "miniapp_entry_enabled": False,
}


def _profile_dict(p: StoreProfile) -> dict:
    return {"store_id": p.store_id, "slug": p.slug, "name": p.name, "slogan": p.slogan,
            "logo_url": p.logo_url, "primary_color": p.primary_color, "theme": p.theme,
            "miniapp_name": p.miniapp_name, "miniapp_appid": p.miniapp_appid,
            "miniapp_entry_enabled": p.miniapp_entry_enabled}


@router.get("/store/profile", summary="当前门店白标资料（后台按店换肤）")
def get_store_profile(staff: Staff = Depends(staff_auth), db: Session = Depends(get_db)):
    """租户读自己门店的品牌；超管不属于任何门店 → 返回平台品牌（不影响门店数据）。"""
    if staff.store_id is None:
        return dict(PLATFORM_BRAND)
    p = db.query(StoreProfile).filter(StoreProfile.store_id == staff.store_id).first()
    if not p:
        raise HTTPException(404, "门店资料不存在")
    return _profile_dict(p)


@router.put("/store/profile", summary="【已停用】门店白标改由平台超管统一配置")
def update_store_profile(staff: Staff = Depends(staff_auth)):
    """刻意保留此路由并恒返回 403：给旧调用方一个明确指引，而不是含糊的 404/405。

    品牌配置入口：PUT /api/b/platform/stores/{store_id}/profile（需超管）
    """
    raise HTTPException(
        403,
        "门店品牌由平台统一配置，如需修改请联系平台管理员",
    )
