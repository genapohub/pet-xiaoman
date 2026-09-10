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


def init(reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    db = SessionLocal()
    try:
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
