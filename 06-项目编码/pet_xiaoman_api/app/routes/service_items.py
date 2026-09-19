"""服务项目与价格（B005）：CRUD + 版本化（PRD：每次改价即对外承诺变更）。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import staff_auth
from app.models.service_item import ItemType, ItemStatus, ServiceItem
from app.models.service_item_version import ServiceItemVersion
from app.models.staff import Staff
from app.services.tenant import belongs, scoped

router = APIRouter()


class ItemInput(BaseModel):
    type: str = Field(description="套餐/单项/加购")
    name: str = Field(max_length=50)
    price: float = Field(gt=0)
    weight_tier: str | None = None
    duration_text: str | None = Field(default=None, max_length=20,
                                      description="服务时长文案，如「约 2 小时」「按里程」")

    @field_validator("weight_tier", "duration_text", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        """空白串归一成 None（接口是对外契约，不能只靠前端 trim）。"""
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v


def _version_stamp() -> str:
    return f"v{datetime.now().strftime('%Y%m%d')}"


def _log_version(db: Session, item: ServiceItem) -> None:
    db.add(ServiceItemVersion(item_id=item.id, price=float(item.price), version=item.version))


@router.get("/service-items", summary="列表（type 筛选）")
def list_items(type: str | None = None, staff: Staff = Depends(staff_auth),
               db: Session = Depends(get_db)):
    query = scoped(db, ServiceItem, staff.store_id)
    if type:
        query = query.filter(ServiceItem.type == ItemType(type))
    rows = query.order_by(ServiceItem.id).all()
    return [{"id": i.id, "type": i.type.value, "name": i.name, "price": float(i.price),
             "weight_tier": i.weight_tier, "duration_text": i.duration_text,
             "status": i.status.value, "version": i.version}
            for i in rows]


@router.post("/service-items", summary="新建（含首版价格记录）")
def create_item(payload: ItemInput, staff: Staff = Depends(staff_auth),
                db: Session = Depends(get_db)):
    item = ServiceItem(type=ItemType(payload["type"] if isinstance(payload, dict) else payload.type),
                       name=payload.name, price=payload.price,
                       weight_tier=payload.weight_tier,
                       duration_text=payload.duration_text,
                       status=ItemStatus.ON_SALE, version=_version_stamp(),
                       store_id=staff.store_id)
    db.add(item)
    db.flush()
    _log_version(db, item)
    db.commit()
    return {"id": item.id, "version": item.version}


@router.put("/service-items/{item_id}", summary="编辑（改价即新版本生效，历史订单不受影响）")
def update_item(item_id: int, payload: ItemInput, staff: Staff = Depends(staff_auth),
                db: Session = Depends(get_db)):
    item = db.get(ServiceItem, item_id)
    if not belongs(item, staff.store_id):
        raise HTTPException(404, "服务项目不存在")
    price_changed = float(item.price) != payload.price
    item.name = payload.name
    item.price = payload.price
    item.weight_tier = payload.weight_tier
    # 时长只是说明文案，不参与锁价：改了不影响历史订单金额，故不触发新版本号
    item.duration_text = payload.duration_text
    if price_changed:
        item.version = _version_stamp()
        _log_version(db, item)
    db.commit()
    return {"id": item.id, "price": float(item.price), "version": item.version,
            "price_changed": price_changed,
            "notice": "新价格已公开生效，仅影响新订单" if price_changed else "已保存"}


@router.post("/service-items/{item_id}/off-sale", summary="下架（不物理删除，历史订单引用不受影响）")
def off_sale(item_id: int, staff: Staff = Depends(staff_auth), db: Session = Depends(get_db)):
    item = db.get(ServiceItem, item_id)
    if not belongs(item, staff.store_id):
        raise HTTPException(404, "服务项目不存在")
    item.status = ItemStatus.OFF_SALE
    db.commit()
    return {"id": item.id, "status": item.status.value}


@router.get("/service-items/{item_id}/versions", summary="价格版本历史")
def versions(item_id: int, staff: Staff = Depends(staff_auth), db: Session = Depends(get_db)):
    if not belongs(db.get(ServiceItem, item_id), staff.store_id):
        raise HTTPException(404, "服务项目不存在")
    rows = (db.query(ServiceItemVersion)
            .filter(ServiceItemVersion.item_id == item_id)
            .order_by(ServiceItemVersion.created_at.desc()).all())
    return [{"price": float(r.price), "version": r.version, "created_at": r.created_at.isoformat()}
            for r in rows]
