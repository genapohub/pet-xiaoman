"""C 端补充接口：公开价格表（C002/C003）/ 客户注册（微信登录接入前的轻量身份）/ 宠物档案（C009）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import customer_auth, ensure_customer_match, store_context
from app.models.customer import Customer
from app.models.order import Order
from app.models.pet import Pet
from app.models.service_item import ItemStatus, ServiceItem
from app.models.store_profile import StoreProfile
from app.services.tenant import (
    default_store_id, resolve_store_id_by_slug, scoped, store_clause, store_is_active,
)

router = APIRouter()


@router.get("/store/profile", summary="C 端门店白标（按 slug 换肤；无 slug 返回默认门店）")
def c_store_profile(slug: str | None = None, db: Session = Depends(get_db)):
    """公开接口：小程序进入时按门店标识拉取 logo/标语/主题色/店名，实现运行时换肤。

    门店被停用（store.status=disabled）时按「不存在」处理 → 404，门店不再接单。
    """
    if slug:
        store_id = resolve_store_id_by_slug(db, slug)  # 内含启用校验
        profile = (db.query(StoreProfile).filter(StoreProfile.store_id == store_id).first()
                   if store_id is not None else None)
    else:
        sid = default_store_id(db)
        if sid is not None and not store_is_active(db, sid):
            sid = None
        profile = (db.query(StoreProfile).filter(StoreProfile.store_id == sid).first()
                   if sid is not None else None)
    if not profile:
        raise HTTPException(404, "门店不存在")
    return {"store_id": profile.store_id, "slug": profile.slug, "name": profile.name,
            "slogan": profile.slogan, "logo_url": profile.logo_url,
            "primary_color": profile.primary_color, "theme": profile.theme}


@router.get("/service-items", summary="C002/C003 公开价格表（仅在售，全量单项价公开）")
def c_price_list(store_id: int | None = Depends(store_context), db: Session = Depends(get_db)):
    rows = (scoped(db, ServiceItem, store_id).filter(ServiceItem.status == ItemStatus.ON_SALE)
            .order_by(ServiceItem.type, ServiceItem.id).all())
    return [{"id": i.id, "type": i.type.value, "name": i.name, "price": float(i.price),
             "weight_tier": i.weight_tier, "version": i.version} for i in rows]


class CustomerInput(BaseModel):
    nickname: str = Field(default="微信用户", max_length=50)
    phone: str = Field(default="", max_length=20)


@router.post("/customers", summary="轻量客户注册（返回 id 供本地缓存；微信登录接入前使用）")
def c_register(payload: CustomerInput, store_id: int | None = Depends(store_context),
               db: Session = Depends(get_db)):
    c = Customer(nickname=payload.nickname, phone=payload.phone, store_id=store_id)
    db.add(c)
    db.commit()
    return {"customer_id": c.id}


@router.get("/pets", summary="C009 宠物档案（含服务历史计数）")
def c_pets(user_id: int, db: Session = Depends(get_db),
           token_customer_id: int | None = Depends(customer_auth),
           store_id: int | None = Depends(store_context)):
    user_id = ensure_customer_match(token_customer_id, user_id)
    pets = scoped(db, Pet, store_id).filter(Pet.owner_id == user_id,
                                            Pet.deleted.is_(False)).all()
    result = []
    for p in pets:
        o_q = db.query(Order).filter(Order.pet_id == p.id)
        o_clause = store_clause(Order, store_id)
        if o_clause is not None:
            o_q = o_q.filter(o_clause)
        orders = o_q.order_by(Order.created_at.desc()).all()
        result.append({
            "pet_id": p.id, "name": p.name, "species": p.species.value,
            "weight": float(p.weight) if p.weight else None,
            "orders": [{"order_no": o.order_no, "status": o.status.value,
                        "created_at": o.created_at.isoformat()} for o in orders],
        })
    return result
