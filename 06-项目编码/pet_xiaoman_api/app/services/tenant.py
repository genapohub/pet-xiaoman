"""多租户隔离：统一的按门店查询 / 归属校验封装。

隔离策略（平滑迁移，不阻塞现有单店数据）：
- 新写入一律打上 `store_id`；
- 查询时「本店数据 + 未打标的历史数据（store_id IS NULL）」可见；
- 跑完 `scripts/backfill_store_scope.py` 把历史数据打标到默认门店后，
  即等价于严格隔离（不再有 NULL）。

多租户 SaaS 的信任基石：**B 端一切查询必须经此处过滤**，不要裸用 db.query。
"""
from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.models.store_profile import StoreProfile


def store_clause(model, store_id: int | None):
    """门店过滤条件；store_id 为空时返回 None（不约束，兼容单店/无上下文场景）。"""
    if store_id is None:
        return None
    return or_(model.store_id == store_id, model.store_id.is_(None))


def scoped(db: Session, model, store_id: int | None) -> Query:
    """按门店过滤的查询。B 端所有列表/检索都应走这里。"""
    q = db.query(model)
    clause = store_clause(model, store_id)
    return q if clause is None else q.filter(clause)


def belongs(resource, store_id: int | None) -> bool:
    """单条资源归属校验：属于本店或为未打标历史数据即放行。

    资源不存在（None）恒为 False。用于详情/写操作防跨店猜 ID 访问。
    """
    if resource is None:
        return False
    if store_id is None:
        return True
    return getattr(resource, "store_id", None) in (store_id, None)


def resolve_store_id_by_slug(db: Session, slug: str | None, active_only: bool = True) -> int | None:
    """C 端入口：slug → store_id；未提供 slug 返回 None（legacy 单店模式）。

    `active_only=True`（默认）时已停用门店视为不存在 → C 端 404，
    避免被停用的门店继续接单。
    """
    if not slug:
        return None
    prof = db.query(StoreProfile).filter(StoreProfile.slug == slug).first()
    if prof is None:
        return None
    if active_only and not store_is_active(db, prof.store_id):
        return None
    return prof.store_id


def store_is_active(db: Session, store_id: int | None) -> bool:
    """门店是否正常营业（不存在或已停用 → False）。"""
    from app.models.staff import Store, StoreStatus
    if store_id is None:
        return False
    store = db.get(Store, store_id)
    return store is not None and store.status == StoreStatus.ACTIVE


def default_store_id(db: Session) -> int | None:
    """默认门店（id 最小）。用于单店兼容与历史数据回填。"""
    from app.models.staff import Store
    store = db.query(Store).order_by(Store.id).first()
    return store.id if store else None
