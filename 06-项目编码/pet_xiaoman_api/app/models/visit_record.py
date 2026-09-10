"""回访记录（PRD B009）：订单完成 30 天后动态生成待回访（查询时计算，不建任务表）。"""
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class VisitRecord(BaseModel):
    __tablename__ = "visit_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, index=True)
    satisfaction: Mapped[int] = mapped_column(Integer)            # 1-5 星
    would_recommend: Mapped[bool] = mapped_column(Boolean)        # 是否愿意推荐
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
