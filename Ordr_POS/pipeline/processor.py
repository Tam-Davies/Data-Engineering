# ============================================================
#  pipeline/processor.py  — computes sales aggregates
# ============================================================
import logging
import pandas as pd
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
from sqlalchemy import text

from pipeline.db import (
    get_db, Order, OrderItem, SalesDaily, SalesWeekly,
    SalesMonthly, PipelineRun
)

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────

def _to_float(val) -> float:
    if isinstance(val, Decimal): return float(val)
    return float(val) if val is not None else 0.0


def _pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 2)


# ── Daily aggregates ─────────────────────────────────────────

def compute_daily(target_date: date = None) -> dict:
    """
    Aggregate all paid orders for `target_date` (default: today).
    Upserts a row into sales_daily.
    Returns the computed record as a dict.
    """
    if target_date is None:
        target_date = date.today()

    with get_db() as db:
        orders = (
            db.query(Order)
            .filter(
                Order.status == "paid",
                text("DATE(created_at) = :d").bindparams(d=target_date)
            )
            .all()
        )

        if not orders:
            logger.info(f"compute_daily({target_date}): no orders found")
            return {"date": str(target_date), "total_orders": 0, "total_revenue": 0.0}

        totals    = [_to_float(o.total)  for o in orders]
        revenue   = round(sum(totals), 2)
        avg_val   = round(revenue / len(orders), 2)

        # Top item by quantity
        all_items = []
        for o in orders:
            items = db.query(OrderItem).filter_by(order_id=o.id).all()
            all_items.extend(items)

        item_counts: dict[str, int] = {}
        for it in all_items:
            item_counts[it.name] = item_counts.get(it.name, 0) + it.qty
        top_item = max(item_counts, key=item_counts.get) if item_counts else None

        # Upsert
        row = db.query(SalesDaily).filter_by(date=target_date).first()
        if row:
            row.total_orders  = len(orders)
            row.total_revenue = revenue
            row.avg_order_val = avg_val
            row.top_item      = top_item
            row.updated_at    = datetime.now(timezone.utc)
        else:
            row = SalesDaily(
                date          = target_date,
                total_orders  = len(orders),
                total_revenue = revenue,
                avg_order_val = avg_val,
                top_item      = top_item,
            )
            db.add(row)

        result = {
            "date":          str(target_date),
            "total_orders":  len(orders),
            "total_revenue": revenue,
            "avg_order_val": avg_val,
            "top_item":      top_item,
        }
        logger.info(f"compute_daily({target_date}): {result}")
        return result


# ── Weekly aggregates ────────────────────────────────────────

def compute_weekly(week_start: date = None) -> dict:
    """
    Aggregate for the ISO week containing `week_start`.
    week_start defaults to the Monday of the current week.
    """
    if week_start is None:
        today      = date.today()
        week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    with get_db() as db:
        orders = (
            db.query(Order)
            .filter(
                Order.status == "paid",
                text("DATE(created_at) BETWEEN :s AND :e")
                .bindparams(s=week_start, e=week_end)
            )
            .all()
        )

        revenue  = round(sum(_to_float(o.total) for o in orders), 2)
        avg_val  = round(revenue / len(orders), 2) if orders else 0.0

        # Previous week for WoW comparison
        prev_week_start = week_start - timedelta(days=7)
        prev_row = db.query(SalesWeekly).filter_by(week_start=prev_week_start).first()
        prev_rev = _to_float(prev_row.total_revenue) if prev_row else 0.0
        wow_pct  = _pct_change(revenue, prev_rev)

        row = db.query(SalesWeekly).filter_by(week_start=week_start).first()
        if row:
            row.week_end      = week_end
            row.total_orders  = len(orders)
            row.total_revenue = revenue
            row.avg_order_val = avg_val
            row.wow_change_pct= wow_pct
            row.updated_at    = datetime.now(timezone.utc)
        else:
            row = SalesWeekly(
                week_start      = week_start,
                week_end        = week_end,
                total_orders    = len(orders),
                total_revenue   = revenue,
                avg_order_val   = avg_val,
                wow_change_pct  = wow_pct,
            )
            db.add(row)

        result = {
            "week_start":    str(week_start),
            "week_end":      str(week_end),
            "total_orders":  len(orders),
            "total_revenue": revenue,
            "wow_change_pct": wow_pct,
        }
        logger.info(f"compute_weekly({week_start}): {result}")
        return result


# ── Monthly aggregates ───────────────────────────────────────

def compute_monthly(year: int = None, month: int = None) -> dict:
    """Aggregate for a calendar month (default: current month)."""
    today = date.today()
    if year  is None: year  = today.year
    if month is None: month = today.month

    with get_db() as db:
        orders = (
            db.query(Order)
            .filter(
                Order.status == "paid",
                text("EXTRACT(YEAR  FROM created_at) = :y").bindparams(y=year),
                text("EXTRACT(MONTH FROM created_at) = :m").bindparams(m=month),
            )
            .all()
        )

        revenue = round(sum(_to_float(o.total) for o in orders), 2)
        avg_val = round(revenue / len(orders), 2) if orders else 0.0

        # Previous month for MoM comparison
        if month == 1: prev_year, prev_month = year - 1, 12
        else:          prev_year, prev_month = year, month - 1
        prev_row = (
            db.query(SalesMonthly)
            .filter_by(year=prev_year, month=prev_month)
            .first()
        )
        prev_rev = _to_float(prev_row.total_revenue) if prev_row else 0.0
        mom_pct  = _pct_change(revenue, prev_rev)

        row = db.query(SalesMonthly).filter_by(year=year, month=month).first()
        if row:
            row.total_orders   = len(orders)
            row.total_revenue  = revenue
            row.avg_order_val  = avg_val
            row.mom_change_pct = mom_pct
            row.updated_at     = datetime.now(timezone.utc)
        else:
            row = SalesMonthly(
                year           = year,
                month          = month,
                total_orders   = len(orders),
                total_revenue  = revenue,
                avg_order_val  = avg_val,
                mom_change_pct = mom_pct,
            )
            db.add(row)

        result = {
            "year":          year,
            "month":         month,
            "total_orders":  len(orders),
            "total_revenue": revenue,
            "mom_change_pct": mom_pct,
        }
        logger.info(f"compute_monthly({year}-{month:02d}): {result}")
        return result


# ── Master process job ────────────────────────────────────────

def run_process_job() -> dict:
    """
    Recomputes daily, weekly, and monthly aggregates.
    Called by the scheduler after every fetch job.
    """
    started = datetime.now(timezone.utc)

    with get_db() as db:
        run = PipelineRun(run_type="process", status="running")
        db.add(run)
        db.flush()
        run_id = run.id

    try:
        daily   = compute_daily()
        weekly  = compute_weekly()
        monthly = compute_monthly()

        # Also recompute yesterday (in case late payments came in)
        yesterday = date.today() - timedelta(days=1)
        compute_daily(yesterday)

        with get_db() as db:
            run = db.query(PipelineRun).filter_by(id=run_id).first()
            if run:
                run.status            = "success"
                run.records_processed = 3
                run.finished_at       = datetime.now(timezone.utc)

        result = {
            "status":  "success",
            "daily":   daily,
            "weekly":  weekly,
            "monthly": monthly,
            "duration_s": round((datetime.now(timezone.utc) - started).total_seconds(), 2),
        }
        logger.info(f"Process job complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Process job failed: {e}", exc_info=True)
        with get_db() as db:
            run = db.query(PipelineRun).filter_by(id=run_id).first()
            if run:
                run.status        = "failed"
                run.error_message = str(e)
                run.finished_at   = datetime.now(timezone.utc)
        return {"status": "failed", "error": str(e)}
