"""数据看板（B010）：北极星=月完成单量。漏斗的价格表 UV 依赖埋点（一期未埋，标注待埋）。"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.models.order import Order, OrderStatus, PayType
from app.models.service_media import ServiceMedia
from app.models.visit_record import VisitRecord

router = APIRouter()


def _month_range(month: str | None):
    """YYYY-MM → (月初, 下月初)；缺省当月。"""
    base = datetime.strptime(month, "%Y-%m") if month else datetime.now().replace(day=1, hour=0, minute=0)
    if base.month == 12:
        nxt = base.replace(year=base.year + 1, month=1)
    else:
        nxt = base.replace(month=base.month + 1)
    return base, nxt


@router.get("/stats", summary="B010 数据看板（月度指标汇总）")
def stats(month: str | None = None, db: Session = Depends(get_db)):
    start, end = _month_range(month)
    prev_start = start - timedelta(days=1)
    prev_start = prev_start.replace(day=1)

    def completed_count(a: datetime, b: datetime) -> int:
        return (db.query(Order)
                .filter(Order.status == OrderStatus.COMPLETED,
                        Order.updated_at >= a, Order.updated_at < b).count())

    completed = completed_count(start, end)
    prev_completed = completed_count(prev_start, start)
    mom = round((completed - prev_completed) / prev_completed * 100, 1) if prev_completed else None

    month_orders = (db.query(Order)
                    .filter(Order.created_at >= start, Order.created_at < end).all())
    total = len(month_orders)
    status_dist = {}
    for o in month_orders:
        status_dist[o.status.value] = status_dist.get(o.status.value, 0) + 1

    # KPI（PRD §3.3）
    pay_penetration = round(sum(1 for o in month_orders if o.pay_type != PayType.UNPAID) / total * 100, 1) if total else 0
    addon_rate = round(sum(1 for o in month_orders if o.addons) / total * 100, 1) if total else 0

    # 完成口径统一：与北极星一致按完成时刻（updated_at）取本月完成单
    completed_orders = (db.query(Order)
                        .filter(Order.status == OrderStatus.COMPLETED,
                                Order.updated_at >= start, Order.updated_at < end).all())
    completed_ids = [o.id for o in completed_orders]
    with_media = (db.query(func.count(func.distinct(ServiceMedia.order_id)))
                  .filter(ServiceMedia.order_id.in_(completed_ids or [0]),
                          ServiceMedia.revoked.is_(False)).scalar() or 0)
    media_coverage = round(with_media / len(completed_ids) * 100, 1) if completed_ids else 0

    visits = (db.query(VisitRecord)
              .filter(VisitRecord.created_at >= start, VisitRecord.created_at < end).all())
    good_rate = round(sum(1 for v in visits if v.satisfaction >= 4) / len(visits) * 100, 1) if visits else 0

    source_dist = dict((s.value, n) for s, n in
                       db.query(Customer.source, func.count(Customer.id)).group_by(Customer.source).all())

    return {
        "month": start.strftime("%Y-%m"),
        "north_star": {"label": "月完成单量", "value": completed,
                       "prev": prev_completed, "mom_pct": mom},
        "kpi": {"pay_penetration_pct": pay_penetration, "addon_rate_pct": addon_rate,
                "media_coverage_pct": media_coverage, "good_rate_pct": good_rate,
                "visit_count": len(visits)},
        "status_dist": status_dist,
        "source_dist": source_dist,
        "funnel_note": "价格表 UV→下单 漏斗待埋点接入（PRD §9 price_page_view）",
    }
