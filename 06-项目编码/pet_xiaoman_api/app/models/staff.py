"""门店与员工（组织架构）：平台层超管 + 门店内 1 名店长 + N 名店员。

层级关系用 `manager_id` 表达：店长的 manager_id 为空，店员的 manager_id 指向所属店长。
`role` 决定权限范围（超管/店长/店员），与 RBAC 的 Role 表按 key 对应。

**平台层 vs 门店层**：`store_id` 为空 ＝ 平台级（超管，不属于任何门店）；
有值 ＝ 门店员工。超管不直接操作门店业务数据，改由 /api/b/platform/* 显式指定目标门店。
"""
import enum
from datetime import datetime

from sqlalchemy import String, Integer, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class StaffRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"  # 超管（平台级，store_id 为空）
    MANAGER = "manager"   # 店长
    EMPLOYEE = "employee" # 店员


class StaffStatus(str, enum.Enum):
    ACTIVE = "active"     # 在职
    DISABLED = "disabled" # 停用


class StoreStatus(str, enum.Enum):
    ACTIVE = "active"     # 正常营业
    DISABLED = "disabled" # 已停用（C 端不可访问）


ROLE_DISPLAY = {
    StaffRole.SUPER_ADMIN: "平台超管",
    StaffRole.MANAGER: "店长",
    StaffRole.EMPLOYEE: "店员",
}

# 门店内可创建的角色（超管不能通过门店接口创建）
STORE_ROLES = (StaffRole.MANAGER, StaffRole.EMPLOYEE)

# 可创建/操作任意门店的员工角色（平台级）
PLATFORM_ROLES = (StaffRole.SUPER_ADMIN,)


class Store(BaseModel):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    status: Mapped[StoreStatus] = mapped_column(Enum(StoreStatus), default=StoreStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Staff(BaseModel):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role: Mapped[StaffRole] = mapped_column(Enum(StaffRole), default=StaffRole.EMPLOYEE)
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id"), nullable=True)
    # 两级结构：店员 → 所属店长（manager_id 为空表示店长本人）
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    status: Mapped[StaffStatus] = mapped_column(Enum(StaffStatus), default=StaffStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
