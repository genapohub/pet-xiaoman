"""纪念品管理（B006）与 C 端展示购买（C007）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import staff_auth, store_context
from app.models.order import Order
from app.models.product import Product, ProductOrder, ProductStatus
from app.models.staff import Staff
from app.services import payment as pay_framework
from app.services.tenant import belongs, scoped, store_clause

router = APIRouter()


class ProductInput(BaseModel):
    name: str = Field(max_length=50)
    price: float = Field(gt=0)
    images: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=200)
    category: str | None = Field(default=None, max_length=20, description="分类，如「纪念饰品」")
    stock_note: str | None = Field(default=None, max_length=100)
    # 履约能力（2026-09-19 拍板：混合履约，SKU 声明能力）见 app/models/product.py
    ship_enabled: bool = Field(default=False, description="是否支持邮寄；false=仅到店自取")
    lead_days: int = Field(default=0, ge=0, le=60, description="制作工期（天），0=现货")

    @field_validator("description", "category", "stock_note", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        """空白串一律归一成 None。

        不能只靠前端 trim：接口是对外契约，任何客户端（脚本、别的端）都能传空格进来，
        存成 `'   '` 后列表里会出现「看着是空、但不是 —」的格子，也无法用 IS NULL 筛。
        """
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v


@router.get("/api/c/products", summary="C007 纪念品展示（在售）")
def c_list(store_id: int | None = Depends(store_context), db: Session = Depends(get_db)):
    rows = (scoped(db, Product, store_id).filter(Product.status == ProductStatus.ON_SALE)
            .order_by(Product.id.desc()).all())
    return [{"id": i.id, "name": i.name, "price": float(i.price),
             "image": (i.images or [None])[0], "description": i.description,
             "category": i.category, "stock_note": i.stock_note,
             # 列表卡要显示「现货·到店取」/「定制 3-5 天·可邮寄」，故必须透出履约能力
             "ship_enabled": bool(i.ship_enabled), "lead_days": int(i.lead_days or 0)}
            for i in rows]


@router.get("/api/c/products/{product_id}", summary="C007 纪念品详情")
def c_detail(product_id: int, store_id: int | None = Depends(store_context),
             db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if (not p or p.status != ProductStatus.ON_SALE or not belongs(p, store_id)):
        raise HTTPException(404, "商品不存在或已下架")
    return {
        "id": p.id, "name": p.name, "price": float(p.price),
        "images": p.images or [], "image": (p.images or [None])[0],
        "description": p.description, "category": p.category, "stock_note": p.stock_note,
        "ship_enabled": bool(p.ship_enabled), "lead_days": int(p.lead_days or 0),
    }


@router.post("/api/c/products/{product_id}/buy", summary="C007 单件直购（保留：B 端代客/随单交付用）")
def c_buy(product_id: int, payload: dict, store_id: int | None = Depends(store_context),
          db: Session = Depends(get_db)):
    """单件直购：C 端主流程已改为「纪念清单 → 结算」（见 `app/routes/c_cart.py`），
    本接口保留给 B 端代客下单与「随服务订单交付」场景，故不做移除。"""
    product = db.get(Product, product_id)
    if (not product or product.status != ProductStatus.ON_SALE
            or not belongs(product, store_id)):
        raise HTTPException(422, "商品已下架")
    if not pay_framework.settings.PAY_ENABLED:
        raise HTTPException(422, "线上支付暂未开启，欢迎到店选购")
    customer_id = payload.get("customer_id", 1)
    fulfillment = payload.get("fulfillment", "到店自取")
    linked = payload.get("linked_order_no")
    if fulfillment == "随单交付" and linked:
        linked_order = db.query(Order).filter(Order.order_no == linked).first()
        if not belongs(linked_order, store_id):
            raise HTTPException(422, "关联订单不存在")
    po = ProductOrder(product_id=product_id, customer_id=customer_id, qty=1,
                      amount=float(product.price), fulfillment=fulfillment,
                      linked_order_no=linked, pay_status="已支付", store_id=store_id)
    db.add(po)
    db.commit()
    # TODO(商户号开通后)：统一下单返回支付参数；当前开关关闭时上方已拦截
    return {"product_order_id": po.id, "amount": float(po.amount),
            "fulfillment": po.fulfillment, "pay_status": po.pay_status}


@router.get("/api/b/products", summary="B006 列表（含下架）")
def b_list(staff: Staff = Depends(staff_auth), db: Session = Depends(get_db)):
    rows = scoped(db, Product, staff.store_id).order_by(Product.id.desc()).all()
    return [{"id": i.id, "name": i.name, "price": float(i.price), "images": i.images or [],
             "description": i.description, "category": i.category,
             "status": i.status.value, "stock_note": i.stock_note,
             "ship_enabled": bool(i.ship_enabled), "lead_days": int(i.lead_days or 0)}
            for i in rows]


@router.post("/api/b/products", summary="B006 新建")
def b_create(payload: ProductInput, staff: Staff = Depends(staff_auth),
             db: Session = Depends(get_db)):
    item = Product(**payload.model_dump(), status=ProductStatus.ON_SALE,
                   store_id=staff.store_id)
    db.add(item)
    db.commit()
    return {"id": item.id}


@router.put("/api/b/products/{product_id}", summary="B006 编辑")
def b_update(product_id: int, payload: ProductInput, staff: Staff = Depends(staff_auth),
             db: Session = Depends(get_db)):
    item = db.get(Product, product_id)
    if not belongs(item, staff.store_id):
        raise HTTPException(404, "商品不存在")
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    db.commit()
    return {"id": item.id}


@router.post("/api/b/products/{product_id}/toggle", summary="B006 上架/下架切换")
def b_toggle(product_id: int, staff: Staff = Depends(staff_auth),
             db: Session = Depends(get_db)):
    item = db.get(Product, product_id)
    if not belongs(item, staff.store_id):
        raise HTTPException(404, "商品不存在")
    item.status = (ProductStatus.OFF_SALE if item.status == ProductStatus.ON_SALE
                   else ProductStatus.ON_SALE)
    db.commit()
    return {"id": item.id, "status": item.status.value}
