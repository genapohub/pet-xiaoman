"""平台层（超管）门店管理：开店 / 启停 / 配品牌 / 开门店账号。

设计要点：
- 全部接口要求 `super_admin`（`store_id` 为空）＋ 对应的平台权限 code；
- **所有门店业务操作都在路径里显式带 store_id**，绝不依赖 `staff.store_id is None`
  去"看到全部数据"——那是 `tenant.scoped()` 为兼容 legacy 单店调用留的口子，不是超管特权；
- 租户侧接口（`/api/b/store/profile`、`/api/b/staff`）保持"只能操作自己那家店"，
  品牌配置已收归超管，租户不可改。
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_super_admin
from app.models.staff import (
    Store, StoreStatus, Staff, StaffRole, StaffStatus, ROLE_DISPLAY, STORE_ROLES,
)
from app.models.store_profile import StoreProfile, DEFAULT_PRIMARY_COLOR
from app.services.staff_auth_service import hash_password
from app.services.validators import (
    valid_slug, valid_hex_color, valid_logo_url, valid_slogan,
)

router = APIRouter()


def _platform_perm(code: str):
    """超管身份 + 具体平台权限（权限可由 RBAC 页调整，故不只认角色）。"""
    def dep(staff: Staff = Depends(require_super_admin)) -> Staff:
        if code not in getattr(staff, "permissions", []):
            raise HTTPException(403, f"缺少平台权限：{code}")
        return staff

    return dep


# ---------- 入参 ----------
class StoreCreateInput(BaseModel):
    store_name: str = Field(max_length=50, description="门店名称（内部）")
    slug: str = Field(max_length=50, description="C 端入口标识，全局唯一")
    brand_name: str | None = Field(default=None, max_length=50, description="对外店名，默认同门店名称")
    slogan: str | None = None
    primary_color: str | None = None
    logo_url: str | None = None
    admin_username: str = Field(max_length=32, description="该店首位店长账号")
    admin_password: str = Field(min_length=6)
    admin_name: str = Field(default="店长", max_length=50)

    _check_slug = field_validator("slug")(valid_slug)
    _check_slogan = field_validator("slogan")(valid_slogan)
    _check_logo = field_validator("logo_url")(valid_logo_url)

    @field_validator("primary_color")
    @classmethod
    def _check_color(cls, v: str | None) -> str | None:
        return valid_hex_color(v)


class StoreProfileInput(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    slogan: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    theme_json: dict | None = None

    _check_slogan = field_validator("slogan")(valid_slogan)
    _check_logo = field_validator("logo_url")(valid_logo_url)

    @field_validator("primary_color")
    @classmethod
    def _check_color(cls, v: str | None) -> str | None:
        return valid_hex_color(v)


class StoreStatusInput(BaseModel):
    status: StoreStatus


class StoreStaffInput(BaseModel):
    username: str = Field(max_length=32)
    password: str = Field(min_length=6)
    name: str = Field(max_length=50)
    phone: str | None = None
    role: StaffRole = StaffRole.EMPLOYEE

    @field_validator("role")
    @classmethod
    def _check_role(cls, v: StaffRole) -> StaffRole:
        if v not in STORE_ROLES:
            raise ValueError("门店内只能创建店长或店员")
        return v


class StoreStaffUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    password: str | None = None
    status: StaffStatus | None = None


# ---------- 序列化 ----------
def _profile_dict(p: StoreProfile) -> dict:
    return {"store_id": p.store_id, "slug": p.slug, "name": p.name, "slogan": p.slogan,
            "logo_url": p.logo_url, "primary_color": p.primary_color, "theme": p.theme}


def _staff_dict(s: Staff) -> dict:
    return {"id": s.id, "username": s.username, "name": s.name, "phone": s.phone,
            "role": s.role.value, "role_name": ROLE_DISPLAY.get(s.role, s.role.value),
            "store_id": s.store_id, "manager_id": s.manager_id, "status": s.status.value,
            "created_at": s.created_at.isoformat() if s.created_at else None}


def _get_store(db: Session, store_id: int) -> Store:
    store = db.get(Store, store_id)
    if store is None:
        raise HTTPException(404, "门店不存在")
    return store


def _get_profile(db: Session, store_id: int) -> StoreProfile:
    prof = db.query(StoreProfile).filter(StoreProfile.store_id == store_id).first()
    if prof is None:
        raise HTTPException(404, "该门店尚未配置品牌资料")
    return prof


def _store_dict(db: Session, store: Store) -> dict:
    prof = db.query(StoreProfile).filter(StoreProfile.store_id == store.id).first()
    managers = (db.query(Staff)
                .filter(Staff.store_id == store.id, Staff.role == StaffRole.MANAGER).count())
    staff_total = db.query(Staff).filter(Staff.store_id == store.id).count()
    return {
        "store_id": store.id,
        "name": store.name,
        "status": store.status.value,
        "created_at": store.created_at.isoformat() if store.created_at else None,
        "profile": _profile_dict(prof) if prof else None,
        "manager_count": managers,
        "staff_count": staff_total,
    }


# ---------- 门店 ----------
@router.get("/stores", summary="门店列表（平台超管）")
def list_stores(staff: Staff = Depends(_platform_perm("store.manage")),
                db: Session = Depends(get_db)):
    stores = db.query(Store).order_by(Store.id).all()
    return [_store_dict(db, s) for s in stores]


@router.post("/stores", summary="开通门店（建店 + 品牌 + 首位店长）")
def create_store(payload: StoreCreateInput,
                 staff: Staff = Depends(_platform_perm("store.manage")),
                 db: Session = Depends(get_db)):
    if db.query(StoreProfile).filter(StoreProfile.slug == payload.slug).first():
        raise HTTPException(409, f"门店标识 {payload.slug} 已被占用")
    if db.query(Staff).filter(Staff.username == payload.admin_username).first():
        raise HTTPException(409, "账号已存在")

    store = Store(name=payload.store_name, status=StoreStatus.ACTIVE)
    db.add(store)
    db.commit()
    db.refresh(store)

    prof = StoreProfile(
        store_id=store.id, slug=payload.slug,
        name=payload.brand_name or payload.store_name, slogan=payload.slogan,
        logo_url=payload.logo_url,
        primary_color=payload.primary_color or DEFAULT_PRIMARY_COLOR, theme_json={},
    )
    db.add(prof)
    mgr = Staff(username=payload.admin_username,
                password_hash=hash_password(payload.admin_password),
                name=payload.admin_name, role=StaffRole.MANAGER, store_id=store.id,
                manager_id=None, status=StaffStatus.ACTIVE)
    db.add(mgr)
    db.commit()
    db.refresh(prof)
    db.refresh(mgr)
    return {"store": _store_dict(db, store), "manager": _staff_dict(mgr)}


@router.get("/stores/{store_id}", summary="门店详情（平台超管）")
def get_store(store_id: int, staff: Staff = Depends(_platform_perm("store.manage")),
              db: Session = Depends(get_db)):
    return _store_dict(db, _get_store(db, store_id))


@router.post("/stores/{store_id}/status", summary="启用 / 停用门店")
def set_store_status(store_id: int, payload: StoreStatusInput,
                     staff: Staff = Depends(_platform_perm("store.manage")),
                     db: Session = Depends(get_db)):
    """停用后 C 端按该店 slug 访问一律 404（门店不再接单），后台数据保留。"""
    store = _get_store(db, store_id)
    store.status = payload.status
    db.commit()
    return _store_dict(db, store)


# ---------- 品牌（超管代配，租户不可改）----------
@router.get("/stores/{store_id}/profile", summary="读取指定门店品牌（平台超管）")
def get_store_profile(store_id: int,
                      staff: Staff = Depends(_platform_perm("store.brand")),
                      db: Session = Depends(get_db)):
    _get_store(db, store_id)
    return _profile_dict(_get_profile(db, store_id))


@router.put("/stores/{store_id}/profile", summary="配置指定门店品牌与 UI（平台超管）")
def update_store_profile(store_id: int, payload: StoreProfileInput,
                         staff: Staff = Depends(_platform_perm("store.brand")),
                         db: Session = Depends(get_db)):
    """店名 / 标语 / logo / 主色 由此统一配置，租户侧已收权不可改。"""
    prof = _get_profile(db, _get_store(db, store_id).id)
    if payload.name is not None:
        prof.name = payload.name
    if payload.slogan is not None:
        prof.slogan = payload.slogan
    if payload.logo_url is not None:
        prof.logo_url = payload.logo_url
    if payload.primary_color is not None:
        prof.primary_color = payload.primary_color
    if payload.theme_json is not None:
        prof.theme_json = payload.theme_json
    db.commit()
    db.refresh(prof)
    return _profile_dict(prof)


# ---------- 门店账号 ----------
@router.get("/stores/{store_id}/staff", summary="门店账号列表（平台超管）")
def list_store_staff(store_id: int,
                     staff: Staff = Depends(_platform_perm("store.provision")),
                     db: Session = Depends(get_db)):
    _get_store(db, store_id)
    rows = (db.query(Staff).filter(Staff.store_id == store_id)
            .order_by(Staff.role, Staff.id).all())
    return [_staff_dict(s) for s in rows]


@router.post("/stores/{store_id}/staff", summary="为门店开账号（店长 / 店员）")
def create_store_staff(store_id: int, payload: StoreStaffInput,
                       staff: Staff = Depends(_platform_perm("store.provision")),
                       db: Session = Depends(get_db)):
    _get_store(db, store_id)
    if db.query(Staff).filter(Staff.username == payload.username).first():
        raise HTTPException(409, "账号已存在")
    # 店员默认挂在门店的店长名下；店长本人 manager_id 为空
    manager_id = None
    if payload.role == StaffRole.EMPLOYEE:
        mgr = (db.query(Staff)
               .filter(Staff.store_id == store_id, Staff.role == StaffRole.MANAGER)
               .order_by(Staff.id).first())
        manager_id = mgr.id if mgr else None
    emp = Staff(username=payload.username,
                password_hash=hash_password(payload.password),
                name=payload.name, phone=payload.phone, role=payload.role,
                store_id=store_id, manager_id=manager_id, status=StaffStatus.ACTIVE)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return _staff_dict(emp)


def _same_store_staff(db: Session, store_id: int, staff_id: int) -> Staff:
    s = db.query(Staff).filter(Staff.id == staff_id, Staff.store_id == store_id).first()
    if s is None:
        raise HTTPException(404, "该门店下无此账号")
    return s


@router.put("/stores/{store_id}/staff/{staff_id}", summary="改门店账号（改密 / 改名 / 状态）")
def update_store_staff(store_id: int, staff_id: int, payload: StoreStaffUpdate,
                       staff: Staff = Depends(_platform_perm("store.provision")),
                       db: Session = Depends(get_db)):
    s = _same_store_staff(db, store_id, staff_id)
    if payload.name is not None:
        s.name = payload.name
    if payload.phone is not None:
        s.phone = payload.phone
    if payload.password:
        s.password_hash = hash_password(payload.password)
    if payload.status is not None:
        s.status = payload.status
    db.commit()
    return _staff_dict(s)


@router.post("/stores/{store_id}/staff/{staff_id}/disable", summary="停用门店账号")
def disable_store_staff(store_id: int, staff_id: int,
                        staff: Staff = Depends(_platform_perm("store.provision")),
                        db: Session = Depends(get_db)):
    """停用账号不做角色限制（超管可停店长），但不允许停用自己。"""
    s = _same_store_staff(db, store_id, staff_id)
    if s.id == staff.id:
        raise HTTPException(400, "不能停用当前登录账号")
    s.status = StaffStatus.DISABLED
    db.commit()
    return _staff_dict(s)
