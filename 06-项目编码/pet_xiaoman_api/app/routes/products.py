"""纪念品管理（B006）与 C 端展示购买（C007）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order
from app.models.product import Product, ProductOrder, ProductStatus
from app.services import payment as pay_framework

router = APIRouter()


class ProductInput(BaseModel):
    name: str = Field(max_length=50)
    price: float = Field(gt=0)
    images: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=200)
    stock_note: str | None = Field(default=None, max_length=100)


@router.get("/api/c/products", summary="C007 纪念品展示（在售）")
def c_list(db: Session = Depends(get_db)):
    rows = (db.query(Product).filter(Product.status == ProductStatus.ON_SALE)
            .order_by(Product.id.desc()).all())
    return [{"id": i.id, "name": i.name, "price": float(i.price),
             "image": (i.images or [None])[0], "description": i.description,
             "stock_note": i.stock_note} for i in rows]


@router.post("/api/c/products/{product_id}/buy", summary="C007 单件直购（支付开关关闭时提示到店选购）")
def c_buy(product_id: int, payload: dict, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or product.status != ProductStatus.ON_SALE:
        raise HTTPException(422, "商品已下架")
    if not pay_framework.settings.PAY_ENABLED:
        raise HTTPException(422, "线上支付暂未开启，欢迎到店选购")
    customer_id = payload.get("customer_id", 1)
    fulfillment = payload.get("fulfillment", "到店自取")
    linked = payload.get("linked_order_no")
    if fulfillment == "随单交付" and linked:
        if not db.query(Order).filter(Order.order_no == linked).first():
            raise HTTPException(422, "关联订单不存在")
    po = ProductOrder(product_id=product_id, customer_id=customer_id,
                      amount=float(product.price), fulfillment=fulfillment,
                      linked_order_no=linked, pay_status="已支付")
    db.add(po)
    db.commit()
    # TODO(商户号开通后)：统一下单返回支付参数；当前开关关闭时上方已拦截
    return {"product_order_id": po.id, "amount": float(po.amount),
            "fulfillment": po.fulfillment, "pay_status": po.pay_status}


@router.get("/api/b/products", summary="B006 列表（含下架）")
def b_list(db: Session = Depends(get_db)):
    rows = db.query(Product).order_by(Product.id.desc()).all()
    return [{"id": i.id, "name": i.name, "price": float(i.price), "images": i.images or [],
             "description": i.description, "status": i.status.value, "stock_note": i.stock_note}
            for i in rows]


@router.post("/api/b/products", summary="B006 新建")
def b_create(payload: ProductInput, db: Session = Depends(get_db)):
    item = Product(**payload.model_dump(), status=ProductStatus.ON_SALE)
    db.add(item)
    db.commit()
    return {"id": item.id}


@router.put("/api/b/products/{product_id}", summary="B006 编辑")
def b_update(product_id: int, payload: ProductInput, db: Session = Depends(get_db)):
    item = db.get(Product, product_id)
    if not item:
        raise HTTPException(404, "商品不存在")
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    db.commit()
    return {"id": item.id}


@router.post("/api/b/products/{product_id}/toggle", summary="B006 上架/下架切换")
def b_toggle(product_id: int, db: Session = Depends(get_db)):
    item = db.get(Product, product_id)
    if not item:
        raise HTTPException(404, "商品不存在")
    item.status = (ProductStatus.OFF_SALE if item.status == ProductStatus.ON_SALE
                   else ProductStatus.ON_SALE)
    db.commit()
    return {"id": item.id, "status": item.status.value}
