# ORDR Pipeline — Data Pipeline, Processing & Alerts

Connects to the ORDR POS API, syncs sales data to PostgreSQL,
computes daily/weekly/monthly aggregates, and fires alerts on threshold breaches.

## Project Structure
```
pipeline/
├── scheduler.py              # Entry point — start this to run everything
├── requirements.txt
├── .env.template             # Copy to .env and configure
│
├── pipeline/
│   ├── config.py             # All settings (reads from .env)
│   ├── db.py                 # SQLAlchemy models + session factory
│   ├── fetcher.py            # Polls POS API, syncs to PostgreSQL
│   └── processor.py          # Computes daily/weekly/monthly aggregates
│
├── alerts/
│   └── alerts.py             # Threshold detection + email/Slack notifications
│
├── migrations/
│   └── 001_schema.sql        # Full PostgreSQL schema (run once)
│
└── powerbi/
    └── POWERBI_SETUP.md      # Power BI connection + DAX measures guide
```

---

## Quick Start

### 1. Create the database
```bash
psql -U postgres -c "CREATE DATABASE ordr_db;"
psql -U postgres -d ordr_db -f migrations/001_schema.sql
```

### 2. Configure environment
```bash
cp .env.template .env
# Edit .env with your DB credentials, email/Slack settings
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the pipeline
```bash
python scheduler.py
```

That's it. The pipeline will:
- Run immediately on startup
- Fetch new orders from the POS API every 5 minutes
- Recompute aggregates every hour
- Do a full daily recompute at 00:05
- Fire email/Slack alerts when revenue thresholds are breached

---

## Pipeline Flow

```
POS API (/api/orders, /api/menu)
    │
    ▼  every 5 min
fetcher.py  →  syncs orders + menu items to PostgreSQL
    │
    ▼  after every fetch
processor.py  →  recomputes sales_daily, sales_weekly, sales_monthly
    │
    ▼  after every process
alerts.py  →  checks thresholds, sends email/Slack, logs to alert_log
    │
    ▼  always
PostgreSQL  →  all tables available for Power BI DirectQuery
```

---

## Alert Thresholds (configure in config.py)

| Alert | Default Threshold |
|-------|-----------------|
| Daily revenue drop | -10% vs yesterday |
| Daily revenue spike | +25% vs yesterday |
| Weekly revenue drop | -15% WoW |
| Weekly revenue spike | +30% WoW |
| Monthly revenue drop | -20% MoM |
| Monthly revenue spike | +40% MoM |
| Low daily orders | < 5 orders |

---

## Connecting to Power BI
See `powerbi/POWERBI_SETUP.md` for the full guide including DAX measures.

---

## Adding Email Alerts (Gmail)
1. Enable 2FA on your Gmail account
2. Generate an App Password: myaccount.google.com → Security → App Passwords
3. Set `EMAIL_ENABLED=true`, fill in `EMAIL_USER`, `EMAIL_PASS` in `.env`

## Adding Slack Alerts
1. Create an Incoming Webhook at api.slack.com/apps
2. Set `SLACK_ENABLED=true`, paste the webhook URL into `.env`
# Fix deploy config
