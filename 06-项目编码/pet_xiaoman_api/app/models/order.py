"""订单：主状态机见 PRD §6.4，支付子状态独立流转。字段定义 = PRD §7.1。"""
import enum
from datetime import datetime

from sqlalchemy import String, Integer, Enum, DateTime, Boolean, DECIMAL, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import StoreScopedModel


class OrderStatus(str, enum.Enum):
    PENDING_CONFIRM = "待确认"
    BOOKED = "已预约"
    PICKING = "接宠中"
    IN_SERVICE = "服务中"
    WAIT_DELIVERY = "待交付"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


class PayType(str, enum.Enum):
    UNPAID = "未支付"
    DEPOSIT_PAID = "定金已付"
    FULL_PAID = "全款已付"
    SETTLED_OFFLINE = "到店付已结清"


class RefundStatus(str, enum.Enum):
    NONE = "无"
    REFUNDING = "退款中"
    REFUNDED = "已退款"
    FAILED = "退款失败"


class Order(StoreScopedModel):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING_CONFIRM)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    pet_id: Mapped[int] = mapped_column(Integer, index=True)
    pkg_id: Mapped[int] = mapped_column(Integer)                    # 套餐 service_item.id
    price_version: Mapped[str] = mapped_column(String(10))          # 下单时锁价快照
    addons: Mapped[list] = mapped_column(JSON, default=list)        # [{item_id, price_snapshot}]
    expect_time: Mapped[datetime] = mapped_column(DateTime)
    address: Mapped[str | None] = mapped_column(String(200))        # 自送时为空
    is_night: Mapped[bool] = mapped_column(Boolean, default=False)  # 22:00-7:00 下单
    total_amount: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)
    pay_type: Mapped[PayType] = mapped_column(Enum(PayType), default=PayType.UNPAID)
    paid_amount: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)
    refund_status: Mapped[RefundStatus] = mapped_column(Enum(RefundStatus), default=RefundStatus.NONE)
    cancel_reason: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)                 # 内部备注，客户不可见
    reschedule_count: Mapped[int] = mapped_column(Integer, default=0)  # 免费改期 1 次（PRD §6.2）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
