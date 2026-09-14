"""后台员工登录 / RBAC / 两级组织 / C 端手机号登录（PRD §8 权限管理 + C 端手机号登录）。

覆盖：
(a) 后台账号密码登录 + token 校验 + 停用拒绝；
(b) RBAC 角色/操作权限强制（require_perm / 角色动态分配生效）；
(c) 团队成员 CRUD（店长专属，店员 403）；
(d) 客户手机号按登录角色脱敏（店长全量 / 店员脱敏，不信任前端）；
(e) C 端手机号一键登录 dev 兜底路径（幂等 + 强制模式缺 code 报错）。
"""
import pytest

from app.models.customer import Customer
from app.models.staff import Staff, StaffRole, StaffStatus
from app.services.staff_auth_service import hash_password

ALL_PERMS = ["customer.full_phone", "order.refund", "media.revoke",
             "price.edit", "staff.manage", "role.manage"]
MENU_KEYS = ["dashboard", "orders", "service-items", "products", "boarding",
             "customers", "stats", "staff", "rbac"]
EMPLOYEE_MENUS = ["dashboard", "orders", "service-items", "products",
                  "boarding", "customers", "stats"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------- (a) 后台登录 ----------
def test_staff_login_issues_token(client, org):
    """店长账号密码登录 → token + 完整角色档案（9 菜单 / 6 权限）。"""
    resp = client.post("/api/b/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token"].count(".") == 2
    staff = body["staff"]
    assert staff["role"] == "manager"
    assert staff["role_name"] == "店长"
    assert len(staff["menus"]) == 9
    assert set(ALL_PERMS).issubset(set(staff["permissions"]))


def test_staff_login_wrong_password_401(client, org):
    resp = client.post("/api/b/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_staff_login_disabled_rejected(client, db, org):
    """已停用员工登录 → 401。"""
    emp = Staff(username="disabled1", password_hash=hash_password("p123"),
                name="停用员", role=StaffRole.EMPLOYEE, store_id=org["store_id"],
                manager_id=org["manager_id"], status=StaffStatus.DISABLED)
    db.add(emp)
    db.commit()
    resp = client.post("/api/b/auth/login", json={"username": "disabled1", "password": "p123"})
    assert resp.status_code == 401


def test_staff_token_grants_me(client, org):
    """合法 token 访问 /auth/me → 登录态 + 角色权限。"""
    resp = client.get("/api/b/auth/me", headers=_headers(org["manager_token"]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["logged_in"] is True
    assert body["role"] == "manager"
    assert "staff.manage" in body["permissions"]


def test_staff_no_token_401(client):
    """缺 Bearer → 401（后台接口强制登录，与 C 端软校验不同）。"""
    assert client.get("/api/b/auth/me").status_code == 401
    assert client.get("/api/b/staff").status_code == 401


# ---------- (b) RBAC 强制 ----------
def test_employee_lacks_staff_perm_403(client, org):
    """店员无 staff.manage → 访问成员列表 403。"""
    resp = client.get("/api/b/staff", headers=_headers(org["employee_token"]))
    assert resp.status_code == 403


def test_manager_rbac_role_assign_and_dynamic(client, org):
    """店长改员工角色权限后，店员即时具备该操作权限（RBAC 动态生效）。"""
    # 改前：店员无 staff.manage
    before = client.get("/api/b/staff", headers=_headers(org["employee_token"]))
    assert before.status_code == 403
    # 店长给 employee 角色分配 staff.manage + 仅部分菜单
    assign = client.put(
        "/api/b/roles/employee",
        json={"menu_keys": EMPLOYEE_MENUS[:2], "permissions": ["staff.manage"]},
        headers=_headers(org["manager_token"]),
    )
    assert assign.status_code == 200
    assert assign.json()["permissions"] == ["staff.manage"]
    # 改后：店员现在能进成员列表
    after = client.get("/api/b/staff", headers=_headers(org["employee_token"]))
    assert after.status_code == 200


def test_rbac_assign_rejects_unknown_menu(client, org):
    """分配未知菜单 key → 400（防越权/脏数据）。"""
    resp = client.put(
        "/api/b/roles/employee",
        json={"menu_keys": ["not_a_menu"], "permissions": []},
        headers=_headers(org["manager_token"]),
    )
    assert resp.status_code == 400


def test_rbac_catalog_exposed(client, org):
    """权限目录与角色列表可查，店员默认无操作权限。"""
    perms = client.get("/api/b/permissions").json()
    assert {p["code"] for p in perms} == set(ALL_PERMS)
    roles = {r["key"]: r for r in client.get("/api/b/roles").json()}
    assert set(roles["manager"]["menus"]) == set(MENU_KEYS)
    assert set(roles["employee"]["menus"]) == set(EMPLOYEE_MENUS)
    assert roles["employee"]["permissions"] == []


# ---------- (c) 团队成员 CRUD ----------
def test_manager_lists_staff(client, org):
    """店长列表含本店店长 + 店员。"""
    resp = client.get("/api/b/staff", headers=_headers(org["manager_token"]))
    assert resp.status_code == 200
    usernames = {s["username"] for s in resp.json()}
    assert usernames == {"admin", "emp"}


def test_manager_creates_employee(client, org):
    """店长新建店员 → 自动归属本店、上级为当前店长。"""
    resp = client.post(
        "/api/b/staff",
        json={"username": "newemp", "password": "p123", "name": "新店员", "phone": "13900000000"},
        headers=_headers(org["manager_token"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "employee"
    assert body["store_id"] == org["store_id"]
    assert body["manager_id"] == org["manager_id"]


def test_duplicate_username_409(client, org):
    resp = client.post(
        "/api/b/staff",
        json={"username": "emp", "password": "p123", "name": "重名"},
        headers=_headers(org["manager_token"]),
    )
    assert resp.status_code == 409


def test_employee_cannot_create_staff(client, org):
    resp = client.post(
        "/api/b/staff",
        json={"username": "x", "password": "p123", "name": "x"},
        headers=_headers(org["employee_token"]),
    )
    assert resp.status_code == 403


def test_manager_disable_employee(client, org):
    """店长停用店员成功；停用店长被拒（400）。"""
    d = client.post(f"/api/b/staff/{org['employee_id']}/disable",
                    headers=_headers(org["manager_token"]))
    assert d.status_code == 200
    assert d.json()["status"] == "disabled"
    m = client.post(f"/api/b/staff/{org['manager_id']}/disable",
                    headers=_headers(org["manager_token"]))
    assert m.status_code == 400


# ---------- (d) 客户手机号按角色脱敏 ----------
def test_customer_phone_mask_by_role(client, db, org):
    """店长看全量手机号，店员看脱敏（角色取自 token，不信任前端）。"""
    c = Customer(nickname="客户甲", phone="13812345678")
    db.add(c)
    db.commit()

    mgr_view = client.get("/api/b/customers", headers=_headers(org["manager_token"])).json()
    emp_view = client.get("/api/b/customers", headers=_headers(org["employee_token"])).json()
    assert mgr_view[0]["phone"] == "13812345678"
    assert emp_view[0]["phone"] == "138****5678"


# ---------- (e) C 端手机号一键登录 ----------
def test_phone_login_dev_issues_token(client):
    """dev 模式：dev_phone 直换 token，且幂等（同手机号同客户）。"""
    r1 = client.post("/api/c/auth/phone-login", json={"dev_phone": "13800000000"})
    assert r1.status_code == 200
    t1, cid1 = r1.json()["token"], r1.json()["customer_id"]
    me = client.get("/api/c/auth/me", headers={"X-Customer-Token": t1}).json()
    assert me["logged_in"] is True
    assert me["customer_id"] == cid1
    assert me["phone_masked"] == "138****0000"

    r2 = client.post("/api/c/auth/phone-login", json={"dev_phone": "13800000000"})
    assert r2.json()["customer_id"] == cid1  # 幂等：不重复建客户


def test_phone_login_requires_code_when_enabled(client, monkeypatch):
    """WX_LOGIN_ENABLED=true 且无 phone_code → 422（不触发网络请求）。"""
    from app import config
    monkeypatch.setattr(config.settings, "WX_LOGIN_ENABLED", True)
    resp = client.post("/api/c/auth/phone-login", json={})
    assert resp.status_code == 422
    assert "手机号授权" in resp.json()["detail"]


def test_phone_login_binds_openid_when_enabled(client, db, monkeypatch):
    """正式微信登录：手机号授权 + wx.login code 同步绑定 openid，供 JSAPI 支付使用。"""
    from app import config
    from app.models.customer import Customer
    from app.services import auth_service

    monkeypatch.setattr(config.settings, "WX_LOGIN_ENABLED", True)
    monkeypatch.setattr(auth_service, "get_phone_number", lambda phone_code: "13800002222")
    monkeypatch.setattr(auth_service, "code_to_session", lambda code: "openid-jsapi-001")

    resp = client.post("/api/c/auth/phone-login", json={"phone_code": "phone-code", "code": "login-code"})
    assert resp.status_code == 200
    customer = db.get(Customer, resp.json()["customer_id"])
    assert customer.phone == "13800002222"
    assert customer.openid == "openid-jsapi-001"


def test_phone_login_legacy_requires_dev_phone(client):
    """WX_LOGIN_ENABLED=false 且无 dev_phone → 422。"""
    resp = client.post("/api/c/auth/phone-login", json={})
    assert resp.status_code == 422
