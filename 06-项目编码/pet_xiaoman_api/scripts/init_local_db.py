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
DEV_MINIAPP_APPID = os.getenv("DEV_MINIAPP_APPID", "")        # 独立小程序 AppID，本地可留空
DEFAULT_STORE_NAME = "宠小满·示例门店"
DEFAULT_STORE_SLOGAN = "爱意小满，不留遗憾"
DEFAULT_CONTACT_PHONE = os.getenv("DEV_STORE_PHONE", "0371-00000000")
DEFAULT_CONTACT_ADDRESS = os.getenv("DEV_STORE_ADDRESS", "郑州市宠物善终服务中心")
DEFAULT_BUSINESS_HOURS = os.getenv("DEV_STORE_HOURS", "24 小时可约")
# 门店经纬度（wx.openLocation 导航用）；示例门店落在郑州市区，真实门店由品牌配置页填写。
DEFAULT_LAT = float(os.getenv("DEV_STORE_LAT", "34.7466"))
DEFAULT_LNG = float(os.getenv("DEV_STORE_LNG", "113.6240"))

# 门店级品牌文案（首页轮播 / 三承诺 / 入口宫格 / 关于与承诺）。
# 此前这些写死在 C 端 JS 常量里、双端对不齐；现归到数据层，B 端品牌配置可维护、C 端按 slug 读取。
# icon 字段保留原 C 端图标名，url 为入口路由，便于 B 端改文案/入口而不动前端。
DEFAULT_CONTENT = {
    "heroes": [
        {"key": "brand", "brand": "宠小满", "title": "温柔送别，不失温度", "slogan": "爱意小满，不留遗憾"},
        {"key": "price", "eyebrow": "透明价格", "title": "明码标价，安心托付", "slogan": "每一程，都看得见"},
        {"key": "memory", "eyebrow": "温柔纪念", "title": "纪念，是最好的告别", "slogan": "为爱留一处温柔归处"},
    ],
    "promises": [
        {"key": "price", "icon": "shield-primary.png", "title": "明码标价", "desc": "无隐藏费用"},
        {"key": "single", "icon": "heart-primary.png", "title": "单独火化", "desc": "专属送别"},
        {"key": "24h", "icon": "clock-primary.png", "title": "24h 可约", "desc": "随时响应"},
    ],
    "entries": [
        {"key": "booking", "title": "预约火化", "desc": "安心送别", "icon": "check-primary.png", "url": "/pages/order-create/index"},
        {"key": "price", "title": "服务价格", "desc": "明码标价", "icon": "price-primary.png", "url": "/pages/prices/prices"},
        {"key": "gift", "title": "纪念品", "desc": "把爱留驻", "icon": "box-primary.png", "url": "/pages/products/products"},
        {"key": "archive", "title": "宠物档案", "desc": "记忆永存", "icon": "paw-primary.png", "url": "/pages/pets/pets"},
    ],
    "about_promises": {
        "proofs": [
            {"value": "价格", "label": "下单前公开"},
            {"value": "节点", "label": "订单内留痕"},
            {"value": "联系", "label": "服务前确认"},
        ],
        "promises": [
            {"title": "明码标价", "text": "服务项目和加购项在下单前公开展示，提交预约时锁定价格版本，后续不因沟通环节临时加价。", "icon": "/assets/icons/price-primary.png"},
            {"title": "单独火化", "text": "服务套餐默认按单独火化口径履约，关键节点会进入订单时间线，减少家属对混灰和流程草率的担心。", "icon": "/assets/icons/shield-primary.png"},
            {"title": "过程可见", "text": "接宠、服务、交付等节点可沉淀影像记录，家属可以在订单详情查看服务进度。", "icon": "/assets/icons/camera-primary.png"},
        ],
        "flows": [
            {"step": "01", "title": "提交预约", "text": "填写宠物信息、服务项目与接宠地址。"},
            {"step": "02", "title": "电话确认", "text": "门店确认时间、价格和服务细节后再履约。"},
            {"step": "03", "title": "节点跟进", "text": "关键服务节点进入订单详情，方便家属回看。"},
        ],
    },
}

# 服务项目 + 每项的服务介绍 / 流程步骤 / 常见问题（数据层来源，替代原 C 端写死的 JS 常量）。
# 字段：(type, name, price, weight_tier, status, description, steps, faq)
SERVICE_ITEMS = [
    # 套餐：按体重分档（PRD §5.2 透明价格）
    (ItemType.PACKAGE, "基础告别套餐", 800, "0-10kg", ItemStatus.ON_SALE,
     "一对一专属送别，含上门接宠、独立告别空间与单独火化，适合 10kg 以内毛孩子。",
     ["电话确认", "上门接宠", "告别仪式", "单独火化", "骨灰交付"],
     [{"q": "套餐包含哪些服务？", "a": "含上门接宠、独立告别空间、单独火化与骨灰交付，加购项可另行选择。"},
      {"q": "可以先不在线支付吗？", "a": "可以，一期支持到店付款，门店会电话确认预约。"}]),
    (ItemType.PACKAGE, "标准告别套餐", 1280, "10-20kg", ItemStatus.ON_SALE,
     "面向 10–20kg 毛孩子的完整告别，含独立告别空间、单独火化与基础骨灰罐。",
     ["电话确认", "上门接宠", "告别仪式", "单独火化", "骨灰交付"],
     [{"q": "比基础套餐多什么？", "a": "覆盖更大体型火化能耗，并含基础骨灰罐一只。"},
      {"q": "价格会变吗？", "a": "下单时锁定价格版本，门店确认后不会临时加价。"}]),
    (ItemType.PACKAGE, "尊享告别套餐", 1980, "20kg+", ItemStatus.ON_SALE,
     "尊享级送别，含专车接宠、独立仪式空间、单独火化与升级骨灰纪念。",
     ["电话确认", "专车接宠", "告别仪式", "单独火化", "骨灰交付"],
     [{"q": "适合哪些家庭？", "a": "希望有更充裕告别时间与升级纪念品的家庭。"},
      {"q": "可以加购纪念品吗？", "a": "可以，毛发爪印、照片纪念册等可在预约时一并选择。"}]),
    # 单项服务
    (ItemType.SINGLE, "单独火化", 500, None, ItemStatus.ON_SALE,
     "按单独火化口径履约，关键节点进入订单时间线，避免混灰。",
     ["预约火化", "单独火化", "骨灰归集", "骨灰交付"],
     [{"q": "怎么确认是单独火化？", "a": "接宠、火化、交付等节点会上传影像，可在订单详情查看。"},
      {"q": "骨灰怎么交付？", "a": "火化完成后由门店当面交付，可随附纪念品。"}]),
    (ItemType.SINGLE, "上门接运", 150, None, ItemStatus.ON_SALE,
     "专车上门接宠，全程温柔稳妥，减轻家属奔波。",
     ["预约接运", "专车上门", "温柔接送"],
     [{"q": "接运范围？", "a": "以门店可服务区域为准，电话确认时门店会说明。"},
      {"q": "需要家属陪同吗？", "a": "无需陪同，门店专车接宠后电话同步进度。"}]),
    (ItemType.SINGLE, "告别仪式场地", 300, None, ItemStatus.ON_SALE,
     "独立告别空间，给家属一段安静道别的时间。",
     ["预约场地", "独立空间告别", "仪式留影"],
     [{"q": "可以自带布置吗？", "a": "可提前与门店沟通，门店会尽量配合。"},
      {"q": "时长有限制吗？", "a": "以门店当日排期为准，电话确认时约定。"}]),
    # 加购
    (ItemType.ADDON, "毛发爪印留存", 50, None, ItemStatus.ON_SALE,
     "留存毛孩子爪印与一缕毛发，做成可携带的纪念。", [], []),
    (ItemType.ADDON, "骨灰罐升级", 180, None, ItemStatus.ON_SALE,
     "升级骨灰罐材质与工艺，长久安放思念。", [], []),
    (ItemType.ADDON, "照片纪念册", 120, None, ItemStatus.ON_SALE,
     "精选服务影像，制成可翻看的纪念册。", [], []),
    (ItemType.ADDON, "已下架加购（用例）", 99, None, ItemStatus.OFF_SALE,
     "（下架用例）用于演示下架态展示。", [], []),
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
                            contact_phone=DEFAULT_CONTACT_PHONE,
                            contact_address=DEFAULT_CONTACT_ADDRESS,
                            business_hours=DEFAULT_BUSINESS_HOURS,
                            miniapp_name=DEFAULT_STORE_NAME,
                            miniapp_appid=DEV_MINIAPP_APPID or None,
                            miniapp_entry_enabled=True,
                            primary_color=DEFAULT_PRIMARY_COLOR, theme_json={},
                            content_json=DEFAULT_CONTENT, lat=DEFAULT_LAT, lng=DEFAULT_LNG))
        db.commit()
    else:
        changed = False
        if not profile.slogan:
            # slogan 列是后加的（ALTER TABLE），老库的历史行会是 NULL。
            # 只在为空时补齐，不覆盖后台已经改过的值 —— 保持种子幂等。
            profile.slogan = DEFAULT_STORE_SLOGAN
            changed = True
            print(f"已补齐默认示例门店标语：{DEFAULT_STORE_SLOGAN}")
        if not profile.miniapp_name:
            profile.miniapp_name = profile.name or DEFAULT_STORE_NAME
            changed = True
        if profile.miniapp_entry_enabled is None:
            profile.miniapp_entry_enabled = True
            changed = True
        if not profile.contact_phone:
            profile.contact_phone = DEFAULT_CONTACT_PHONE
            changed = True
        if not profile.contact_address:
            profile.contact_address = DEFAULT_CONTACT_ADDRESS
            changed = True
        if not profile.business_hours:
            profile.business_hours = DEFAULT_BUSINESS_HOURS
            changed = True
        if DEV_MINIAPP_APPID and not profile.miniapp_appid:
            profile.miniapp_appid = DEV_MINIAPP_APPID
            changed = True
        if not profile.content_json:
            # 品牌文案列是后加的，老库历史行会是空字典；只在为空时补齐示例文案，
            # 不覆盖后台已经改过的值 —— 保持种子幂等。
            profile.content_json = DEFAULT_CONTENT
            changed = True
        if profile.lat is None:
            profile.lat = DEFAULT_LAT
            changed = True
        if profile.lng is None:
            profile.lng = DEFAULT_LNG
            changed = True
        if changed:
            db.commit()

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
            print(f"种子数据已存在（version={SEED_VERSION}，{exist} 条），跳过重建。如需重建：--reset")
        else:
            db.add_all([
                ServiceItem(type=t, name=name, price=price, weight_tier=wt, status=st,
                            description=desc, steps_json=steps, faq_json=faq,
                            version=SEED_VERSION, store_id=store.id)
                for (t, name, price, wt, st, desc, steps, faq) in SERVICE_ITEMS
            ])
            db.add_all([
                Product(name=name, price=price, images=[], description=desc,
                        status=ProductStatus.ON_SALE, stock_note=note, store_id=store.id)
                for (name, price, desc, note) in PRODUCTS
            ])
            db.commit()
            print(f"完成：服务项目 {len(SERVICE_ITEMS)} 条 / 纪念品 {len(PRODUCTS)} 条（version={SEED_VERSION}）")

        # 内容字段回填（幂等）：老库已存在但缺介绍/流程/FAQ 的服务项目，补真实文案。
        # 只在 description 为 NULL 时补，已维护过的不覆盖。
        backfilled = 0
        for (t, name, price, wt, st, desc, steps, faq) in SERVICE_ITEMS:
            item = (db.query(ServiceItem)
                    .filter(ServiceItem.store_id == store.id, ServiceItem.name == name).first())
            if item and item.description is None:
                item.description = desc
                item.steps_json = steps
                item.faq_json = faq
                backfilled += 1
        if backfilled:
            db.commit()
            print(f"已回填服务介绍/流程/FAQ：{backfilled} 条")

        # 全局门店品牌文案/经纬度回填（幂等）：任何门店（含试点门店）缺内容时补示例文案，
        # 不覆盖后台已维护的值 —— 保证双端（C 端内容 / B 端地图导航）都有数据可对齐。
        prof_backfilled = 0
        for prof in db.query(StoreProfile).all():
            changed = False
            if not prof.content_json:
                prof.content_json = DEFAULT_CONTENT
                changed = True
            if prof.lat is None:
                prof.lat = DEFAULT_LAT
                changed = True
            if prof.lng is None:
                prof.lng = DEFAULT_LNG
                changed = True
            if changed:
                prof_backfilled += 1
        if prof_backfilled:
            db.commit()
            print(f"已回填门店品牌文案/经纬度：{prof_backfilled} 家")
    finally:
        db.close()


if __name__ == "__main__":
    init(reset="--reset" in sys.argv)
