"""C 端补充接口测试：公开价格表（只出在售）/ 轻量注册 / 宠物档案含历史。"""
from datetime import datetime

import pytest


@pytest.fixture
def seeded(client, db):
    from app.models.customer import Customer
    from app.models.order import Order
    from app.models.pet import Pet
    from app.models.service_item import ItemType, ServiceItem
    on = ServiceItem(type=ItemType.PACKAGE, name="在售套餐", price=800, version="v1")
    off = ServiceItem(type=ItemType.SINGLE, name="下架单项", price=99, version="v1")
    off.status = "下架"
    db.add_all([on, off])
    c = Customer(nickname="张三", phone="13800001111")
    db.add(c)
    db.flush()
    pet = Pet(name="豆豆", owner_id=c.id)
    db.add(pet)
    db.flush()
    order = Order(order_no="GDTEST900", user_id=c.id, pet_id=pet.id, pkg_id=on.id,
                  price_version="v1", expect_time=datetime.now(), total_amount=800,
                  status="已完成")
    db.add(order)
    db.commit()
    return {"customer_id": c.id, "pet_id": pet.id, "on_id": on.id, "off_id": off.id}


def test_price_list_only_on_sale(client, seeded):
    rows = client.get("/api/c/service-items").json()
    ids = [r["id"] for r in rows]
    assert seeded["on_id"] in ids
    assert seeded["off_id"] not in ids


def test_customer_register_returns_id(client):
    resp = client.post("/api/c/customers", json={"nickname": "微信用户"})
    assert resp.status_code == 200
    assert "customer_id" in resp.json()


def test_subscribe_config_from_env(client, monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "SUBSCRIBE_TEMPLATE_IDS", ["tmpl-order", "tmpl-done"])
    resp = client.get("/api/c/subscribe/config")
    assert resp.status_code == 200
    assert resp.json() == {"enabled": True, "template_ids": ["tmpl-order", "tmpl-done"]}


def test_integrations_config_is_configurable_without_secrets(client, monkeypatch):
    """支付/订阅/地图都先按配置位暴露状态，不把密钥下发到 C 端。"""
    from app import config

    monkeypatch.setattr(config.settings, "PAY_ENABLED", False)
    monkeypatch.setattr(config.settings, "SUBSCRIBE_TEMPLATE_IDS", ["tmpl-order"])
    monkeypatch.setattr(config.settings, "MAP_PROVIDER", "tencent")
    monkeypatch.setattr(config.settings, "MAP_PICKER_ENABLED", False)
    monkeypatch.setattr(config.settings, "MAP_KEY", "secret-map-key")

    data = client.get("/api/c/integrations/config").json()
    assert data["payment"]["enabled"] is False
    assert data["payment"]["fallback"] == "到店付"
    assert data["subscribe"]["template_count"] == 1
    assert data["map"]["provider"] == "tencent"
    assert data["map"]["picker_enabled"] is False
    assert data["map"]["key_configured"] is True
    assert "secret-map-key" not in str(data)


def test_pets_with_order_history(client, seeded):
    resp = client.get("/api/c/pets", params={"user_id": seeded["customer_id"]})
    assert resp.status_code == 200
    pets = resp.json()
    assert len(pets) == 1
    assert pets[0]["name"] == "豆豆"
    assert pets[0]["orders"][0]["order_no"] == "GDTEST900"


def test_pets_empty_for_unknown_user(client):
    resp = client.get("/api/c/pets", params={"user_id": 99999})
    assert resp.status_code == 200
    assert resp.json() == []
