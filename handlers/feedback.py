# handlers/feedback.py
from __future__ import annotations
import logging
from datetime import date, timedelta, datetime
import config
from handlers.brief import _get_text, _resolve_open_ids, ASSIGNMENT_FIELDS

log = logging.getLogger(__name__)

RATING_SCORES = {"Fast": 0.85, "Normal": 1.0, "Slow": 1.2}


def _days_since(date_str: str) -> int:
    if not date_str:
        return 0
    try:
        d = datetime.strptime(str(date_str)[:10], "%Y-%m-%d").date()
        return (date.today() - d).days
    except (ValueError, TypeError):
        return 0


def should_ask_supervisor(job: dict) -> bool:
    done_date = job["fields"].get(config.F_LAST_AGENT_SYNC) or ""
    return _days_since(done_date) >= config.SUPERVISOR_ASK_DELAY_DAYS


def should_ask_ecd(job: dict) -> bool:
    done_date = job["fields"].get(config.F_LAST_AGENT_SYNC) or ""
    return _days_since(done_date) >= config.ECD_ASK_DELAY_DAYS


def compute_speed_index(ratings: list[str]) -> float:
    """Weighted average: recent ratings (last 3) count 2x, older 1x."""
    if not ratings:
        return 1.0
    n = len(ratings)
    total_weight = 0.0
    weighted_sum = 0.0
    for i, r in enumerate(ratings):
        weight = 2.0 if i >= n - 3 else 1.0  # last 3 ratings are "recent"
        score = RATING_SCORES.get(r, 1.0)
        weighted_sum += score * weight
        total_weight += weight
    return round(weighted_sum / total_weight, 3)


def classify_speed_trend(recent_indices: list[float]) -> str:
    if len(recent_indices) < 3:
        return "Stable"
    diffs = [recent_indices[i + 1] - recent_indices[i] for i in range(len(recent_indices) - 1)]
    avg_diff = sum(diffs) / len(diffs)
    if avg_diff < -0.02:
        return "Getting Faster"
    elif avg_diff > 0.05:
        return "Getting Slower"
    return "Stable"


def handle_feedback_dispatch(job: dict, base, im, roster: list, **_) -> None:
    """For completed jobs, queue feedback questions to supervisor and ECD."""
    fields = job["fields"]
    if fields.get(config.F_ACCOUNT_STATUS) != "DONE":
        return
    actual_hours = fields.get(config.F_ACTUAL_HOURS)
    if not actual_hours:
        return

    job_title = _get_text(fields.get(config.F_JOB_TITLE))

    # Check if feedback already requested
    existing_feedback = base.list_feedback_records()
    already_asked_supervisor = any(
        f["fields"].get("Job") and job["record_id"] in str(f["fields"]["Job"])
        and f["fields"].get("Reviewer Type") == "Supervisor"
        for f in existing_feedback
    )
    already_asked_ecd = any(
        f["fields"].get("Job") and job["record_id"] in str(f["fields"]["Job"])
        and f["fields"].get("Reviewer Type") == "ECD"
        for f in existing_feedback
    )

    # Collect assigned people for feedback context
    for fld in ASSIGNMENT_FIELDS:
        linked = fields.get(fld) or []
        if not isinstance(linked, list) or not linked:
            continue
        resolved = _resolve_open_ids(linked, roster)
        for open_id, person_name in resolved:
            if not already_asked_supervisor and should_ask_supervisor(job):
                supervisor_open_id = _find_supervisor(open_id, roster)
                if supervisor_open_id:
                    _send_feedback_question(
                        supervisor_open_id, job, person_name, actual_hours, base, im, "Supervisor"
                    )

            if not already_asked_ecd and should_ask_ecd(job) and config.ECD_OPEN_ID:
                _send_feedback_question(
                    config.ECD_OPEN_ID, job, person_name, actual_hours, base, im, "ECD"
                )
        break  # only process first discipline to avoid duplicate feedback cards per job


def _find_supervisor(person_open_id: str, roster: list[dict]) -> str | None:
    """Find a Creative Director or Senior on the team."""
    supervisor_roles = {
        "Creative Director", "Senior Art Director", "Senior Copywriter",
        "Senior Graphic Designer", "Senior Motion Designer"
    }
    for r in roster:
        role_val = r["fields"].get(config.R_ROLE)
        role = role_val[0].get("text", "") if isinstance(role_val, list) and role_val else str(role_val or "")
        if role in supervisor_roles:
            open_id = r["fields"].get(config.R_OPEN_ID)
            if open_id and str(open_id) != person_open_id:
                return str(open_id)
    return None


def _send_feedback_question(reviewer_open_id: str, job: dict, person_name: str,
                             actual_hours: float, base, im, reviewer_type: str) -> None:
    job_title = _get_text(job["fields"].get(config.F_JOB_TITLE))
    im.send_feedback_card(
        reviewer_open_id, job_title, "output type",
        0.0, float(actual_hours), person_name, "team member"
    )
    base.create_feedback_record({
        "Job": [{"id": job["record_id"]}],
        "Actual Hours": float(actual_hours),
        "Reviewer Type": reviewer_type,
        "Asked At": date.today().strftime("%Y-%m-%d %H:%M:%S"),
    })
    log.info(f"Feedback question sent to {reviewer_type} for {job['record_id']}")


def run_calibration(base) -> None:
    """Run after N new feedbacks: update Speed Index per person in Team Roster."""
    feedback_records = base.list_feedback_records()
    new_answers = [
        f for f in feedback_records
        if f["fields"].get("Rating") and not f["fields"].get("Used in Calibration")
    ]
    if len(new_answers) < config.FEEDBACK_CALIBRATION_THRESHOLD:
        return

    log.info(f"Running calibration with {len(new_answers)} new feedbacks")
    # Group by person record
    by_person: dict[str, list[str]] = {}
    for f in feedback_records:
        if not f["fields"].get("Rating"):
            continue
        person_links = f["fields"].get("Person") or []
        for p in (person_links if isinstance(person_links, list) else []):
            rec_id = p.get("id") if isinstance(p, dict) else None
            if rec_id:
                by_person.setdefault(rec_id, []).append(f["fields"]["Rating"])

    for person_rec_id, ratings in by_person.items():
        new_index = compute_speed_index(ratings)
        base.update_roster_record(person_rec_id, config.R_SPEED_INDEX, new_index)
        recent = [compute_speed_index(ratings[max(0, i - 3):i + 1]) for i in range(2, len(ratings))]
        if len(recent) >= 3:
            trend = classify_speed_trend(recent[-3:])
            base.update_roster_record(person_rec_id, config.R_SPEED_TREND, trend)
        base.update_roster_record(person_rec_id, config.R_FEEDBACK_COUNT, len(ratings))
        log.info(f"Updated Speed Index for {person_rec_id}: {new_index}")

    # Mark all new answers as used
    for f in new_answers:
        base._patch_record(config.FEEDBACK_TABLE, f["record_id"], {"Used in Calibration": True})
