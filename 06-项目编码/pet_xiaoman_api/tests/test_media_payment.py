"""影像上传与支付回调测试：PRD §5.2.2 强制影像（服务端查库）/ §5.2.6 幂等落账与结清。"""
import io

from app.models.order import Order, PayType


def _upload(client, order_no, node="接宠完成", filename="photo.jpg"):
    return client.post(f"/api/b/orders/{order_no}/media?node={node}",
                       files={"file": (filename, io.BytesIO(b"fake-image-bytes"), "image/jpeg")})


def _new_confirmed_order(client, order_input):
    order_no = create_order(client, order_input)
    assert client.post(f"/api/b/orders/{order_no}/confirm", json={}).status_code == 200
    return order_no


def create_order(client, order_input):
    resp = client.post("/api/c/orders", json=order_input)
    assert resp.status_code == 200, resp.text
    return resp.json()["order_no"]


def test_upload_media_unlocks_transition_by_server_check(client, order_input):
    """强制影像改为服务端查库：不传影像流转被拦，上传接宠完成影像后放行。"""
    order_no = _new_confirmed_order(client, order_input)
    assert client.post(f"/api/b/orders/{order_no}/transition",
                       json={"target": "接宠中"}).status_code == 200
    # 无影像：流转服务中被拦（服务端查库校验，前端传 has_media=True 也无效）
    resp = client.post(f"/api/b/orders/{order_no}/transition",
                       json={"target": "服务中", "has_media": True})
    assert resp.status_code == 422
    assert "影像" in resp.json()["detail"]

    # 上传接宠完成影像 → 放行
    resp = _upload(client, order_no)
    assert resp.status_code == 200, resp.text
    resp = client.post(f"/api/b/orders/{order_no}/transition", json={"target": "服务中"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "服务中"


def test_upload_rejects_oversize_and_format(client, order_input):
    order_no = _new_confirmed_order(client, order_input)
    client.post(f"/api/b/orders/{order_no}/transition", json={"target": "接宠中"})
    big = client.post(f"/api/b/orders/{order_no}/media?node=接宠完成",
                      files={"file": ("big.jpg", io.BytesIO(b"0" * (10 * 1024 * 1024 + 1)), "image/jpeg")})
    assert big.status_code == 422
    bad = client.post(f"/api/b/orders/{order_no}/media?node=接宠完成",
                      files={"file": ("evil.gif", io.BytesIO(b"x"), "image/gif")})
    assert bad.status_code == 422


def test_media_visible_to_customer(client, order_input):
    order_no = _new_confirmed_order(client, order_input)
    _upload(client, order_no)
    media = client.get(f"/api/c/orders/{order_no}/media").json()
    assert len(media) == 1
    assert media[0]["node"] == "接宠完成"


def test_revoke_owner_only(client, order_input):
    order_no = _new_confirmed_order(client, order_input)
    media_id = _upload(client, order_no).json()["media_id"]
    # 店员（非店长）撤回 → 403
    resp = client.post(f"/api/b/media/{media_id}/revoke", json={"role": "店员", "reason": "误传"})
    assert resp.status_code == 403
    # 店长撤回 → 成功，且流转再次被拦（影像证据消失）
    resp = client.post(f"/api/b/media/{media_id}/revoke", json={"role": "店长", "reason": "照片拍错"})
    assert resp.status_code == 200
    resp = client.post(f"/api/b/orders/{order_no}/transition", json={"target": "服务中"})
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


def test_settle_offline_unlocks_completion(client, order_input):
    """到店付结清：标记实收 → pay_type=到店付已结清 → 可流转已完成。"""
    order_no = _new_confirmed_order(client, order_input)
    client.post(f"/api/b/orders/{order_no}/transition", json={"target": "接宠中"})
    client.post(f"/api/b/orders/{order_no}/media?node=接宠完成",
                files={"file": ("a.jpg", io.BytesIO(b"x"), "image/jpeg")})
    client.post(f"/api/b/orders/{order_no}/transition", json={"target": "服务中"})
    client.post(f"/api/b/orders/{order_no}/media?node=火化完成",
                files={"file": ("b.jpg", io.BytesIO(b"x"), "image/jpeg")})
    client.post(f"/api/b/orders/{order_no}/transition", json={"target": "待交付"})

    # 尾款不足被拒
    underpay = client.post(f"/api/b/orders/{order_no}/settle", json={"amount": 100})
    assert underpay.status_code == 422
    # 足额结清 → 已完成可流转
    resp = client.post(f"/api/b/orders/{order_no}/settle", json={"amount": 800})
    assert resp.status_code == 200
    assert resp.json()["pay_type"] == "到店付已结清"
    done = client.post(f"/api/b/orders/{order_no}/transition", json={"target": "已完成"})
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
