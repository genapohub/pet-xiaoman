from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BaseModel(Base):
    __abstract__ = True


class StoreScopedModel(BaseModel):
    """多租户基类：业务数据按门店隔离。

    `store_id` 为空 = 迁移前的历史（单店期）数据，可见性由查询层决定
    （app/services/tenant.py 的 scoped()：本店 + 未打标数据）。
    所有新增写入都应带上 store_id，跑完 backfill 后不再有 NULL。
    """
    __abstract__ = True

    store_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("stores.id"), nullable=True, index=True
    )
