"""平台超管验收：统一开店 / 开账号 / 配品牌 / 启停门店。

核心诉求：品牌与 UI 由超管统一配置，不让租户自己配；
且超管**不属于任何门店**，所有门店操作必须显式带 store_id（防串店）。
"""
import pytest


def _H(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _S(slug: str) -> dict:
    return {"X-Store-Slug": slug}


@pytest.fixture
def new_store(client, org):
    """超管开通一家新门店，返回 store_id 与店长 token。"""
    resp = client.post("/api/b/platform/stores", json={
        "store_name": "喵星人善终", "slug": "meow",
        "brand_name": "喵星人宠物善终", "slogan": "给ta最后的体面",
        "primary_color": "#C97B63",
        "admin_username": "meow_boss", "admin_password": "meow123456", "admin_name": "喵店长",
    }, headers=_H(org["super_token"]))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    token = client.post("/api/b/auth/login",
                        json={"username": "meow_boss", "password": "meow123456"}).json()["token"]
    return {"store_id": body["store"]["store_id"], "profile": body["store"]["profile"],
            "manager_token": token, "manager_id": body["manager"]["id"]}


# ---------- 开店 ----------
def test_created_store_carries_brand_from_onboarding(client, new_store):
    p = new_store["profile"]
    assert p["slug"] == "meow"
    assert p["name"] == "喵星人宠物善终"     # brand_name 优先于 store_name
    assert p["slogan"] == "给ta最后的体面"
    assert p["primary_color"] == "#C97B63"


def test_created_store_brand_visible_on_c_end(client, new_store):
    c = client.get("/api/c/store/profile", params={"slug": "meow"}).json()
    assert c["name"] == "喵星人宠物善终"
    assert c["slogan"] == "给ta最后的体面"
    assert c["primary_color"] == "#C97B63"


# ---------- 开账号 ----------
def test_super_admin_provisions_store_accounts(client, org, new_store):
    H = _H(org["super_token"])
    base = f"/api/b/platform/stores/{new_store['store_id']}/staff"

    emp = client.post(base, json={"username": "meow_emp", "password": "emp123456",
                                 "name": "喵店员"}, headers=H)
    assert emp.status_code == 200, emp.text
    # 店员默认挂在门店店长名下（两级归属）
    assert emp.json()["role"] == "employee"
    assert emp.json()["manager_id"] == new_store["manager_id"]
    assert emp.json()["store_id"] == new_store["store_id"]

    # 新开的店员账号可直接登录，且看不到平台菜单
    login = client.post("/api/b/auth/login", json={"username": "meow_emp", "password": "emp123456"})
    assert login.status_code == 200
    assert "stores" not in login.json()["staff"]["menus"]

    listed = client.get(base, headers=H).json()
    assert {s["username"] for s in listed} == {"meow_boss", "meow_emp"}
    # 超管不属于任何门店，绝不出现在门店账号列表里
    assert all(s["role"] != "super_admin" for s in listed)


def test_store_staff_cannot_be_super_admin(client, org, new_store):
    """门店接口不能创建平台级账号（越权提权的口子必须堵死）。"""
    resp = client.post(f"/api/b/platform/stores/{new_store['store_id']}/staff",
                       json={"username": "evil", "password": "evil123456",
                             "name": "越权", "role": "super_admin"},
                       headers=_H(org["super_token"]))
    assert resp.status_code == 422


def test_super_admin_can_update_and_disable_store_account(client, org, new_store):
    H = _H(org["super_token"])
    base = f"/api/b/platform/stores/{new_store['store_id']}/staff"
    emp_id = client.post(base, json={"username": "meow_emp2", "password": "emp123456",
                                     "name": "喵店员2"}, headers=H).json()["id"]

    upd = client.put(f"{base}/{emp_id}", json={"name": "改名了", "password": "newpass123"},
                     headers=H)
    assert upd.status_code == 200
    assert upd.json()["name"] == "改名了"
    assert client.post("/api/b/auth/login",
                       json={"username": "meow_emp2", "password": "newpass123"}).status_code == 200

    assert client.post(f"{base}/{emp_id}/disable", headers=H).status_code == 200
    assert client.post("/api/b/auth/login",
                       json={"username": "meow_emp2", "password": "newpass123"}).status_code == 401


def test_cross_store_staff_access_blocked(client, org, new_store):
    """路径里的 store_id 与账号所属门店必须一致，否则 404（防跨店改号）。"""
    H = _H(org["super_token"])
    resp = client.put(f"/api/b/platform/stores/{org['store_id']}/staff/{new_store['manager_id']}",
                      json={"name": "偷改"}, headers=H)
    assert resp.status_code == 404


# ---------- 启停门店 ----------
def test_disable_store_blocks_c_end(client, org, new_store):
    H = _H(org["super_token"])
    url = f"/api/b/platform/stores/{new_store['store_id']}/status"

    assert client.post(url, json={"status": "disabled"}, headers=H).json()["status"] == "disabled"
    assert client.get("/api/c/store/profile", params={"slug": "meow"}).status_code == 404
    assert client.post("/api/c/customers", json={"nickname": "x"},
                       headers=_S("meow")).status_code == 404

    assert client.post(url, json={"status": "active"}, headers=H).json()["status"] == "active"
    assert client.get("/api/c/store/profile", params={"slug": "meow"}).status_code == 200


# ---------- 平台身份语义 ----------
def test_super_admin_has_no_store_and_sees_platform_brand(client, org):
    """超管不属于任何门店：读品牌返回平台品牌，不是某家门店的品牌。"""
    me = client.get("/api/b/auth/me", headers=_H(org["super_token"])).json()
    assert me["role"] == "super_admin"
    assert me["store_id"] is None
    assert "stores" in me["menus"]

    brand = client.get("/api/b/store/profile", headers=_H(org["super_token"])).json()
    assert brand["store_id"] is None
    assert brand["slug"] is None


def test_super_admin_sees_platform_menu_only(client, org):
    """超管只该看到平台菜单：给他租户菜单，他会以 store_id=None 造出门店查不到的孤儿数据。"""
    me = client.get("/api/b/auth/me", headers=_H(org["super_token"])).json()
    assert me["menus"] == ["stores"]

    # 平台权限仍然是全的（开店 / 开账号 / 配品牌都要用）
    assert {"store.manage", "store.provision", "store.brand"} <= set(me["permissions"])


def test_tenant_admin_never_gains_platform_menu_even_if_fully_permissioned(client, org, db):
    """店长即使被授予平台权限，也拿不到平台菜单（菜单与权限双闸）。"""
    from app.models.rbac import Role
    from app.models.staff import StaffRole

    role = db.query(Role).filter(Role.key == StaffRole.MANAGER.value).first()
    role.permissions = sorted(set(list(role.permissions) + ["store.manage", "store.brand"]))
    db.commit()

    me = client.get("/api/b/auth/me", headers=_H(org["manager_token"])).json()
    assert "stores" not in me["menus"]
    # 即便持有 store.manage 权限，也进不了平台接口（require_super_admin 先拦身份）
    assert client.get("/api/b/platform/stores",
                      headers=_H(org["manager_token"])).status_code == 403


def test_unauthenticated_store_self_service_is_closed(client, org):
    """自助入驻已关闭（原 /api/b/stores/register 曾可未登录开店 → 已下线）。"""
    assert client.post("/api/b/stores/register", json={
        "store_name": "野生店", "slug": "wild", "username": "wild1", "password": "wild123"}).status_code == 404


def test_store_profile_listing_counts(client, org, new_store):
    rows = client.get("/api/b/platform/stores", headers=_H(org["super_token"])).json()
    meow = next(r for r in rows if r["store_id"] == new_store["store_id"])
    assert meow["manager_count"] == 1
    assert meow["staff_count"] == 1
    assert meow["status"] == "active"
    assert meow["profile"]["slug"] == "meow"


# ---------- 越权提权防护（租户侧 RBAC 页不得触及平台层）----------
def test_rbac_page_hides_platform_scope(client, org):
    """租户的「角色权限」页看不到平台菜单、平台权限、平台角色。"""
    H = _H(org["manager_token"])
    menus = client.get("/api/b/menus", headers=H).json()
    assert "stores" not in {m["key"] for m in menus}

    perms = client.get("/api/b/permissions", headers=H).json()
    assert all(not p.get("platform") for p in perms)
    assert "store.brand" not in {p["code"] for p in perms}

    roles = client.get("/api/b/roles", headers=H).json()
    assert "super_admin" not in {r["key"] for r in roles}


def test_tenant_cannot_grant_itself_platform_permission(client, org):
    """店长不能把平台权限分配给自己或店员（越权提权的口子）。"""
    H = _H(org["manager_token"])
    resp = client.put("/api/b/roles/employee",
                      json={"menu_keys": ["orders"], "permissions": ["store.brand"]}, headers=H)
    assert resp.status_code == 403


def test_tenant_cannot_edit_super_admin_role(client, org):
    H = _H(org["manager_token"])
    resp = client.put("/api/b/roles/super_admin",
                      json={"menu_keys": ["dashboard"], "permissions": []}, headers=H)
    assert resp.status_code == 403
