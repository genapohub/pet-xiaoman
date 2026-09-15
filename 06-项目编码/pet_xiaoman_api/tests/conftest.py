"""测试基建：SQLite 内存库 + StaticPool（PRD AC 转用例，环境变量在 import app 前设置）。
SQLITE_FALLBACK 仅为测试通道；生产禁止降级（ADR-002 / config.py）。"""
import os

os.environ["SQLITE_FALLBACK"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False)
Base.metadata.create_all(engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()


@pytest.fixture
def seed(db):
    """价格表种子：套餐 800 / 加购 50 / 下架加购。"""
    from app.models.service_item import ItemType, ItemStatus, ServiceItem
    pkg = ServiceItem(type=ItemType.PACKAGE, name="基础告别套餐", price=800,
                      weight_tier="0-10kg", version="v20260905", status=ItemStatus.ON_SALE)
    addon = ServiceItem(type=ItemType.ADDON, name="毛发爪印留存", price=50,
                        version="v20260905", status=ItemStatus.ON_SALE)
    off = ServiceItem(type=ItemType.ADDON, name="已下架加购", price=99,
                      version="v20260905", status=ItemStatus.OFF_SALE)
    db.add_all([pkg, addon, off])
    db.commit()
    return {"pkg_id": pkg.id, "addon_id": addon.id, "off_id": off.id}


@pytest.fixture
def order_input(seed):
    """合法下单入参模板。"""
    from datetime import datetime, timedelta
    return {
        "user_id": 1,
        "pet_name": "豆豆",
        "species": "犬",
        "pkg_id": seed["pkg_id"],
        "addon_ids": [],
        "expect_time": (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0).isoformat(),
        "address": "郑州市金水区XX路1号",
    }


@pytest.fixture
def org(db):
    """最小组织 + RBAC 基线（供后台鉴权/RBAC/两级组织/超管测试复用）：
    门店 + 10 菜单 + 超管(平台级)/店长(全部租户权限)/店员(无操作权限)三角色 + 各一名在职员工。"""
    from app.models.staff import Store, Staff, StaffRole, StaffStatus
    from app.models.rbac import (
        Role, Menu, RoleMenu, PERMISSION_CATALOG, PLATFORM_MENU_KEYS, TENANT_PERMISSION_CODES,
    )
    from app.models.store_profile import StoreProfile, DEFAULT_PRIMARY_COLOR
    from app.services.staff_auth_service import hash_password, create_staff_token

    ALL_PERMS = [p["code"] for p in PERMISSION_CATALOG]
    TENANT_PERMS = list(TENANT_PERMISSION_CODES)
    MENU_KEYS = ["stores", "dashboard", "orders", "service-items", "products", "boarding",
                 "customers", "stats", "staff", "rbac"]
    TENANT_MENUS = [k for k in MENU_KEYS if k not in PLATFORM_MENU_KEYS]
    EMPLOYEE_MENUS = [k for k in TENANT_MENUS if k not in ("staff", "rbac")]

    store = Store(name="测试门店")
    db.add(store)
    db.commit()
    db.refresh(store)

    # 白标资料（供 C 端按 slug 换肤与跨店隔离测试）
    db.add(StoreProfile(store_id=store.id, slug="store-a", name="门店A",
                        slogan="门店A 的标语",
                        primary_color=DEFAULT_PRIMARY_COLOR, theme_json={}))
    db.commit()

    db.add_all([Menu(key=k, title=k, icon="", sort=i) for i, k in enumerate(MENU_KEYS)])
    db.commit()

    sa = Role(key="super_admin", name="平台超管", permissions=list(ALL_PERMS))
    manager = Role(key="manager", name="店长", permissions=TENANT_PERMS)
    employee = Role(key="employee", name="店员", permissions=[])
    db.add_all([sa, manager, employee])
    db.commit()
    for r in (sa, manager, employee):
        db.refresh(r)

    # 超管只绑平台菜单：他不管门店履约，进租户页会以 store_id=None 落库成孤儿数据
    db.add_all([RoleMenu(role_id=sa.id, menu_key=k) for k in PLATFORM_MENU_KEYS])
    db.add_all([RoleMenu(role_id=manager.id, menu_key=k) for k in TENANT_MENUS])
    db.add_all([RoleMenu(role_id=employee.id, menu_key=k) for k in EMPLOYEE_MENUS])
    db.commit()

    mgr = Staff(username="admin", password_hash=hash_password("admin123"),
                name="示例店长", role=StaffRole.MANAGER, store_id=store.id,
                manager_id=None, status=StaffStatus.ACTIVE)
    emp = Staff(username="emp", password_hash=hash_password("emp123"),
                name="示例店员", role=StaffRole.EMPLOYEE, store_id=store.id,
                manager_id=None, status=StaffStatus.ACTIVE)
    root = Staff(username="superadmin", password_hash=hash_password("super123"),
                 name="平台管理员", role=StaffRole.SUPER_ADMIN, store_id=None,
                 manager_id=None, status=StaffStatus.ACTIVE)
    db.add_all([mgr, emp, root])
    db.commit()
    for s in (mgr, emp, root):
        db.refresh(s)
    emp.manager_id = mgr.id  # 两级归属：店员上级为店长
    db.commit()

    return {
        "store_id": store.id,
        "manager_id": mgr.id,
        "employee_id": emp.id,
        "super_id": root.id,
        "manager_token": create_staff_token(mgr.id),
        "employee_token": create_staff_token(emp.id),
        "super_token": create_staff_token(root.id),
    }
