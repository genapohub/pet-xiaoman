"""把历史（单店期）未打标数据回填到默认门店，使多租户隔离从「宽松」转为「严格」。

背景：多租户改造后，`store_id IS NULL` 的历史数据对任意门店可见（平滑迁移）。
把存量数据全部打标到默认门店后，NULL 消失，隔离即严格生效。

用法：
    env -u PYTHONPATH SQLITE_FALLBACK=true ./.venv/bin/python -m scripts.backfill_store_scope
"""
import os

os.environ.setdefault("SQLITE_FALLBACK", "true")

from app.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Boarding, Customer, Order, PaymentRecord, Pet, Product, ProductOrder,
    ServiceItem, ServiceMedia, VisitRecord,
)
from app.services.tenant import default_store_id  # noqa: E402

# 需要打标的租户表（与 StoreScopedModel 子类保持一致）
SCOPED_MODELS = [Order, Customer, Pet, ServiceItem, Product, ProductOrder,
                 Boarding, ServiceMedia, VisitRecord, PaymentRecord]


def backfill() -> None:
    db = SessionLocal()
    try:
        store_id = default_store_id(db)
        if store_id is None:
            print("无门店，跳过回填")
            return
        total = 0
        for model in SCOPED_MODELS:
            n = (db.query(model)
                 .filter(model.store_id.is_(None))
                 .update({model.store_id: store_id}, synchronize_session=False))
            if n:
                print(f"{model.__tablename__}: {n} 行 → store_id={store_id}")
            total += n
        db.commit()
        print(f"完成：共回填 {total} 行到默认门店 store_id={store_id}")
    finally:
        db.close()


if __name__ == "__main__":
    backfill()
