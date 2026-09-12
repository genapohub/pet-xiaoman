"""把默认示例门店的历史店长账号迁移到新账号（清掉旧 admin 残留）。

背景：本地种子曾把默认店长定为 admin / admin123。后来默认门店示例改为宠小满，
     店长账号也跟着叫 petxiaoman / petxiaoman123（与门店品牌一致、好记）。
     老库里还留着 admin 账号 + 一些自检残留账号，这里一并清理。

职责边界（与配套脚本的区别）：
  - scripts/init_local_db.py          —— 建表 + 新库种子（idempotent）
  - scripts/purge_demo_stores.py      —— 回收自检/演示门店（按 slug 白名单）
  - scripts/migrate_dev_accounts.py   —— 本脚本：默认店长账号对齐 + 残留账号清理（按 username 白名单）

用法：
    # 先看会动什么（不落库）
    env -u PYTHONPATH SQLITE_FALLBACK=true ./.venv/bin/python -m scripts.migrate_dev_accounts
    # 确认后执行
    env -u PYTHONPATH SQLITE_FALLBACK=true ./.venv/bin/python -m scripts.migrate_dev_accounts --apply
"""
import os
import sys

os.environ.setdefault("SQLITE_FALLBACK", "true")

from app.database import SessionLocal  # noqa: E402
from app.models.staff import Staff, Store, StaffRole, StaffStatus  # noqa: E402
from app.models.store_profile import StoreProfile  # noqa: E402
from app.services.staff_auth_service import hash_password  # noqa: E402

# 目标：默认示例门店 = 宠小满 的店长。改这个 = 改种子默认值，记得同步 init_local_db.py。
TARGET_USERNAME = "petxiaoman"
TARGET_PASSWORD = "petxiaoman123"

# 默认示例门店用 slug 定位（不是「第一家门店」—— 否则 E2E 自检店也可能误中）。
DEFAULT_STORE_SLUG = "chongxiaoman"

# 历史/残留账号白名单：只删这些，绝不碰别的工作账号
LEGACY_MANAGER_USERNAMES = ["admin"]      # 历史默认店长
RESIDUE_STAFF_USERNAMES = ["pet_xiaoman01"]  # 历史自检残留（店员）


def _default_store_id(db) -> int | None:
    p = db.query(StoreProfile).filter(StoreProfile.slug == DEFAULT_STORE_SLUG).first()
    return p.store_id if p else None


def _plan(db) -> dict:
    """幂等地算出当前→目标的变更集合，不落库。"""
    plan = {
        "default_store_id": _default_store_id(db),
        "target_user": {"username": TARGET_USERNAME, "password": TARGET_PASSWORD},
        "rename": None,        # (old_username -> petxiaoman, store_id) 需要把谁的 username 改掉
        "create": False,       # 是否要新建 petxiaoman
        "reset_pw": False,     # petxiaoman 已存在，是否要重置密码
        "delete_users": [],    # 要删的 (username, store_id, role)
    }

    sid = plan["default_store_id"]
    if sid is None:
        return plan

    existing_target = db.query(Staff).filter(Staff.username == TARGET_USERNAME).first()
    if existing_target:
        # 已存在 petxiaoman —— 只重置密码（保证 DEV_MANAGER_PASS 一致）
        plan["reset_pw"] = True
    else:
        # 在默认店里找「能改成 petxiaoman」的店长
        mgr_on_default = (db.query(Staff)
                          .filter(Staff.store_id == sid, Staff.role == StaffRole.MANAGER)
                          .all())
        if not mgr_on_default:
            plan["create"] = True
        else:
            # 优先改「admin」（历史默认），否则改第一家店长
            legacy = next((m for m in mgr_on_default if m.username in LEGACY_MANAGER_USERNAMES), None)
            victim = legacy or mgr_on_default[0]
            plan["rename"] = (victim.username, sid, victim.id)

    # 残留账号：先看默认店里有没有要删的（删前要确认不是 petxiaoman / 不是被保留的店长）
    for username in LEGACY_MANAGER_USERNAMES + RESIDUE_STAFF_USERNAMES:
        rows = db.query(Staff).filter(Staff.username == username).all()
        for r in rows:
            # 改名目标行（victim）不要重复删：它会被改名到 petxiaoman，等于「admin 已不存在」
            if plan["rename"] and r.id == plan["rename"][2]:
                continue
            plan["delete_users"].append((r.username, r.store_id, r.role, r.id))

    return plan


def _print_plan(plan, apply: bool) -> None:
    sid = plan["default_store_id"]
    if sid is None:
        print("没找到默认示例门店（slug=chongxiaoman）。先跑 scripts/init_local_db.py 建库。")
        return
    print(f"默认门店：store_id={sid}（slug={DEFAULT_STORE_SLUG}）")
    print(f"目标店长：{TARGET_USERNAME} / {TARGET_PASSWORD}")

    actions = []
    if plan["rename"]:
        actions.append(f"改 {plan['rename'][0]!r} 的 username → {TARGET_USERNAME}（store_id={plan['rename'][1]}），并重置密码")
    elif plan["create"]:
        actions.append(f"新建店长 {TARGET_USERNAME}（store_id={sid}）")
    elif plan["reset_pw"]:
        actions.append(f"重置 {TARGET_USERNAME} 的密码为 {TARGET_PASSWORD}")

    for u, s, r, _id in plan["delete_users"]:
        actions.append(f"删残留账号 {u!r}（store_id={s} role={r}）")

    tag = "[将执行]" if apply else "[预演]"
    if not actions:
        print(f"{tag} 无需变更（已是目标状态）。")
    for a in actions:
        print(f"{tag} {a}")


def _apply(plan) -> None:
    sid = plan["default_store_id"]
    if sid is None:
        return

    if plan["rename"]:
        _, _, victim_id = plan["rename"]
        v = db.get(Staff, victim_id)
        v.username = TARGET_USERNAME
        v.password_hash = hash_password(TARGET_PASSWORD)
        v.status = StaffStatus.ACTIVE
        print(f"  ✓ {plan['rename'][0]} → {TARGET_USERNAME}（密码已重置）")
    elif plan["create"]:
        db.add(Staff(username=TARGET_USERNAME, password_hash=hash_password(TARGET_PASSWORD),
                     name="示例店长", role=StaffRole.MANAGER, store_id=sid,
                     manager_id=None, status=StaffStatus.ACTIVE))
        print(f"  ✓ 新建店长 {TARGET_USERNAME}")
    elif plan["reset_pw"]:
        v = db.query(Staff).filter(Staff.username == TARGET_USERNAME).first()
        v.password_hash = hash_password(TARGET_PASSWORD)
        v.status = StaffStatus.ACTIVE
        print(f"  ✓ 重置 {TARGET_USERNAME} 密码")

    for u, _s, _r, uid in plan["delete_users"]:
        n = db.query(Staff).filter(Staff.id == uid).delete(synchronize_session=False)
        if n:
            print(f"  ✓ 删残留账号 {u!r}（{n} 行）")

    db.commit()


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    db = SessionLocal()
    try:
        plan = _plan(db)
        _print_plan(plan, apply)
        if not apply:
            print("\n以上为预演。确认无误后加 --apply 真正执行。")
        elif any([plan["rename"], plan["create"], plan["reset_pw"], plan["delete_users"]]):
            _apply(plan)
            # 再跑一次 plan 确认落库后状态
            after = _plan(db)
            print("\n--- 落库后复查 ---")
            _print_plan(after, apply=True)
    finally:
        db.close()