"""B 端补充功能测试：详情/备注/改期/价格版本（PRD B003/B005 验收标准）。"""
from datetime import datetime, timedelta

import io


def _seed_and_order(client, seed):
    """下一个已确认订单，返回 order_no。"""
    pkg = {"type": "套餐", "name": "基础告别套餐", "price": 800,
           "version": "v20260905", "status": "在售"}
    resp = client.post("/api/b/service-items", json=pkg)
    pkg_id = resp.json()["id"]
    order_no = client.post("/api/c/orders", json={
        "user_id": 1, "pet_name": "豆豆", "species": "犬", "pkg_id": pkg_id,
        "expect_time": (datetime.now() + timedelta(days=1)).isoformat(),
        "address": "郑州市金水区",
    }).json()["order_no"]
    client.post(f"/api/b/orders/{order_no}/confirm", json={})
    return order_no, pkg_id


def test_b_detail_contains_media_and_notes(client, seed):
    """B003 详情：全字段 + 影像列表 + 备注可保存回读。"""
    order_no, _ = _seed_and_order(client, seed)
    client.post(f"/api/b/orders/{order_no}/media?node=接宠完成",
                files={"file": ("a.jpg", io.BytesIO(b"x"), "image/jpeg")})
    client.put(f"/api/b/orders/{order_no}/notes", json={"notes": "客户情绪低落，沟通放慢"})
    detail = client.get(f"/api/b/orders/{order_no}").json()
    assert detail["notes"] == "客户情绪低落，沟通放慢"
    assert len(detail["media"]) == 1
    assert detail["pay_type"] == "未支付"


def test_reschedule_free_once_then_rejected(client, seed):
    """改期：免费 1 次，第二次拒绝（PRD §6.2）。"""
    order_no, _ = _seed_and_order(client, seed)
    first = client.post(f"/api/b/orders/{order_no}/reschedule",
                        json={"expect_time": (datetime.now() + timedelta(days=2)).isoformat()})
    assert first.status_code == 200
    assert first.json()["reschedule_count"] == 1
    second = client.post(f"/api/b/orders/{order_no}/reschedule",
                         json={"expect_time": (datetime.now() + timedelta(days=3)).isoformat()})
    assert second.status_code == 422
    assert "已用完" in second.json()["detail"]


def test_price_update_creates_version_and_log(client, seed, db):
    """改价：新版本生效 + 版本流水落库；下架不删除。"""
    order_no, pkg_id = _seed_and_order(client, seed)
    detail_before = client.get(f"/api/b/orders/{order_no}").json()
    price_before = detail_before["total_amount"]

    upd = client.put(f"/api/b/service-items/{pkg_id}",
                     json={"type": "套餐", "name": "基础告别套餐", "price": 880})
    assert upd.status_code == 200
    assert upd.json()["price_changed"] is True
    new_version = upd.json()["version"]

    log = client.get(f"/api/b/service-items/{pkg_id}/versions").json()
    assert len(log) == 2  # 首版 + 改价版
    assert log[0]["version"] == new_version

    # 锁价回归：旧订单总额不变
    detail_after = client.get(f"/api/b/orders/{order_no}").json()
    assert detail_after["total_amount"] == price_before

    # 下架：状态变更不删除
    off = client.post(f"/api/b/service-items/{pkg_id}/off-sale")
    assert off.json()["status"] == "下架"
    assert client.get(f"/api/b/orders/{order_no}").status_code == 200
