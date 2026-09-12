import enum

from sqlalchemy import String, Integer, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import StoreScopedModel


class Source(str, enum.Enum):
    XHS = "小红书"
    REFERRAL = "转介绍"
    ORGANIC = "自然搜索"
    OTHER = "其他"


class Customer(StoreScopedModel):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(20))  # 脱敏存储；店长可见全量
    openid: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)  # 微信登录绑定
    source: Mapped[Source] = mapped_column(Enum(Source), default=Source.OTHER)
