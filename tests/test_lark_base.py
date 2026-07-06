"""Tests for lark_base.BaseClient — subprocess/lark-cli architecture."""
import json
import pytest
from unittest.mock import MagicMock, patch


def test_list_active_jobs_excludes_done_and_on_hold(mock_base_client):
    """list_active_jobs returns only non-DONE, non-ON-HOLD records."""
    jobs = mock_base_client.list_active_jobs()
    statuses = [j["fields"].get("Account Status") for j in jobs]
    assert "DONE" not in statuses
    assert "ON HOLD" not in statuses


def test_update_record_calls_api_with_correct_fields(mock_base_client, mocker):
    """update_record sends patch with correct field IDs."""
    mock_patch = mocker.patch.object(mock_base_client, "_patch_record", return_value=True)
    mock_base_client.update_record("recXXX", {"fld7PcmubU": True})
    mock_patch.assert_called_once_with("tblpNqjumvstYOnj", "recXXX", {"fld7PcmubU": True})


def test_get_roster_returns_all_members(mock_base_client):
    """get_roster returns all Team Roster records with Lark Open ID."""
    roster = mock_base_client.get_roster()
    assert len(roster) > 0
    assert all("Lark Open ID" in r["fields"] or "fldFrxViIu" in r["fields"] for r in roster)


def test_update_roster_record_only_writes_if_changed(mock_base_client, mocker):
    """update_roster_record skips write if value unchanged."""
    mock_patch = mocker.patch.object(mock_base_client, "_patch_record", return_value=True)
    # Same value — should skip
    mock_base_client.update_roster_record("recXXX", "Current Jobs Text", "Nike AO", current_value="Nike AO")
    mock_patch.assert_not_called()
    # Different value — should write
    mock_base_client.update_roster_record("recXXX", "Current Jobs Text", "Nike AO · Grab", current_value="Nike AO")
    mock_patch.assert_called_once()


def test_list_records_pagination(mocker):
    """_list_records handles has_more pagination with offset increments."""
    from lark_base import BaseClient

    client = BaseClient.__new__(BaseClient)
    client.base_token = "HH0qb3myka5wPmsyInGlH6l3grd"

    page1 = {
        "code": 0,
        "data": {
            "items": [{"record_id": "rec1", "fields": {"Status": "IN PROGRESS"}}],
            "has_more": True,
        },
    }
    page2 = {
        "code": 0,
        "data": {
            "items": [{"record_id": "rec2", "fields": {"Status": "DONE"}}],
            "has_more": False,
        },
    }

    mock_run = mocker.patch("lark_base._run", side_effect=[page1, page2])
    records = client._list_records("tblpNqjumvstYOnj", page_size=1)

    assert len(records) == 2
    assert records[0]["record_id"] == "rec1"
    assert records[1]["record_id"] == "rec2"
    assert mock_run.call_count == 2

    # Second call should have offset=1
    second_call_cmd = mock_run.call_args_list[1][0][0]
    offset_idx = second_call_cmd.index("--offset")
    assert second_call_cmd[offset_idx + 1] == "1"


def test_patch_record_runs_upsert_command(mocker):
    """_patch_record constructs the correct lark-cli command."""
    from lark_base import BaseClient

    client = BaseClient.__new__(BaseClient)
    client.base_token = "HH0qb3myka5wPmsyInGlH6l3grd"

    mock_run = mocker.patch("lark_base._run", return_value={"code": 0, "data": {}})
    client._patch_record("tblpNqjumvstYOnj", "recABC", {"fld7PcmubU": True})

    cmd = mock_run.call_args[0][0]
    assert "+record-upsert" in cmd
    assert "--record-id" in cmd
    assert "recABC" in cmd
    assert "--as" in cmd
    assert "user" in cmd
    # Verify the --json flag carries the fields
    json_idx = cmd.index("--json")
    payload = json.loads(cmd[json_idx + 1])
    assert payload == {"fld7PcmubU": True}


def test_get_chat_ids_returns_dict(mocker):
    """get_chat_ids returns a {team_name: chat_id} dict."""
    from lark_base import BaseClient

    client = BaseClient.__new__(BaseClient)
    client.base_token = "HH0qb3myka5wPmsyInGlH6l3grd"

    mocker.patch.object(
        client,
        "_list_records",
        return_value=[
            {"record_id": "recQ1", "fields": {"fld2YQOPp6": "Creative Team A", "fldIZIhz9f": "oc_abc123"}},
            {"record_id": "recQ2", "fields": {"fld2YQOPp6": "Creative Team B", "fldIZIhz9f": "oc_def456"}},
        ],
    )

    result = client.get_chat_ids()
    assert result == {"Creative Team A": "oc_abc123", "Creative Team B": "oc_def456"}


def test_create_feedback_record_no_record_id(mocker):
    """create_feedback_record calls +record-upsert without --record-id."""
    from lark_base import BaseClient

    client = BaseClient.__new__(BaseClient)
    client.base_token = "HH0qb3myka5wPmsyInGlH6l3grd"

    mock_run = mocker.patch("lark_base._run", return_value={"code": 0, "data": {}})
    client.create_feedback_record({"Score": 5, "Note": "Great"})

    cmd = mock_run.call_args[0][0]
    assert "+record-upsert" in cmd
    assert "--record-id" not in cmd
    json_idx = cmd.index("--json")
    payload = json.loads(cmd[json_idx + 1])
    assert payload["Score"] == 5
