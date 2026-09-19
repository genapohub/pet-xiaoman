"""纪念品（PRD §7.1 product 表）：纪念清单（购物车）下单 + 到店选购，不做库存扣减（v1.1 决策）。

**履约口径（2026-09-19 拍板：混合履约，由 SKU 声明能力）**

不做「全邮寄」或「全自取」的二选一，而是让每个 SKU 声明它支持什么：

- `ship_enabled=False`（默认）→ **仅到店自取**。客户本来就得到店办火化/告别，
  现货纪念品当场交付：情绪闭环最强、免运费、无物流破损纠纷。
- `ship_enabled=True` → 结算时客户**可选**「到店自取」或「顺丰邮寄 + 收货信息」。
- `lead_days` = 制作工期（0=现货；>0=定制，如刻字件 3-5 天）。
  工期 >0 的件若选自取，意味着客户要二次到店——故这类默认引导邮寄。

因此「确认订单」页按履约方式**分区展示**（本次到店取 / N 天后寄出），而不是二选一。
"""
import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, DECIMAL, Enum, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import StoreScopedModel


class ProductStatus(str, enum.Enum):
    ON_SALE = "在售"
    OFF_SALE = "下架"


class ProductFulfillment(str, enum.Enum):
    """纪念品的交付方式（写入 ProductOrder.fulfillment）。"""
    PICKUP = "到店自取"
    SHIP = "顺丰邮寄"


class Product(StoreScopedModel):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    price: Mapped[float] = mapped_column(DECIMAL(10, 2))
    images: Mapped[list] = mapped_column(JSON, default=list)   # 图片 url 数组，首图=列表图
    description: Mapped[str | None] = mapped_column(String(200))
    # 分类（自由文本，如「纪念饰品 / 影像纪念 / 骨灰纪念」）。
    # 用文本而非枚举：不同门店卖的纪念品差异很大，枚举会逼门店往错误分类里塞。
    category: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[ProductStatus] = mapped_column(Enum(ProductStatus), default=ProductStatus.ON_SALE)
    stock_note: Mapped[str | None] = mapped_column(String(100))  # 库存备注文本（不做扣减）
    # 履约能力：不支持邮寄的件只能到店自取；支持邮寄的件由客户在结算时二选一
    ship_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    lead_days: Mapped[int] = mapped_column(Integer, default=0)   # 制作工期（天），0=现货
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CartItem(StoreScopedModel):
    """纪念清单（购物车）条目。

    设计取舍：
      - `(customer_id, product_id)` **唯一**：重复加购是累加 `qty` 而不是插新行，
        否则购物车里会出现两行同名商品，客户会以为是重复下单。
      - 不存价格快照：购物车是「意向」，价格以结算时刻的 `Product.price` 为准
        （与预约订单「提交时锁价」口径一致；只有结算生成的 ProductOrder 才落金额）。
      - 不做库存占用：纪念品不做库存扣减（v1.1 决策），故无 reserved 字段。
    """
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("customer_id", "product_id", name="uq_cart_customer_product"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, index=True)
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    qty: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ProductOrder(StoreScopedModel):
    """纪念品购买记录。

    一行 = 一件商品（含数量）。同一次结算的多件共享 `group_no`，便于门店按批备货/发货。
    之所以不做「订单头 + 明细」两张表：一期支付未开通（`PAY_ENABLED=false`），
    纪念品订单没有支付流水要挂，单表 + 分组号已经够用；
    等接入支付、需要按单收款时再拆头表（届时 `group_no` 就是天然的头主键）。
    """
    __tablename__ = "product_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_no: Mapped[str | None] = mapped_column(String(24), index=True)   # 一次结算的分组号
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, index=True)
    qty: Mapped[int] = mapped_column(Integer, default=1)
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2))                  # 单价 × qty
    fulfillment: Mapped[str] = mapped_column(String(20), default=ProductFulfillment.PICKUP.value)
    linked_order_no: Mapped[str | None] = mapped_column(String(20))        # 随服务订单交付时关联
    # 收货信息：仅「顺丰邮寄」的件填写；自取件留空
    contact_name: Mapped[str | None] = mapped_column(String(30))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    ship_address: Mapped[str | None] = mapped_column(String(200))
    pay_status: Mapped[str] = mapped_column(String(20), default="待支付")  # 待支付/已支付（微信支付开关后）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
