"""骨灰寄存（B007/C008）：登记/续存/取回/到期提醒 + 客户查询。"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import staff_auth, store_context
from app.models.boarding import Boarding, BoardingStatus
from app.models.pet import Pet
from app.models.staff import Staff
from app.services.tenant import belongs, store_clause

router = APIRouter()


class BoardingInput(BaseModel):
    pet_id: int
    customer_id: int
    location: str = Field(max_length=50)
    start_date: date = Field(default_factory=date.today)
    expire_date: date


def _brief(b: Boarding, pet: Pet | None) -> dict:
    return {"id": b.id, "pet_name": pet.name if pet else "-",
            "location": b.location, "start_date": b.start_date.isoformat(),
            "expire_date": b.expire_date.isoformat(), "days_left": b.days_left,
            "severity": b.severity, "status": b.status.value}


@router.get("/api/b/boardings", summary="B007 列表（临期标黄/到期标红，待取回置顶）")
def b_list(staff: Staff = Depends(staff_auth), db: Session = Depends(get_db)):
    query = (db.query(Boarding, Pet)
             .outerjoin(Pet, Boarding.pet_id == Pet.id))
    clause = store_clause(Boarding, staff.store_id)
    if clause is not None:
        query = query.filter(clause)
    rows = query.order_by(Boarding.expire_date).all()
    result = [_brief(b, pet) for b, pet in rows if b.status != BoardingStatus.TAKEN]
    result += [_brief(b, pet) for b, pet in rows if b.status == BoardingStatus.TAKEN]
    return result


@router.post("/api/b/boardings", summary="B007 登记（同门店内位置在存唯一）")
def b_create(payload: BoardingInput, staff: Staff = Depends(staff_auth),
             db: Session = Depends(get_db)):
    if payload.expire_date <= payload.start_date:
        raise HTTPException(422, "到期日必须晚于寄存日")
    conflict_q = (db.query(Boarding)
                  .filter(Boarding.location == payload.location,
                          Boarding.status.in_([BoardingStatus.STORED, BoardingStatus.RENEWED])))
    clause = store_clause(Boarding, staff.store_id)
    if clause is not None:
        conflict_q = conflict_q.filter(clause)
    if conflict_q.first():
        raise HTTPException(422, f"位置 {payload.location} 已被占用")
    b = Boarding(**payload.model_dump(), store_id=staff.store_id)
    db.add(b)
    db.commit()
    return {"id": b.id}


@router.post("/api/b/boardings/{boarding_id}/renew", summary="续存（改到期日留痕）")
def renew(boarding_id: int, payload: dict, staff: Staff = Depends(staff_auth),
          db: Session = Depends(get_db)):
    b = db.get(Boarding, boarding_id)
    if not belongs(b, staff.store_id) or b.status == BoardingStatus.TAKEN:
        raise HTTPException(404, "寄存记录不存在或已取回")
    new_date = date.fromisoformat(payload["expire_date"])
    if new_date <= b.expire_date:
        raise HTTPException(422, "续存日期必须晚于当前到期日")
    b.expire_date = new_date
    b.status = BoardingStatus.RENEWED
    b.reminder_sent = False
    db.commit()
    return {"id": b.id, "expire_date": b.expire_date.isoformat()}


@router.post("/api/b/boardings/{boarding_id}/take", summary="取回（必填取回人）")
def take(boarding_id: int, payload: dict, staff: Staff = Depends(staff_auth),
         db: Session = Depends(get_db)):
    b = db.get(Boarding, boarding_id)
    if not belongs(b, staff.store_id) or b.status == BoardingStatus.TAKEN:
        raise HTTPException(404, "寄存记录不存在或已取回")
    taker = payload.get("taken_by")
    if not taker:
        raise HTTPException(422, "必填取回人")
    b.status = BoardingStatus.TAKEN
    b.notes = f"取回人：{taker}"
    db.commit()
    return {"id": b.id, "status": b.status.value}


@router.get("/api/c/boardings/query", summary="C008 寄存查询（手机号后四位验证）")
def c_query(phone_tail: str, store_id: int | None = Depends(store_context),
            db: Session = Depends(get_db)):
    if len(phone_tail) != 4 or not phone_tail.isdigit():
        raise HTTPException(422, "请输入手机号后四位")
    query = (db.query(Boarding, Pet)
             .outerjoin(Pet, Boarding.pet_id == Pet.id)
             .filter(Boarding.status != BoardingStatus.TAKEN))
    clause = store_clause(Boarding, store_id)
    if clause is not None:
        query = query.filter(clause)
    rows = query.all()
    # 单店简化：客户 phone 脱敏存储，校验用后四位匹配 customer 表
    from app.models.customer import Customer
    result = []
    for b, pet in rows:
        customer = db.get(Customer, b.customer_id)
        if customer and customer.phone.endswith(phone_tail):
            result.append({"pet_name": pet.name if pet else "-",
                           "location": b.location,
                           "expire_date": b.expire_date.isoformat(),
                           "days_left": b.days_left,
                           "severity": b.severity})
    if not result:
        raise HTTPException(404, "未找到匹配的寄存记录")
    return result
