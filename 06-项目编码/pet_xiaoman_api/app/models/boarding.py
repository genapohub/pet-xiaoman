"""骨灰寄存（PRD §7.1 boarding 表）：到期前 7 天提醒（PRD B007）。"""
import enum
from datetime import date, datetime

from sqlalchemy import String, Integer, Enum, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BoardingStatus(str, enum.Enum):
    STORED = "在存"
    RENEWED = "已续存"
    TAKEN = "已取回"


class Boarding(BaseModel):
    __tablename__ = "boardings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pet_id: Mapped[int] = mapped_column(Integer, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, index=True)
    location: Mapped[str] = mapped_column(String(50), unique=True)  # 如 A-01，在存状态唯一
    start_date: Mapped[date] = mapped_column(Date, default=date.today)
    expire_date: Mapped[date] = mapped_column(Date)
    status: Mapped[BoardingStatus] = mapped_column(Enum(BoardingStatus), default=BoardingStatus.STORED)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def days_left(self) -> int:
        return (self.expire_date - date.today()).days

    @property
    def severity(self) -> str:
        """正常 / 临期（≤7天）/ 已到期。"""
        if self.days_left < 0:
            return "已到期"
        if self.days_left <= 7:
            return "临期"
        return "正常"
