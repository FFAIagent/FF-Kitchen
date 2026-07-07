# scheduler.py
from __future__ import annotations
import logging
import threading
from datetime import datetime
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from lark_base import BaseClient, EmployeesClient
from lark_im import IMClient
from poller import Poller
from handlers.brief import handle_brief_announced
from handlers.reminder import handle_deadline_reminders
from handlers.presentation import handle_post_presentation
from handlers.stage import handle_stage_advance
from handlers.feedback import handle_feedback_dispatch, run_calibration
from handlers.employee import run_employee_updates, run_calibration_from_actuals
from handlers.hours import handle_hours_collection, handle_daily_hours_checkin
from webhook import create_app
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger(__name__)

WIB = pytz.timezone(config.TIMEZONE)


def in_polling_window() -> bool:
    """Return True if current WIB time is within the polling window (08:00–22:00)."""
    now = datetime.now(WIB)
    return config.POLL_START_HOUR <= now.hour < config.POLL_END_HOUR


def poll_job(poller: Poller) -> None:
    """Run one poll cycle if within operating hours."""
    if not in_polling_window():
        log.info("Outside polling window — skipping")
        return
    try:
        # Per-job handlers
        poller.run_once()
        # Batch employee card update after all jobs processed
        jobs = poller.base.list_active_jobs()
        roster = poller.base.get_roster()
        run_employee_updates(jobs, roster, poller.base, poller.employees)
        # Role Bobot calibration from any newly completed jobs with actual hours
        all_jobs = poller.base._list_records(config.DAPUR_TABLE)
        run_calibration_from_actuals(all_jobs, poller.base)
        # Speed Index calibration run if feedback threshold met
        run_calibration(poller.base)
    except Exception as e:
        log.error(f"Poll failed: {e}", exc_info=True)


def daily_hours_job(base: BaseClient, employees: EmployeesClient, im: IMClient) -> None:
    """Morning check-in: DM each person for each active job they're assigned to.

    Runs at 09:00 WIB daily. Fetches roster fresh each run so new hires
    and reassignments are always reflected.
    Gated by config.DAILY_HOURS_ENABLED — set True to activate.
    """
    if not config.DAILY_HOURS_ENABLED:
        log.info("daily_hours_job: skipped (DAILY_HOURS_ENABLED=False)")
        return
    try:
        roster = base.get_roster()
        handle_daily_hours_checkin(base=base, employees=employees, im=im, roster=roster)
    except Exception as e:
        log.error(f"Daily hours check-in failed: {e}", exc_info=True)


def start_webhook(base: BaseClient, im: IMClient, employees: EmployeesClient) -> None:
    app = create_app(base, im, employees)
    app.run(host="0.0.0.0", port=config.WEBHOOK_PORT, debug=False, use_reloader=False)


def main() -> None:
    base = BaseClient()
    im = IMClient()
    employees = EmployeesClient()

    poller = Poller()
    poller.base = base
    poller.im = im
    poller.employees = employees
    poller.register(handle_brief_announced)
    poller.register(handle_deadline_reminders)
    poller.register(handle_post_presentation)
    poller.register(handle_stage_advance)
    poller.register(handle_feedback_dispatch)
    poller.register(handle_hours_collection)

    # Start Flask webhook in a background daemon thread
    webhook_thread = threading.Thread(
        target=start_webhook, args=(base, im, employees), daemon=True
    )
    webhook_thread.start()
    log.info(f"Webhook listener started on port {config.WEBHOOK_PORT}")

    # APScheduler: poll every N minutes in WIB timezone
    scheduler = BlockingScheduler(timezone=WIB)
    scheduler.add_job(
        poll_job,
        "interval",
        minutes=config.POLLING_INTERVAL_MINUTES,
        args=[poller],
        id="ff_kitchen_poll",
    )
    # Daily 09:00 WIB — ask each person how many hours they spent yesterday per active job
    scheduler.add_job(
        daily_hours_job,
        "cron",
        hour=9, minute=0,
        timezone=WIB,
        args=[base, employees, im],
        id="ff_daily_hours",
    )
    log.info("Scheduler starting — FF Kitchen agent running")
    # Run immediately on startup
    poll_job(poller)
    scheduler.start()


if __name__ == "__main__":
    main()
