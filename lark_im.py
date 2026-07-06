"""Lark IM client using lark-cli subprocess calls with user auth.

All interactive cards use Lark Card Kit v1 schema (config/elements structure).
Button actions use URL links to the local Flask action server.
"""
from __future__ import annotations

import json
import subprocess
import urllib.parse
from typing import Any


_IM_CMD = ["lark-cli", "im", "+messages-send", "--as", "user"]
_ACTION_BASE = "http://localhost:5001/action"


def _run(cmd: list[str]) -> dict:
    """Run a lark-cli command and return parsed JSON output."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"lark-cli error (exit {result.returncode}): {result.stderr.strip()}"
        )
    try:
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        return {"raw": result.stdout}


def _action_url(params: dict[str, str]) -> str:
    """Build a localhost action URL with query parameters."""
    return f"{_ACTION_BASE}?{urllib.parse.urlencode(params)}"


class IMClient:
    """Send text messages and interactive cards via lark-cli."""

    # ------------------------------------------------------------------
    # Plain text senders
    # ------------------------------------------------------------------

    def send_text(self, open_id: str, text: str) -> dict:
        """Send a plain text DM to a user by open_id."""
        cmd = [*_IM_CMD, "--user-id", open_id, "--text", text]
        return _run(cmd)

    def send_group_text(self, chat_id: str, text: str) -> dict:
        """Send a plain text message to a group chat."""
        cmd = [*_IM_CMD, "--chat-id", chat_id, "--text", text]
        return _run(cmd)

    # ------------------------------------------------------------------
    # Interactive card helpers
    # ------------------------------------------------------------------

    def _send_card(self, open_id: str, card: dict) -> dict:
        """Send an interactive card DM to a user by open_id."""
        content = json.dumps(card, ensure_ascii=False)
        cmd = [*_IM_CMD, "--user-id", open_id, "--msg-type", "interactive", "--content", content]
        return _run(cmd)

    def _button(self, label: str, url: str, btn_type: str = "default") -> dict:
        """Build a v1 card button element with a URL action."""
        return {
            "tag": "button",
            "text": {"content": label, "tag": "plain_text"},
            "type": btn_type,
            "url": url,
        }

    # ------------------------------------------------------------------
    # Card senders
    # ------------------------------------------------------------------

    def send_reminder_card(
        self,
        open_id: str,
        job_title: str,
        stage: str,
        date: str,
        record_id: str,
    ) -> dict:
        """Send a deadline reminder card with Got It / Request Extension buttons."""
        card = {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": (
                            f"**Deadline Reminder**\n\n"
                            f"Job: **{job_title}**\n"
                            f"Stage: **{stage}**\n"
                            f"Date: **{date}**\n\n"
                            f"Please confirm or request an extension."
                        ),
                        "tag": "lark_md",
                    },
                },
                {
                    "actions": [
                        self._button(
                            "Got it",
                            _action_url({"action": "got_it", "record_id": record_id}),
                            "primary",
                        ),
                        self._button(
                            "Request Extension",
                            _action_url({
                                "action": "request_extension",
                                "record_id": record_id,
                                "stage": stage,
                            }),
                            "default",
                        ),
                    ],
                    "tag": "action",
                },
            ],
        }
        return self._send_card(open_id, card)

    def send_post_pres_card(
        self,
        open_id: str,
        job_title: str,
        client_name: str,
        pres_date: str,
        record_id: str,
    ) -> dict:
        """Send a post-presentation approval card."""
        card = {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": (
                            f"**Post-Presentation Check**\n\n"
                            f"Job: **{job_title}**\n"
                            f"Client: **{client_name}**\n"
                            f"Presented: **{pres_date}**\n\n"
                            f"Was the presentation approved by the client?"
                        ),
                        "tag": "lark_md",
                    },
                },
                {
                    "actions": [
                        self._button(
                            "Approved",
                            _action_url({"action": "pres_approved", "record_id": record_id}),
                            "primary",
                        ),
                        self._button(
                            "Needs Revision",
                            _action_url({"action": "pres_revision", "record_id": record_id}),
                            "danger",
                        ),
                    ],
                    "tag": "action",
                },
            ],
        }
        return self._send_card(open_id, card)

    def send_feedback_card(
        self,
        open_id: str,
        job_title: str,
        output_type: str,
        estimated_h: float,
        actual_h: float,
        person_name: str,
        role: str,
    ) -> dict:
        """Send a speed calibration feedback card to the supervisor."""
        job_enc = urllib.parse.quote(job_title)
        person_enc = urllib.parse.quote(person_name)

        card = {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": (
                            f"**Speed Calibration**\n\n"
                            f"**{person_name}** ({role}) completed **{job_title}**\n"
                            f"Output type: {output_type}\n"
                            f"Estimated: **{estimated_h}h** | Actual: **{actual_h}h**\n\n"
                            f"For their level, how was their speed?"
                        ),
                        "tag": "lark_md",
                    },
                },
                {
                    "actions": [
                        self._button(
                            "Fast",
                            _action_url({
                                "action": "feedback_fast",
                                "job": job_enc,
                                "person": person_enc,
                            }),
                            "primary",
                        ),
                        self._button(
                            "Normal",
                            _action_url({
                                "action": "feedback_normal",
                                "job": job_enc,
                                "person": person_enc,
                            }),
                            "default",
                        ),
                        self._button(
                            "Slow",
                            _action_url({
                                "action": "feedback_slow",
                                "job": job_enc,
                                "person": person_enc,
                            }),
                            "danger",
                        ),
                        self._button(
                            "Skip",
                            _action_url({"action": "feedback_skip"}),
                            "default",
                        ),
                    ],
                    "tag": "action",
                },
            ],
        }
        return self._send_card(open_id, card)

    def send_pm_extension_alert(
        self,
        pm_open_id: str,
        requester_name: str,
        job_title: str,
        stage: str,
        current_date: str,
        record_url: str,
    ) -> dict:
        """Send a plain text DM to the PM when someone requests a deadline extension."""
        text = (
            f"Extension Request — {job_title}\n"
            f"{requester_name} needs more time on {stage} (currently {current_date})\n"
            f"Update the date here: {record_url}"
        )
        return self.send_text(pm_open_id, text)
