"""门店白标资料（多租户「品牌可定制」）。

一店一份：slug 作为 C 端入口标识（二维码/链接带 slug），logo/主题色驱动
后台与小程序运行时换肤。Store 存组织身份（name），StoreProfile 存品牌呈现。
"""
from datetime import datetime

from sqlalchemy import Boolean, String, Integer, JSON, DateTime, Float, ForeignKey
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
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)    # C 端咨询电话
    contact_address: Mapped[str | None] = mapped_column(String(120), nullable=True) # C 端门店地址
    business_hours: Mapped[str | None] = mapped_column(String(50), nullable=True)   # C 端营业时间
    miniapp_name: Mapped[str | None] = mapped_column(String(50), nullable=True)     # 独立小程序名称
    miniapp_appid: Mapped[str | None] = mapped_column(String(64), nullable=True)    # 独立小程序 AppID
    miniapp_entry_enabled: Mapped[bool] = mapped_column(Boolean, default=True)      # 搜索入口是否启用
    # 品牌文案（门店级编辑文案，与 theme_json 的「UI token」区分开）：首页轮播、三承诺、
    # 服务入口宫格、关于与承诺页的信任文案等。此前这些写死在 C 端 JS 常量里，门店无法改、
    # 双端也对不齐；现归到数据层，B 端品牌配置可维护、C 端按 slug 读取同一份。
    content_json: Mapped[dict] = mapped_column(JSON, default=dict)
    # 门店经纬度（wx.openLocation 导航用）。C 端此前因缺经纬度只能「复制地址」，
    # 补字段后可由品牌配置页填写，C 端接地图导航。
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def theme(self) -> dict:
        """合并主题：主色 + 扩展 token，供前端直接消费。"""
        return {"primary_color": self.primary_color, **(self.theme_json or {})}
