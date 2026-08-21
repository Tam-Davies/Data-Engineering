# ============================================================
#  pipeline/alerts.py  — threshold detection + notifications
# ============================================================
import smtplib
import logging
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from datetime             import date, timedelta, datetime, timezone
from dataclasses          import dataclass, field
from typing               import List, Optional

from pipeline.config      import (
    ALERT_THRESHOLDS,
    EMAIL_ENABLED, EMAIL_HOST, EMAIL_PORT,
    EMAIL_USER,    EMAIL_PASS, EMAIL_FROM, EMAIL_TO,
    SLACK_ENABLED, SLACK_WEBHOOK, SLACK_CHANNEL,
)
from pipeline.db import get_db, SalesDaily, SalesWeekly, SalesMonthly, AlertLog

logger = logging.getLogger(__name__)


# ── Data structures ──────────────────────────────────────────

@dataclass
class Alert:
    alert_type:    str
    period:        str          # 'daily' | 'weekly' | 'monthly'
    metric:        str
    current_val:   float
    previous_val:  float
    change_pct:    Optional[float]
    threshold_pct: float
    message:       str
    channels:      List[str] = field(default_factory=list)


# ── Detection ────────────────────────────────────────────────

def detect_daily_alerts() -> List[Alert]:
    alerts: List[Alert] = []
    today     = date.today()
    yesterday = today - timedelta(days=1)

    with get_db() as db:
        today_row = db.query(SalesDaily).filter_by(date=today).first()
        prev_row  = db.query(SalesDaily).filter_by(date=yesterday).first()

    if not today_row:
        return alerts

    today_rev = float(today_row.total_revenue)
    prev_rev  = float(prev_row.total_revenue) if prev_row else 0.0

    # Only compute pct change if we have a valid previous day
    if prev_rev > 0:
        pct = round(((today_rev - prev_rev) / prev_rev) * 100, 2)

        drop_threshold  = ALERT_THRESHOLDS["revenue_drop_daily"]
        spike_threshold = ALERT_THRESHOLDS["revenue_spike_daily"]

        if pct <= drop_threshold:
            alerts.append(Alert(
                alert_type   = "revenue_drop",
                period       = "daily",
                metric       = "revenue",
                current_val  = today_rev,
                previous_val = prev_rev,
                change_pct   = pct,
                threshold_pct= drop_threshold,
                message      = (
                    f"⚠️  Daily revenue dropped {pct:.1f}% vs yesterday. "
                    f"Today: ₦{today_rev:,.2f}  |  Yesterday: ₦{prev_rev:,.2f}"
                )
            ))
        elif pct >= spike_threshold:
            alerts.append(Alert(
                alert_type   = "revenue_spike",
                period       = "daily",
                metric       = "revenue",
                current_val  = today_rev,
                previous_val = prev_rev,
                change_pct   = pct,
                threshold_pct= spike_threshold,
                message      = (
                    f"🚀  Daily revenue up {pct:.1f}% vs yesterday! "
                    f"Today: ₦{today_rev:,.2f}  |  Yesterday: ₦{prev_rev:,.2f}"
                )
            ))

    # Low order count alert
    if today_row.total_orders < ALERT_THRESHOLDS["low_orders_daily"]:
        alerts.append(Alert(
            alert_type   = "low_orders",
            period       = "daily",
            metric       = "order_count",
            current_val  = today_row.total_orders,
            previous_val = 0,
            change_pct   = None,
            threshold_pct= float(ALERT_THRESHOLDS["low_orders_daily"]),
            message      = (
                f"🔔  Only {today_row.total_orders} orders today "
                f"(threshold: {ALERT_THRESHOLDS['low_orders_daily']})"
            )
        ))

    return alerts


def detect_weekly_alerts() -> List[Alert]:
    alerts: List[Alert] = []
    today      = date.today()
    week_start = today - timedelta(days=today.weekday())
    prev_start = week_start - timedelta(days=7)

    with get_db() as db:
        this_week = db.query(SalesWeekly).filter_by(week_start=week_start).first()
        prev_week = db.query(SalesWeekly).filter_by(week_start=prev_start).first()

    if not this_week or not prev_week:
        return alerts

    pct = this_week.wow_change_pct
    if pct is None:
        return alerts

    pct = float(pct)
    if pct <= ALERT_THRESHOLDS["revenue_drop_weekly"]:
        alerts.append(Alert(
            alert_type   = "revenue_drop",
            period       = "weekly",
            metric       = "revenue",
            current_val  = float(this_week.total_revenue),
            previous_val = float(prev_week.total_revenue),
            change_pct   = pct,
            threshold_pct= ALERT_THRESHOLDS["revenue_drop_weekly"],
            message      = (
                f"⚠️  Weekly revenue down {pct:.1f}% WoW. "
                f"This week: ₦{this_week.total_revenue:,.2f}  |  "
                f"Last week: ₦{prev_week.total_revenue:,.2f}"
            )
        ))
    elif pct >= ALERT_THRESHOLDS["revenue_spike_weekly"]:
        alerts.append(Alert(
            alert_type   = "revenue_spike",
            period       = "weekly",
            metric       = "revenue",
            current_val  = float(this_week.total_revenue),
            previous_val = float(prev_week.total_revenue),
            change_pct   = pct,
            threshold_pct= ALERT_THRESHOLDS["revenue_spike_weekly"],
            message      = (
                f"🚀  Weekly revenue up {pct:.1f}% WoW! "
                f"This week: ₦{this_week.total_revenue:,.2f}"
            )
        ))
    return alerts


def detect_monthly_alerts() -> List[Alert]:
    alerts: List[Alert] = []
    today = date.today()
    mom_pct = None
    this_revenue = 0.0
    with get_db() as db:
        row = (
            db.query(SalesMonthly)
            .filter_by(year=today.year, month=today.month)
            .first()
        )
        if row:
            mom_pct      = row.mom_change_pct
            this_revenue = float(row.total_revenue)
    if mom_pct is None:
        return alerts
    pct = float(mom_pct)
    if pct <= ALERT_THRESHOLDS["revenue_drop_monthly"]:
        alerts.append(Alert(
            alert_type   = "revenue_drop",
            period       = "monthly",
            metric       = "revenue",
            current_val  = this_revenue,
            previous_val = 0,
            change_pct   = pct,
            threshold_pct= ALERT_THRESHOLDS["revenue_drop_monthly"],
            message      = (
                f"Monthly revenue down {pct:.1f}% MoM. "
                f"This month: {this_revenue:,.2f}"
            )
        ))
    elif pct >= ALERT_THRESHOLDS["revenue_spike_monthly"]:
        alerts.append(Alert(
            alert_type   = "revenue_spike",
            period       = "monthly",
            metric       = "revenue",
            current_val  = this_revenue,
            previous_val = 0,
            change_pct   = pct,
            threshold_pct= ALERT_THRESHOLDS["revenue_spike_monthly"],
            message      = (
                f"Monthly revenue up {pct:.1f}% MoM! "
                f"This month: {this_revenue:,.2f}"
            )
        ))
    return alerts

def _send_email(alert: Alert):
    if not EMAIL_ENABLED:
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[ORDR Alert] {alert.alert_type.replace('_',' ').title()} — {alert.period.title()}"
        msg["From"]    = EMAIL_FROM
        msg["To"]      = ", ".join(EMAIL_TO)

        html = f"""
        <html><body style="font-family:sans-serif;color:#1a1a1a;padding:24px">
          <h2 style="color:#e8813a">ORDR Sales Alert</h2>
          <p style="font-size:16px">{alert.message}</p>
          <table style="border-collapse:collapse;margin-top:16px">
            <tr><td style="padding:6px 12px;background:#f5f5f5">Period</td>
                <td style="padding:6px 12px">{alert.period.title()}</td></tr>
            <tr><td style="padding:6px 12px;background:#f5f5f5">Current Value</td>
                <td style="padding:6px 12px">₦{alert.current_val:,.2f}</td></tr>
            <tr><td style="padding:6px 12px;background:#f5f5f5">Previous Value</td>
                <td style="padding:6px 12px">₦{alert.previous_val:,.2f}</td></tr>
            {'<tr><td style="padding:6px 12px;background:#f5f5f5">Change</td>'
              f'<td style="padding:6px 12px;color:{"red" if alert.change_pct<0 else "green"}">'
              f'{alert.change_pct:+.1f}%</td></tr>' if alert.change_pct is not None else ''}
          </table>
          <p style="color:#888;font-size:12px;margin-top:24px">
            Sent by ORDR Pipeline · {datetime.now().strftime('%Y-%m-%d %H:%M')}
          </p>
        </body></html>"""

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

        logger.info(f"Email alert sent: {alert.alert_type}")
        alert.channels.append("email")

    except Exception as e:
        logger.error(f"Email send failed: {e}")


def _send_slack(alert: Alert):
    if not SLACK_ENABLED or not SLACK_WEBHOOK:
        return
    try:
        color   = "#e85555" if "drop" in alert.alert_type else "#3ecf8e"
        payload = {
            "channel": SLACK_CHANNEL,
            "attachments": [{
                "color":  color,
                "title":  f"ORDR Sales Alert — {alert.period.title()}",
                "text":   alert.message,
                "fields": [
                    {"title": "Current",  "value": f"₦{alert.current_val:,.2f}", "short": True},
                    {"title": "Previous", "value": f"₦{alert.previous_val:,.2f}", "short": True},
                    *([{"title": "Change", "value": f"{alert.change_pct:+.1f}%", "short": True}]
                      if alert.change_pct is not None else []),
                ],
                "footer": f"ORDR Pipeline · {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            }]
        }
        requests.post(SLACK_WEBHOOK, json=payload, timeout=5)
        logger.info(f"Slack alert sent: {alert.alert_type}")
        alert.channels.append("slack")

    except Exception as e:
        logger.error(f"Slack send failed: {e}")


def _log_alert(alert: Alert):
    """Persist every triggered alert to the database."""
    with get_db() as db:
        db.add(AlertLog(
            alert_type    = alert.alert_type,
            period        = alert.period,
            metric        = alert.metric,
            current_val   = alert.current_val,
            previous_val  = alert.previous_val,
            change_pct    = alert.change_pct,
            threshold_pct = alert.threshold_pct,
            message       = alert.message,
            channels      = alert.channels,
        ))


# ── Master alert job ─────────────────────────────────────────

def run_alert_job() -> dict:
    """
    Runs all alert detectors and dispatches notifications.
    Called by the scheduler after the process job.
    """
    all_alerts: List[Alert] = []
    all_alerts.extend(detect_daily_alerts())
    all_alerts.extend(detect_weekly_alerts())
    all_alerts.extend(detect_monthly_alerts())

    for alert in all_alerts:
        logger.warning(f"ALERT: {alert.message}")
        _send_email(alert)
        _send_slack(alert)
        _log_alert(alert)

    result = {
        "alerts_triggered": len(all_alerts),
        "alerts": [
            {"type": a.alert_type, "period": a.period, "change_pct": a.change_pct,
             "message": a.message}
            for a in all_alerts
        ],
    }
    logger.info(f"Alert job complete: {len(all_alerts)} alerts triggered")
    return result