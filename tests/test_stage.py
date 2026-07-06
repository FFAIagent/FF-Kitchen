import pytest
from unittest.mock import MagicMock
from handlers.stage import handle_stage_advance

def make_job(stage, revision_count=0, pm_record_id="recPM1"):
    return {
        "record_id": "recJOB1",
        "fields": {
            "fldNwVKYVH": stage,
            "fld0dWannS": revision_count,
            "fld6elh0J7": [{"text": "Nike AO"}],
            "fldH4QtERK": [{"id": pm_record_id}] if pm_record_id else [],
        }
    }

def make_ctx(pm_open_id="ou_pm"):
    base = MagicMock()
    im = MagicMock()
    roster = [{"record_id": "recPM1", "fields": {"fldFrxViIu": pm_open_id, "fldLy0sa0j": "Billie"}}]
    return dict(base=base, im=im, roster=roster, chat_ids={})

def test_advances_to_client_pres_when_revision_count_zero():
    job = make_job("1st Internal Review", revision_count=0)
    ctx = make_ctx()
    handle_stage_advance(job, **ctx)
    ctx["base"].update_record.assert_called_once_with("recJOB1", {"fldNwVKYVH": "Client Presentation"})

def test_dms_pm_when_revision_count_nonzero():
    job = make_job("1st Internal Review", revision_count=2)
    ctx = make_ctx()
    handle_stage_advance(job, **ctx)
    ctx["base"].update_record.assert_not_called()
    ctx["im"].send_text.assert_called_once()
    msg = ctx["im"].send_text.call_args[0][1]
    assert "Nike AO" in msg
    assert "Revision" in msg

def test_skips_non_review_stages():
    job = make_job("Briefing Scheduled", revision_count=0)
    ctx = make_ctx()
    handle_stage_advance(job, **ctx)
    ctx["base"].update_record.assert_not_called()
    ctx["im"].send_text.assert_not_called()

def test_handles_all_review_stage_variants():
    for stage in ["1st Internal Review", "2nd Internal Review", "3rd Internal Review", "Revision Internal Review"]:
        job = make_job(stage, revision_count=0)
        ctx = make_ctx()
        handle_stage_advance(job, **ctx)
        ctx["base"].update_record.assert_called_once_with("recJOB1", {"fldNwVKYVH": "Client Presentation"})
