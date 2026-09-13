"""多租户（不同个体老板共用一套系统）验收：数据硬隔离 + 白标可定制 + 超管统一开店。

信任基石用例：**A 店的数据 B 店绝不能看见/操作**（跨店返回 404/不在列表）。
开店入口已从自助入驻收归超管：POST /api/b/platform/stores（见 test_super_admin.py）。
"""
import pytest


def _H(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _S(slug: str) -> dict:
    return {"X-Store-Slug": slug}


@pytest.fixture
def two_stores(client, org):
    """门店A（org fixture，slug=store-a）+ 由超管开通的门店B（slug=store-b）。"""
    resp = client.post("/api/b/platform/stores", json={
        "store_name": "门店B", "slug": "store-b",
        "admin_username": "bossb", "admin_password": "b123456", "admin_name": "B店长",
        "primary_color": "#FF6600",
    }, headers=_H(org["super_token"]))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    b_token = client.post("/api/b/auth/login",
                          json={"username": "bossb", "password": "b123456"}).json()["token"]
    return {
        "a_token": org["manager_token"],
        "a_employee_token": org["employee_token"],
        "a_slug": "store-a",
        "b_token": b_token,
        "b_slug": "store-b",
        "b_store_id": body["store"]["store_id"],
    }


# ---------- 门店开通（超管）----------
def test_onboarding_creates_store_brand_and_manager(client, org):
    resp = client.post("/api/b/platform/stores", json={
        "store_name": "新门店C", "slug": "store-c",
        "miniapp_appid": "wxstorec1234567890",
        "admin_username": "bossc", "admin_password": "c123456", "admin_name": "C店长",
    }, headers=_H(org["super_token"]))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["store"]["profile"]["slug"] == "store-c"
    assert body["store"]["profile"]["name"] == "新门店C"
    assert body["store"]["profile"]["primary_color"] == "#5B8C85"  # 默认品牌色
    assert body["store"]["profile"]["miniapp_name"] == "新门店C"
    assert body["store"]["profile"]["miniapp_appid"] == "wxstorec1234567890"
    assert body["store"]["profile"]["miniapp_entry_enabled"] is True
    assert body["manager"]["role"] == "manager"

    # 店长能登录，且菜单里没有平台专属的「门店管理」
    login = client.post("/api/b/auth/login", json={"username": "bossc", "password": "c123456"})
    assert login.status_code == 200
    menus = login.json()["staff"]["menus"]
    assert "stores" not in menus
    assert len(menus) == 9


def test_onboarding_rejects_duplicate_slug_and_username(client, org):
    H = _H(org["super_token"])
    base = {"store_name": "撞店", "admin_username": "unique1", "admin_password": "p123456"}
    assert client.post("/api/b/platform/stores",
                       json={**base, "slug": "store-a"}, headers=H).status_code == 409
    assert client.post("/api/b/platform/stores",
                       json={**base, "slug": "fresh-slug", "admin_username": "admin"},
                       headers=H).status_code == 409

    ok = client.post("/api/b/platform/stores",
                     json={**base, "slug": "fresh-slug", "miniapp_appid": "wxfresh1234567890"},
                     headers=H)
    assert ok.status_code == 200, ok.text
    assert client.post("/api/b/platform/stores",
                       json={**base, "slug": "another-slug", "admin_username": "unique2",
                             "miniapp_appid": "wxfresh1234567890"},
                       headers=H).status_code == 409


# ---------- 跨店订单隔离 ----------
def test_cross_store_order_isolation(client, order_input, two_stores):
    """A 店下单：A 店长可见可操作，B 店长列表不可见、详情/流转 404。"""
    r = client.post("/api/c/orders", json=order_input, headers=_S("store-a"))
    assert r.status_code == 200, r.text
    order_no = r.json()["order_no"]

    a_list = client.get("/api/b/orders", headers=_H(two_stores["a_token"])).json()
    assert any(o["order_no"] == order_no for o in a_list["items"])
    assert client.get(f"/api/b/orders/{order_no}",
                      headers=_H(two_stores["a_token"])).status_code == 200

    b_list = client.get("/api/b/orders", headers=_H(two_stores["b_token"])).json()
    assert all(o["order_no"] != order_no for o in b_list["items"])
    assert client.get(f"/api/b/orders/{order_no}",
                      headers=_H(two_stores["b_token"])).status_code == 404
    # B 店长不能流转 A 的订单
    assert client.post(f"/api/b/orders/{order_no}/transition", json={"target": "接宠中"},
                       headers=_H(two_stores["b_token"])).status_code == 404


def test_c_order_detail_scoped_by_slug(client, order_input, two_stores):
    """同一订单：带 A 的 slug 可看，带 B 的 slug → 404（防跨店猜单号）。"""
    order_no = client.post("/api/c/orders", json=order_input,
                           headers=_S("store-a")).json()["order_no"]
    assert client.get(f"/api/c/orders/{order_no}", headers=_S("store-a")).status_code == 200
    assert client.get(f"/api/c/orders/{order_no}", headers=_S("store-b")).status_code == 404


def test_unknown_store_slug_rejected(client, order_input):
    """带不存在的门店标识 → 404，避免静默串店。"""
    assert client.post("/api/c/orders", json=order_input,
                       headers=_S("no-such-store")).status_code == 404


# ---------- 跨店客户/商品隔离 ----------
def test_cross_store_customer_isolation(client, two_stores):
    cid = client.post("/api/c/customers", json={"nickname": "A客户", "phone": "13800001111"},
                      headers=_S("store-a")).json()["customer_id"]
    a = client.get("/api/b/customers", headers=_H(two_stores["a_token"])).json()
    assert any(c["customer_id"] == cid for c in a)
    b = client.get("/api/b/customers", headers=_H(two_stores["b_token"])).json()
    assert all(c["customer_id"] != cid for c in b)
    assert client.get(f"/api/b/customers/{cid}",
                      headers=_H(two_stores["b_token"])).status_code == 404


def test_cross_store_product_isolation(client, two_stores):
    """A 店新建的纪念品：B 店后台看不到、B 店 C 端也不展示。"""
    pid = client.post("/api/b/products", json={"name": "A店专属", "price": 99},
                      headers=_H(two_stores["a_token"])).json()["id"]
    assert any(p["id"] == pid for p in
               client.get("/api/b/products", headers=_H(two_stores["a_token"])).json())
    assert all(p["id"] != pid for p in
               client.get("/api/b/products", headers=_H(two_stores["b_token"])).json())
    assert any(p["id"] == pid for p in
               client.get("/api/c/products", headers=_S("store-a")).json())
    assert all(p["id"] != pid for p in
               client.get("/api/c/products", headers=_S("store-b")).json())


def test_cross_store_stats_isolated(client, order_input, two_stores):
    """看板只统计本店：B 店看板看不到 A 店的订单量。"""
    client.post("/api/c/orders", json=order_input, headers=_S("store-a"))
    a_stats = client.get("/api/b/stats", headers=_H(two_stores["a_token"])).json()
    b_stats = client.get("/api/b/stats", headers=_H(two_stores["b_token"])).json()
    assert sum(a_stats["status_dist"].values()) == 1
    assert sum(b_stats["status_dist"].values()) == 0


# ---------- 白标：超管可改，租户只读 ----------
def test_super_admin_configures_store_brand_and_public_reads_it(client, org):
    H = _H(org["super_token"])
    upd = client.put(f"/api/b/platform/stores/{org['store_id']}/profile", json={
        "name": "门店A旗舰店", "slogan": "陪你到最后",
        "logo_url": "/uploads/logo-a.png", "primary_color": "#FF0066",
        "miniapp_name": "门店A旗舰店小程序",
        "miniapp_appid": "wxstorea1234567890",
        "miniapp_entry_enabled": True,
    }, headers=H)
    assert upd.status_code == 200
    assert upd.json()["primary_color"] == "#FF0066"
    assert upd.json()["slogan"] == "陪你到最后"
    assert upd.json()["logo_url"].endswith("logo-a.png")
    assert upd.json()["miniapp_name"] == "门店A旗舰店小程序"
    assert upd.json()["miniapp_appid"] == "wxstorea1234567890"
    assert upd.json()["miniapp_entry_enabled"] is True

    # 租户读自己门店（前台展示用）
    tenant_view = client.get("/api/b/store/profile", headers=_H(org["manager_token"])).json()
    assert tenant_view["name"] == "门店A旗舰店"
    assert tenant_view["slogan"] == "陪你到最后"
    assert tenant_view["miniapp_name"] == "门店A旗舰店小程序"

    # C 端公开接口（换肤数据源）
    c = client.get("/api/c/store/profile", params={"slug": "store-a"}).json()
    assert c["primary_color"] == "#FF0066"
    assert c["name"] == "门店A旗舰店"
    assert c["slogan"] == "陪你到最后"
    assert c["theme"]["primary_color"] == "#FF0066"
    assert c["miniapp_appid"] == "wxstorea1234567890"


def test_tenant_cannot_write_brand(client, org):
    """品牌配置已收归超管：店长与店员写一律 403。"""
    for token in (org["manager_token"], org["employee_token"]):
        assert client.put("/api/b/store/profile", json={"name": "被篡改"},
                          headers=_H(token)).status_code == 403


def test_tenant_cannot_reach_platform_api(client, org):
    """平台层接口对租户完全关闭。"""
    for token in (org["manager_token"], org["employee_token"]):
        assert client.get("/api/b/platform/stores", headers=_H(token)).status_code == 403


def test_c_store_profile_defaults_to_first_store(client, org):
    """不带 slug → 返回默认门店白标（单店模式兜底）。"""
    c = client.get("/api/c/store/profile").json()
    assert c["slug"] == "store-a"
    assert c["store_id"] == org["store_id"]


def test_c_store_profile_unknown_slug_404(client, org):
    assert client.get("/api/c/store/profile", params={"slug": "ghost"}).status_code == 404


# ---------- 入参校验（脏值会毁掉整站换肤，必须在入口拦下） ----------
def test_white_label_rejects_invalid_primary_color(client, org):
    """非十六进制色值 → 422（前端按该值派生整套色阶，脏值会让样式失效）。"""
    H = _H(org["super_token"])
    url = f"/api/b/platform/stores/{org['store_id']}/profile"
    for bad in ["红色", "red", "#12", "#GGGGGG", "5B8C85"]:
        assert client.put(url, json={"primary_color": bad}, headers=H).status_code == 422, \
            f"未拦下 {bad!r}"
    # 三位缩写与六位均合法
    for good in ["#F60", "#ff6600"]:
        assert client.put(url, json={"primary_color": good}, headers=H).status_code == 200, \
            f"误拦 {good!r}"
    assert client.get("/api/c/store/profile",
                      params={"slug": "store-a"}).json()["primary_color"] == "#ff6600"


def test_white_label_logo_url_validated_and_clearable(client, org):
    """Logo 只收站内路径或 http(s) 地址；空串表示清空（前端回落中性占位）。"""
    H = _H(org["super_token"])
    url = f"/api/b/platform/stores/{org['store_id']}/profile"
    for bad in ["#C97B63", "logo.png", "ftp://x/a.png"]:
        assert client.put(url, json={"logo_url": bad}, headers=H).status_code == 422, \
            f"未拦下 {bad!r}"

    ok = client.put(url, json={"logo_url": "/uploads/logo-a.png"}, headers=H)
    assert ok.status_code == 200
    assert client.get("/api/c/store/profile",
                      params={"slug": "store-a"}).json()["logo_url"] == "/uploads/logo-a.png"

    # 空串 = 清空，而不是「未提供」
    cleared = client.put(url, json={"logo_url": ""}, headers=H)
    assert cleared.status_code == 200
    assert cleared.json()["logo_url"] == ""
