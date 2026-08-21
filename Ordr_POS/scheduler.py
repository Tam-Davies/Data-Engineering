#!/usr/bin/env python3
# ============================================================
#  scheduler.py  — APScheduler orchestrator
#  Run: python scheduler.py
# ============================================================
import logging
import os
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

sys.path.insert(0, os.path.dirname(__file__))

from pipeline.config   import FETCH_INTERVAL, LOG_LEVEL, LOG_FILE
from pipeline.db       import create_tables
from pipeline.fetcher  import run_fetch_job
from pipeline.processor import run_process_job
from alerts.alerts     import run_alert_job

# -- Logging setup --------------------------------------------─
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level   = getattr(logging, LOG_LEVEL, logging.INFO),
    format  = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
    handlers= [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE),
    ]
)
logger = logging.getLogger("scheduler")


# -- Pipeline steps --------------------------------------------

def pipeline_run():
    """Full pipeline: fetch, process, alert."""
    logger.info("=" * 60)
    logger.info(f"  Pipeline run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    fetch_result   = run_fetch_job()
    process_result = run_process_job()
    alert_result   = run_alert_job()

    logger.info("Pipeline run summary:")
    logger.info(f"  Fetch:   {fetch_result.get('status')}  ({fetch_result.get('orders_synced',0)} orders)")
    logger.info(f"  Process: {process_result.get('status')}")
    logger.info(f"  Alerts:  {alert_result.get('alerts_triggered',0)} triggered")
    logger.info("=" * 60)


def daily_full_recompute():
    """Midnight job: recompute all aggregates from scratch for today."""
    logger.info("Daily full recompute triggered")
    run_process_job()
    run_alert_job()


# -- APScheduler setup ----------------------------------------

def on_job_error(event):
    logger.error(f"Job {event.job_id} failed: {event.exception}")

def on_job_executed(event):
    logger.debug(f"Job {event.job_id} completed in {event.retval}")


def main():
    logger.info("Starting ORDR pipeline scheduler…")

    # Ensure tables exist before any job runs
    create_tables()

    scheduler = BlockingScheduler(timezone="Africa/Lagos")
    scheduler.add_listener(on_job_error,    EVENT_JOB_ERROR)
    scheduler.add_listener(on_job_executed, EVENT_JOB_EXECUTED)

    # -- Main pipeline: every N minutes (default 5) ------------
    scheduler.add_job(
        pipeline_run,
        trigger    = "interval",
        seconds    = FETCH_INTERVAL,
        id         = "pipeline_run",
        name       = "Fetch + Process + Alert",
        max_instances = 1,
        misfire_grace_time = 60,
    )

    # -- Hourly process-only refresh --------------------------─
    scheduler.add_job(
        run_process_job,
        trigger    = "cron",
        minute     = 0,
        id         = "hourly_process",
        name       = "Hourly aggregate recompute",
        max_instances = 1,
    )

    # -- Daily midnight full recompute ------------------------─
    scheduler.add_job(
        daily_full_recompute,
        trigger    = "cron",
        hour       = 0,
        minute     = 5,
        id         = "daily_recompute",
        name       = "Daily full recompute",
        max_instances = 1,
    )

    # -- Run once immediately on startup ----------------------─
    scheduler.add_job(
        pipeline_run,
        trigger       = "date",
        run_date      = datetime.now(),
        id            = "startup_run",
        name          = "Startup run",
    )

    logger.info(f"Scheduler started. Fetch interval: every {FETCH_INTERVAL}s")
    logger.info("Scheduled jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  · {job.name}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()