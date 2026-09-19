import enum
from sqlalchemy import String, Integer, Enum, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import StoreScopedModel


class ItemType(str, enum.Enum):
    PACKAGE = "套餐"
    SINGLE = "单项"
    ADDON = "加购"


class ItemStatus(str, enum.Enum):
    ON_SALE = "在售"
    OFF_SALE = "下架"  # 只下架不物理删除（历史订单引用）


class ServiceItem(StoreScopedModel):
    __tablename__ = "service_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[ItemType] = mapped_column(Enum(ItemType))
    name: Mapped[str] = mapped_column(String(50))
    price: Mapped[float] = mapped_column(DECIMAL(10, 2))
    weight_tier: Mapped[str | None] = mapped_column(String(10))  # 0-10kg/10-20kg/20kg+
    # 服务时长（自由文本：「约 2 小时」「按里程」）。刻意不做结构化分钟数：
    # 善终服务受交通与仪式时长影响，写死分钟数会与门店实际承诺不符，
    # 门店在 C 端/合同里承诺的就是这类模糊表述。
    duration_text: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus), default=ItemStatus.ON_SALE)
    version: Mapped[str] = mapped_column(String(10))  # 价格版本 v20260905
