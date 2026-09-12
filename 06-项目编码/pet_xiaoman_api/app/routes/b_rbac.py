"""角色与权限（店长专属）：菜单树、角色列表、角色→菜单/权限分配（RBAC）。

菜单级权限 = 角色可访问哪些菜单（驱动侧边栏与路由）；
操作级权限 = 角色拥有的操作 code 列表（如 order.refund / media.revoke），
由后端关键路由经 dependencies.require_perm 强制校验。

**平台边界（重要，防越权提权）**：本组接口是租户（店长）用的，因此
- 不暴露平台专属菜单（stores）与平台权限（store.manage/provision/brand）；
- 不允许编辑 `super_admin` 角色；
- 不允许把平台菜单/权限分配给任何租户角色。
超管改平台角色走平台脚本（scripts/create_super_admin.py），不走租户接口。
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_perm
from app.models.staff import Staff, StaffRole
from app.models.rbac import (
    Role, Menu, RoleMenu, PERMISSION_CATALOG, PLATFORM_MENU_KEYS, PLATFORM_PERMISSION_CODES,
)

router = APIRouter()


class RoleAssign(BaseModel):
    menu_keys: list[str] = []
    permissions: list[str] = []


@router.get("/menus", summary="菜单定义（按 sort 排序；不含平台专属菜单）")
def list_menus(db: Session = Depends(get_db)):
    menus = (db.query(Menu).filter(Menu.key.notin_(PLATFORM_MENU_KEYS))
             .order_by(Menu.sort).all())
    return [{"key": m.key, "title": m.title, "icon": m.icon,
             "parent_key": m.parent_key, "sort": m.sort} for m in menus]


@router.get("/permissions", summary="操作权限定义（不含平台权限）")
def list_permissions():
    return [p for p in PERMISSION_CATALOG if not p.get("platform")]


@router.get("/roles", summary="角色列表（含已分配菜单与权限；不含平台角色）")
def list_roles(db: Session = Depends(get_db)):
    out = []
    for r in db.query(Role).all():
        if r.key == StaffRole.SUPER_ADMIN.value:
            continue  # 平台角色不出现在租户侧
        menus = [rm.menu_key for rm in db.query(RoleMenu).filter(RoleMenu.role_id == r.id)]
        out.append({"key": r.key, "name": r.name, "description": r.description,
                    "permissions": list(r.permissions), "menus": menus})
    return out


@router.put("/roles/{role_key}", summary="分配角色可访问菜单与操作权限（租户角色）")
def assign_role(role_key: str, payload: RoleAssign,
                staff: Staff = Depends(require_perm("role.manage")), db: Session = Depends(get_db)):
    if role_key == StaffRole.SUPER_ADMIN.value:
        raise HTTPException(403, "平台角色不可在门店后台修改")
    role = db.query(Role).filter(Role.key == role_key).first()
    if not role:
        raise HTTPException(404, "角色不存在")

    valid = {m.key for m in db.query(Menu).filter(Menu.key.notin_(PLATFORM_MENU_KEYS)).all()}
    invalid = [k for k in payload.menu_keys if k not in valid]
    if invalid:
        raise HTTPException(400, f"未知菜单: {invalid}")

    # 租户角色不得持有平台权限（否则等于给自己发平台能力）
    illegal = [p for p in payload.permissions if p in PLATFORM_PERMISSION_CODES]
    if illegal:
        raise HTTPException(403, f"平台权限不可分配给门店角色: {illegal}")

    role.permissions = list(payload.permissions)
    db.query(RoleMenu).filter(RoleMenu.role_id == role.id).delete()
    db.add_all([RoleMenu(role_id=role.id, menu_key=k) for k in payload.menu_keys])
    db.commit()
    return {"key": role.key, "menus": payload.menu_keys, "permissions": list(role.permissions)}
