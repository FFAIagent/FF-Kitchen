# handlers/hours.py
"""Collect actual hours per role from team members when a job is marked DONE.

Flow:
  1. Job Account Status → DONE
  2. handle_hours_collection() detects each assigned role that hasn't been asked yet
  3. Sends DM hours card to the assigned person
  4. Sets Hours Requested [Discipline] = True (dedup flag)
  5. Person clicks an hour bucket on the card
  6. webhook.py action=log_hours writes Actual Hours [Discipline] to DAPUR
  7. calibrate_role_bobot() updates Role Bobot via EMA
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
