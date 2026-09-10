"""第二批测试：纪念品/寄存/客户档案（PRD B006-B009/C007/C008 验收标准）。"""
from datetime import date, datetime, timedelta

import pytest


@pytest.fixture
def seeded_order(client, db):
    """建客户+宠物+已完成订单（用于档案/回访场景）。"""
    from app.models.customer import Customer
    from app.models.order import Order
    from app.models.pet import Pet
    from app.models.service_item import ItemType, ServiceItem
    pkg = ServiceItem(type=ItemType.PACKAGE, name="基础告别套餐", price=800, version="v20260905")
    db.add(pkg)
    customer = Customer(nickname="测试客户", phone="13812345678")
    db.add(customer)
    db.flush()
    pet = Pet(name="豆豆", owner_id=customer.id)
    db.add(pet)
    db.flush()
    order = Order(order_no="GDTEST001", user_id=customer.id, pet_id=pet.id, pkg_id=pkg.id,
                  price_version="v20260905", expect_time=datetime.now(),
                  total_amount=800, status="已完成")
    db.add(order)
    db.commit()
    return {"customer_id": customer.id, "pet_id": pet.id, "order_no": "GDTEST001", "phone": "13812345678"}


# ===== B006/C007 纪念品 =====
def test_product_crud_and_c_list(client):
    create = client.post("/api/b/products", json={"name": "爪印相框", "price": 128,
                                                  "description": "实木相框"})
    assert create.status_code == 200
    pid = create.json()["id"]
    # C 端可见
    c_list = client.get("/api/c/products").json()
    assert any(p["id"] == pid for p in c_list)
    # 下架后 C 端不可见
    client.post(f"/api/b/products/{pid}/toggle")
    c_list = client.get("/api/c/products").json()
    assert not any(p["id"] == pid for p in c_list)


def test_c_buy_blocked_when_pay_disabled(client):
    create = client.post("/api/b/products", json={"name": "陶瓷摆件", "price": 200})
    pid = create.json()["id"]
    resp = client.post(f"/api/c/products/{pid}/buy", json={"customer_id": 1})
    assert resp.status_code == 422
    assert "到店选购" in resp.json()["detail"]


def test_c_buy_linked_order_check(client):
    create = client.post("/api/b/products", json={"name": "木质牌", "price": 88})
    pid = create.json()["id"]
    client.post("/api/b/products", json={"name": "占位", "price": 1})
    resp = client.post(f"/api/c/products/{pid}/buy",
                       json={"customer_id": 1, "fulfillment": "随单交付", "linked_order_no": "GDNOPE"})
    assert resp.status_code == 422


# ===== B007/C008 寄存 =====
def test_boarding_location_conflict(client, seeded_order):
    body = {"pet_id": seeded_order["pet_id"], "customer_id": seeded_order["customer_id"],
            "location": "A-01", "expire_date": (date.today() + timedelta(days=30)).isoformat()}
    assert client.post("/api/b/boardings", json=body).status_code == 200
    conflict = client.post("/api/b/boardings", json=body)
    assert conflict.status_code == 422
    assert "已被占用" in conflict.json()["detail"]


def test_boarding_renew_and_take(client, seeded_order):
    body = {"pet_id": seeded_order["pet_id"], "customer_id": seeded_order["customer_id"],
            "location": "B-02", "expire_date": (date.today() + timedelta(days=30)).isoformat()}
    bid = client.post("/api/b/boardings", json=body).json()["id"]
    # 续存不能早于当前到期
    bad = client.post(f"/api/b/boardings/{bid}/renew",
                      json={"expire_date": (date.today() + timedelta(days=10)).isoformat()})
    assert bad.status_code == 422
    ok = client.post(f"/api/b/boardings/{bid}/renew",
                     json={"expire_date": (date.today() + timedelta(days=60)).isoformat()})
    assert ok.status_code == 200
    # 取回必填取回人
    no_taker = client.post(f"/api/b/boardings/{bid}/take", json={})
    assert no_taker.status_code == 422
    taken = client.post(f"/api/b/boardings/{bid}/take", json={"taken_by": "张三"})
    assert taken.json()["status"] == "已取回"


def test_c_query_phone_tail(client, seeded_order):
    body = {"pet_id": seeded_order["pet_id"], "customer_id": seeded_order["customer_id"],
            "location": "C-03", "expire_date": (date.today() + timedelta(days=3)).isoformat()}
    client.post("/api/b/boardings", json=body)
    # 手机号 13812345678 后四位 5678
    resp = client.get("/api/c/boardings/query", params={"phone_tail": "5678"})
    assert resp.status_code == 200
    assert resp.json()[0]["severity"] == "临期"  # 3 天后到期
    wrong = client.get("/api/c/boardings/query", params={"phone_tail": "9999"})
    assert wrong.status_code == 404


# ===== B008/B009 客户档案与回访 =====
def test_customer_list_masked_for_staff(client, seeded_order):
    staff = client.get("/api/b/customers", params={"role": "店员"}).json()
    owner = client.get("/api/b/customers", params={"role": "店长"}).json()
    assert staff[0]["phone"] == "138****5678"
    assert owner[0]["phone"] == "13812345678"


def test_visit_pending_and_register(client, seeded_order, db):
    """订单完成 30 天后动态待回访；登记后关闭。"""
    from app.models.order import Order
    # 把完成时间改到 31 天前
    order = db.query(Order).filter(Order.order_no == "GDTEST001").first()
    order.updated_at = datetime.now() - timedelta(days=31)
    db.commit()

    listed = client.get("/api/b/customers", params={"role": "店长"}).json()
    assert listed[0]["visit_status"] == "待回访"

    bad = client.post(f"/api/b/customers/{seeded_order['customer_id']}/visit",
                      json={"satisfaction": 9})
    assert bad.status_code == 422
    ok = client.post(f"/api/b/customers/{seeded_order['customer_id']}/visit",
                     json={"satisfaction": 5, "would_recommend": True, "notes": "很满意"})
    assert ok.status_code == 200
    listed = client.get("/api/b/customers", params={"role": "店长"}).json()
    assert listed[0]["visit_status"] == "已回访"


def test_source_tag_update(client, seeded_order):
    resp = client.post(f"/api/b/customers/{seeded_order['customer_id']}/source",
                       json={"source": "小红书"})
    assert resp.json()["source"] == "小红书"
