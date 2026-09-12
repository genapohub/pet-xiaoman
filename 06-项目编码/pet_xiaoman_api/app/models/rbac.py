"""RBAC：角色 / 菜单 / 角色-菜单映射（基于菜单与角色的访问控制）。

- Menu：后台侧边栏与路由对应的菜单项（key 唯一，如 dashboard/orders）。
- Role：店长(manager) / 店员(employee)，key 与 Staff.role 枚举值对应。
- RoleMenu：角色可访问的菜单（菜单级权限）。
- Role.permissions：操作级权限 code 列表（如 order.refund / media.revoke），
  由后端关键路由按角色校验（详见 dependencies.require_perm）。
"""
from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Role(BaseModel):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # manager / employee
    name: Mapped[str] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(String(120), nullable=True)
    permissions: Mapped[list] = mapped_column(JSON, default=list)  # 操作权限 code 列表


class Menu(BaseModel):
    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(32))
    icon: Mapped[str | None] = mapped_column(String(32), nullable=True)
    parent_key: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class RoleMenu(BaseModel):
    __tablename__ = "role_menus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), index=True)
    menu_key: Mapped[str] = mapped_column(String(32), index=True)


# 操作级权限目录（唯一事实源：种子数据与后台「角色权限」页共用，避免两处各写一份）
# 菜单本身存在 Menu 表里，故不在此处重复。
# 前三条为平台级权限，仅 super_admin 角色持有，租户角色一律不分配。
PERMISSION_CATALOG: list[dict] = [
    {"code": "store.manage", "label": "门店开通与启停", "platform": True},
    {"code": "store.provision", "label": "门店账号开通", "platform": True},
    {"code": "store.brand", "label": "配置门店品牌与 UI", "platform": True},
    {"code": "customer.full_phone", "label": "查看客户完整手机号"},
    {"code": "order.refund", "label": "订单退款"},
    {"code": "media.revoke", "label": "撤回服务影像"},
    {"code": "price.edit", "label": "调整服务价格"},
    {"code": "staff.manage", "label": "管理团队成员"},
    {"code": "role.manage", "label": "分配角色权限"},
]

# 平台级权限（只给超管；租户店长默认权限必须排除）
PLATFORM_PERMISSION_CODES = [p["code"] for p in PERMISSION_CATALOG if p.get("platform")]
TENANT_PERMISSION_CODES = [p["code"] for p in PERMISSION_CATALOG if not p.get("platform")]
# 平台专属菜单（门店铺级别，租户侧边栏不出现）
PLATFORM_MENU_KEYS = ["stores"]
