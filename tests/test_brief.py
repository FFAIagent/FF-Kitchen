import pytest
from unittest.mock import MagicMock, call
from handlers.brief import handle_brief_announced

def make_job(announced=False, approved=True, team="Team Yodha",
             art=None, copy=None, title="Nike AO"):
    return {
        "record_id": "recJOB1",
        "fields": {
            "fld7PcmubU": announced,           # Brief Announced
            "fld5ci4q1p": "Approved" if approved else "Pending",
            "fldDXtWPj0": [{"text": team}] if team else [],
            "fld6elh0J7": [{"text": title}],
            "fldEX4xvDL": [{"id": "recART1"}] if art else [],   # Art Assigned
            "fldqZGdn7Z": [],
            "fldUFuqlPa": [],
            "fldE5yJTeM": [],
            "fldc8ikiB1": [],
            "fldrM1lwar": [],
            "fldH4QtERK": [{"id": "recPM1"}],   # PM PIC
            "fldFcsIm6z": None,   # 1st Internal Review Date
            "fldJQ9yhx0": None,   # Client Presentation Date
            "fldHwV7ihE": [{"text": "https://doc.link"}],
        }
    }

def make_context(art_open_id="ou_art", pm_open_id="ou_pm", chat_id="oc_team"):
    base = MagicMock()
    base.update_record = MagicMock(return_value=True)
    base.get_roster = MagicMock(return_value=[])
    im = MagicMock()
    roster = [
        {"record_id": "recART1", "fields": {"fldFrxViIu": art_open_id, "fldLy0sa0j": "Yodha", "fld0eDLpb8": ["Art"]}},
        {"record_id": "recPM1",  "fields": {"fldFrxViIu": pm_open_id,  "fldLy0sa0j": "Billie", "fld0eDLpb8": ["PM"]}},
    ]
    chat_ids = {"Team Yodha": chat_id}
    return dict(base=base, im=im, roster=roster, chat_ids=chat_ids)

def test_skip_if_already_announced():
    job = make_job(announced=True)
    ctx = make_context()
    handle_brief_announced(job, **ctx)
    ctx["im"].send_group_text.assert_not_called()

def test_skip_if_not_approved():
    job = make_job(approved=False)
    ctx = make_context()
    handle_brief_announced(job, **ctx)
    ctx["im"].send_group_text.assert_not_called()

def test_sends_group_message_when_announced(mocker):
    job = make_job(announced=False, approved=True)
    ctx = make_context()
    handle_brief_announced(job, **ctx)
    ctx["im"].send_group_text.assert_called_once_with("oc_team", mocker.ANY)

def test_sets_brief_announced_true():
    job = make_job(announced=False, approved=True)
    ctx = make_context()
    handle_brief_announced(job, **ctx)
    # The last call to update_record should set Brief Announced = True
    calls = ctx["base"].update_record.call_args_list
    assert any(c == call("recJOB1", {"fld7PcmubU": True}) for c in calls)
