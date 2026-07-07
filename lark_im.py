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

    def send_hours_card(
        self,
        open_id: str,
        job_title: str,
        discipline: str,
        record_id: str,
    ) -> dict:
        """Ask a team member how many hours they spent on a completed job.

        Sends a card with hour-bucket buttons. Each button POSTs back to the
        webhook with action=log_hours, record_id, discipline, and hours.
        """
        rec_enc = urllib.parse.quote(record_id)
        dis_enc = urllib.parse.quote(discipline)

        def _h_btn(label: str, hours: str) -> dict:
            return self._button(
                label,
                _action_url({
                    "action": "log_hours",
                    "record_id": rec_enc,
                    "discipline": dis_enc,
                    "hours": hours,
                }),
                "default",
            )

        card = {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": (
                            f"**Hours Log Request**\n\n"
                            f"Job: **{job_title}**\n"
                            f"Role: **{discipline}**\n\n"
                            f"How many hours did you spend on this job in total?"
                        ),
                        "tag": "lark_md",
                    },
                },
                {
                    "actions": [
                        _h_btn("1h",  "1"),
                        _h_btn("2h",  "2"),
                        _h_btn("4h",  "4"),
                        _h_btn("6h",  "6"),
                        _h_btn("8h",  "8"),
                        _h_btn("10h", "10"),
                    ],
                    "tag": "action",
                },
                {
                    "actions": [
                        _h_btn("12h", "12"),
                        _h_btn("16h", "16"),
                        _h_btn("20h", "20"),
                        _h_btn("24h", "24"),
                        _h_btn("32h", "32"),
                        self._button(
                            "Skip",
                            _action_url({"action": "log_hours_skip"}),
                            "default",
                        ),
                    ],
                    "tag": "action",
                },
            ],
        }
        return self._send_card(open_id, card)

    def send_daily_hours_card(
        self,
        open_id: str,
        job_title: str,
        discipline: str,
        record_id: str,
    ) -> dict:
        """Ask a team member how many hours they spent on a job yesterday.

        Daily morning check-in (09:00 WIB). Different from send_hours_card which
        asks for total hours at job completion. Here we ask about yesterday only.
        Action=log_daily_hours so webhook handles it separately (writes to Timesheet
        + increments DAPUR Actual Hours + updates Employee weekly/monthly totals).
        open_id is embedded in the URL so the webhook knows who answered.
        """
        rec_enc = urllib.parse.quote(record_id)
        dis_enc = urllib.parse.quote(discipline)
        oid_enc = urllib.parse.quote(open_id)

        def _h_btn(label: str, hours: str) -> dict:
            return self._button(
                label,
                _action_url({
                    "action": "log_daily_hours",
                    "record_id": rec_enc,
                    "discipline": dis_enc,
                    "hours": hours,
                    "open_id": oid_enc,
                }),
                "default",
            )

        card = {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": (
                            f"⏱️ **Daily Hours Check-in**\n\n"
                            f"Job: **{job_title}**\n"
                            f"Role: **{discipline}**\n\n"
                            f"Yesterday, how many hours did you spend on this job?"
                        ),
                        "tag": "lark_md",
                    },
                },
                {
                    "actions": [
                        _h_btn("0.5h", "0.5"),
                        _h_btn("1h",   "1"),
                        _h_btn("2h",   "2"),
                        _h_btn("3h",   "3"),
                        _h_btn("4h",   "4"),
                        _h_btn("5h",   "5"),
                    ],
                    "tag": "action",
                },
                {
                    "actions": [
                        _h_btn("6h",  "6"),
                        _h_btn("7h",  "7"),
                        _h_btn("8h",  "8"),
                        _h_btn("10h", "10"),
                        self._button(
                            "0 — none",
                            _action_url({
                                "action": "log_daily_hours",
                                "record_id": rec_enc,
                                "discipline": dis_enc,
                                "hours": "0",
                                "open_id": oid_enc,
                            }),
                            "default",
                        ),
                    ],
                    "tag": "action",
                },
            ],
        }
        return self._send_card(open_id, card)

    def send_client_revision_card(
        self,
        open_id: str,
        job_title: str,
        revision_count: int,
        record_id: str,
    ) -> dict:
        """Send a client revision notification card to Account PIC.

        Fires when Account PIC clicks 'Needs Revision' on the post-presentation
        card. Includes a direct link to the Revision Form.
        """
        REVISION_FORM_URL = (
            "https://fcn.sg.larksuite.com/share/base/shrlgo316eNoyhDixv1WkN7EdRe"
        )
        record_url = (
            f"https://fcn.sg.larksuite.com/base/{config.BASE_TOKEN}"
            f"?table={config.DAPUR_TABLE}&record={record_id}"
        )
        card = {
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": (
                            f"**🔄 Client Revision #{revision_count}**\n\n"
                            f"Job: **{job_title}**\n\n"
                            f"The client has requested revisions. Please submit the "
                            f"revision details using the form — the team will be "
                            f"notified once it's submitted."
                        ),
                        "tag": "lark_md",
                    },
                },
                {
                    "actions": [
                        self._button(
                            "📝 Submit Revision Details",
                            REVISION_FORM_URL,
                            "primary",
                        ),
                        self._button(
                            "Open Job Record",
                            record_url,
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
