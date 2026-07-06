# handlers/employee.py
from __future__ import annotations
import logging
import config
from handlers.brief import ASSIGNMENT_FIELDS, _get_text

log = logging.getLogger(__name__)


def build_person_job_map(active_jobs: list[dict], roster: list[dict]) -> dict[str, list[dict]]:
    """Return {roster_record_id: [job_summary_dicts]} for each assigned person."""
    roster_ids = {r["record_id"] for r in roster}
    person_map: dict[str, list[dict]] = {r["record_id"]: [] for r in roster}

    for job in active_jobs:
        fields = job["fields"]
        title = _get_text(fields.get(config.F_JOB_TITLE))
        stage = fields.get(config.F_STAGE_STATUS) or ""
        if isinstance(stage, list):
            stage = stage[0].get("text", "") if stage else ""
        next_date = fields.get(config.F_NEXT_MILESTONE) or ""
        if isinstance(next_date, (int, float)):
            from datetime import datetime
            next_date = datetime.fromtimestamp(next_date / 1000).strftime("%Y-%m-%d") if next_date > 1e10 else str(int(next_date))
        next_date = str(next_date)[:10] if next_date else ""

        job_summary = {"title": title, "stage": stage, "next_date": next_date}

        for fld in ASSIGNMENT_FIELDS:
            linked = fields.get(fld) or []
            if isinstance(linked, list):
                for item in linked:
                    rec_id = item.get("id") if isinstance(item, dict) else None
                    if rec_id and rec_id in roster_ids:
                        person_map[rec_id].append(job_summary)

    return person_map


def format_current_jobs(jobs: list[dict]) -> str:
    if not jobs:
        return ""
    parts = []
    for j in jobs:
        label = j["title"]
        if j["stage"]:
            label += f" ({j['stage']}"
            if j["next_date"]:
                label += f" {j['next_date']}"
            label += ")"
        parts.append(label)
    return " · ".join(parts)


def run_employee_updates(active_jobs: list[dict], roster: list[dict], base) -> None:
    person_map = build_person_job_map(active_jobs, roster)
    roster_lookup = {r["record_id"]: r for r in roster}

    for rec_id, jobs in person_map.items():
        person = roster_lookup.get(rec_id, {})
        if not person:
            continue
        fields = person.get("fields", {})

        new_text = format_current_jobs(jobs)
        current_text = fields.get(config.R_CURRENT_JOBS) or ""
        if isinstance(current_text, list):
            current_text = current_text[0].get("text", "") if current_text else ""
        base.update_roster_record(rec_id, config.R_CURRENT_JOBS, new_text, current_value=current_text)

        if jobs:
            dates = [j["next_date"] for j in jobs if j["next_date"]]
            earliest = min(dates) if dates else None
            current_deadline = fields.get(config.R_NEXT_DEADLINE) or ""
            if isinstance(current_deadline, (int, float)):
                current_deadline = ""
            base.update_roster_record(rec_id, config.R_NEXT_DEADLINE, earliest, current_value=current_deadline)


def handle_employee_update(job: dict, base, roster: list, **_) -> None:
    """Per-job hook called from poller. Batching handled separately in run_employee_updates."""
    pass  # employee updates are done as a batch after all jobs — see scheduler.py
