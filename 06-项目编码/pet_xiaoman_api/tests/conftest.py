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
    from datetime import datetime
    return {
        "user_id": 1,
        "pet_name": "豆豆",
        "species": "犬",
        "pkg_id": seed["pkg_id"],
        "addon_ids": [],
        "expect_time": datetime.now().isoformat(),
        "address": "郑州市金水区XX路1号",
    }
