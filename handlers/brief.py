from __future__ import annotations
import logging
import config

log = logging.getLogger(__name__)

ASSIGNMENT_FIELDS = [
    config.F_ART_ASSIGNED, config.F_COPY_ASSIGNED, config.F_GD_ASSIGNED,
    config.F_MOTION_ASSIGNED, config.F_STRATEGY_ASSIGNED, config.F_FA_ASSIGNED,
]


def _get_text(field_val) -> str:
    if isinstance(field_val, list) and field_val:
        return field_val[0].get("text", "") if isinstance(field_val[0], dict) else str(field_val[0])
    return str(field_val) if field_val else ""


def _resolve_open_ids(linked_ids: list[dict], roster: list[dict]) -> list[tuple[str, str]]:
    """Given [{id: record_id}], return [(open_id, name)] for each resolved person."""
    roster_map = {r["record_id"]: r["fields"] for r in roster}
    result = []
    for item in linked_ids:
        rec_id = item.get("id") if isinstance(item, dict) else None
        if rec_id and rec_id in roster_map:
            fields = roster_map[rec_id]
            open_id = fields.get(config.R_OPEN_ID, "")
            name_val = fields.get(config.R_NAME, "")
            name = name_val[0]["text"] if isinstance(name_val, list) and name_val else str(name_val)
            if open_id:
                result.append((str(open_id), name))
    return result


def handle_brief_announced(job: dict, base, im, roster: list, chat_ids: dict, **_) -> None:
    fields = job["fields"]
    if fields.get(config.F_BRIEF_ANNOUNCED):
        return
    if fields.get(config.F_APPROVAL_STATUS) != "Approved":
        return

    job_title = _get_text(fields.get(config.F_JOB_TITLE))
    team_name = _get_text(fields.get(config.F_CREATIVE_TEAM))
    brief_link = _get_text(fields.get(config.F_BRIEF_LINK))

    # Collect all assigned people
    assigned: list[tuple[str, str]] = []
    for fld in ASSIGNMENT_FIELDS:
        linked = fields.get(fld) or []
        if isinstance(linked, list):
            assigned.extend(_resolve_open_ids(linked, roster))
    # Deduplicate by open_id
    seen: set = set()
    unique_assigned = [(oid, name) for oid, name in assigned if not (oid in seen or seen.add(oid))]

    # PM
    pm_links = fields.get(config.F_PM_PIC) or []
    pm_people = _resolve_open_ids(pm_links, roster)
    pm_name = pm_people[0][1] if pm_people else "PM"

    # Build names list
    names_str = " · ".join(name for _, name in unique_assigned) or "TBD"

    # Review / presentation dates
    first_review = _get_text(fields.get(config.F_FIRST_REVIEW_DATE))
    client_pres = _get_text(fields.get(config.F_CLIENT_PRES_DATE))

    # Send group message
    chat_id = chat_ids.get(team_name)
    group_msg = (
        f"📋 New brief: **{job_title}**\n"
        f"👥 Team: {names_str}\n"
        f"📅 1st Review: {first_review or 'TBD'} | Client Presentation: {client_pres or 'TBD'}\n"
        f"PM: {pm_name}\n"
        f"Brief doc: {brief_link or '—'}"
    )
    if chat_id:
        im.send_group_text(chat_id, group_msg)
    else:
        log.warning(f"No chat ID for team '{team_name}' on job {job['record_id']}")

    # Send individual DMs
    for open_id, name in unique_assigned:
        dm = (
            f"Hey {name} 👋 You've been assigned to **{job_title}**.\n"
            f"1st Internal Review: {first_review or 'TBD'} | Client Presentation: {client_pres or 'TBD'}\n"
            f"PM: {pm_name} | Brief: {brief_link or '—'}"
        )
        im.send_text(open_id, dm)

    # Write Estimated Hours (Base Hours × Complexity × Speed Index average)
    estimated_h = _calc_estimated_hours(fields, unique_assigned, base)
    if estimated_h:
        base.update_record(job["record_id"], {config.F_ESTIMATED_HOURS: estimated_h})

    # Mark announced
    base.update_record(job["record_id"], {config.F_BRIEF_ANNOUNCED: True})
    log.info(f"Brief announced for {job['record_id']} ({job_title}), estimated {estimated_h}h")


def _calc_estimated_hours(fields: dict, assigned_people: list[tuple], base) -> float | None:
    """Estimate hours: average(Speed Index of assigned) × complexity × 8h base."""
    job_type_raw = fields.get("Job Type") or ""
    if isinstance(job_type_raw, list):
        job_type_raw = job_type_raw[0].get("text", "") if job_type_raw else ""
    complexity = config.COMPLEXITY.get(str(job_type_raw), 1.0)
    if not assigned_people:
        return None
    # Use base hours of 8h as default when Output Type Bobot lookup not available
    base_hours = 8.0
    # Average Speed Index across assigned people from roster
    roster = base.get_roster()
    speed_indices = []
    for _, name in assigned_people:
        for rec in roster:
            if _get_text(rec["fields"].get(config.R_NAME)) == name:
                idx = rec["fields"].get(config.R_SPEED_INDEX, 1.0)
                speed_indices.append(float(idx) if idx else 1.0)
    avg_speed = sum(speed_indices) / len(speed_indices) if speed_indices else 1.0
    return round(base_hours * complexity * avg_speed, 1)
