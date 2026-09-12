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
from app.models.store_profile import StoreProfile, DEFAULT_PRIMARY_COLOR  # noqa: E402
from app.models.rbac import (  # noqa: E402
    Role, Menu, RoleMenu, PERMISSION_CATALOG, PLATFORM_MENU_KEYS, TENANT_PERMISSION_CODES,
)
from app.services.staff_auth_service import hash_password  # noqa: E402

SEED_VERSION = "v20260910"

# 默认示例门店 = 宠小满。它是「演示样品间」：自带宠小满自己的品牌 UI（店名 / 标语 / 主色 / logo）。
# 注意别把它当成品牌兜底——品牌兜底在前后端都是中性的（admin stores/user.js、C 端 utils/brand.js），
# 新门店没配品牌时只会显示店名首字占位，绝不会继承宠小满的标。
DEV_STORE_SLUG = os.getenv("DEV_STORE_SLUG", "chongxiaoman")  # C 端换肤入口标识
DEFAULT_STORE_NAME = "宠小满·示例门店"
DEFAULT_STORE_SLOGAN = "爱意小满，不留遗憾"

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


# 后台菜单（与 router/index.js 的路径一一对应）
# stores 为平台专属（仅超管可见）；staff/rbac 仅店长可见
MENUS = [
    ("stores", "门店管理", "Shop", 5),
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
# 店长默认拥有全部【租户】操作权限；店员为空 —— 这就是「按角色区分操作权限」的默认基线。
# 平台权限（store.manage/provision/brand）只给超管，绝不下放给租户角色。
TENANT_PERMS = list(TENANT_PERMISSION_CODES)
EMPLOYEE_PERMS: list[str] = []

# 本地联调默认店长（生产请走 POST /api/b/auth/setup，并务必改密）
# 账号名跟着默认示例门店走 = petxiaoman。历史上是 admin，老库请跑
# `scripts/migrate_dev_accounts.py --apply` 迁移（脚本会把历史 admin 改名，不留残留）。
DEV_MANAGER_USER = os.getenv("DEV_MANAGER_USER", "petxiaoman")
DEV_MANAGER_PASS = os.getenv("DEV_MANAGER_PASS", "petxiaoman123")

# 本地联调默认超管（平台级；租户账号看不到「门店管理」）
DEV_SUPER_USER = os.getenv("SUPER_ADMIN_USER", "superadmin")
DEV_SUPER_PASS = os.getenv("SUPER_ADMIN_PASS", "super123456")


def _seed_org_and_rbac(db) -> Store:
    """组织与权限种子（幂等）：默认门店 + 白标资料 + 超管/店长/店员三角色 + 菜单映射。"""
    store = db.query(Store).first()
    if not store:
        store = Store(name=DEFAULT_STORE_NAME)
        db.add(store)
        db.commit()
        db.refresh(store)

    # 白标资料（多租户换肤；slug 作为 C 端入口标识）
    profile = db.query(StoreProfile).filter(StoreProfile.store_id == store.id).first()
    if not profile:
        db.add(StoreProfile(store_id=store.id, slug=DEV_STORE_SLUG, name=DEFAULT_STORE_NAME,
                            slogan=DEFAULT_STORE_SLOGAN,
                            primary_color=DEFAULT_PRIMARY_COLOR, theme_json={}))
        db.commit()
    elif not profile.slogan:
        # slogan 列是后加的（ALTER TABLE），老库的历史行会是 NULL。
        # 只在为空时补齐，不覆盖后台已经改过的值 —— 保持种子幂等。
        profile.slogan = DEFAULT_STORE_SLOGAN
        db.commit()
        print(f"已补齐默认示例门店标语：{DEFAULT_STORE_SLOGAN}")

    existing_keys = {m.key for m in db.query(Menu).all()}
    missing = [(k, t, i, s) for (k, t, i, s) in MENUS if k not in existing_keys]
    if missing:
        db.add_all([Menu(key=k, title=t, icon=i, sort=s) for (k, t, i, s) in missing])
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

    super_admin = _role("super_admin", "平台超管", ALL_PERMS)
    manager = _role("manager", "店长", TENANT_PERMS)
    employee = _role("employee", "店员", EMPLOYEE_PERMS)

    all_keys = [k for (k, *_rest) in MENUS]
    tenant_keys = [k for k in all_keys if k not in PLATFORM_MENU_KEYS]
    def _bind(role: Role, keys: list) -> None:
        if db.query(RoleMenu).filter(RoleMenu.role_id == role.id).count():
            return  # 已被后台改过就不覆盖，避免重置店长的权限分配
        db.add_all([RoleMenu(role_id=role.id, menu_key=k) for k in keys])
        db.commit()

    # 超管只拿平台菜单（门店管理）：他的职责是开店 / 开账号 / 配品牌，不做门店履约。
    # 若把租户菜单也给他，他会以 store_id=None 落库，
    # 造出「任何门店都查不到」的孤儿数据（服务项目 / 纪念品 / 订单…）。
    # 租户角色则一律不含平台菜单。
    _bind(super_admin, list(PLATFORM_MENU_KEYS))
    _bind(manager, tenant_keys)
    _bind(employee, [k for k in tenant_keys if k not in ("staff", "rbac")])

    if db.query(Staff).count() == 0:
        db.add(Staff(username=DEV_MANAGER_USER, password_hash=hash_password(DEV_MANAGER_PASS),
                     name="示例店长", role=StaffRole.MANAGER, store_id=store.id,
                     manager_id=None, status=StaffStatus.ACTIVE))
        db.commit()
        print(f"已创建默认店长：{DEV_MANAGER_USER} / {DEV_MANAGER_PASS}（仅本地联调，生产请改密或走 /api/b/auth/setup）")

    # 平台超管（不属于任何门店；门店管理与品牌配置入口只对他可见）
    if not db.query(Staff).filter(Staff.role == StaffRole.SUPER_ADMIN).first():
        db.add(Staff(username=DEV_SUPER_USER, password_hash=hash_password(DEV_SUPER_PASS),
                     name="平台管理员", role=StaffRole.SUPER_ADMIN, store_id=None,
                     manager_id=None, status=StaffStatus.ACTIVE))
        db.commit()
        print(f"已创建默认超管：{DEV_SUPER_USER} / {DEV_SUPER_PASS}（登录后侧边栏可见「门店管理」）")

    return store


def init(reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    db = SessionLocal()
    try:
        store = _seed_org_and_rbac(db)
        exist = db.query(ServiceItem).filter_by(version=SEED_VERSION).count()
        if exist:
            print(f"种子数据已存在（version={SEED_VERSION}，{exist} 条），跳过。如需重建：--reset")
            return

        db.add_all([
            ServiceItem(type=t, name=name, price=price, weight_tier=wt, status=st,
                        version=SEED_VERSION, store_id=store.id)
            for (t, name, price, wt, st) in SERVICE_ITEMS
        ])
        db.add_all([
            Product(name=name, price=price, images=[], description=desc,
                    status=ProductStatus.ON_SALE, stock_note=note, store_id=store.id)
            for (name, price, desc, note) in PRODUCTS
        ])
        db.commit()
        print(f"完成：服务项目 {len(SERVICE_ITEMS)} 条 / 纪念品 {len(PRODUCTS)} 条（version={SEED_VERSION}）")
    finally:
        db.close()


if __name__ == "__main__":
    init(reset="--reset" in sys.argv)
