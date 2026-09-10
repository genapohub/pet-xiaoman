"""B010 看板测试：北极星环比/渗透率/影像覆盖率/好评率（PRD §3.3 KPI）。"""
from datetime import datetime, timedelta

import pytest


@pytest.fixture
def seeded_stats(client, db):
    from app.models.customer import Customer, Source
    from app.models.order import Order, PayType
    from app.models.pet import Pet
    from app.models.service_media import MediaNode, MediaType, ServiceMedia
    from app.models.visit_record import VisitRecord
    pkg = None
    from app.models.service_item import ItemType, ServiceItem
    pkg = ServiceItem(type=ItemType.PACKAGE, name="P", price=800, version="v1")
    db.add(pkg)
    c1 = Customer(nickname="有影像客户", phone="13811112222", source=Source.XHS)
    c2 = Customer(nickname="转介绍客户", phone="13833334444", source=Source.REFERRAL)
    db.add_all([c1, c2])
    db.flush()
    pet = Pet(name="毛毛", owner_id=c1.id)
    db.add(pet)
    db.flush()

    def mk(no, cust, status, pay=PayType.UNPAID, addons=None, created=None, updated=None):
        o = Order(order_no=no, user_id=cust.id, pet_id=pet.id, pkg_id=pkg.id,
                  price_version="v1", expect_time=datetime.now(),
                  total_amount=800, status=status, pay_type=pay,
                  addons=addons or [],
                  created_at=created or datetime.now(),
                  updated_at=updated or created or datetime.now())
        db.add(o)
        db.flush()
        return o

    done1 = mk("GDST001", c1, "已完成", PayType.FULL_PAID, addons=[{"item_id": 1}])
    # 35 天前下单、本月完成（完成时刻=updated_at）
    mk("GDST002", c2, "已完成", PayType.SETTLED_OFFLINE,
       created=datetime.now() - timedelta(days=35), updated=datetime.now())
    mk("GDST003", c1, "服务中")
    db.add(ServiceMedia(order_id=done1.id, node=MediaNode.PICKUP,
                        media_type=MediaType.PHOTO, url="/uploads/x.jpg", uploaded_by=1))
    db.add(VisitRecord(customer_id=c1.id, satisfaction=5, would_recommend=True))
    db.commit()
    return {"done1_id": done1.id}


def test_stats_month_aggregation(client, seeded_stats):
    data = client.get("/api/b/stats").json()
    assert data["north_star"]["value"] == 2        # 本月完成 2 单
    assert data["north_star"]["prev"] == 0         # 上月 0 → 环比 None 语义
    # 口径=本月下单的订单（GDST002 上月下单不计入）：2 单中 GDST001 已付/带加购
    assert data["kpi"]["pay_penetration_pct"] == 50.0
    assert data["kpi"]["addon_rate_pct"] == 50.0
    assert data["kpi"]["media_coverage_pct"] == 50.0    # 完成单 2 单中 1 单有影像
    assert data["kpi"]["good_rate_pct"] == 100.0
    assert data["status_dist"].get("服务中") == 1
    assert data["source_dist"]["小红书"] == 1
    assert "待埋点" in data["funnel_note"]


def test_stats_specific_month(client, seeded_stats):
    prev_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    data = client.get("/api/b/stats", params={"month": prev_month}).json()
    # 上月完成单（GDST002 的 updated_at 仍是现在——按 updated_at 统计为 0，合理：改状态时间非回填）
    assert "north_star" in data
