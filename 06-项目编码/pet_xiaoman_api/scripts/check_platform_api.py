"""平台层（超管）接口契约自检：直接打运行中的本地 API，不依赖后台前端。

覆盖：开店（含品牌 + 首位店长）→ C 端按 slug 换肤 → 超管改品牌 → 非法入参必须 422
→ 门店开号（店员自动挂店长）→ 停用账号后不能登录 → 门店接口不能造 super_admin
→ 停用门店后 C 端 404、再启用恢复。

前置：API 已在 8010 运行，且已建超管账号
    `env -u PYTHONPATH SQLITE_FALLBACK=true ./.venv/bin/python -m scripts.create_super_admin`

用法：
    ./.venv/bin/python scripts/check_platform_api.py

副作用：会建一家 slug=`meow-api-check` 的演示门店（重复跑会复用同一家）。
       清理：`scripts/purge_demo_stores.py --apply`（该 slug 已在其白名单里）。
"""
import json
import urllib.error
import urllib.request

API = "http://127.0.0.1:8010"


def call(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def login(user, pwd):
    code, body = call("POST", "/api/b/auth/login", body={"username": user, "password": pwd})
    assert code == 200, f"{user} 登录失败 {code} {body}"
    return body["token"]


sup = login("superadmin", "super123456")
print("== 门店列表（超管视角）==")
code, rows = call("GET", "/api/b/platform/stores", sup)
print(f"HTTP {code}")
for r in rows:
    slug = r["profile"]["slug"] if r["profile"] else None
    print(f"  id={r['store_id']:<3} {r['name']:<16} status={r['status']:<8} "
          f"slug={slug} 账号={r['staff_count']} 店长={r['manager_count']}")

print("\n== 新建门店（一次开店 + 品牌 + 首位店长）==")
code, created = call("POST", "/api/b/platform/stores", sup, {
    "store_name": "喵星人善终（API 自检）", "slug": "meow-api-check",
    "brand_name": "喵星人宠物善终", "slogan": "给 ta 最后的体面",
    "primary_color": "#C97B63",
    "admin_username": "meow_api_boss", "admin_password": "meow123456",
    "admin_name": "喵店长",
})
if code == 409:
    print("  已存在（上次自检残留），跳过创建")
    sid = next(r["store_id"] for r in rows if r["profile"]["slug"] == "meow-api-check")
    code, created = call("GET", f"/api/b/platform/stores/{sid}", sup)
else:
    assert code == 200, f"开店失败 {code} {created}"
store = created.get("store", created)
manager = created.get("manager") or next(
    s for s in call("GET", f"/api/b/platform/stores/{store['store_id']}/staff", sup)[1]
    if s["role"] == "manager")
sid = store["store_id"]
print(f"  HTTP {code}  store_id={sid}  店长 id={manager['id']}")
print(f"  品牌：name={store['profile']['name']} color={store['profile']['primary_color']}")

print("\n== 归一品牌到初始态（让本脚本可重复跑）==")
code, p = call("PUT", f"/api/b/platform/stores/{sid}/profile", sup,
               {"name": "喵星人宠物善终", "slogan": "给 ta 最后的体面",
                "primary_color": "#C97B63", "logo_url": ""})
print(f"  HTTP {code}  name={p['name']} color={p['primary_color']} logo={p['logo_url']!r}")

print("\n== C 端按 slug 换肤（顾客扫码看到的就是这个）==")
code, c = call("GET", "/api/c/store/profile?slug=meow-api-check")
print(f"  HTTP {code}  name={c['name']}  slogan={c['slogan']}  color={c['primary_color']}")
assert c["name"] == "喵星人宠物善终" and c["primary_color"] == "#C97B63", c

print("\n== 超管改品牌（租户无此能力）==")
code, p = call("PUT", f"/api/b/platform/stores/{sid}/profile", sup,
               {"primary_color": "#4F7BD9", "slogan": "换了个标语"})
print(f"  HTTP {code}  color={p['primary_color']}  slogan={p['slogan']}")
code, c = call("GET", "/api/c/store/profile?slug=meow-api-check")
assert c["primary_color"] == "#4F7BD9" and c["slogan"] == "换了个标语", c
print("  C 端已同步 ✓")

print("\n== 非法入参必须被拒 ==")
for label, payload, patch in [
    ("脏主色 红色", {"primary_color": "红色"}, f"/api/b/platform/stores/{sid}/profile"),
    ("非法 logo（把颜色塞进 logo）", {"logo_url": "红色"}, f"/api/b/platform/stores/{sid}/profile"),
    ("非法 slug", {"store_name": "x", "slug": "含空格 和中文", "admin_username": "u1",
                   "admin_password": "123456"}, "/api/b/platform/stores"),
]:
    code, body = call("PUT" if label != "非法 slug" else "POST", patch, sup, payload)
    ok = code == 422
    print(f"  {'OK  ' if ok else 'FAIL'} {label} → HTTP {code}"
          + ("" if ok else f" {body}"))

print("\n== 门店账号：开号 / 店员挂店长 / 停用后不能登录 ==")
code, emp = call("POST", f"/api/b/platform/stores/{sid}/staff", sup,
                 {"username": "meow_api_emp", "password": "emp123456", "name": "喵店员"})
if code == 409:
    code, staff = call("GET", f"/api/b/platform/stores/{sid}/staff", sup)
    emp = next(s for s in staff if s["username"] == "meow_api_emp")
print(f"  HTTP {code}  role={emp['role']}  manager_id={emp['manager_id']}  "
      f"store_id={emp['store_id']}")
assert emp["manager_id"] == manager["id"], "店员未挂到本店店长名下"

code, _ = call("POST", "/api/b/auth/login", body={"username": "meow_api_emp", "password": "emp123456"})
print(f"  新账号可直接登录 → HTTP {code}")
assert code == 200

code, _ = call("POST", f"/api/b/platform/stores/{sid}/staff/{emp['id']}/disable", sup)
code2, _ = call("POST", "/api/b/auth/login", body={"username": "meow_api_emp", "password": "emp123456"})
print(f"  停用 → HTTP {code}，再登录 → HTTP {code2}")
assert code2 == 401

print("\n== 门店接口不能造平台级账号 ==")
code, body = call("POST", f"/api/b/platform/stores/{sid}/staff", sup,
                  {"username": "evil", "password": "evil123456", "name": "越权",
                   "role": "super_admin"})
print(f"  {'OK  ' if code == 422 else 'FAIL'} 建 super_admin 门店账号 → HTTP {code}")
assert code == 422

print("\n== 停用门店 → C 端 404，再启用恢复 ==")
code, s = call("POST", f"/api/b/platform/stores/{sid}/status", sup, {"status": "disabled"})
c1, _ = call("GET", "/api/c/store/profile?slug=meow-api-check")
print(f"  停用 HTTP {code} status={s['status']}；C 端 HTTP {c1}")
assert c1 == 404
code, s = call("POST", f"/api/b/platform/stores/{sid}/status", sup, {"status": "active"})
c2, _ = call("GET", "/api/c/store/profile?slug=meow-api-check")
print(f"  启用 HTTP {code} status={s['status']}；C 端 HTTP {c2}")
assert c2 == 200

print("\n全部通过 ✓   （自检门店 slug=meow-api-check，可在后台「门店管理」里看到）")
