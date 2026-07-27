"""handlers/load_sync.py — Per-person workload tracker driven by Lark Tasks.

Replaces the old DAPUR-assignment-field-based load tracking.

Poll loop usage:
    from handlers.load_sync import run_load_sync
    run_load_sync(base)

For each active DAPUR job that has a Lark Task ID:
  1. Fetch subtask list via `lark-cli task subtasks list --task-guid <guid> --as user`
  2. For each non-completed subtask with assignees:
     - Map assignee open_id → Team Roster record (via R_OPEN_ID)
     - Estimate hours from Output Type Bobot by subtask summary name match
  3. Aggregate per person:
     - task_load_score: sum of bobot hours for their active subtasks
     - current_jobs: distinct parent job titles joined by ", "
     - next_deadline: earliest due_date from their active subtasks (ms epoch)
     - task_count: number of active subtasks assigned
     - task_links: applinks to active tasks
  4. Write aggregates to Team Roster in a single pass per person.
     People with no active subtasks are written with zeros — never left
     with stale data from a previous cycle.
"""
from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime
from typing import Any

import config

log = logging.getLogger(__name__)

DEFAULT_HOURS = 4.0  # fallback when bobot has no match for a subtask name


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_lark(cmd: list[str]) -> dict | None:
    """Run a lark-cli command, return parsed JSON or None on error."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            log.warning(f"lark-cli error: {result.stderr.strip()[:200]}")
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        log.warning(f"lark-cli call failed ({cmd[2] if len(cmd) > 2 else '?'}): {e}")
        return None


def _get_subtasks(task_guid: str) -> list[dict]:
    """Return list of subtask dicts from lark-cli task subtasks list."""
    data = _run_lark([
        "lark-cli", "task", "subtasks", "list",
        "--task-guid", task_guid,
        "--as", "user",
        "--format", "json",
    ])
    if not data:
        return []
    inner = data.get("data", {})
    return inner.get("items", inner.get("tasks", []))


def _bobot_match(bobot_map: dict[str, dict[str, float]], summary: str) -> dict[str, float]:
    """Return the hours-by-discipline dict for the best matching bobot entry.

    Matching is case-insensitive substring: checks if the bobot output type
    name appears in the subtask summary or vice versa.
    Returns empty dict if no match (caller uses DEFAULT_HOURS fallback).
    """
    summary_lower = summary.lower().strip()
    for output_type, hours_by_disc in bobot_map.items():
        if output_type.lower() in summary_lower or summary_lower in output_type.lower():
            return hours_by_disc
    log.debug(f"load_sync: no bobot match for '{summary[:60]}'")
    return {}


def _extract_open_ids(members: Any) -> list[str]:
    """Extract list of open_ids from subtask members field.

    Lark returns members as a list of dicts with various shapes:
      {"id": "ou_xxx", ...}  or  {"open_id": "ou_xxx", ...}
    """
    if not isinstance(members, list):
        return []
    result = []
    for m in members:
        if not isinstance(m, dict):
            continue
        oid = m.get("id") or m.get("open_id") or ""
        if oid:
            result.append(str(oid))
    return result


def _build_roster_index(roster: list[dict]) -> dict[str, dict]:
    """Return {open_id: roster_record} for quick lookup."""
    index: dict[str, dict] = {}
    for rec in roster:
        oid = rec.get("fields", {}).get(config.R_OPEN_ID, "")
        if isinstance(oid, list):
            oid = oid[0] if oid else ""
        if oid:
            index[str(oid)] = rec
    return index


def _get_discipline_for_person(roster_record: dict) -> str:
    """Extract discipline string from a roster record."""
    disc = roster_record.get("fields", {}).get(config.R_DISCIPLINE, "")
    if isinstance(disc, list):
        disc = disc[0].get("text", "") if disc else ""
    return str(disc).strip()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_load_sync(base) -> None:
    """Compute and write per-person workload from Lark Tasks.

    base: a BaseClient instance (from lark_base.py).
    """
    log.info("load_sync: starting")
    try:
        jobs    = base.list_active_jobs()
        roster  = base.get_roster()
        bobot_map = base.get_output_type_bobot_map()
    except Exception as e:
        log.error(f"load_sync: failed to fetch base data: {e}", exc_info=True)
        return

    roster_index = _build_roster_index(roster)

    # person_data[open_id] = {
    #   "load_hours": float, "task_count": int,
    #   "task_guids": set, "job_titles": set, "earliest_due_ms": int|None
    # }
    person_data: dict[str, dict] = {}

    jobs_with_tasks = 0
    subtasks_processed = 0

    for job in jobs:
        fields    = job.get("fields", {})
        task_guid = fields.get(config.F_LARK_TASK_ID)
        if not task_guid:
            continue

        job_title = fields.get(config.F_JOB_TITLE, "")
        if isinstance(job_title, list):
            job_title = job_title[0].get("text", "") if job_title else ""
        job_title = str(job_title).strip()

        jobs_with_tasks += 1
        subtasks = _get_subtasks(str(task_guid).strip())

        for subtask in subtasks:
            # Skip completed subtasks.
            # completed_at / complete_time come back as "0" (string) when not set —
            # treat "0" and empty string as falsy to avoid skipping active tasks.
            status        = subtask.get("status", "")
            complete_time = subtask.get("complete_time")
            is_completed  = subtask.get("is_completed")
            completed_at  = subtask.get("completed_at")
            agent_status  = subtask.get("agent_task_status")

            def _is_set(v) -> bool:
                """Return True only if v is a meaningful (non-zero) value."""
                if v is None:
                    return False
                return str(v).strip() not in ("", "0", "false", "False")

            if (
                status in ("done", "completed")
                or _is_set(complete_time)
                or _is_set(is_completed)
                or _is_set(completed_at)
                or agent_status == 2  # 2 = done in Lark task API
            ):
                continue

            subtasks_processed += 1
            summary = str(subtask.get("summary") or subtask.get("title") or "").strip()
            members = subtask.get("members") or subtask.get("assignees") or []
            due     = subtask.get("due") or subtask.get("due_time") or {}
            due_ms  = None
            if isinstance(due, dict):
                raw_due = due.get("timestamp") or due.get("due_time")
                if raw_due:
                    try:
                        due_ms = int(raw_due) * 1000 if int(raw_due) < 1e12 else int(raw_due)
                    except (TypeError, ValueError):
                        pass

            open_ids    = _extract_open_ids(members)
            bobot_hours = _bobot_match(bobot_map, summary)

            for oid in open_ids:
                if oid not in roster_index:
                    log.debug(f"load_sync: open_id {oid} not in Team Roster — skipping")
                    continue

                roster_rec = roster_index[oid]
                disc       = _get_discipline_for_person(roster_rec)

                # Hours for this person's discipline from bobot, else DEFAULT_HOURS
                contrib = bobot_hours.get(disc, DEFAULT_HOURS) if bobot_hours else DEFAULT_HOURS

                if oid not in person_data:
                    person_data[oid] = {
                        "discipline":   disc,
                        "load_hours":   0.0,
                        "task_count":   0,
                        "task_guids":   set(),
                        "job_titles":   set(),
                        "earliest_due_ms": None,
                    }

                pd = person_data[oid]
                pd["load_hours"]  += contrib
                pd["task_count"]  += 1
                pd["task_guids"].add(str(task_guid))
                if job_title:
                    pd["job_titles"].add(job_title)
                if due_ms is not None:
                    if pd["earliest_due_ms"] is None or due_ms < pd["earliest_due_ms"]:
                        pd["earliest_due_ms"] = due_ms

    log.info(
        f"load_sync: scanned {len(jobs)} active jobs, {jobs_with_tasks} with task IDs, "
        f"{subtasks_processed} non-done subtasks, {len(person_data)} people to update"
    )

    # Write to Team Roster — single pass, everyone gets updated atomically.
    # People with subtasks get their computed values; everyone else gets zeros.
    # This avoids the stale-data problem of clearing first then re-filling.
    writes = 0
    for rec in roster:
        oid    = rec.get("fields", {}).get(config.R_OPEN_ID, "")
        if isinstance(oid, list):
            oid = oid[0] if oid else ""
        oid = str(oid)
        rec_id = rec["record_id"]

        pd = person_data.get(oid)
        if pd:
            load_score      = round(pd["load_hours"], 1)
            current_jobs_str = ", ".join(sorted(pd["job_titles"]))
            task_links      = ", ".join(
                f"https://applink.larksuite.com/client/todo/detail?guid={g}"
                for g in pd["task_guids"]
            )
            deadline_ms = pd["earliest_due_ms"]
            task_count  = pd["task_count"]
        else:
            load_score       = 0.0
            current_jobs_str = ""
            task_links       = ""
            deadline_ms      = None
            task_count       = 0

        # Read current values to skip unnecessary writes
        current_score = rec.get("fields", {}).get(config.R_LOAD_SCORE)
        try:
            current_score = float(current_score) if current_score is not None else None
        except (TypeError, ValueError):
            current_score = None

        patch: dict[str, Any] = {
            config.R_LOAD_SCORE:    load_score,
            config.R_CURRENT_JOBS:  current_jobs_str,
            config.R_TASK_COUNT:    task_count,
            config.R_TASK_LINKS:    task_links,
        }
        if deadline_ms is not None:
            patch[config.R_NEXT_DEADLINE] = deadline_ms

        try:
            base.update_roster_record(
                record_id=rec_id,
                field_id=config.R_LOAD_SCORE,  # used only for skip-check
                new_val=load_score,
                current_value=current_score,    # skip write if unchanged
            )
            # Always write the full patch via _patch_record
            base._patch_record(config.ROSTER_TABLE, rec_id, patch)
            if pd:
                log.debug(
                    f"load_sync: {oid} → load={load_score}h "
                    f"jobs={current_jobs_str[:40]} "
                    f"deadline={'none' if not deadline_ms else datetime.fromtimestamp(deadline_ms/1000).strftime('%Y-%m-%d')}"
                )
            writes += 1
        except Exception as e:
            log.error(f"load_sync: failed to write roster for {oid} (rec={rec_id}): {e}")

    log.info(f"load_sync: done — {writes} roster records updated")
