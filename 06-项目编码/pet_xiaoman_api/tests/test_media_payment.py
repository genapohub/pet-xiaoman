"""影像上传与支付回调测试：PRD §5.2.2 强制影像（服务端查库）/ §5.2.6 幂等落账与结清。"""
import io

from app.models.order import Order, PayType


def _upload(client, order_no, token, node="接宠完成", filename="photo.jpg"):
    # 多租户改造后：影像上传需员工 token（并据此落到本店）
    return client.post(f"/api/b/orders/{order_no}/media?node={node}",
                       files={"file": (filename, io.BytesIO(b"fake-image-bytes"), "image/jpeg")},
                       headers={"Authorization": f"Bearer {token}"})


def _new_confirmed_order(client, order_input, token):
    order_no = create_order(client, order_input)
    assert client.post(f"/api/b/orders/{order_no}/confirm", json={},
                       headers={"Authorization": f"Bearer {token}"}).status_code == 200
    return order_no


def create_order(client, order_input):
    resp = client.post("/api/c/orders", json=order_input)
    assert resp.status_code == 200, resp.text
    return resp.json()["order_no"]


def test_upload_media_unlocks_transition_by_server_check(client, order_input, org):
    """强制影像改为服务端查库：不传影像流转被拦，上传接宠完成影像后放行。"""
    H = {"Authorization": f"Bearer {org['manager_token']}"}
    order_no = _new_confirmed_order(client, order_input, org["manager_token"])
    assert client.post(f"/api/b/orders/{order_no}/transition",
                       json={"target": "接宠中"}, headers=H).status_code == 200
    # 无影像：流转服务中被拦（服务端查库校验，前端传 has_media=True 也无效）
    resp = client.post(f"/api/b/orders/{order_no}/transition",
                       json={"target": "服务中", "has_media": True}, headers=H)
    assert resp.status_code == 422
    assert "影像" in resp.json()["detail"]

    # 上传接宠完成影像 → 放行
    resp = _upload(client, order_no, org["manager_token"])
    assert resp.status_code == 200, resp.text
    resp = client.post(f"/api/b/orders/{order_no}/transition", json={"target": "服务中"}, headers=H)
    assert resp.status_code == 200
    assert resp.json()["status"] == "服务中"


def test_upload_rejects_oversize_and_format(client, order_input, org):
    order_no = _new_confirmed_order(client, order_input, org["manager_token"])
    H = {"Authorization": f"Bearer {org['manager_token']}"}
    client.post(f"/api/b/orders/{order_no}/transition", json={"target": "接宠中"}, headers=H)
    big = client.post(f"/api/b/orders/{order_no}/media?node=接宠完成",
                      files={"file": ("big.jpg", io.BytesIO(b"0" * (10 * 1024 * 1024 + 1)), "image/jpeg")},
                      headers=H)
    assert big.status_code == 422
    bad = client.post(f"/api/b/orders/{order_no}/media?node=接宠完成",
                      files={"file": ("evil.gif", io.BytesIO(b"x"), "image/gif")}, headers=H)
    assert bad.status_code == 422


def test_media_visible_to_customer(client, order_input, org):
    order_no = _new_confirmed_order(client, order_input, org["manager_token"])
    _upload(client, order_no, org["manager_token"])
    media = client.get(f"/api/c/orders/{order_no}/media").json()
    assert len(media) == 1
    assert media[0]["node"] == "接宠完成"


def test_revoke_owner_only(client, order_input, org):
    """影像撤回仅店长可操作（RBAC media.revoke）；店员 → 403。"""
    order_no = _new_confirmed_order(client, order_input, org["manager_token"])
    media_id = _upload(client, order_no, org["manager_token"]).json()["media_id"]
    HE = {"Authorization": f"Bearer {org['employee_token']}"}
    HM = {"Authorization": f"Bearer {org['manager_token']}"}
    # 店员（无 media.revoke 权限）撤回 → 403
    resp = client.post(f"/api/b/media/{media_id}/revoke", json={"reason": "误传"}, headers=HE)
    assert resp.status_code == 403
    # 店长撤回 → 成功，且流转再次被拦（影像证据消失）
    resp = client.post(f"/api/b/media/{media_id}/revoke", json={"reason": "照片拍错"}, headers=HM)
    assert resp.status_code == 200
    resp = client.post(f"/api/b/orders/{order_no}/transition", json={"target": "服务中"}, headers=HM)
    assert resp.status_code == 422


def test_pay_callback_requires_verify(client, order_input, db):
    """fail-check：验签失败 → FAIL 且不落账（PAY_ENABLED=false 时验签层直接拒绝）。"""
    order_no = create_order(client, order_input)
    resp = client.post("/api/pay/notify/wechat",
                       content=b'{"order_no": "%s", "amount": 800, "transaction_id": "WX001"}' % order_no.encode(),
                       headers={"signature": "", "timestamp": "", "nonce": ""})
    assert resp.json()["code"] == "FAIL"
    from app.models.payment_record import PaymentRecord
    assert db.query(PaymentRecord).count() == 0


def test_pay_config_reports_missing_when_enabled(monkeypatch):
    """PAY_ENABLED=true 但商户资料没配齐时，接口给出可理解的缺失项。"""
    from app import config
    from app.services import payment

    monkeypatch.setattr(config.settings, "PAY_ENABLED", True)
    monkeypatch.setattr(config.settings, "WX_APPID", "")
    status = payment.pay_config_status()
    assert status["ready"] is False
    assert "WX_APPID" in status["missing"]


def test_jsapi_params_call_wechat_when_configured(monkeypatch):
    """配置齐全后：后端可完成 v3 JSAPI 下单并返回小程序调起支付参数。"""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    from app import config
    from app.services import payment

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()

    monkeypatch.setattr(config.settings, "PAY_ENABLED", True)
    monkeypatch.setattr(config.settings, "WX_APPID", "wx667ddd8e0d8dd8fb")
    monkeypatch.setattr(config.settings, "WX_MCH_ID", "1900000001")
    monkeypatch.setattr(config.settings, "WX_PAY_SERIAL_NO", "ABC123SERIAL")
    monkeypatch.setattr(config.settings, "WX_PAY_NOTIFY_URL", "https://example.com/api/pay/notify/wechat")
    monkeypatch.setattr(config.settings, "WX_PAY_API_V3_KEY", "a" * 32)
    monkeypatch.setattr(config.settings, "WX_PAY_PRIVATE_KEY", private_pem)
    monkeypatch.setattr(config.settings, "WX_PAY_PRIVATE_KEY_PATH", "")

    seen = {}

    class FakeResp:
        status_code = 200

        @staticmethod
        def json():
            return {"prepay_id": "wx-prepay-001"}

    def fake_post(url, content, headers, timeout):
        seen["url"] = url
        seen["content"] = content
        seen["headers"] = headers
        return FakeResp()

    monkeypatch.setattr(payment.httpx, "post", fake_post)
    params = payment.create_jsapi_params("PXM202609130001", 12.34, "openid-001")

    assert seen["url"].endswith("/v3/pay/transactions/jsapi")
    assert '"total":1234' in seen["content"]
    assert seen["headers"]["Authorization"].startswith("WECHATPAY2-SHA256-RSA2048")
    assert params["package"] == "prepay_id=wx-prepay-001"
    assert params["signType"] == "RSA"
    assert params["paySign"]


def test_settle_offline_unlocks_completion(client, order_input, org):
    """到店付结清：标记实收 → pay_type=到店付已结清 → 可流转已完成。"""
    H = {"Authorization": f"Bearer {org['manager_token']}"}
    order_no = _new_confirmed_order(client, order_input, org["manager_token"])
    client.post(f"/api/b/orders/{order_no}/transition", json={"target": "接宠中"}, headers=H)
    client.post(f"/api/b/orders/{order_no}/media?node=接宠完成",
                files={"file": ("a.jpg", io.BytesIO(b"x"), "image/jpeg")}, headers=H)
    client.post(f"/api/b/orders/{order_no}/transition", json={"target": "服务中"}, headers=H)
    client.post(f"/api/b/orders/{order_no}/media?node=火化完成",
                files={"file": ("b.jpg", io.BytesIO(b"x"), "image/jpeg")}, headers=H)
    client.post(f"/api/b/orders/{order_no}/transition", json={"target": "待交付"}, headers=H)

    # 尾款不足被拒
    underpay = client.post(f"/api/b/orders/{order_no}/settle", json={"amount": 100}, headers=H)
    assert underpay.status_code == 422
    # 足额结清 → 已完成可流转
    resp = client.post(f"/api/b/orders/{order_no}/settle", json={"amount": 800}, headers=H)
    assert resp.status_code == 200
    assert resp.json()["pay_type"] == "到店付已结清"
    done = client.post(f"/api/b/orders/{order_no}/transition", json={"target": "已完成"}, headers=H)
    assert done.status_code == 200


def test_apply_payment_idempotent_deposit_then_full(client, order_input, db):
    """幂等落账：定金回调 → 补全款回调 → 全款已付（paid_amount 累加）；重复 txid 只落账一次。"""
    from app.models.order import Order, PayType
    from app.services import payment_service
    from app.services.payment import PayResult

    order_no = create_order(client, order_input)
    order = db.query(Order).filter(Order.order_no == order_no).first()

    r1 = payment_service.apply_payment(db, order, PayResult(order_no, 160, "WX-D1"))
    assert r1["duplicated"] is False
    assert order.pay_type == PayType.DEPOSIT_PAID
    assert float(order.paid_amount) == 160.0

    r2 = payment_service.apply_payment(db, order, PayResult(order_no, 640, "WX-F1"))
    assert r2["duplicated"] is False
    assert order.pay_type == PayType.FULL_PAID
    assert float(order.paid_amount) == 800.0  # 累加而非覆盖（回归：v1.1 框架 bug）

    r3 = payment_service.apply_payment(db, order, PayResult(order_no, 640, "WX-F1"))
    assert r3["duplicated"] is True
