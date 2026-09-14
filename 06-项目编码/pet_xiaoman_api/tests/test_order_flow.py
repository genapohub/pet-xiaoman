"""订单主链路测试：PRD §5.2.1/§5.2.2/§6.4 验收标准直接转用例。"""
from datetime import datetime

from app.services.order_service import is_night_order


def create(client, order_input, **override):
    payload = {**order_input, **override}
    resp = client.post("/api/c/orders", json=payload)
    return resp


def test_create_order_generates_order_no_and_locked_price(client, order_input):
    """AC1：提交预约生成 GD+日期+序号、状态待确认、按当前版本锁价。"""
    resp = create(client, order_input)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["order_no"].startswith(f"GD{datetime.now().strftime('%Y%m%d')}")
    assert data["status"] == "待确认"
    assert data["total_amount"] == 800.0
    assert data["price_version"] == "v20260905"
    assert "30 分钟内确认" in data["message"]


def test_create_order_with_addon_sums_total(client, order_input, seed):
    """加购计入总额：800 + 50 = 850。"""
    resp = create(client, order_input, addon_ids=[seed["addon_id"]])
    assert resp.status_code == 200
    assert resp.json()["total_amount"] == 850.0


def test_create_order_rejects_offsale_addon(client, order_input, seed):
    """下架加购项 → 422 且文案可读（PRD 异常处理）。"""
    resp = create(client, order_input, addon_ids=[seed["off_id"]])
    assert resp.status_code == 422
    assert "不可用" in resp.json()["detail"]


def test_duplicate_active_order_rejected(client, order_input):
    """AC3：同客户存在进行中订单时重复下单被拦截（网络重试场景由幂等拦截兜底）。"""
    assert create(client, order_input).status_code == 200
    resp = create(client, order_input)
    assert resp.status_code == 422
    assert "进行中的订单" in resp.json()["detail"]


def test_price_locked_after_item_price_change(client, order_input, db, seed):
    """锁价：下单后改套餐价，已建订单总额不变（PRD §5.2.1 业务规则③）。"""
    from app.models.service_item import ServiceItem
    resp = create(client, order_input)
    assert resp.status_code == 200
    pkg = db.get(ServiceItem, seed["pkg_id"])
    pkg.price = 880
    db.commit()
    detail = client.get(f"/api/c/orders/{resp.json()['order_no']}").json()
    assert detail["total_amount"] == 800.0


def test_cancel_with_deposit_triggers_refund(client, order_input, db):
    """退款规则：已付定金订单在接宠前取消 → 全额转退款（PRD §5.2.6）。"""
    from app.models.order import Order, PayType, RefundStatus
    resp = create(client, order_input)
    order_no = resp.json()["order_no"]
    order = db.query(Order).filter(Order.order_no == order_no).first()
    order.pay_type = PayType.DEPOSIT_PAID
    order.paid_amount = 160
    db.commit()

    resp = client.post(f"/api/c/orders/{order_no}/cancel", json={"reason": "改期不成"})
    data = resp.json()
    assert data["status"] == "已取消"
    assert data["refund_status"] == "退款中"
    assert "原路退回" in data["message"]


def test_cancel_in_service_rejected(client, order_input, db, org):
    """服务中订单客户不可直接取消（PRD §6.4：已发生服务）。"""
    from app.models.order import Order
    H = {"Authorization": f"Bearer {org['manager_token']}"}
    order_no = create(client, order_input).json()["order_no"]
    assert client.post(f"/api/b/orders/{order_no}/confirm", json={}, headers=H).status_code == 200
    order = db.query(Order).filter(Order.order_no == order_no).first()
    order.status = "服务中"
    db.commit()

    resp = client.post(f"/api/c/orders/{order_no}/cancel", json={})
    assert resp.status_code == 422
    assert "请联系门店" in resp.json()["detail"]


def test_reschedule_once_succeeds_with_quota_left(client, order_input):
    """C 端免费改期：第一次成功，返回 quota_left=0；订单的 expect_time 更新。"""
    from datetime import datetime, timedelta
    new_time = (datetime.now() + timedelta(days=2)).replace(microsecond=0).isoformat()
    order_no = create(client, order_input).json()["order_no"]

    resp = client.post(f"/api/c/orders/{order_no}/reschedule", json={"expect_time": new_time})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["reschedule_count"] == 1
    assert data["reschedule_quota_left"] == 0
    assert data["expect_time"].startswith(new_time[:16])

    detail = client.get(f"/api/c/orders/{order_no}").json()
    assert detail["reschedule_count"] == 1
    assert detail["reschedule_quota_left"] == 0


def test_reschedule_twice_rejected(client, order_input):
    """C 端免费改期：第二次必须被拒（PRD §6.2 免费 1 次），前端引导「请联系店长」。"""
    from datetime import datetime, timedelta
    order_no = create(client, order_input).json()["order_no"]
    for _ in range(2):
        client.post(f"/api/c/orders/{order_no}/reschedule",
                    json={"expect_time": (datetime.now() + timedelta(days=2)).isoformat()})

    resp = client.post(f"/api/c/orders/{order_no}/reschedule",
                       json={"expect_time": (datetime.now() + timedelta(days=3)).isoformat()})
    assert resp.status_code == 422
    assert "请联系店长" in resp.json()["detail"]


def test_reschedule_in_service_rejected(client, order_input, db, org):
    """服务中订单不可改期（接宠完成 → 走门店人工通道）。"""
    from datetime import datetime, timedelta
    from app.models.order import Order
    H = {"Authorization": f"Bearer {org['manager_token']}"}
    order_no = create(client, order_input).json()["order_no"]
    assert client.post(f"/api/b/orders/{order_no}/confirm", json={}, headers=H).status_code == 200
    order = db.query(Order).filter(Order.order_no == order_no).first()
    order.status = "服务中"
    db.commit()

    resp = client.post(f"/api/c/orders/{order_no}/reschedule",
                       json={"expect_time": (datetime.now() + timedelta(days=1)).isoformat()})
    assert resp.status_code == 422
    assert "请联系门店" in resp.json()["detail"]


def test_reschedule_to_past_time_rejected(client, order_input):
    """改期到过去时间必须被拒（业务校验，不允许把订单改回历史）。"""
    from datetime import datetime, timedelta
    order_no = create(client, order_input).json()["order_no"]
    resp = client.post(f"/api/c/orders/{order_no}/reschedule",
                       json={"expect_time": (datetime.now() - timedelta(days=1)).isoformat()})
    assert resp.status_code == 422
    assert "晚于现在" in resp.json()["detail"]


def test_transition_full_path_requires_media_and_settlement(client, order_input, db, org):
    """主链路流转：确认→接宠中→服务中（需影像）→待交付（需影像）→已完成（需结清）。"""
    H = {"Authorization": f"Bearer {org['manager_token']}"}
    order_no = create(client, order_input).json()["order_no"]
    import io
    upload = lambda node: client.post(f"/api/b/orders/{order_no}/media?node={node}",
                                      files={"file": (f"{node}.jpg", io.BytesIO(b"x"), "image/jpeg")},
                                      headers=H)
    path = [
        ("confirm", {}, "已预约"),
        ("transition", {"target": "接宠中"}, "接宠中"),
        ("transition", {"target": "服务中", "has_media": True}, "服务中"),  # has_media 被忽略，见下
        ("transition", {"target": "待交付", "has_media": True}, "待交付"),
        ("transition", {"target": "已完成"}, None),  # 未结清，应被拦截
    ]
    # 影像由服务端查库校验：流转前需真实上传对应节点影像
    assert upload("接宠完成").status_code == 200
    assert upload("火化完成").status_code == 200
    for action, payload, expected in path:
        resp = client.post(f"/api/b/orders/{order_no}/{action}", json=payload, headers=H)
        if expected is None:
            assert resp.status_code == 422
            assert "未结清" in resp.json()["detail"]
        else:
            assert resp.status_code == 200, resp.text
            assert resp.json()["status"] == expected

    # 到店付结清后可标记完成
    resp = client.post(f"/api/b/orders/{order_no}/transition",
                       json={"target": "已完成", "pay_settled": True}, headers=H)
    assert resp.status_code == 422  # pay_type 仍为未支付，结清校验在状态机内，需真实标记

    from app.models.order import Order, PayType
    order = db.query(Order).filter(Order.order_no == order_no).first()
    order.pay_type = PayType.SETTLED_OFFLINE
    db.commit()
    resp = client.post(f"/api/b/orders/{order_no}/transition", json={"target": "已完成"}, headers=H)
    assert resp.status_code == 200
    assert resp.json()["status"] == "已完成"


def test_transition_without_media_blocked(client, order_input, org):
    """强制影像节点：待确认→已预约→接宠中 后，无影像不可流转服务中。"""
    H = {"Authorization": f"Bearer {org['manager_token']}"}
    order_no = create(client, order_input).json()["order_no"]
    client.post(f"/api/b/orders/{order_no}/confirm", json={}, headers=H)
    client.post(f"/api/b/orders/{order_no}/transition", json={"target": "接宠中"}, headers=H)
    resp = client.post(f"/api/b/orders/{order_no}/transition", json={"target": "服务中"}, headers=H)
    assert resp.status_code == 422
    assert "影像" in resp.json()["detail"]


def test_night_order_judgement():
    """夜间单判定（PRD §7.2）：22:00-次日 7:00。"""
    assert is_night_order(datetime(2026, 9, 5, 23, 30)) is True
    assert is_night_order(datetime(2026, 9, 6, 2, 0)) is True
    assert is_night_order(datetime(2026, 9, 6, 8, 0)) is False
    assert is_night_order(datetime(2026, 9, 5, 22, 0)) is True
    assert is_night_order(datetime(2026, 9, 5, 21, 59)) is False
