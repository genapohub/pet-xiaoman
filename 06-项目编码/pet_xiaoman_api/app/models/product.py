"""纪念品（PRD §7.1 product 表）：线上单件直购 + 到店选购，不做库存扣减（v1.1 决策）。"""
import enum
from datetime import datetime

from sqlalchemy import String, Integer, Enum, DECIMAL, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import StoreScopedModel


class ProductStatus(str, enum.Enum):
    ON_SALE = "在售"
    OFF_SALE = "下架"


class Product(StoreScopedModel):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    price: Mapped[float] = mapped_column(DECIMAL(10, 2))
    images: Mapped[list] = mapped_column(JSON, default=list)   # 图片 url 数组，首图=列表图
    description: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[ProductStatus] = mapped_column(Enum(ProductStatus), default=ProductStatus.ON_SALE)
    stock_note: Mapped[str | None] = mapped_column(String(100))  # 库存备注文本（不做扣减）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ProductOrder(StoreScopedModel):
    """纪念品购买记录（单件直购）：随单交付或到店自取。"""
    __tablename__ = "product_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, index=True)
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2))
    fulfillment: Mapped[str] = mapped_column(String(20), default="到店自取")  # 随单交付/到店自取
    linked_order_no: Mapped[str | None] = mapped_column(String(20))          # 随单交付时关联
    pay_status: Mapped[str] = mapped_column(String(20), default="待支付")     # 待支付/已支付（微信支付开关后）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
