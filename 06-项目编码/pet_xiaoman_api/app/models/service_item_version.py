"""价格版本流水（PRD B005：改动留版本记录，历史订单按快照不受影响）。"""
from datetime import datetime

from sqlalchemy import String, Integer, DECIMAL, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ServiceItemVersion(BaseModel):
    __tablename__ = "service_item_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(Integer, index=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2))
    version: Mapped[str] = mapped_column(String(10))  # v20260905
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
