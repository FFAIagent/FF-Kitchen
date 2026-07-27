# handlers/employee.py
from __future__ import annotations
import logging
import config
from handlers.brief import ASSIGNMENT_FIELDS, _get_text

log = logging.getLogger(__name__)

# Fallback average hours when Role Bobot has no entry for a combination
_FALLBACK_HOURS = 4.0


def build_person_job_map(
    active_jobs: list[dict],
    roster: list[dict],
    role_bobot: dict | None = None,
) -> dict[str, list[dict]]:
    """Return {roster_record_id: [job_summary_dicts]} for each assigned person.

    Each job_summary includes role_hours — the expected contribution for
    that person's role on this specific job type, looked up from Role Bobot.
    Falls back to estimated_hours / num_assigned if no bobot entry found.
    """
    roster_ids = {r["record_id"] for r in roster}
    person_map: dict[str, list[dict]] = {r["record_id"]: [] for r in roster}
    role_bobot = role_bobot or {}

    for job in active_jobs:
        fields = job["fields"]
        title    = _get_text(fields.get(config.F_JOB_TITLE))
        stage    = fields.get(config.F_STAGE_STATUS) or ""
        if isinstance(stage, list):
            stage = stage[0].get("text", "") if stage else ""
        next_date = fields.get(config.F_NEXT_MILESTONE) or ""
        if isinstance(next_date, (int, float)):
            from datetime import datetime
            next_date = datetime.fromtimestamp(next_date / 1000).strftime("%Y-%m-%d") if next_date > 1e10 else str(int(next_date))
        next_date = str(next_date)[:10] if next_date else ""

        job_type = fields.get(config.F_JOB_TITLE)  # we use Job Type field
        # Correct: Job Type is a separate field
        job_type_raw = fields.get("fldoGTF6g5")  # F_JOB_TYPE field ID in DAPUR
        job_type = job_type_raw if isinstance(job_type_raw, str) else ""

        est_hours = fields.get(config.F_ESTIMATED_HOURS)
        try:
            est_hours = float(est_hours) if est_hours is not None else 0.0
        except (TypeError, ValueError):
            est_hours = 0.0

        # Count total assigned people on this job for fallback division
        total_assigned = sum(
            len([i for i in (fields.get(fld) or []) if isinstance(i, dict)])
            for fld in ASSIGNMENT_FIELDS
        )

        for fld in ASSIGNMENT_FIELDS:
            discipline = config.ASSIGNMENT_FIELD_TO_DISCIPLINE.get(fld, "")
            linked = fields.get(fld) or []
            if isinstance(linked, list):
                for item in linked:
                    rec_id = item.get("id") if isinstance(item, dict) else None
                    if not rec_id or rec_id not in roster_ids:
                        continue

                    # Role-specific hours from Bobot
                    role_hours = role_bobot.get((job_type, discipline))
                    if role_hours is None:
                        # Fallback: split estimated hours equally
                        role_hours = (est_hours / total_assigned) if total_assigned else _FALLBACK_HOURS

                    job_summary = {
                        "title": title,
                        "stage": stage,
                        "next_date": next_date,
                        "estimated_hours": est_hours,  # total job estimate
                        "role_hours": round(float(role_hours), 1),  # this person's contribution
                        "job_type": job_type,
                        "discipline": discipline,
                    }
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


def run_employee_updates(
    roster: list[dict],
    employees_client=None,
) -> None:
    """Mirror Team Roster workload data → FF Employees base.

    Called after run_load_sync() has already written accurate workload data
    (from Lark Tasks) into Team Roster. This function reads those pre-computed
    values and copies them to the Employees base — no independent calculation.

    Matches Roster → Employee records via Lark Open ID (R_OPEN_ID / E_OPEN_ID).
    """
    if employees_client is None:
        return

    # Build Open ID → Employee record map
    emp_by_open_id: dict[str, dict] = {}
    for emp in employees_client.get_employees():
        oid = emp["fields"].get(config.E_OPEN_ID, "")
        if isinstance(oid, list):
            oid = oid[0] if oid else ""
        if oid:
            emp_by_open_id[str(oid)] = emp

    from datetime import datetime
    import pytz
    now_wib = datetime.now(pytz.timezone(config.TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")

    updated = 0
    for roster_rec in roster:
        fields = roster_rec.get("fields", {})
        open_id = fields.get(config.R_OPEN_ID, "")
        if isinstance(open_id, list):
            open_id = open_id[0] if open_id else ""
        if not open_id:
            continue

        emp = emp_by_open_id.get(str(open_id))
        if not emp:
            continue

        # Read workload values already written by load_sync
        current_jobs = fields.get(config.R_CURRENT_JOBS) or ""
        if isinstance(current_jobs, list):
            current_jobs = current_jobs[0].get("text", "") if current_jobs else ""

        task_count = fields.get(config.R_TASK_COUNT) or 0
        try:
            task_count = int(task_count)
        except (TypeError, ValueError):
            task_count = 0

        load_score = fields.get(config.R_LOAD_SCORE) or 0.0
        try:
            load_score = float(load_score)
        except (TypeError, ValueError):
            load_score = 0.0

        emp_fields = emp.get("fields", {})
        current_proj = emp_fields.get(config.E_CURRENT_PROJECTS) or ""

        employees_client.update_employee(
            record_id=emp["record_id"],
            current_projects=current_jobs,
            active_jobs_count=task_count,
            load_score=load_score,
            last_updated=now_wib,
            current_projects_val=current_proj,
        )
        updated += 1

    log.info(f"employee_sync: mirrored {updated} roster records → Employees")


def handle_employee_update(job: dict, base, roster: list, **_) -> None:
    """Per-job hook called from poller. Batching handled separately in run_employee_updates."""
    pass  # employee updates are done as a batch after all jobs — see scheduler.py
