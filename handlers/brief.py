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

    # Send group message (non-fatal — a missing/inaccessible chat must not block
    # the individual DMs or the F_BRIEF_ANNOUNCED flag from being written)
    chat_id = chat_ids.get(team_name)
    group_msg = (
        f"📋 New brief: **{job_title}**\n"
        f"👥 Team: {names_str}\n"
        f"📅 1st Review: {first_review or 'TBD'} | Client Presentation: {client_pres or 'TBD'}\n"
        f"PM: {pm_name}\n"
        f"Brief doc: {brief_link or '—'}"
    )
    if chat_id:
        try:
            im.send_group_text(chat_id, group_msg)
        except Exception as e:
            log.warning(
                f"Brief group send failed for team '{team_name}' (job {job['record_id']}): {e} — continuing"
            )
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

    # Write Estimated Hours — per-discipline + total
    est = _calc_estimated_hours(fields, unique_assigned, base, roster=roster)
    if est:
        patch: dict = {}
        total = est.pop("_total", 0.0)
        # Per-discipline fields
        for disc, fid in config.DISCIPLINE_EST_FIELDS.items():
            h = est.get(disc)
            if h:
                patch[fid] = h
        # Total (F_ESTIMATED_HOURS — kept for Load Score / billing)
        if total:
            patch[config.F_ESTIMATED_HOURS] = total
        if patch:
            base.update_record(job["record_id"], patch)
        log.info(
            f"Brief announced for {job['record_id']} ({job_title}): "
            f"total={total}h per-disc={est}"
        )
    else:
        log.info(f"Brief announced for {job['record_id']} ({job_title}): no estimate produced")

    # Mark announced
    base.update_record(job["record_id"], {config.F_BRIEF_ANNOUNCED: True})


def _read_deliverables(fields: dict) -> dict[str, float]:
    """Read Deliverable 1–5 Type/Qty pairs from a DAPUR job record.

    Returns {output_type_name: quantity} — e.g. {"Key Visual (KV)": 2, "Social Media Static Post": 5}.
    Empty slots (Type = None/blank) are skipped. Qty defaults to 1 if blank.
    """
    deliverables: dict[str, float] = {}
    for type_fid, qty_fid in zip(config.DELIV_TYPE_FIELDS, config.DELIV_QTY_FIELDS):
        d_type = fields.get(type_fid)
        if not d_type:
            continue
        if isinstance(d_type, list):
            d_type = d_type[0] if d_type else None
        if not d_type:
            continue
        d_type = str(d_type).strip()
        qty_raw = fields.get(qty_fid)
        try:
            qty = float(qty_raw) if qty_raw is not None else 1.0
        except (TypeError, ValueError):
            qty = 1.0
        if qty <= 0:
            continue
        deliverables[d_type] = deliverables.get(d_type, 0.0) + qty
    return deliverables


def _fuzzy_match_bobot(name: str, bobot_map: dict) -> dict | None:
    """Case-insensitive name match against Output Type Bobot map keys."""
    name_norm = name.strip().lower()
    # Exact match first
    for k, v in bobot_map.items():
        if k.strip().lower() == name_norm:
            return v
    # Substring match (e.g. "Short TVC" matches 'Short TVC (15-30")')
    for k, v in bobot_map.items():
        if name_norm in k.strip().lower() or k.strip().lower() in name_norm:
            return v
    return None


def _speed_index_map(roster: list[dict]) -> dict[str, float]:
    """Return {person_name: speed_index} from the Team Roster."""
    result: dict[str, float] = {}
    for rec in roster:
        f = rec["fields"]
        name = _get_text(f.get(config.R_NAME))
        idx = f.get(config.R_SPEED_INDEX)
        try:
            result[name] = float(idx) if idx else 1.0
        except (TypeError, ValueError):
            result[name] = 1.0
    return result


def _calc_estimated_hours(
    fields: dict,
    assigned_people: list[tuple],   # [(open_id, name), ...]
    base,
    roster: list | None = None,
) -> dict[str, float] | None:
    """Estimate hours per discipline using Output Type Bobot × deliverables × speed index.

    Returns {discipline: hours, ..., "_total": total} or None if nothing can be estimated.

    Algorithm:
      deliverables = read Deliverable 1–5 Type/Qty from job fields
      For each discipline with assigned people:
        per_person_est = SUM over deliverables of (qty × bobot[output_type][discipline])
        adjusted       = per_person_est × person_speed_index
      Write per-discipline AND total.

    Fallback: if no deliverables are filled in, falls back to Role Bobot v1
    (flat 8h × complexity × avg_speed) and logs a warning.
    """
    deliverables = _read_deliverables(fields)

    if not deliverables:
        # Fallback to v1 (Role Bobot)
        log.warning("_calc_estimated_hours: no deliverables on job — falling back to Role Bobot v1")
        return _calc_estimated_hours_v1(fields, assigned_people, base, roster)

    bobot_map = base.get_output_type_bobot_map()

    # Build per-discipline estimated hours
    # Group assigned people by discipline (from their roster record)
    if roster is None:
        roster = base.get_roster()
    speed_map = _speed_index_map(roster)

    # Map name → discipline from roster
    name_to_disc: dict[str, str] = {}
    for rec in roster:
        f = rec["fields"]
        name = _get_text(f.get(config.R_NAME))
        disc = _get_text(f.get(config.R_DISCIPLINE))
        if name and disc:
            name_to_disc[name] = disc

    # Compute base hours per discipline from deliverables (before speed adjustment)
    disc_base: dict[str, float] = {d: 0.0 for d in config.DISCIPLINE_OB_FIELDS}
    for d_type, qty in deliverables.items():
        bobot = _fuzzy_match_bobot(d_type, bobot_map)
        if bobot is None:
            log.warning(f"_calc_estimated_hours: no bobot entry for deliverable '{d_type}' — skipped")
            continue
        for disc, fid in config.DISCIPLINE_OB_FIELDS.items():
            disc_base[disc] = disc_base.get(disc, 0.0) + qty * bobot.get(disc, 0.0)

    # Apply speed index per assigned person and accumulate
    disc_est: dict[str, float] = {}
    for open_id, name in assigned_people:
        disc = name_to_disc.get(name)
        if not disc or disc not in disc_base:
            continue
        speed = speed_map.get(name, 1.0)
        prev = disc_est.get(disc, 0.0)
        disc_est[disc] = prev + disc_base[disc] * speed

    if not disc_est:
        log.warning("_calc_estimated_hours: no discipline estimates produced (no assigned people matched roster)")
        return None

    total = round(sum(disc_est.values()), 1)
    result = {disc: round(h, 1) for disc, h in disc_est.items()}
    result["_total"] = total
    return result


def _calc_estimated_hours_v1(
    fields: dict,
    assigned_people: list[tuple],
    base,
    roster: list | None = None,
) -> dict[str, float] | None:
    """Legacy fallback: flat 8h × complexity × avg_speed → total only."""
    job_type_raw = fields.get(config.F_JOB_TYPE) or ""
    if isinstance(job_type_raw, list):
        job_type_raw = job_type_raw[0] if job_type_raw else ""
        if isinstance(job_type_raw, dict):
            job_type_raw = job_type_raw.get("text", "")
    complexity = config.COMPLEXITY.get(str(job_type_raw), 1.0)
    if not assigned_people:
        return None
    base_hours = 8.0
    if roster is None:
        roster = base.get_roster()
    speed_indices = []
    for _, name in assigned_people:
        for rec in roster:
            if _get_text(rec["fields"].get(config.R_NAME)) == name:
                idx = rec["fields"].get(config.R_SPEED_INDEX, 1.0)
                speed_indices.append(float(idx) if idx else 1.0)
    avg_speed = sum(speed_indices) / len(speed_indices) if speed_indices else 1.0
    total = round(base_hours * complexity * avg_speed, 1)
    return {"_total": total}
