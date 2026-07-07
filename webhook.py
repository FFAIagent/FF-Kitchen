# webhook.py
from __future__ import annotations
import logging
from datetime import date
from flask import Flask, request, current_app
import config

log = logging.getLogger(__name__)

_HTML_DONE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Done</title>
<style>body{{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#f5f5f5}}
.card{{background:white;padding:40px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.1);text-align:center}}
h2{{color:#00b388}}p{{color:#555}}</style></head>
<body><div class="card"><h2>&#x2705; Done!</h2><p>You can close this tab.</p></div></body>
</html>"""


def create_app(base, im, employees=None) -> Flask:
    app = Flask(__name__)
    app.base = base
    app.im = im
    app.employees = employees

    @app.route("/action", methods=["GET"])
    def action():
        action_name = request.args.get("action", "")
        record_id   = request.args.get("record_id", "")
        stage       = request.args.get("stage", "")
        job         = request.args.get("job", "")
        person      = request.args.get("person", "")
        discipline  = request.args.get("discipline", "")
        hours       = request.args.get("hours", "")
        open_id     = request.args.get("open_id", "")
        try:
            _handle_action(action_name, record_id, stage, job, person,
                           discipline, hours, open_id,
                           current_app.base, current_app.im, current_app.employees)
        except Exception as e:
            log.error(f"Action error [{action_name}]: {e}", exc_info=True)
        return _HTML_DONE, 200

    return app


def _handle_action(action: str, record_id: str, stage: str, job: str, person: str,
                   discipline: str, hours: str, open_id: str,
                   base, im, employees=None) -> None:
    if action == "got_it":
        log.info(f"Got it on record {record_id}")

    elif action == "request_extension":
        _action_request_extension(record_id, stage, base, im)

    elif action == "pres_approved":
        base.update_record(record_id, {config.F_STAGE_STATUS: config.STAGE_PRODUCTION})
        log.info(f"Presentation approved for {record_id}, stage set to Production")

    elif action == "pres_revision":
        _action_pres_revision(record_id, base, im)

    elif action in ("feedback_fast", "feedback_normal", "feedback_slow"):
        rating_map = {
            "feedback_fast": "Fast",
            "feedback_normal": "Normal",
            "feedback_slow": "Slow",
        }
        rating = rating_map[action]
        base.create_feedback_record({
            "Rating": rating,
            "Reviewer Type": "Supervisor",
            "Answered At": date.today().strftime("%Y-%m-%d %H:%M:%S"),
            "Used in Calibration": False,
        })
        log.info(f"Feedback recorded: {rating} for {person} on {job}")

    elif action == "feedback_skip":
        log.info(f"Feedback skipped for {person} on {job}")

    elif action == "log_hours":
        _action_log_hours(record_id, discipline, hours, base)

    elif action == "log_hours_skip":
        log.info(f"Hours log skipped for {record_id} / {discipline}")

    elif action == "log_daily_hours":
        _action_log_daily_hours(record_id, discipline, hours, open_id, base, employees)

    else:
        log.warning(f"Unknown action: {action}")


def _action_pres_revision(record_id: str, base, im) -> None:
    """Handle 'Needs Revision' click on post-presentation card.

    1. Increment Revision Count on the DAPUR job.
    2. Set Stage Status = Client Revision Received.
    3. DM Account PIC with a card linking to the Revision Form.
    """
    from handlers.brief import _get_text

    # Fetch job — check active first, then all records as fallback
    jobs = base.list_active_jobs()
    job = next((j for j in jobs if j["record_id"] == record_id), None)
    if not job:
        log.warning(
            f"pres_revision: {record_id} not in active jobs — trying full table"
        )
        all_records = base._list_records(config.DAPUR_TABLE)
        job = next((r for r in all_records if r["record_id"] == record_id), None)
    if not job:
        log.error(f"pres_revision: record {record_id} not found")
        return

    fields = job["fields"]
    job_title = _get_text(fields.get(config.F_JOB_TITLE)) or record_id

    # Increment revision count
    current = fields.get(config.F_REVISION_COUNT) or 0
    if isinstance(current, float):
        current = int(current)
    new_count = current + 1

    # Write: stage + revision count
    base.update_record(record_id, {
        config.F_STAGE_STATUS: config.STAGE_CLIENT_REVISION,
        config.F_REVISION_COUNT: new_count,
    })
    log.info(
        f"pres_revision: {record_id} ({job_title}) — "
        f"stage=Client Revision Received, revision_count={new_count}"
    )

    # DM Account PIC with revision card
    account_pic = fields.get(config.F_ACCOUNT_PIC) or []
    if isinstance(account_pic, list):
        open_ids = [
            p.get("id") or p.get("open_id")
            for p in account_pic
            if isinstance(p, dict)
        ]
    else:
        open_ids = [str(account_pic)] if account_pic else []
    open_ids = [oid for oid in open_ids if oid]

    if open_ids:
        for open_id in open_ids:
            im.send_client_revision_card(open_id, job_title, new_count, record_id)
        log.info(f"pres_revision: revision card sent to {open_ids}")
    else:
        log.warning(
            f"pres_revision: no Account PIC on {record_id} — "
            "stage updated but no DM sent"
        )


def _action_request_extension(record_id: str, stage: str, base, im) -> None:
    """Find PM for the job and notify them of the extension request."""
    from handlers.brief import _get_text, _resolve_open_ids
    jobs = base.list_active_jobs()
    roster = base.get_roster()
    job = next((j for j in jobs if j["record_id"] == record_id), None)
    if not job:
        log.warning(f"Extension request: job {record_id} not found")
        return
    pm_links = job["fields"].get(config.F_PM_PIC) or []
    pm_people = _resolve_open_ids(pm_links, roster)
    job_title = _get_text(job["fields"].get(config.F_JOB_TITLE))
    for pm_open_id, _ in pm_people:
        im.send_pm_extension_alert(
            pm_open_id, "—", job_title, stage or "milestone", "—",
            f"https://fcn.sg.larksuite.com/base/{config.BASE_TOKEN}"
        )


def _action_log_hours(record_id: str, discipline: str, hours_str: str, base) -> None:
    """Write per-role actual hours to DAPUR (cumulative) and trigger Role Bobot calibration.

    Changed 2026-07-07: now increments Actual Hours rather than replacing,
    so daily Timesheet accumulation and end-of-job reporting coexist correctly.
    """
    try:
        hours = float(hours_str)
    except (ValueError, TypeError):
        log.error(f"log_hours: invalid hours value '{hours_str}'")
        return

    hours_field, _ = config.DISCIPLINE_HOURS_FIELDS.get(discipline, (None, None))
    if not hours_field:
        log.error(f"log_hours: unknown discipline '{discipline}'")
        return

    # Fetch DAPUR record once — needed for current hours + job_type
    try:
        all_records = base._list_records(config.DAPUR_TABLE)
        job = next((r for r in all_records if r["record_id"] == record_id), None)
    except Exception as e:
        log.error(f"log_hours: failed to fetch DAPUR record {record_id}: {e}")
        return

    # Increment (not replace) — DAPUR hours compound daily
    current_hours = float(job["fields"].get(hours_field) or 0) if job else 0.0
    new_hours = current_hours + hours
    base.update_record(record_id, {hours_field: new_hours})
    log.info(
        f"Actual hours logged (cumulative): {discipline} "
        f"{current_hours}+{hours}={new_hours}h on {record_id}"
    )

    # Role Bobot calibration
    if job and hours > 0:
        try:
            job_type = job["fields"].get("fldoGTF6g5", "")
            if job_type:
                base.calibrate_role_bobot(job_type, discipline, new_hours)
                log.info(f"Role Bobot calibrated: {job_type} × {discipline} = {new_hours}h")
        except Exception as e:
            log.error(f"Role Bobot calibration failed after log_hours: {e}")


def _action_log_daily_hours(
    record_id: str,
    discipline: str,
    hours_str: str,
    open_id: str,
    base,
    employees,
) -> None:
    """Handle daily morning hours check-in response (action=log_daily_hours).

    1. Increment Actual Hours [Discipline] in DAPUR (cumulative)
    2. Write a Timesheet row for yesterday in FF Employees Base
    3. Recompute and write Employee weekly/monthly totals + Overloaded flag
    """
    from datetime import datetime, timedelta
    import pytz

    if employees is None:
        log.error("log_daily_hours: employees client not available")
        return

    try:
        hours = float(hours_str)
    except (ValueError, TypeError):
        log.error(f"log_daily_hours: invalid hours value '{hours_str}'")
        return

    hours_field, _ = config.DISCIPLINE_HOURS_FIELDS.get(discipline, (None, None))
    if not hours_field:
        log.error(f"log_daily_hours: unknown discipline '{discipline}'")
        return

    WIB = pytz.timezone(config.TIMEZONE)
    yesterday = (datetime.now(WIB) - timedelta(days=1)).strftime("%Y-%m-%d")

    # ── 1. Fetch DAPUR job, increment Actual Hours ─────────────────────
    try:
        all_records = base._list_records(config.DAPUR_TABLE)
        job = next((r for r in all_records if r["record_id"] == record_id), None)
        if not job:
            log.error(f"log_daily_hours: job {record_id} not found in DAPUR")
            return

        job_title = job["fields"].get(config.F_JOB_TITLE, "")
        if isinstance(job_title, list):
            job_title = job_title[0].get("text", "") if job_title else ""

        current_hours = float(job["fields"].get(hours_field) or 0)
        new_hours = current_hours + hours
        base.update_record(record_id, {hours_field: new_hours})
        log.info(
            f"log_daily_hours DAPUR update: {discipline} "
            f"{current_hours}+{hours}={new_hours}h on {record_id}"
        )
    except Exception as e:
        log.error(f"log_daily_hours: failed to update DAPUR: {e}")
        return

    # Skip Timesheet write + Employee update when 0 hours reported
    if hours == 0:
        log.info(f"log_daily_hours: 0h reported — DAPUR updated, Timesheet skipped")
        return

    # ── 2. Write Timesheet row ─────────────────────────────────────────
    try:
        all_employees = employees.get_employees()
        emp = next(
            (e for e in all_employees if e["fields"].get(config.E_OPEN_ID) == open_id),
            None,
        )
        if not emp:
            log.error(f"log_daily_hours: no employee record for open_id={open_id}")
            return
        emp_record_id = emp["record_id"]

        employees.create_timesheet_record({
            config.TS_DATE:       f"{yesterday} 00:00:00",
            config.TS_PERSON:     [{"record_id": emp_record_id}],
            config.TS_JOB_TITLE:  job_title,
            config.TS_JOB_REC_ID: record_id,
            config.TS_DISCIPLINE: discipline,
            config.TS_HOURS:      hours,
        })
        log.info(f"Timesheet row written: {emp_record_id} / {discipline} / {hours}h on {yesterday}")
    except Exception as e:
        log.error(f"log_daily_hours: failed to write Timesheet row: {e}")
        return

    # ── 3. Recompute Employee weekly/monthly totals ────────────────────
    try:
        ts_records = employees._list_timesheet_records()
        now_wib = datetime.now(WIB)
        current_week  = now_wib.isocalendar()[1]
        current_month = now_wib.month
        current_year  = now_wib.year

        weekly_h  = 0.0
        monthly_h = 0.0

        for row in ts_records:
            f = row["fields"]
            person_links = f.get(config.TS_PERSON, [])
            is_mine = isinstance(person_links, list) and any(
                isinstance(p, dict) and p.get("record_id") == emp_record_id
                for p in person_links
            )
            if not is_mine:
                continue

            row_hours = float(f.get(config.TS_HOURS) or 0)
            date_val  = f.get(config.TS_DATE)
            if date_val is None:
                continue

            if isinstance(date_val, (int, float)):
                row_dt = datetime.fromtimestamp(date_val / 1000, tz=pytz.utc).astimezone(WIB)
            else:
                try:
                    row_dt = WIB.localize(datetime.strptime(str(date_val)[:10], "%Y-%m-%d"))
                except Exception:
                    continue

            if row_dt.year != current_year:
                continue
            if row_dt.month == current_month:
                monthly_h += row_hours
            if row_dt.isocalendar()[1] == current_week:
                weekly_h += row_hours

        overloaded = weekly_h > 40
        employees.update_employee_hours(emp_record_id, weekly_h, monthly_h, overloaded)
    except Exception as e:
        log.error(f"log_daily_hours: failed to update Employee totals: {e}")


if __name__ == "__main__":
    from lark_base import BaseClient, EmployeesClient
    from lark_im import IMClient
    app = create_app(BaseClient(), IMClient(), EmployeesClient())
    app.run(host="0.0.0.0", port=config.WEBHOOK_PORT, debug=False, use_reloader=False)
