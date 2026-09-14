"""B 端补充功能测试：详情/备注/改期/价格版本（PRD B003/B005 验收标准）。"""
from datetime import datetime, timedelta

import io


def _seed_and_order(client, seed, token):
    """下一个已确认订单，返回 order_no。B 端接口需带员工 token（多租户鉴权）。"""
    H = {"Authorization": f"Bearer {token}"}
    pkg = {"type": "套餐", "name": "基础告别套餐", "price": 800,
           "version": "v20260905", "status": "在售"}
    resp = client.post("/api/b/service-items", json=pkg, headers=H)
    pkg_id = resp.json()["id"]
    order_no = client.post("/api/c/orders", json={
        "user_id": 1, "pet_name": "豆豆", "species": "犬", "pkg_id": pkg_id,
        "expect_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "address": "郑州市金水区",
    }).json()["order_no"]
    client.post(f"/api/b/orders/{order_no}/confirm", json={}, headers=H)
    return order_no, pkg_id


def test_b_detail_contains_media_and_notes(client, seed, org):
    """B003 详情：全字段 + 影像列表 + 备注可保存回读。"""
    H = {"Authorization": f"Bearer {org['manager_token']}"}
    order_no, _ = _seed_and_order(client, seed, org["manager_token"])
    client.post(f"/api/b/orders/{order_no}/media?node=接宠完成",
                files={"file": ("a.jpg", io.BytesIO(b"x"), "image/jpeg")}, headers=H)
    client.put(f"/api/b/orders/{order_no}/notes", json={"notes": "客户情绪低落，沟通放慢"}, headers=H)
    detail = client.get(f"/api/b/orders/{order_no}", headers=H).json()
    assert detail["notes"] == "客户情绪低落，沟通放慢"
    assert len(detail["media"]) == 1
    assert detail["pay_type"] == "未支付"


def test_reschedule_free_once_then_rejected(client, seed, org):
    """改期：免费 1 次，第二次拒绝（PRD §6.2）。"""
    H = {"Authorization": f"Bearer {org['manager_token']}"}
    order_no, _ = _seed_and_order(client, seed, org["manager_token"])
    first = client.post(f"/api/b/orders/{order_no}/reschedule",
                        json={"expect_time": (datetime.now() + timedelta(days=2)).isoformat()},
                        headers=H)
    assert first.status_code == 200
    assert first.json()["reschedule_count"] == 1
    second = client.post(f"/api/b/orders/{order_no}/reschedule",
                         json={"expect_time": (datetime.now() + timedelta(days=3)).isoformat()},
                         headers=H)
    assert second.status_code == 422
    assert "已用完" in second.json()["detail"]


def test_b_reschedule_past_time_rejected(client, seed, org):
    """B 端改期也不能改到过去时间，避免和 C 端规则不一致。"""
    H = {"Authorization": f"Bearer {org['manager_token']}"}
    order_no, _ = _seed_and_order(client, seed, org["manager_token"])
    resp = client.post(f"/api/b/orders/{order_no}/reschedule",
                       json={"expect_time": (datetime.now() - timedelta(days=1)).isoformat()},
                       headers=H)
    assert resp.status_code == 422
    assert "晚于现在" in resp.json()["detail"]


def test_manual_refund_task_can_be_closed(client, seed, db, org):
    """支付/退款第三方未开启时，后台可用人工退款任务闭环。"""
    from app.models.order import Order, PayType, RefundStatus
    from app.models.payment_record import BizType, PayStatus, PaymentRecord

    H = {"Authorization": f"Bearer {org['manager_token']}"}
    order_no, _ = _seed_and_order(client, seed, org["manager_token"])
    order = db.query(Order).filter(Order.order_no == order_no).first()
    order.pay_type = PayType.DEPOSIT_PAID
    order.paid_amount = 160
    db.add(PaymentRecord(order_id=order.id, store_id=order.store_id, biz_type=BizType.DEPOSIT,
                         amount=160, transaction_id="WX-REFUND-001", pay_status=PayStatus.SUCCESS))
    db.commit()

    cancel = client.post(f"/api/b/orders/{order_no}/transition",
                         json={"target": "已取消", "reason": "客户取消，需退定金"},
                         headers=H)
    assert cancel.status_code == 200
    detail = client.get(f"/api/b/orders/{order_no}", headers=H).json()
    assert detail["refund_status"] == "退款中"

    tasks = client.get("/api/b/refunds", headers=H).json()
    assert any(row["order_no"] == order_no for row in tasks)

    done = client.post(f"/api/b/orders/{order_no}/refund/mark",
                       json={"status": "已退款", "note": "微信商户后台已退"},
                       headers=H)
    assert done.status_code == 200
    assert done.json()["refund_status"] == "已退款"
    db.refresh(order)
    assert order.refund_status == RefundStatus.REFUNDED
    assert db.query(PaymentRecord).first().pay_status == PayStatus.REFUNDED


def test_price_update_creates_version_and_log(client, seed, db, org):
    """改价：新版本生效 + 版本流水落库；下架不删除。"""
    H = {"Authorization": f"Bearer {org['manager_token']}"}
    order_no, pkg_id = _seed_and_order(client, seed, org["manager_token"])
    detail_before = client.get(f"/api/b/orders/{order_no}", headers=H).json()
    price_before = detail_before["total_amount"]

    upd = client.put(f"/api/b/service-items/{pkg_id}",
                     json={"type": "套餐", "name": "基础告别套餐", "price": 880}, headers=H)
    assert upd.status_code == 200
    assert upd.json()["price_changed"] is True
    new_version = upd.json()["version"]

    log = client.get(f"/api/b/service-items/{pkg_id}/versions", headers=H).json()
    assert len(log) == 2  # 首版 + 改价版
    assert log[0]["version"] == new_version

    # 锁价回归：旧订单总额不变
    detail_after = client.get(f"/api/b/orders/{order_no}", headers=H).json()
    assert detail_after["total_amount"] == price_before

    # 下架：状态变更不删除
    off = client.post(f"/api/b/service-items/{pkg_id}/off-sale", headers=H)
    assert off.json()["status"] == "下架"
    assert client.get(f"/api/b/orders/{order_no}", headers=H).status_code == 200
