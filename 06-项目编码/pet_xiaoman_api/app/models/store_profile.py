"""门店白标资料（多租户「品牌可定制」）。

一店一份：slug 作为 C 端入口标识（二维码/链接带 slug），logo/主题色驱动
后台与小程序运行时换肤。Store 存组织身份（name），StoreProfile 存品牌呈现。
"""
from datetime import datetime

from sqlalchemy import String, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

DEFAULT_PRIMARY_COLOR = "#5B8C85"  # 与现有品牌主色一致（暖松绿）


class StoreProfile(BaseModel):
    __tablename__ = "store_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # C 端入口标识
    name: Mapped[str] = mapped_column(String(50))                           # 对外展示店名
    slogan: Mapped[str | None] = mapped_column(String(50), nullable=True)   # 对外标语（未配则前端不展示）
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(20), default=DEFAULT_PRIMARY_COLOR)
    theme_json: Mapped[dict] = mapped_column(JSON, default=dict)            # 预留其他 UI token
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def theme(self) -> dict:
        """合并主题：主色 + 扩展 token，供前端直接消费。"""
        return {"primary_color": self.primary_color, **(self.theme_json or {})}
