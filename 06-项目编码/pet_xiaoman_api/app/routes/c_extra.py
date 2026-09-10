"""C 端补充接口：公开价格表（C002/C003）/ 客户注册（微信登录接入前的轻量身份）/ 宠物档案（C009）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import customer_auth, ensure_customer_match
from app.models.customer import Customer
from app.models.order import Order
from app.models.pet import Pet
from app.models.service_item import ItemStatus, ServiceItem

router = APIRouter()


@router.get("/service-items", summary="C002/C003 公开价格表（仅在售，全量单项价公开）")
def c_price_list(db: Session = Depends(get_db)):
    rows = (db.query(ServiceItem).filter(ServiceItem.status == ItemStatus.ON_SALE)
            .order_by(ServiceItem.type, ServiceItem.id).all())
    return [{"id": i.id, "type": i.type.value, "name": i.name, "price": float(i.price),
             "weight_tier": i.weight_tier, "version": i.version} for i in rows]


class CustomerInput(BaseModel):
    nickname: str = Field(default="微信用户", max_length=50)
    phone: str = Field(default="", max_length=20)


@router.post("/customers", summary="轻量客户注册（返回 id 供本地缓存；微信登录接入前使用）")
def c_register(payload: CustomerInput, db: Session = Depends(get_db)):
    c = Customer(nickname=payload.nickname, phone=payload.phone)
    db.add(c)
    db.commit()
    return {"customer_id": c.id}


@router.get("/pets", summary="C009 宠物档案（含服务历史计数）")
def c_pets(user_id: int, db: Session = Depends(get_db),
           token_customer_id: int | None = Depends(customer_auth)):
    user_id = ensure_customer_match(token_customer_id, user_id)
    pets = db.query(Pet).filter(Pet.owner_id == user_id, Pet.deleted.is_(False)).all()
    result = []
    for p in pets:
        orders = (db.query(Order)
                  .filter(Order.pet_id == p.id)
                  .order_by(Order.created_at.desc()).all())
        result.append({
            "pet_id": p.id, "name": p.name, "species": p.species.value,
            "weight": float(p.weight) if p.weight else None,
            "orders": [{"order_no": o.order_no, "status": o.status.value,
                        "created_at": o.created_at.isoformat()} for o in orders],
        })
    return result
