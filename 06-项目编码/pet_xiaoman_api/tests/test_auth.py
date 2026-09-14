"""微信登录测试：dev 模式发 token / me / 身份一致性 / 强制模式 401（PRD 微信登录接入）。"""
import os

import pytest


@pytest.fixture
def seeded_customer(client, db):
    from app.models.customer import Customer
    c = Customer(nickname="登录测试", phone="13800009999")
    db.add(c)
    db.commit()
    return {"customer_id": c.id}


def test_dev_login_issues_token(client, seeded_customer):
    """开关关闭时 dev 模式：customer_id 直换有效 token。"""
    resp = client.post("/api/c/auth/login",
                       json={"customer_id": seeded_customer["customer_id"]})
    assert resp.status_code == 200
    token = resp.json()["token"]
    assert token.count(".") == 2
    me = client.get("/api/c/auth/me", headers={"X-Customer-Token": token}).json()
    assert me["logged_in"] is True
    assert me["customer_id"] == seeded_customer["customer_id"]
    assert me["nickname"] == "登录测试"
    assert me["phone_masked"] == "138****9999"


def test_invalid_token_rejected(client):
    me = client.get("/api/c/auth/me", headers={"X-Customer-Token": "bad.token.here"})
    assert me.status_code == 401


def test_token_user_mismatch_403(client, seeded_customer, order_input):
    """token 与请求体 user_id 不一致 → 403（防伪造他人身份下单）。"""
    login = client.post("/api/c/auth/login",
                        json={"customer_id": seeded_customer["customer_id"]}).json()
    headers = {"X-Customer-Token": login["token"]}
    resp = client.post("/api/c/orders", json={**order_input, "user_id": 999},
                       headers=headers)
    assert resp.status_code == 403
    assert "身份不匹配" in resp.json()["detail"]
    # 一致时放行
    ok = client.post("/api/c/orders",
                     json={**order_input, "user_id": seeded_customer["customer_id"]},
                     headers=headers)
    assert ok.status_code == 200


def test_legacy_mode_allows_no_token(client, order_input):
    """WX_LOGIN_ENABLED=false（legacy）：无 token 仍可按 user_id 下单。"""
    assert client.post("/api/c/orders", json=order_input).status_code == 200


def test_forced_mode_requires_token(client, order_input, monkeypatch):
    """WX_LOGIN_ENABLED=true：无 token → 401（强制模式）。"""
    monkeypatch.setenv("WX_LOGIN_ENABLED", "true")
    # 环境变量在 Settings 类属性加载时读取，需重载配置对象
    from app import config
    monkeypatch.setattr(config.settings, "WX_LOGIN_ENABLED", True)

    resp = client.post("/api/c/orders", json=order_input)
    assert resp.status_code == 401
    assert "请先登录" in resp.json()["detail"]


def test_code_mode_without_config_rejected(client, monkeypatch):
    """开关开但未配 appid/secret → 明确报错（fail-check）。"""
    from app import config
    monkeypatch.setattr(config.settings, "WX_LOGIN_ENABLED", True)
    monkeypatch.setattr(config.settings, "WX_APPID", "")
    monkeypatch.setattr(config.settings, "WX_SECRET", "")
    resp = client.post("/api/c/auth/login", json={"code": "any-code"})
    assert resp.status_code == 422
    assert "配置缺失" in resp.json()["detail"]
