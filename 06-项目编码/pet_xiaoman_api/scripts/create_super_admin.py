"""创建 / 重置平台超管账号（平台级，不属于任何门店）。

超管职责：开通门店、启停门店、配置门店品牌与 UI、为门店开通账号。
门店品牌配置已收归超管，租户（店长）不可自配。

用法：
    env -u PYTHONPATH SQLITE_FALLBACK=true ./.venv/bin/python -m scripts.create_super_admin
    # 自定义账号（默认 superadmin / super123456）
    ./.venv/bin/python -m scripts.create_super_admin --username boss --password 'Xx123456' --name 平台管理员

环境变量：SUPER_ADMIN_USER / SUPER_ADMIN_PASS / SUPER_ADMIN_NAME
幂等：同名账号已存在则只重置密码、确保在职、角色为 super_admin。
"""
import argparse
import os

os.environ.setdefault("SQLITE_FALLBACK", "true")

from app.database import SessionLocal  # noqa: E402
from app.models.staff import Staff, StaffRole, StaffStatus  # noqa: E402
from app.services.staff_auth_service import hash_password  # noqa: E402
from scripts.migrate_tenant import _ensure_platform_rbac  # noqa: E402

DEFAULT_USER = os.getenv("SUPER_ADMIN_USER", "superadmin")
DEFAULT_PASS = os.getenv("SUPER_ADMIN_PASS", "super123456")
DEFAULT_NAME = os.getenv("SUPER_ADMIN_NAME", "平台管理员")


def create(username: str, password: str, name: str) -> None:
    db = SessionLocal()
    try:
        for note in _ensure_platform_rbac(db):
            print("RBAC：" + note)

        staff = db.query(Staff).filter(Staff.username == username).first()
        if staff:
            staff.password_hash = hash_password(password)
            staff.role = StaffRole.SUPER_ADMIN
            staff.store_id = None          # 平台级
            staff.manager_id = None
            staff.status = StaffStatus.ACTIVE
            if name:
                staff.name = name
            db.commit()
            print(f"已重置超管账号：{username}（id={staff.id}）")
        else:
            staff = Staff(username=username, password_hash=hash_password(password),
                          name=name, role=StaffRole.SUPER_ADMIN, store_id=None,
                          manager_id=None, status=StaffStatus.ACTIVE)
            db.add(staff)
            db.commit()
            db.refresh(staff)
            print(f"已创建超管账号：{username}（id={staff.id}）")

        total = db.query(Staff).filter(Staff.role == StaffRole.SUPER_ADMIN).count()
        print(f"\n当前超管数：{total}")
        print(f"登录账号：{username}")
        print(f"登录密码：{password}")
        print("\n超管后台入口：登录后侧边栏出现「门店管理」（租户账号看不到该菜单）。")
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="创建 / 重置平台超管账号")
    ap.add_argument("--username", default=DEFAULT_USER)
    ap.add_argument("--password", default=DEFAULT_PASS)
    ap.add_argument("--name", default=DEFAULT_NAME)
    args = ap.parse_args()
    create(args.username, args.password, args.name)
