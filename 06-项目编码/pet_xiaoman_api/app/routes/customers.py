"""客户档案（B008/B009）：列表脱敏、详情、回访动态计算与登记、来源标记。"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import staff_auth
from app.models.customer import Customer, Source
from app.models.order import Order, OrderStatus
from app.models.pet import Pet
from app.models.staff import Staff, StaffRole
from app.models.visit_record import VisitRecord
from app.services.tenant import belongs, scoped

router = APIRouter()

VISIT_AFTER_DAYS = 30  # PRD：完成 30 天后回访


def _mask(phone: str, is_owner: bool) -> str:
    """店长可见全量，店员脱敏（PRD §8.5）。角色来自登录态 token 解析，不信任前端。"""
    return phone if is_owner else (phone[:3] + "****" + phone[-4:] if len(phone) >= 7 else "****")


@router.get("/customers", summary="B008 客户列表（含动态回访状态）")
def b_list(staff: Staff = Depends(staff_auth), db: Session = Depends(get_db)):
    is_owner = staff.role == StaffRole.MANAGER
    customers = scoped(db, Customer, staff.store_id).order_by(Customer.id.desc()).all()
    result = []
    for c in customers:
        pets = db.query(Pet).filter(Pet.owner_id == c.id, Pet.deleted.is_(False)).all()
        orders = db.query(Order).filter(Order.user_id == c.id).all()
        completed = [o for o in orders if o.status == OrderStatus.COMPLETED]
        visits = db.query(VisitRecord).filter(VisitRecord.customer_id == c.id).all()
        # 动态回访：最近完成单超 30 天且无回访记录
        pending_visit = False
        if completed and not visits:
            latest = max(o.updated_at for o in completed)
            pending_visit = datetime.now() - latest > timedelta(days=VISIT_AFTER_DAYS)
        result.append({
            "customer_id": c.id, "nickname": c.nickname,
            "phone": _mask(c.phone, is_owner),
            "pets": [p.name for p in pets],
            "order_count": len(orders),
            "last_order_at": max((o.created_at for o in orders), default=None).isoformat() if orders else None,
            "visit_status": "待回访" if pending_visit else ("已回访" if visits else "无需回访"),
        })
    return result


@router.get("/customers/{customer_id}", summary="B009 客户详情（服务历史 + 回访记录）")
def b_detail(customer_id: int, staff: Staff = Depends(staff_auth), db: Session = Depends(get_db)):
    c = db.get(Customer, customer_id)
    if not belongs(c, staff.store_id):
        raise HTTPException(404, "客户不存在")
    is_owner = staff.role == StaffRole.MANAGER
    pets = db.query(Pet).filter(Pet.owner_id == c.id, Pet.deleted.is_(False)).all()
    orders = db.query(Order).filter(Order.user_id == c.id).order_by(Order.created_at.desc()).all()
    visits = (db.query(VisitRecord).filter(VisitRecord.customer_id == c.id)
              .order_by(VisitRecord.created_at.desc()).all())
    return {
        "customer_id": c.id, "nickname": c.nickname,
        "phone": _mask(c.phone, is_owner), "source": c.source.value,
        "pets": [{"name": p.name, "species": p.species.value} for p in pets],
        "orders": [{"order_no": o.order_no, "status": o.status.value,
                    "total_amount": float(o.total_amount),
                    "created_at": o.created_at.isoformat()} for o in orders],
        "visits": [{"satisfaction": v.satisfaction, "would_recommend": v.would_recommend,
                    "notes": v.notes, "created_at": v.created_at.isoformat()} for v in visits],
    }


@router.post("/customers/{customer_id}/source", summary="来源渠道标记（可修正一次留痕）")
def set_source(customer_id: int, payload: dict, staff: Staff = Depends(staff_auth),
               db: Session = Depends(get_db)):
    c = db.get(Customer, customer_id)
    if not belongs(c, staff.store_id):
        raise HTTPException(404, "客户不存在")
    c.source = Source(payload["source"])
    db.commit()
    return {"customer_id": c.id, "source": c.source.value}


@router.post("/customers/{customer_id}/visit", summary="回访登记（提交后待回访关闭）")
def register_visit(customer_id: int, payload: dict, staff: Staff = Depends(staff_auth),
                   db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not belongs(customer, staff.store_id):
        raise HTTPException(404, "客户不存在")
    satisfaction = payload.get("satisfaction")
    if not satisfaction or not 1 <= int(satisfaction) <= 5:
        raise HTTPException(422, "满意度需为 1-5")
    v = VisitRecord(customer_id=customer_id, satisfaction=int(satisfaction),
                    would_recommend=bool(payload.get("would_recommend")),
                    notes=payload.get("notes"), store_id=staff.store_id)
    db.add(v)
    db.commit()
    return {"visit_id": v.id}
