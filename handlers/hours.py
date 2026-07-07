# handlers/hours.py
"""Collect actual hours per role from team members.

End-of-job flow (existing):
  1. Job Account Status → DONE
  2. handle_hours_collection() detects each assigned role that hasn't been asked yet
  3. Sends DM hours card to the assigned person
  4. Sets Hours Requested [Discipline] = True (dedup flag)
  5. Person clicks an hour bucket on the card
  6. webhook.py action=log_hours writes Actual Hours [Discipline] to DAPUR
  7. calibrate_role_bobot() updates Role Bobot via EMA

Daily check-in flow (new — 2026-07-07):
  1. APScheduler fires handle_daily_hours_checkin() at 09:00 WIB every day
  2. For each active job × assigned discipline, checks Timesheet for dedup
  3. Sends DM daily hours card (action=log_daily_hours) if not already answered
  4. webhook.py _action_log_daily_hours() increments DAPUR Actual Hours,
     writes a Timesheet row, and updates Employee weekly/monthly totals
"""
from __future__ import annotations
import logging
import config
from handlers.brief import ASSIGNMENT_FIELDS, _get_text, _resolve_open_ids

log = logging.getLogger(__name__)


def handle_hours_collection(job: dict, base, im, roster: list, **_) -> None:
    """For each DONE job, DM assigned people to collect their actual hours."""
    fields = job["fields"]
    if fields.get(config.F_ACCOUNT_STATUS) != "DONE":
        return

    job_title = _get_text(fields.get(config.F_JOB_TITLE))
    record_id = job["record_id"]

    for assignment_field, discipline in config.ASSIGNMENT_FIELD_TO_DISCIPLINE.items():
        hours_field, requested_flag = config.DISCIPLINE_HOURS_FIELDS.get(discipline, (None, None))
        if not hours_field or not requested_flag:
            continue

        # Skip if already requested or already filled in
        if fields.get(requested_flag):
            continue
        if fields.get(hours_field) is not None:
            continue

        # Find assigned people for this discipline
        linked = fields.get(assignment_field) or []
        if not isinstance(linked, list) or not linked:
            continue

        resolved = _resolve_open_ids(linked, roster)
        for open_id, person_name in resolved:
            if not open_id:
                continue
            try:
                im.send_hours_card(open_id, job_title, discipline, record_id)
                log.info(f"Hours card sent to {person_name} ({discipline}) for {record_id}")
            except Exception as e:
                log.error(f"Failed to send hours card to {person_name}: {e}")

        # Set dedup flag — one request per discipline per job
        base.update_record(record_id, {requested_flag: True})


def handle_daily_hours_checkin(base, employees, im, roster: list, **_) -> None:
    """Morning check-in: DM each person for each active job they're assigned to.

    Runs at 09:00 WIB daily via APScheduler (not the 30-min poll).
    For each active DAPUR job × discipline, checks if the person already
    submitted hours for yesterday (Timesheet dedup). Sends a daily hours
    card only if not yet answered.

    Args:
        base:      BaseClient — to list active DAPUR jobs
        employees: EmployeesClient — for Timesheet dedup check
        im:        IMClient — to send DM cards
        roster:    list of Team Roster records (fetched by caller)
    """
    active_jobs = base.list_active_jobs()
    log.info(f"daily_hours_checkin: {len(active_jobs)} active jobs to process")

    for job in active_jobs:
        fields = job["fields"]
        job_title = _get_text(fields.get(config.F_JOB_TITLE)) or "Unknown Job"
        record_id = job["record_id"]

        for assignment_field, discipline in config.ASSIGNMENT_FIELD_TO_DISCIPLINE.items():
            linked = fields.get(assignment_field) or []
            if not isinstance(linked, list) or not linked:
                continue

            resolved = _resolve_open_ids(linked, roster)
            for open_id, person_name in resolved:
                if not open_id:
                    continue

                # Dedup: skip if this person already logged hours for yesterday on this job
                try:
                    already_logged = employees.get_timesheet_today(open_id, record_id)
                except Exception as e:
                    log.error(f"Timesheet dedup check failed for {person_name} / {record_id}: {e}")
                    already_logged = False

                if already_logged:
                    log.debug(
                        f"Daily check-in skip (already logged): "
                        f"{person_name} / {discipline} / {record_id}"
                    )
                    continue

                try:
                    im.send_daily_hours_card(open_id, job_title, discipline, record_id)
                    log.info(
                        f"Daily hours card sent → {person_name} ({discipline}) "
                        f"job={record_id}"
                    )
                except Exception as e:
                    log.error(
                        f"Failed to send daily hours card to {person_name} "
                        f"({discipline}) job={record_id}: {e}"
                    )
