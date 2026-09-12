"""支付流水（PRD §7.1 payment 表）：微信支付对账的唯一事实源。"""
import enum
from datetime import datetime

from sqlalchemy import String, Integer, Enum, DateTime, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import StoreScopedModel


class BizType(str, enum.Enum):
    DEPOSIT = "定金"
    TAIL = "尾款"
    FULL = "全款"
    PRODUCT = "纪念品"


class PayStatus(str, enum.Enum):
    SUCCESS = "成功"
    FAILED = "失败"
    REFUNDED = "已退款"
    PARTIAL_REFUNDED = "部分退款"


class PaymentRecord(StoreScopedModel):
    __tablename__ = "payment_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, index=True)
    biz_type: Mapped[BizType] = mapped_column(Enum(BizType))
    amount: Mapped[float] = mapped_column(DECIMAL(10, 2))
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # 微信单号，对账唯一键
    pay_status: Mapped[PayStatus] = mapped_column(Enum(PayStatus), default=PayStatus.SUCCESS)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
