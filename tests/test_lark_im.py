"""Tests for lark_im.IMClient — mocks subprocess.run to avoid real lark-cli calls."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from lark_im import IMClient


@pytest.fixture
def client():
    """Return an IMClient without calling __init__ subprocess setup."""
    return IMClient()


def _mock_run(mocker) -> MagicMock:
    """Patch subprocess.run in lark_im to return a successful empty response."""
    mock = mocker.patch("lark_im.subprocess.run")
    mock.return_value = MagicMock(
        returncode=0,
        stdout='{"code": 0}',
        stderr="",
    )
    return mock


# ------------------------------------------------------------------
# send_text
# ------------------------------------------------------------------

def test_send_text_uses_user_id(client, mocker):
    mock = _mock_run(mocker)
    client.send_text("ou_abc", "Hello team")
    cmd = mock.call_args[0][0]
    assert "--user-id" in cmd
    assert "ou_abc" in cmd
    assert "--text" in cmd
    assert "Hello team" in cmd


def test_send_text_not_chat_id(client, mocker):
    mock = _mock_run(mocker)
    client.send_text("ou_abc", "Hello")
    cmd = mock.call_args[0][0]
    assert "--chat-id" not in cmd


# ------------------------------------------------------------------
# send_group_text
# ------------------------------------------------------------------

def test_send_group_text_uses_chat_id(client, mocker):
    mock = _mock_run(mocker)
    client.send_group_text("oc_chat123", "Brief in!")
    cmd = mock.call_args[0][0]
    assert "--chat-id" in cmd
    assert "oc_chat123" in cmd
    assert "--text" in cmd
    assert "Brief in!" in cmd


def test_send_group_text_not_user_id(client, mocker):
    mock = _mock_run(mocker)
    client.send_group_text("oc_chat123", "Hello")
    cmd = mock.call_args[0][0]
    assert "--user-id" not in cmd


# ------------------------------------------------------------------
# send_reminder_card
# ------------------------------------------------------------------

def test_reminder_card_uses_interactive_msg_type(client, mocker):
    mock = _mock_run(mocker)
    client.send_reminder_card("ou_abc", "Nike AO", "1st Internal Review", "2026-07-14", "recXXX")
    cmd = mock.call_args[0][0]
    assert "--msg-type" in cmd
    assert "interactive" in cmd


def test_reminder_card_contains_job_title(client, mocker):
    mock = _mock_run(mocker)
    client.send_reminder_card("ou_abc", "Nike AO", "1st Internal Review", "2026-07-14", "recXXX")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "Nike AO" in content


def test_reminder_card_contains_stage(client, mocker):
    mock = _mock_run(mocker)
    client.send_reminder_card("ou_abc", "Nike AO", "1st Internal Review", "2026-07-14", "recXXX")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "1st Internal Review" in content


def test_reminder_card_contains_date(client, mocker):
    mock = _mock_run(mocker)
    client.send_reminder_card("ou_abc", "Nike AO", "1st Internal Review", "2026-07-14", "recXXX")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "2026-07-14" in content


def test_reminder_card_got_it_action_url(client, mocker):
    mock = _mock_run(mocker)
    client.send_reminder_card("ou_abc", "Nike AO", "1st Internal Review", "2026-07-14", "recXXX")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "got_it" in content
    assert "recXXX" in content


def test_reminder_card_extension_action_url(client, mocker):
    mock = _mock_run(mocker)
    client.send_reminder_card("ou_abc", "Nike AO", "1st Internal Review", "2026-07-14", "recXXX")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "request_extension" in content


# ------------------------------------------------------------------
# send_post_pres_card
# ------------------------------------------------------------------

def test_post_pres_card_uses_interactive(client, mocker):
    mock = _mock_run(mocker)
    client.send_post_pres_card("ou_abc", "Grab Ramadan", "Grab Indonesia", "2026-07-18", "recXXX")
    cmd = mock.call_args[0][0]
    assert "interactive" in cmd


def test_post_pres_card_has_approved_button(client, mocker):
    mock = _mock_run(mocker)
    client.send_post_pres_card("ou_abc", "Grab Ramadan", "Grab Indonesia", "2026-07-18", "recXXX")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "Approved" in content


def test_post_pres_card_has_revision_button(client, mocker):
    mock = _mock_run(mocker)
    client.send_post_pres_card("ou_abc", "Grab Ramadan", "Grab Indonesia", "2026-07-18", "recXXX")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "Revision" in content


def test_post_pres_card_approved_url(client, mocker):
    mock = _mock_run(mocker)
    client.send_post_pres_card("ou_abc", "Grab Ramadan", "Grab Indonesia", "2026-07-18", "recXXX")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "pres_approved" in content
    assert "pres_revision" in content


# ------------------------------------------------------------------
# send_feedback_card
# ------------------------------------------------------------------

def test_feedback_card_uses_interactive(client, mocker):
    mock = _mock_run(mocker)
    client.send_feedback_card("ou_abc", "Nike AO", "Social Post", 3.0, 2.1, "Yodha", "Art Director")
    cmd = mock.call_args[0][0]
    assert "interactive" in cmd


def test_feedback_card_has_fast_button(client, mocker):
    mock = _mock_run(mocker)
    client.send_feedback_card("ou_abc", "Nike AO", "Social Post", 3.0, 2.1, "Yodha", "Art Director")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "Fast" in content


def test_feedback_card_has_normal_button(client, mocker):
    mock = _mock_run(mocker)
    client.send_feedback_card("ou_abc", "Nike AO", "Social Post", 3.0, 2.1, "Yodha", "Art Director")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "Normal" in content


def test_feedback_card_has_slow_button(client, mocker):
    mock = _mock_run(mocker)
    client.send_feedback_card("ou_abc", "Nike AO", "Social Post", 3.0, 2.1, "Yodha", "Art Director")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "Slow" in content


def test_feedback_card_action_urls(client, mocker):
    mock = _mock_run(mocker)
    client.send_feedback_card("ou_abc", "Nike AO", "Social Post", 3.0, 2.1, "Yodha", "Art Director")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "feedback_fast" in content
    assert "feedback_normal" in content
    assert "feedback_slow" in content
    assert "feedback_skip" in content


def test_feedback_card_person_in_url(client, mocker):
    mock = _mock_run(mocker)
    client.send_feedback_card("ou_abc", "Nike AO", "Social Post", 3.0, 2.1, "Yodha", "Art Director")
    cmd = mock.call_args[0][0]
    content_idx = cmd.index("--content") + 1
    content = cmd[content_idx]
    assert "Yodha" in content


# ------------------------------------------------------------------
# send_pm_extension_alert
# ------------------------------------------------------------------

def test_pm_alert_sends_plain_text(client, mocker):
    mock = _mock_run(mocker)
    client.send_pm_extension_alert(
        "ou_pm_001", "Yodha", "Nike AO", "1st Internal Review", "2026-07-14",
        "https://base.example.com/rec123"
    )
    cmd = mock.call_args[0][0]
    assert "--user-id" in cmd
    assert "ou_pm_001" in cmd
    assert "--text" in cmd


def test_pm_alert_contains_requester_name(client, mocker):
    mock = _mock_run(mocker)
    client.send_pm_extension_alert(
        "ou_pm_001", "Yodha", "Nike AO", "1st Internal Review", "2026-07-14",
        "https://base.example.com/rec123"
    )
    cmd = mock.call_args[0][0]
    text_idx = cmd.index("--text") + 1
    text = cmd[text_idx]
    assert "Yodha" in text
    assert "Nike AO" in text
    assert "1st Internal Review" in text
