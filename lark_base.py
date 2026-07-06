"""Lark Base client using lark-cli subprocess calls with user auth."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from typing import Any

import pytz

import config

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

    def _list_records(self, table_id: str, page_size: int = 200) -> list[dict]:
        """Fetch all records from a table using offset-based pagination."""
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
            data = _run(cmd)
            # lark-cli JSON envelope: {"code":0,"data":{"items":[...],"has_more":bool,...}}
            items = []
            has_more = False
            if isinstance(data, dict):
                inner = data.get("data", data)
                raw_items = inner.get("items", inner if isinstance(inner, list) else [])
                has_more = bool(inner.get("has_more", False))
                for item in raw_items:
                    record_id = item.get("record_id", "")
                    fields = item.get("fields", {})
                    items.append({"record_id": record_id, "fields": fields})
            elif isinstance(data, list):
                # Flat list response (no envelope)
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

    def list_active_jobs(self) -> list[dict]:
        """Return all DAPUR records where Account Status is not DONE or ON HOLD."""
        all_records = self._list_records(config.DAPUR_TABLE)
        return [
            r for r in all_records
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

    def create_feedback_record(self, fields: dict) -> bool:
        """Create a new record in the Feedback Log table."""
        return self._create_record(config.FEEDBACK_TABLE, fields)

    def list_feedback_records(self) -> list[dict]:
        """Return all Feedback Log records."""
        return self._list_records(config.FEEDBACK_TABLE)
