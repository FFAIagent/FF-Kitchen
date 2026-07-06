from __future__ import annotations
import logging
from datetime import date, timedelta
import config
from handlers.brief import _resolve_open_ids, _get_text, ASSIGNMENT_FIELDS

log = logging.getLogger(__name__)

MILESTONES = [
    ("Job Brief",             config.F_JOB_BRIEF_DATE,     config.F_JOB_BRIEF_REMINDER),
    ("1st Internal Review",   config.F_FIRST_REVIEW_DATE,  config.F_FIRST_REVIEW_REMINDER),
    ("Client Presentation",   config.F_CLIENT_PRES_DATE,   config.F_CLIENT_PRES_REMINDER),
    ("2nd Internal Review",   config.F_SECOND_REVIEW_DATE, config.F_SECOND_REVIEW_REMINDER),
]


def _is_tomorrow(date_val) -> bool:
    if not date_val:
        return False
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    if isinstance(date_val, list):
        date_val = date_val[0].get("text", "") if date_val and isinstance(date_val[0], dict) else ""
    date_str = str(date_val)[:10]  # first 10 chars = YYYY-MM-DD
    return date_str == tomorrow


def _is_yesterday(date_val) -> bool:
    if not date_val:
        return False
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    if isinstance(date_val, list):
        date_val = date_val[0].get("text", "") if date_val and isinstance(date_val[0], dict) else ""
    return str(date_val)[:10] == yesterday


def handle_deadline_reminders(job: dict, base, im, roster: list, chat_ids: dict, **_) -> None:
    fields = job["fields"]
    job_title = _get_text(fields.get(config.F_JOB_TITLE))

    # Collect assigned people (all disciplines)
    assigned = []
    for fld in ASSIGNMENT_FIELDS:
        linked = fields.get(fld) or []
        if isinstance(linked, list):
            assigned.extend(_resolve_open_ids(linked, roster))
    seen: set = set()
    unique = [(oid, name) for oid, name in assigned if not (oid in seen or seen.add(oid))]

    for stage_name, date_field, flag_field in MILESTONES:
        if fields.get(flag_field):
            continue  # already sent
        date_val = fields.get(date_field)
        if not _is_tomorrow(date_val):
            continue
        date_str = str(date_val)[:10] if date_val else ""
        for open_id, _ in unique:
            im.send_reminder_card(open_id, job_title, stage_name, date_str, job["record_id"])
        base.update_record(job["record_id"], {flag_field: True})
        log.info(f"Reminder sent for {job['record_id']} ({stage_name})")
