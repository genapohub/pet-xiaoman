"""服务影像（PRD §7.1 service_media 表）：节点影像是强制流转的前置证据。"""
import enum
from datetime import datetime

from sqlalchemy import String, Integer, Enum, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import StoreScopedModel


class MediaNode(str, enum.Enum):
    PICKUP = "接宠完成"
    FAREWELL = "告别仪式"
    CREMATION = "火化完成"
    DELIVERY = "交付完成"


class MediaType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"


class ServiceMedia(StoreScopedModel):
    __tablename__ = "service_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, index=True)
    node: Mapped[MediaNode] = mapped_column(Enum(MediaNode))
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType))
    url: Mapped[str] = mapped_column(String(255))
    uploaded_by: Mapped[int] = mapped_column(Integer)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)  # 撤回仅店长，留审计日志
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
