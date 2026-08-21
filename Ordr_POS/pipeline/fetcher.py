# ============================================================
#  pipeline/fetcher.py  — polls POS API, syncs to PostgreSQL
# ============================================================
import requests
import logging
from datetime import datetime, timezone
from typing import Optional

from pipeline.config import POS_API_BASE, POS_API_KEY
from pipeline.db import get_db, Order, OrderItem, MenuItem, MenuCategory, PipelineRun

logger = logging.getLogger(__name__)

HEADERS = {"Authorization": f"Bearer {POS_API_KEY}"} if POS_API_KEY else {}


# ── Low-level API calls ───────────────────────────────────────

def _get(path: str) -> dict:
    url = POS_API_BASE + path
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ── Sync functions ───────────────────────────────────────────

def sync_menu() -> int:
    """Pull all menu items from POS API and upsert into PostgreSQL."""
    data   = _get("/api/menu")
    menu   = data.get("menu", {})
    count  = 0

    with get_db() as db:
        for cat_name, items in menu.items():
            # Upsert category
            cat = db.query(MenuCategory).filter_by(name=cat_name).first()
            if not cat:
                cat = MenuCategory(name=cat_name)
                db.add(cat)
                db.flush()

            for item in items:
                existing = db.query(MenuItem).filter_by(id=item["id"]).first()
                if existing:
                    existing.name       = item["name"]
                    existing.price      = float(item["price"])
                    existing.emoji      = item.get("emoji", "🍽️")
                    existing.category_id = cat.id
                else:
                    db.add(MenuItem(
                        id          = item["id"],
                        category_id = cat.id,
                        name        = item["name"],
                        price       = float(item["price"]),
                        emoji       = item.get("emoji", "🍽️"),
                    ))
                    count += 1

    logger.info(f"sync_menu: {count} new items inserted")
    return count


def sync_orders(since: Optional[datetime] = None) -> int:
    """
    Pull paid orders from POS API and upsert into PostgreSQL.
    If `since` is given, only pulls orders created after that timestamp.
    """
    path = "/api/orders?status=paid"
    data = _get(path)
    orders = data.get("orders", [])

    if since:
        orders = [
            o for o in orders
            if datetime.fromisoformat(o["created_at"]).replace(tzinfo=timezone.utc) > since
        ]

    count = 0
    with get_db() as db:
        for o in orders:
            existing = db.query(Order).filter_by(id=o["id"]).first()
            if existing:
                # Update status if it changed
                existing.status     = o["status"]
                existing.updated_at = datetime.fromisoformat(o["updated_at"])
                continue

            order = Order(
                id         = o["id"],
                table_id   = o.get("table_id"),
                staff_id   = o.get("staff_id"),
                status     = o["status"],
                note       = o.get("note", ""),
                subtotal   = float(o.get("subtotal", 0)),
                tax        = float(o.get("tax", 0)),
                total      = float(o.get("total", 0)),
                created_at = datetime.fromisoformat(o["created_at"]),
                updated_at = datetime.fromisoformat(o["updated_at"]),
            )
            db.add(order)
            db.flush()

            for item in o.get("items", []):
                db.add(OrderItem(
                    order_id     = order.id,
                    menu_item_id = item.get("id"),
                    name         = item["name"],
                    price        = float(item["price"]),
                    qty          = int(item["qty"]),
                ))
            count += 1

    logger.info(f"sync_orders: {count} new orders synced")
    return count


def sync_pending_orders() -> int:
    """Also sync pending orders so status changes are tracked."""
    data   = _get("/api/orders?status=pending")
    orders = data.get("orders", [])
    count  = 0

    with get_db() as db:
        for o in orders:
            existing = db.query(Order).filter_by(id=o["id"]).first()
            if existing:
                existing.status = o["status"]
                continue
            order = Order(
                id         = o["id"],
                table_id   = o.get("table_id"),
                staff_id   = o.get("staff_id"),
                status     = o["status"],
                note       = o.get("note", ""),
                subtotal   = float(o.get("subtotal", 0)),
                tax        = float(o.get("tax", 0)),
                total      = float(o.get("total", 0)),
                created_at = datetime.fromisoformat(o["created_at"]),
                updated_at = datetime.fromisoformat(o["updated_at"]),
            )
            db.add(order)
            db.flush()
            for item in o.get("items", []):
                db.add(OrderItem(
                    order_id     = order.id,
                    menu_item_id = item.get("id"),
                    name         = item["name"],
                    price        = float(item["price"]),
                    qty          = int(item["qty"]),
                ))
            count += 1

    return count


# ── Full fetch job ────────────────────────────────────────────

def run_fetch_job() -> dict:
    """
    Master fetch function. Called by the scheduler.
    Returns summary dict for logging and alerting.
    """
    started = datetime.now(timezone.utc)
    run_record = None

    try:
        with get_db() as db:
            run_record = PipelineRun(run_type="fetch", status="running")
            db.add(run_record)
            db.flush()
            run_id = run_record.id

        logger.info("-- Fetch job started --")
        menu_count   = sync_menu()
        order_count  = sync_orders()
        pending_count= sync_pending_orders()
        total        = order_count + pending_count

        with get_db() as db:
            run = db.query(PipelineRun).filter_by(id=run_id).first()
            if run:
                run.status            = "success"
                run.records_processed = total
                run.finished_at       = datetime.now(timezone.utc)

        result = {
            "status":          "success",
            "menu_items":      menu_count,
            "orders_synced":   order_count,
            "pending_synced":  pending_count,
            "duration_s":      round((datetime.now(timezone.utc) - started).total_seconds(), 2),
        }
        logger.info(f"Fetch job complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Fetch job failed: {e}", exc_info=True)
        if run_record:
            with get_db() as db:
                run = db.query(PipelineRun).filter_by(id=run_id).first()
                if run:
                    run.status        = "failed"
                    run.error_message = str(e)
                    run.finished_at   = datetime.now(timezone.utc)
        return {"status": "failed", "error": str(e)}
