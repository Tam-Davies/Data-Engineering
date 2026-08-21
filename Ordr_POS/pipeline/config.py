# ============================================================
#  pipeline/config.py  — central configuration
# ============================================================
import os
from dotenv import load_dotenv

load_dotenv()

# ── POS API ──────────────────────────────────────────────────
POS_API_BASE   = os.getenv("POS_API_BASE",   "http://localhost:5000")
POS_API_KEY    = os.getenv("POS_API_KEY",    "")          # set if you add API key auth
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "300"))  # seconds (default 5 min)

# ── PostgreSQL ───────────────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "ordr_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "password")

DATABASE_URL = os.getenv("DATABASE_URL") or (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ── Alert thresholds ─────────────────────────────────────────
ALERT_THRESHOLDS = {
    "revenue_drop_daily":    -10.0,   # % — alert if daily revenue drops > 10%
    "revenue_spike_daily":    25.0,   # % — alert if daily revenue spikes > 25%
    "revenue_drop_weekly":   -15.0,
    "revenue_spike_weekly":   30.0,
    "revenue_drop_monthly":  -20.0,
    "revenue_spike_monthly":  40.0,
    "low_orders_daily":         5,    # absolute — alert if daily orders < 5
}

# ── Notification channels ────────────────────────────────────
EMAIL_ENABLED   = os.getenv("EMAIL_ENABLED",   "false").lower() == "true"
EMAIL_HOST      = os.getenv("EMAIL_HOST",      "smtp.gmail.com")
EMAIL_PORT      = int(os.getenv("EMAIL_PORT",  "587"))
EMAIL_USER      = os.getenv("EMAIL_USER",      "")
EMAIL_PASS      = os.getenv("EMAIL_PASS",      "")
EMAIL_FROM      = os.getenv("EMAIL_FROM",      "ordr-alerts@yourdomain.com")
EMAIL_TO        = os.getenv("EMAIL_TO",        "manager@yourdomain.com").split(",")

SLACK_ENABLED   = os.getenv("SLACK_ENABLED",  "false").lower() == "true"
SLACK_WEBHOOK   = os.getenv("SLACK_WEBHOOK",  "")
SLACK_CHANNEL   = os.getenv("SLACK_CHANNEL",  "#sales-alerts")

# ── Logging ──────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE  = os.getenv("LOG_FILE",  "pipeline/logs/pipeline.log")
