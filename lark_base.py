"""Lark Base client using lark-cli subprocess calls with user auth."""
from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime
from typing import Any

import pytz

import config

log = logging.getLogger(__name__)

WIB = pytz.timezone(config.TIMEZONE)

_BASE_CMD = ["lark-cli", "base"]
_BASE_TOKEN = config.BASE_TOKEN


def _run(cmd: list[str]) -> dict:
    """Run a lark-cli command and return parsed JSON output."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"lark-cli error (exit {result.returncode}): {result.stderr.strip()}"
        )
    return json.loads(result.stdout)


class BaseClient:
    def __init__(self) -> None:
        self.base_token = config.BASE_TOKEN

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _list_records(
        self,
        table_id: str,
        page_size: int = 200,
        filter_json: str | None = None,
    ) -> list[dict]:
        """Fetch all records from a table using offset-based pagination.

        lark-cli +record-list --format json returns a columnar envelope:
            {"data": {"field_id_list": [...], "record_id_list": [...],
                      "data": [[row0_vals...], ...], "has_more": bool}}
        This method reconstructs the standard {record_id, fields} shape.

        filter_json: optional Lark Base filter expression (--filter-json syntax),
            e.g. '{"logic":"and","conditions":[["Account Status","!=","DONE"]]}'
            Applied server-side to avoid fetching all records when only a subset
            is needed. The caller should still apply Python-side guards as safety nets.
        """
        records: list[dict] = []
        offset = 0
        while True:
            cmd = [
                *_BASE_CMD,
                "+record-list",
                "--base-token", self.base_token,
                "--table-id", table_id,
                "--as", "user",
                "--format", "json",
                "--limit", str(page_size),
                "--offset", str(offset),
            ]
            if filter_json:
                cmd += ["--filter-json", filter_json]
            data = _run(cmd)
            items: list[dict] = []
            has_more = False
            if isinstance(data, dict):
                inner = data.get("data", data)
                has_more = bool(inner.get("has_more", False))
                if isinstance(inner, dict) and "field_id_list" in inner:
                    # Columnar format (current lark-cli)
                    # Single-select values come back as ["option"] — unwrap to "option"
                    # so handler comparisons (== "Approved", == "DONE") work unchanged.
                    # Lists of dicts (link/user fields) and multi-element lists are kept as-is.
                    def _unwrap(v):
                        if isinstance(v, list) and len(v) == 1 and isinstance(v[0], str):
                            return v[0]
                        return v

                    field_ids  = inner.get("field_id_list", [])
                    record_ids = inner.get("record_id_list", [])
                    rows       = inner.get("data", [])
                    for i, row in enumerate(rows):
                        rec_id = record_ids[i] if i < len(record_ids) else ""
                        fields = {
                            field_ids[j]: _unwrap(row[j])
                            for j in range(min(len(field_ids), len(row)))
                            if row[j] is not None
                        }
                        items.append({"record_id": rec_id, "fields": fields})
                else:
                    # Legacy items format (fallback)
                    raw_items = inner.get("items", inner if isinstance(inner, list) else [])
                    for item in raw_items:
                        record_id = item.get("record_id", "")
                        fields = item.get("fields", {})
                        items.append({"record_id": record_id, "fields": fields})
            elif isinstance(data, list):
                for item in data:
                    record_id = item.get("record_id", "")
                    fields = item.get("fields", {})
                    items.append({"record_id": record_id, "fields": fields})

            records.extend(items)

            if not has_more or not items:
                break
            offset += len(items)

        return records

    def _patch_record(self, table_id: str, record_id: str, fields: dict) -> bool:
        """Update a record via lark-cli +record-upsert."""
        cmd = [
            *_BASE_CMD,
            "+record-upsert",
            "--base-token", self.base_token,
            "--table-id", table_id,
            "--record-id", record_id,
            "--as", "user",
            "--json", json.dumps(fields, ensure_ascii=False),
        ]
        _run(cmd)
        return True

    def _create_record(self, table_id: str, fields: dict) -> bool:
        """Create a new record via lark-cli +record-upsert (no --record-id)."""
        cmd = [
            *_BASE_CMD,
            "+record-upsert",
            "--base-token", self.base_token,
            "--table-id", table_id,
            "--as", "user",
            "--json", json.dumps(fields, ensure_ascii=False),
        ]
        _run(cmd)
        return True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    # Server-side filter: exclude DONE and ON HOLD jobs.
    # Tested 2026-07-08: returns ~140 records vs 395 total (~64% reduction).
    _ACTIVE_JOBS_FILTER = json.dumps({
        "logic": "and",
        "conditions": [
            ["Job Status", "!=", "DONE"],
            ["Job Status", "!=", "ON HOLD"],
        ],
    })

    def list_active_jobs(self) -> list[dict]:
        """Return DAPUR records where Account Status is not DONE or ON HOLD.

        Uses server-side filter to avoid fetching all ~395 records —
        only ~140 active records are returned from the API (~64% reduction).
        Python-side filter is kept as a safety net in case the server filter
        returns unexpected values (e.g. blank Account Status edge cases).
        """
        records = self._list_records(config.DAPUR_TABLE, filter_json=self._ACTIVE_JOBS_FILTER)
        return [
            r for r in records
            if r["fields"].get(config.F_ACCOUNT_STATUS) not in ("DONE", "ON HOLD")
        ]

    def update_record(self, record_id: str, fields: dict) -> bool:
        """Update a DAPUR record."""
        return self._patch_record(config.DAPUR_TABLE, record_id, fields)

    def update_last_sync(self, record_id: str) -> bool:
        """Stamp the Last Agent Sync field with current WIB datetime."""
        now_wib = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
        return self.update_record(record_id, {config.F_LAST_AGENT_SYNC: now_wib})

    def get_roster(self) -> list[dict]:
        """Return all Team Roster records."""
        return self._list_records(config.ROSTER_TABLE)

    def update_roster_record(
        self,
        record_id: str,
        field_id: str,
        new_val: Any,
        current_value: Any = None,
    ) -> bool:
        """Update a Roster record; skip write if value is unchanged."""
        if current_value == new_val:
            return False
        return self._patch_record(config.ROSTER_TABLE, record_id, {field_id: new_val})

    def get_chat_ids(self) -> dict[str, str]:
        """Return {team_name: chat_id} map from Creative Chat ID table."""
        records = self._list_records(config.CHAT_ID_TABLE)
        result: dict[str, str] = {}
        for r in records:
            team = r["fields"].get(config.C_TEAM_NAME)
            chat = r["fields"].get(config.C_CHAT_ID)
            if team and chat:
                if isinstance(team, list):
                    team = team[0].get("text", "") if team else ""
                if isinstance(chat, list):
                    chat = chat[0].get("text", "") if chat else ""
                if team and chat:
                    result[str(team)] = str(chat)
        return result

    def get_output_type_bobot(self) -> list[dict]:
        """Return all Output Type Bobot records."""
        return self._list_records(config.BOBOT_TABLE)

    def get_output_type_bobot_map(self) -> dict[str, dict[str, float]]:
        """Return {output_type_name: {discipline: base_hours}} for estimation engine.

        Normalises names to lowercase-stripped keys for fuzzy matching.
        Only includes disciplines with non-zero entries.
        """
        records = self._list_records(config.BOBOT_TABLE)
        result: dict[str, dict[str, float]] = {}
        for r in records:
            f = r["fields"]
            name = f.get(config.OB_NAME, "")
            if isinstance(name, list):
                name = name[0] if name else ""
            if not name:
                continue
            discipline_hours: dict[str, float] = {}
            for disc, fid in config.DISCIPLINE_OB_FIELDS.items():
                val = f.get(fid)
                try:
                    h = float(val) if val is not None else 0.0
                except (TypeError, ValueError):
                    h = 0.0
                discipline_hours[disc] = h
            result[str(name).strip()] = discipline_hours
        return result

    def update_output_type_bobot(
        self,
        record_id: str,
        discipline: str,
        new_hours: float,
    ) -> bool:
        """EMA-update a single discipline's Base Hours on one Output Type Bobot record."""
        fid = config.DISCIPLINE_OB_FIELDS.get(discipline)
        if not fid:
            log.warning(f"update_output_type_bobot: unknown discipline '{discipline}'")
            return False
        return self._patch_record(config.BOBOT_TABLE, record_id, {fid: round(new_hours, 2)})


class EmployeesClient:
    """Client for the FF Employees base (Flock People System).

    Separate base token from FF Kitchen — used to mirror Current Projects
    and Active Jobs count into the employee directory.
    """

    def __init__(self) -> None:
        self.base_token = config.EMPLOYEES_BASE_TOKEN

    def _run_cmd(self, cmd: list[str]) -> dict:
        return _run(cmd)

    def get_employees(self) -> list[dict]:
        """Return all FF Employees records (uses BaseClient._list_records logic)."""
        # Reuse the same columnar-aware pagination via a throwaway BaseClient-like call
        tmp = BaseClient.__new__(BaseClient)
        tmp.base_token = self.base_token
        return tmp._list_records(config.EMPLOYEES_TABLE)

    def update_employee(
        self,
        record_id: str,
        current_projects: str,
        active_jobs_count: int,
        last_updated: str,
        load_score: float = 0.0,
        current_projects_val: str = None,
    ) -> bool:
        """Write Current Projects, Active Jobs, Load Score, and Last Updated.
        Skips write if Current Projects and Load Score are both unchanged.
        """
        if current_projects_val == current_projects:
            return False
        fields = {
            config.E_CURRENT_PROJECTS: current_projects,
            config.E_ACTIVE_JOBS:      active_jobs_count,
            config.E_LOAD_SCORE:       load_score,
            config.E_LAST_UPDATED:     last_updated,
        }
        cmd = [
            "lark-cli", "base", "+record-upsert",
            "--base-token", self.base_token,
            "--table-id",   config.EMPLOYEES_TABLE,
            "--record-id",  record_id,
            "--as", "user",
            "--json", json.dumps(fields, ensure_ascii=False),
        ]
        _run(cmd)
        return True

    # ------------------------------------------------------------------
    # Timesheet methods (added 2026-07-07)
    # ------------------------------------------------------------------

    def _list_timesheet_records(self) -> list[dict]:
        """Fetch all Timesheet records using the employees base token."""
        tmp = BaseClient.__new__(BaseClient)
        tmp.base_token = self.base_token
        return tmp._list_records(config.TIMESHEET_TABLE)

    def get_timesheet_today(self, person_open_id: str, job_record_id: str) -> bool:
        """Return True if a Timesheet row already exists for this person+job yesterday.

        Used as a dedup check before sending the daily hours DM card.
        Matches on: Date == yesterday (WIB) AND Job Record ID == job_record_id
        AND Person link contains the employee matching person_open_id.
        """
        from datetime import timedelta

        yesterday = (datetime.now(WIB) - timedelta(days=1)).strftime("%Y-%m-%d")

        # Resolve open_id → employee record_id
        employees = self.get_employees()
        emp_record_id = next(
            (e["record_id"] for e in employees
             if e["fields"].get(config.E_OPEN_ID) == person_open_id),
            None,
        )
        if not emp_record_id:
            log.warning(f"get_timesheet_today: no employee found for open_id={person_open_id}")
            return False

        for r in self._list_timesheet_records():
            f = r["fields"]

            # Match date — datetime fields may return ms timestamp or formatted string
            date_val = f.get(config.TS_DATE)
            if date_val is None:
                continue
            if isinstance(date_val, (int, float)):
                # Unix milliseconds → convert to WIB date string
                dt_utc = datetime.fromtimestamp(date_val / 1000, tz=pytz.utc)
                date_str = dt_utc.astimezone(WIB).strftime("%Y-%m-%d")
            else:
                date_str = str(date_val)

            if not date_str.startswith(yesterday):
                continue

            # Match job record ID
            if f.get(config.TS_JOB_REC_ID) != job_record_id:
                continue

            # Match person — link field returns list of {record_id, ...} dicts
            person_links = f.get(config.TS_PERSON, [])
            if isinstance(person_links, list):
                if any(
                    isinstance(p, dict) and p.get("record_id") == emp_record_id
                    for p in person_links
                ):
                    return True

        return False

    def create_timesheet_record(self, fields: dict) -> bool:
        """Write a new daily row to the Timesheet table.

        Expected fields (use config.TS_* constants as keys):
            TS_DATE        → "YYYY-MM-DD 00:00:00"  (datetime string)
            TS_PERSON      → [{"record_id": "recXXX"}]  (link to Employees)
            TS_JOB_TITLE   → str
            TS_JOB_REC_ID  → str  (recXXX from DAPUR)
            TS_DISCIPLINE  → str  (Art / Copy / GD / Motion / Strategy / FA Artist)
            TS_HOURS       → float
        TS_WEEK is a formula field — do NOT include it.
        """
        tmp = BaseClient.__new__(BaseClient)
        tmp.base_token = self.base_token
        return tmp._create_record(config.TIMESHEET_TABLE, fields)

    def update_employee_hours(
        self,
        employee_record_id: str,
        weekly_h: float,
        monthly_h: float,
        overloaded: bool,
    ) -> bool:
        """Write Weekly Hours, Monthly Hours and Overloaded flag to an Employee record.

        Called after every hours submission to keep the Employees table in sync.
        overloaded=True when weekly_h > 40.
        """
        fields = {
            config.E_WEEKLY_HOURS:  round(weekly_h, 1),
            config.E_MONTHLY_HOURS: round(monthly_h, 1),
            config.E_OVERLOADED:    overloaded,
        }
        cmd = [
            "lark-cli", "base", "+record-upsert",
            "--base-token", self.base_token,
            "--table-id",   config.EMPLOYEES_TABLE,
            "--record-id",  employee_record_id,
            "--as", "user",
            "--json", json.dumps(fields, ensure_ascii=False),
        ]
        _run(cmd)
        log.info(
            f"update_employee_hours: rec={employee_record_id} "
            f"weekly={weekly_h}h monthly={monthly_h}h overloaded={overloaded}"
        )
        return True
