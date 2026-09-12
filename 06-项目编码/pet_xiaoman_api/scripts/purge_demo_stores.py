"""清理自检/演示产生的门店（只动白名单里的 slug，绝碰不到真实门店）。

背景：本地库目前没有「删除门店」功能（只有停用，避免误删数据），
     所以自检造出来的演示店需要在这里显式回收。

用法：
    # 先看要删什么（不落库）
    env -u PYTHONPATH SQLITE_FALLBACK=true ./.venv/bin/python -m scripts.purge_demo_stores
    # 确认后执行
    env -u PYTHONPATH SQLITE_FALLBACK=true ./.venv/bin/python -m scripts.purge_demo_stores --apply
"""
import os
import sys

os.environ.setdefault("SQLITE_FALLBACK", "true")

from app.database import SessionLocal  # noqa: E402
from app.models.staff import Staff, Store  # noqa: E402
from app.models.store_profile import StoreProfile  # noqa: E402
from scripts.backfill_store_scope import SCOPED_MODELS  # noqa: E402

# 只允许删这些 slug（自检/演示用）；不在名单里的一律不动
DEMO_SLUGS = ["meow-api-check", "demo-meow", "ui-check"]


def purge(apply: bool) -> None:
    db = SessionLocal()
    try:
        profiles = db.query(StoreProfile).filter(StoreProfile.slug.in_(DEMO_SLUGS)).all()
        if not profiles:
            print("没有需要清理的演示门店。")
            return

        targets = []
        for p in profiles:
            staff = db.query(Staff).filter(Staff.store_id == p.store_id).count()
            targets.append((p.store_id, p.slug, p.name, staff))

        print(f"{'将删除' if apply else '[预演] 将删除'} {len(targets)} 家演示门店：")
        for sid, slug, name, staff in targets:
            print(f"  store_id={sid}  slug={slug}  name={name}  账号={staff}")

        # 安全闸：绝不删最后一家门店（否则整个后台就没有可用门店了）
        total_stores = db.query(Store).count()
        if total_stores - len(targets) < 1:
            print(f"\n拒绝执行：现有门店 {total_stores} 家，删掉这 {len(targets)} 家就没有门店了。")
            return

        if not apply:
            print("\n以上为预演。确认无误后加 --apply 真正执行。")
            return

        for sid, slug, _name, _staff in targets:
            for model in SCOPED_MODELS:
                n = (db.query(model).filter(model.store_id == sid)
                     .delete(synchronize_session=False))
                if n:
                    print(f"  {model.__tablename__}: 删 {n} 行")
            n = db.query(Staff).filter(Staff.store_id == sid).delete(synchronize_session=False)
            print(f"  staff: 删 {n} 行")
            n = db.query(StoreProfile).filter(StoreProfile.store_id == sid).delete(synchronize_session=False)
            print(f"  store_profiles: 删 {n} 行")
            db.query(Store).filter(Store.id == sid).delete(synchronize_session=False)
            print(f"  stores: 删 id={sid} ({slug})")
        db.commit()
        print(f"\n完成，剩余门店 {db.query(Store).count()} 家：")
        for s in db.query(Store).all():
            p = db.query(StoreProfile).filter(StoreProfile.store_id == s.id).first()
            print(f"  id={s.id}  {s.name}  slug={p.slug if p else '-'}")
    finally:
        db.close()


if __name__ == "__main__":
    purge(apply="--apply" in sys.argv)
