"""本地联调用：SQLite 建表 + 最小调试种子数据。

背景：ADR-002 要求本地走 MySQL，但本机无 Docker / 无 MySQL 服务，
故用 config.py 已有的 SQLITE_FALLBACK 通道跑通小程序联调。
生产禁止使用（config.py 已在 ENV=production 时禁止降级 SQLite）。

用法：
    SQLITE_FALLBACK=true python scripts/init_local_db.py [--reset]
"""
import os
import sys

os.environ.setdefault("SQLITE_FALLBACK", "true")

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Product, ServiceItem  # noqa: E402
from app.models.product import ProductStatus  # noqa: E402
from app.models.service_item import ItemStatus, ItemType  # noqa: E402
from app.models.staff import Store, Staff, StaffRole, StaffStatus  # noqa: E402
from app.models.rbac import Role, Menu, RoleMenu, PERMISSION_CATALOG  # noqa: E402
from app.services.staff_auth_service import hash_password  # noqa: E402

SEED_VERSION = "v20260910"

SERVICE_ITEMS = [
    # 套餐：按体重分档（PRD §5.2 透明价格）
    (ItemType.PACKAGE, "基础告别套餐", 800, "0-10kg", ItemStatus.ON_SALE),
    (ItemType.PACKAGE, "标准告别套餐", 1280, "10-20kg", ItemStatus.ON_SALE),
    (ItemType.PACKAGE, "尊享告别套餐", 1980, "20kg+", ItemStatus.ON_SALE),
    # 单项服务
    (ItemType.SINGLE, "单独火化", 500, None, ItemStatus.ON_SALE),
    (ItemType.SINGLE, "上门接运", 150, None, ItemStatus.ON_SALE),
    (ItemType.SINGLE, "告别仪式场地", 300, None, ItemStatus.ON_SALE),
    # 加购
    (ItemType.ADDON, "毛发爪印留存", 50, None, ItemStatus.ON_SALE),
    (ItemType.ADDON, "骨灰罐升级", 180, None, ItemStatus.ON_SALE),
    (ItemType.ADDON, "照片纪念册", 120, None, ItemStatus.ON_SALE),
    (ItemType.ADDON, "已下架加购（用例）", 99, None, ItemStatus.OFF_SALE),
]

PRODUCTS = [
    ("黑胡桃木骨灰盒", 299, "实木手工打磨，可刻字", "现货充足"),
    ("爪印相框", 158, "留爪印 + 照片二合一", "现货充足"),
    ("毛发纪念瓶", 88, "玻璃瓶配木塞挂坠", "现货充足"),
]


# 后台菜单（与 router/index.js 的路径一一对应；staff/rbac 仅店长可见）
MENUS = [
    ("dashboard", "今日工作台", "HomeFilled", 10),
    ("orders", "订单管理", "Tickets", 20),
    ("service-items", "服务项目与价格", "PriceTag", 30),
    ("products", "纪念品管理", "Present", 40),
    ("boarding", "骨灰寄存", "Box", 50),
    ("customers", "客户档案", "User", 60),
    ("stats", "数据看板", "DataLine", 70),
    ("staff", "团队成员", "Avatar", 80),
    ("rbac", "角色权限", "Setting", 90),
]

ALL_PERMS = [p["code"] for p in PERMISSION_CATALOG]
# 店长默认拥有全部操作权限；店员为空 —— 这就是「按角色区分操作权限」的默认基线
EMPLOYEE_PERMS: list[str] = []

# 本地联调默认店长（生产请走 POST /api/b/auth/setup，并务必改密）
DEV_ADMIN_USER = os.getenv("DEV_ADMIN_USER", "admin")
DEV_ADMIN_PASS = os.getenv("DEV_ADMIN_PASS", "admin123")


def _seed_org_and_rbac(db) -> None:
    """组织与权限种子（幂等）：默认门店 + 两角色 + 菜单映射 + 首位店长。"""
    store = db.query(Store).first()
    if not store:
        store = Store(name="宠小满·示例门店")
        db.add(store)
        db.commit()
        db.refresh(store)

    if db.query(Menu).count() == 0:
        db.add_all([Menu(key=k, title=t, icon=i, sort=s) for (k, t, i, s) in MENUS])
        db.commit()

    def _role(key: str, name: str, perms: list) -> Role:
        r = db.query(Role).filter(Role.key == key).first()
        if not r:
            r = Role(key=key, name=name, permissions=list(perms))
            db.add(r)
        else:
            r.permissions = list(perms)
        db.commit()
        db.refresh(r)
        return r

    manager = _role("manager", "店长", ALL_PERMS)
    employee = _role("employee", "店员", EMPLOYEE_PERMS)

    all_keys = [k for (k, *_rest) in MENUS]
    def _bind(role: Role, keys: list) -> None:
        if db.query(RoleMenu).filter(RoleMenu.role_id == role.id).count():
            return  # 已被后台改过就不覆盖，避免重置店长的权限分配
        db.add_all([RoleMenu(role_id=role.id, menu_key=k) for k in keys])
        db.commit()

    _bind(manager, all_keys)
    _bind(employee, [k for k in all_keys if k not in ("staff", "rbac")])

    if db.query(Staff).count() == 0:
        db.add(Staff(username=DEV_ADMIN_USER, password_hash=hash_password(DEV_ADMIN_PASS),
                     name="示例店长", role=StaffRole.MANAGER, store_id=store.id,
                     manager_id=None, status=StaffStatus.ACTIVE))
        db.commit()
        print(f"已创建默认店长：{DEV_ADMIN_USER} / {DEV_ADMIN_PASS}（仅本地联调，生产请改密或走 /api/b/auth/setup）")


def init(reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    db = SessionLocal()
    try:
        _seed_org_and_rbac(db)
        exist = db.query(ServiceItem).filter_by(version=SEED_VERSION).count()
        if exist:
            print(f"种子数据已存在（version={SEED_VERSION}，{exist} 条），跳过。如需重建：--reset")
            return

        db.add_all([
            ServiceItem(type=t, name=name, price=price, weight_tier=wt, status=st, version=SEED_VERSION)
            for (t, name, price, wt, st) in SERVICE_ITEMS
        ])
        db.add_all([
            Product(name=name, price=price, images=[], description=desc,
                    status=ProductStatus.ON_SALE, stock_note=note)
            for (name, price, desc, note) in PRODUCTS
        ])
        db.commit()
        print(f"完成：服务项目 {len(SERVICE_ITEMS)} 条 / 纪念品 {len(PRODUCTS)} 条（version={SEED_VERSION}）")
    finally:
        db.close()


if __name__ == "__main__":
    init(reset="--reset" in sys.argv)
