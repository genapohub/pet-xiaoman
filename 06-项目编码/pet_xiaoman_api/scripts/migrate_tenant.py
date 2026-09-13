"""存量库升级到多租户结构（幂等、非破坏性）。

用途：已有数据的库（SQLite / MySQL），升级到「多租户 + 白标」版本后执行一次。
背景：`Base.metadata.create_all` 只建「缺失的表」，**不会给已有表加列**；
     多租户改造给 10 张表加了 `store_id`，老库必须补列。

做四件事（可重复执行，不删除业务数据）：
  1. 建缺失的表（如 `store_profiles`）；
  2. 给租户表补 `store_id` 列 + 索引；
  3. 修正受约束变更影响的表（boardings 的 `UNIQUE(location)` → `UNIQUE(store_id, location)`）；
  4. 保证默认门店与白标资料存在，并把历史未打标数据回填到默认门店。

用法：
    env -u PYTHONPATH SQLITE_FALLBACK=true ./.venv/bin/python -m scripts.migrate_tenant

环境变量：
    DEV_STORE_SLUG  白标入口标识（默认 chongxiaoman）
"""
import os

os.environ.setdefault("SQLITE_FALLBACK", "true")

from sqlalchemy import text  # noqa: E402

import app.models  # noqa: F401,E402  确保全部模型注册进 metadata
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.boarding import Boarding  # noqa: E402
from app.models.rbac import (  # noqa: E402
    PERMISSION_CATALOG, PLATFORM_MENU_KEYS, PLATFORM_PERMISSION_CODES, Menu, Role, RoleMenu,
)
from app.models.staff import Staff, StaffRole, Store  # noqa: E402
from app.models.store_profile import StoreProfile, DEFAULT_PRIMARY_COLOR  # noqa: E402
from scripts.backfill_store_scope import SCOPED_MODELS  # noqa: E402

DEFAULT_STORE_NAME = "宠小满·示例门店"
DEFAULT_STORE_SLOGAN = "爱意小满，不留遗憾"
DEV_STORE_SLUG = os.getenv("DEV_STORE_SLUG", "chongxiaoman")
IS_SQLITE = engine.dialect.name == "sqlite"

# 多租户改造后新增的普通列（create_all 不会给已有表加列）
#
# ⚠️ stores.status 的默认值必须写「成员名」ACTIVE 而不是值 'active'：
#    SQLAlchemy 的 Enum(StoreStatus) 默认按 **枚举成员名** 落库（ACTIVE / DISABLED），
#    而 ALTER TABLE 是绕过 ORM 的原始 DDL —— 写小写值会让后续 ORM 读取直接抛
#    LookupError: 'active' is not among the defined enum values。
EXTRA_COLUMNS = [
    ("stores", "status", "VARCHAR(8) DEFAULT 'ACTIVE'"),          # 门店启用/停用
    ("store_profiles", "slogan", "VARCHAR(50)"),                  # 对外标语，可空
    ("store_profiles", "miniapp_name", "VARCHAR(50)"),            # 独立小程序名称，可空
    ("store_profiles", "miniapp_appid", "VARCHAR(64)"),           # 独立小程序 AppID，可空
    ("store_profiles", "miniapp_entry_enabled", "BOOLEAN DEFAULT 1"),  # 独立搜索入口开关
]

# 枚举列的历史脏值归一（只归一由脚本原始 DDL 引入的那一列）
ENUM_NAME_COLUMNS = [
    ("stores", "status", ("ACTIVE", "DISABLED")),
]

# 平台层菜单（仅超管可见）
PLATFORM_MENUS = [("stores", "门店管理", "Shop", 5)]

# 超管只绑平台菜单：他的职责是开店 / 开账号 / 配品牌，不做门店履约。
# 若把租户菜单也给他，他会以 store_id=None 落库，造出门店查不到的孤儿数据。
SUPER_ADMIN_MENUS = [k for (k, *_r) in PLATFORM_MENUS]


def _columns(conn, table: str) -> list[str]:
    if IS_SQLITE:
        return [r[1] for r in conn.execute(text(f"PRAGMA table_info({table})"))]
    rows = conn.execute(text(f"SHOW COLUMNS FROM {table}"))
    return [r[0] for r in rows]


def _table_sql(conn, table: str) -> str:
    if not IS_SQLITE:
        return ""
    row = conn.execute(text("select sql from sqlite_master where type='table' and name=:n"),
                       {"n": table}).fetchone()
    return (row[0] or "") if row else ""


def _add_store_columns(conn) -> list[str]:
    """给租户表补 store_id 列（create_all 不会做这件事）。"""
    done = []
    for model in SCOPED_MODELS:
        t = model.__tablename__
        if "store_id" in _columns(conn, t):
            continue
        conn.execute(text(f"ALTER TABLE {t} ADD COLUMN store_id INTEGER"))
        conn.execute(text(f"CREATE INDEX ix_{t}_store_id ON {t} (store_id)"))
        done.append(t)
    return done


def _rebuild_boarding_if_needed(conn) -> str:
    """boardings 原为全局 UNIQUE(location)，多租户后应为 UNIQUE(store_id, location)。

    SQLite 无法删除表级 UNIQUE 约束，只能重建：空表直接重建；
    有数据时保留数据迁移，失败则跳过并提示（不丢数据）。
    """
    if not IS_SQLITE:
        return "非 SQLite：跳过（请按 MySQL 手工调整唯一键）"
    ddl = _table_sql(conn, "boardings")
    if not ddl:
        return "表不存在，无需调整"
    # 归一化空白后再比对（注意先比对手写常量的大小写，避免 upper() 把 location 一起大写）
    norm = " ".join(ddl.upper().split())
    if "UNIQUE (LOCATION)" not in norm:
        return "无需调整"
    n = conn.execute(text("SELECT COUNT(*) FROM boardings")).scalar()
    cols = [c for c in _columns(conn, "boardings") if c != "store_id"]
    col_list = ", ".join(cols)

    # 用模型声明重建一个临时表，搬运数据后替换
    from sqlalchemy.schema import CreateIndex, CreateTable
    tmp_name = "boardings__new"
    ddl_new = str(CreateTable(Boarding.__table__).compile(engine)).replace(
        "CREATE TABLE boardings", f"CREATE TABLE {tmp_name}", 1)
    conn.execute(text(ddl_new))
    conn.execute(text(
        f"INSERT INTO {tmp_name} ({col_list}) SELECT {col_list} FROM boardings"))
    conn.execute(text("DROP TABLE boardings"))
    conn.execute(text(f"ALTER TABLE {tmp_name} RENAME TO boardings"))
    for idx in Boarding.__table__.indexes:
        conn.execute(text(str(CreateIndex(idx).compile(engine))))
    return f"已重建（迁移 {n} 行数据）"


def _add_extra_columns(conn) -> list[str]:
    """补多租户改造后新增的普通列（门店状态 / 门店标语）。"""
    done = []
    for table, col, ddl in EXTRA_COLUMNS:
        cols = _columns(conn, table)
        if not cols or col in cols:
            continue
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))
        done.append(f"{table}.{col}")
    return done


def _normalize_enum_names(conn) -> list[str]:
    """把原始 DDL 写进去的小写枚举值归一成 SQLAlchemy 认的成员名。

    只对 ENUM_NAME_COLUMNS 里列出的列动手，避免误伤普通字符串列。
    """
    done = []
    for table, col, members in ENUM_NAME_COLUMNS:
        cols = _columns(conn, table)
        if not cols or col not in cols:
            continue
        for member in members:
            n = conn.execute(
                text(f"UPDATE {table} SET {col} = :m "
                     f"WHERE UPPER({col}) = :m AND {col} <> :m"),
                {"m": member},
            ).rowcount
            if n:
                done.append(f"{table}.{col} 归一 {n} 行 → {member}")
    return done


def _ensure_platform_rbac(db) -> list[str]:
    """建平台层 RBAC：stores 菜单 + super_admin 角色；并把平台权限从租户角色里摘干净。"""
    notes = []

    for (key, title, icon, sort) in PLATFORM_MENUS:
        if not db.query(Menu).filter(Menu.key == key).first():
            db.add(Menu(key=key, title=title, icon=icon, sort=sort))
            notes.append(f"新增菜单 {key}")
    db.commit()

    # 超管：全部平台权限 + 仅平台菜单
    admin = db.query(Role).filter(Role.key == StaffRole.SUPER_ADMIN.value).first()
    if not admin:
        admin = Role(key=StaffRole.SUPER_ADMIN.value, name="平台超管",
                     description="平台级，跨门店管理", permissions=[])
        db.add(admin)
        db.commit()
        db.refresh(admin)
        notes.append("新增角色 super_admin")
    admin.permissions = sorted(set(list(admin.permissions or []) + [p["code"] for p in PERMISSION_CATALOG]))
    existing = {rm.menu_key for rm in db.query(RoleMenu).filter(RoleMenu.role_id == admin.id)}
    new_keys = [k for k in SUPER_ADMIN_MENUS if k not in existing]
    if new_keys:
        db.add_all([RoleMenu(role_id=admin.id, menu_key=k) for k in new_keys])
        notes.append(f"超管绑定 {len(new_keys)} 个平台菜单")
    # 历史版本曾给超管绑过全部菜单，这里收回（否则他能在租户页造孤儿数据）
    stale = db.query(RoleMenu).filter(RoleMenu.role_id == admin.id,
                                      RoleMenu.menu_key.notin_(SUPER_ADMIN_MENUS)).all()
    if stale:
        for rm in stale:
            db.delete(rm)
        notes.append(f"超管收回 {len(stale)} 个租户菜单")
    db.commit()

    # 租户角色：绝不能持有平台权限与平台菜单（越权风险的根）
    for tenant_key in (StaffRole.MANAGER.value, StaffRole.EMPLOYEE.value):
        role = db.query(Role).filter(Role.key == tenant_key).first()
        if not role:
            continue
        perms = list(role.permissions or [])
        stripped = [p for p in perms if p not in PLATFORM_PERMISSION_CODES]
        if len(stripped) != len(perms):
            role.permissions = stripped
            notes.append(f"{tenant_key} 摘除平台权限 {len(perms) - len(stripped)} 项")
        bad = db.query(RoleMenu).filter(RoleMenu.role_id == role.id,
                                        RoleMenu.menu_key.in_(PLATFORM_MENU_KEYS)).all()
        if bad:
            for rm in bad:
                db.delete(rm)
            notes.append(f"{tenant_key} 摘除平台菜单 {len(bad)} 项")
        db.commit()

    return notes


def migrate() -> None:
    with engine.begin() as conn:
        # 1) 建缺失的表
        existing = set(engine.dialect.get_table_names(conn))
        Base.metadata.create_all(bind=engine)
        created = sorted(set(Base.metadata.tables) - existing)
        print("① 建表：" + ("、".join(created) if created else "无缺失表"))

        # 2) 补 store_id 列
        added = _add_store_columns(conn)
        print("② 补列：" + ("、".join(f"{t}.store_id" for t in added) if added else "无缺失列"))

        # 2b) 补其他新增列
        extra = _add_extra_columns(conn)
        print("③ 补列：" + ("、".join(extra) if extra else "无缺失列"))

        # 3) 约束变更
        print("④ 唯一键：" + _rebuild_boarding_if_needed(conn))

        # 4) 枚举脏值归一（原始 DDL 补列时可能写入了小写枚举值，ORM 读不了）
        fixed = _normalize_enum_names(conn)
        print("⑤ 枚举归一：" + ("；".join(fixed) if fixed else "无脏值"))

    db = SessionLocal()
    try:
        # 5) 平台层 RBAC（超管角色 / stores 菜单 / 摘除租户越权）
        notes = _ensure_platform_rbac(db)
        print("⑥ 平台 RBAC：" + ("；".join(notes) if notes else "已就绪"))

        # 6a) 默认门店 + 白标资料
        store = db.query(Store).order_by(Store.id).first()
        if not store:
            store = Store(name=DEFAULT_STORE_NAME)
            db.add(store)
            db.commit()
            db.refresh(store)
            print(f"⑦ 默认门店：新建 id={store.id} name={store.name}")
        else:
            print(f"⑦ 默认门店：已存在 id={store.id} name={store.name}")

        profile = db.query(StoreProfile).filter(StoreProfile.store_id == store.id).first()
        if profile:
            if profile.slug in ("default", "", None):
                target_slug = DEV_STORE_SLUG
                holder = db.query(StoreProfile).filter(StoreProfile.slug == target_slug).first()
                if holder and holder.store_id != store.id:
                    target_slug = f"{target_slug}-{store.id}"
                profile.slug = target_slug
            if not profile.slogan:
                profile.slogan = DEFAULT_STORE_SLOGAN
            if not profile.name:
                profile.name = DEFAULT_STORE_NAME
            if not profile.miniapp_name:
                profile.miniapp_name = profile.name or DEFAULT_STORE_NAME
            if profile.miniapp_entry_enabled is None:
                profile.miniapp_entry_enabled = True
            db.commit()
            print(f"   白标资料：已存在 slug={profile.slug} 主色={profile.primary_color}")
        else:
            slug = DEV_STORE_SLUG
            if db.query(StoreProfile).filter(StoreProfile.slug == slug).first():
                slug = f"{slug}-{store.id}"
            profile = StoreProfile(store_id=store.id, slug=slug, name=store.name,
                                   slogan=DEFAULT_STORE_SLOGAN,
                                   miniapp_name=store.name, miniapp_entry_enabled=True,
                                   primary_color=DEFAULT_PRIMARY_COLOR, theme_json={})
            db.add(profile)
            db.commit()
            print(f"   白标资料：新建 slug={profile.slug} 主色={profile.primary_color}")

        # 6b) 历史数据回填
        total = 0
        for model in SCOPED_MODELS:
            n = (db.query(model)
                 .filter(model.store_id.is_(None))
                 .update({model.store_id: store.id}, synchronize_session=False))
            if n:
                print(f"   {model.__tablename__}: {n} 行 → store_id={store.id}")
            total += n
        db.commit()
        print(f"⑧ 回填：共 {total} 行" + ("" if total else "（已无未打标数据）"))

        left = sum(db.query(m).filter(m.store_id.is_(None)).count() for m in SCOPED_MODELS)
        print(f"\n完成。未打标残留 {left} 行"
              + ("，隔离已为严格模式。" if left == 0 else "（请检查）"))
        print(f"C 端换肤入口：/api/c/store/profile?slug={profile.slug}")
        supers = db.query(Staff).filter(Staff.role == StaffRole.SUPER_ADMIN).count()
        print(f"超管账号数：{supers}"
              + ("" if supers else "  ← 还没有超管，跑 scripts/create_super_admin.py 创建" ))
        print("请重启 API 进程，让其加载新表结构。")
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
