"""团队成员管理（店长专属）：创建 / 查询 / 更新 / 停用，含两级归属。

单店版两级结构：一名店长（manager_id 为空）+ 若干店员（manager_id=店长）。
店员由店长在本门店内创建，自动归属该店长与门店。
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_perm
from app.models.staff import Staff, StaffRole, StaffStatus, ROLE_DISPLAY
from app.services.staff_auth_service import hash_password

router = APIRouter()


class StaffCreate(BaseModel):
    username: str
    password: str
    name: str
    phone: str | None = None


class StaffUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    password: str | None = None
    status: StaffStatus | None = None


def _serialize(s: Staff) -> dict:
    return {
        "id": s.id, "username": s.username, "name": s.name, "phone": s.phone,
        "role": s.role.value, "role_name": ROLE_DISPLAY.get(s.role, s.role.value),
        "store_id": s.store_id, "manager_id": s.manager_id, "status": s.status.value,
    }


def _same_store(staff: Staff, db: Session, staff_id: int) -> Staff:
    s = db.query(Staff).filter(Staff.id == staff_id, Staff.store_id == staff.store_id).first()
    if not s:
        raise HTTPException(404, "成员不存在")
    return s


@router.get("", summary="团队成员列表（本门店，按层级排序）")
def list_staff(staff: Staff = Depends(require_perm("staff.manage")), db: Session = Depends(get_db)):
    members = (db.query(Staff).filter(Staff.store_id == staff.store_id)
               .order_by(Staff.role, Staff.id).all())
    return [_serialize(m) for m in members]


@router.post("", summary="新建员工（归属本店，上级为当前店长）")
def create_staff(payload: StaffCreate, staff: Staff = Depends(require_perm("staff.manage")),
                db: Session = Depends(get_db)):
    if db.query(Staff).filter(Staff.username == payload.username).first():
        raise HTTPException(409, "账号已存在")
    emp = Staff(
        username=payload.username, password_hash=hash_password(payload.password),
        name=payload.name, phone=payload.phone, role=StaffRole.EMPLOYEE,
        store_id=staff.store_id, manager_id=staff.id, status=StaffStatus.ACTIVE,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return _serialize(emp)


@router.get("/{staff_id}", summary="成员详情")
def get_staff(staff_id: int, staff: Staff = Depends(require_perm("staff.manage")),
             db: Session = Depends(get_db)):
    return _serialize(_same_store(staff, db, staff_id))


@router.put("/{staff_id}", summary="更新成员")
def update_staff(staff_id: int, payload: StaffUpdate,
                staff: Staff = Depends(require_perm("staff.manage")), db: Session = Depends(get_db)):
    s = _same_store(staff, db, staff_id)
    if payload.name is not None:
        s.name = payload.name
    if payload.phone is not None:
        s.phone = payload.phone
    if payload.password:
        s.password_hash = hash_password(payload.password)
    if payload.status is not None:
        s.status = payload.status
    db.commit()
    return _serialize(s)


@router.post("/{staff_id}/disable", summary="停用成员（店长不可停用）")
def disable_staff(staff_id: int, staff: Staff = Depends(require_perm("staff.manage")),
                 db: Session = Depends(get_db)):
    s = _same_store(staff, db, staff_id)
    if s.role == StaffRole.MANAGER:
        raise HTTPException(400, "店长不可停用")
    s.status = StaffStatus.DISABLED
    db.commit()
    return _serialize(s)
