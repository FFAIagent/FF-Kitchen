import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta
from handlers.presentation import handle_post_presentation
from handlers.reminder import _is_yesterday

def test_is_yesterday():
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert _is_yesterday(yesterday) is True

def test_sends_card_when_pres_was_yesterday_and_not_sent():
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    job = {
        "record_id": "recJOB1",
        "fields": {
            "fldJQ9yhx0": yesterday,    # Client Presentation Date = yesterday
            "fld4zp29Z7": False,         # Post-Presentation Card Sent = false
            "fld6elh0J7": [{"text": "Grab Ramadan"}],
            "fld7MDHHJN": [{"id": "recCLIENT1"}],
            "fldylh3KLO": [{"id": "ou_account1"}],
        }
    }
    im = MagicMock()
    base = MagicMock()
    handle_post_presentation(job, base=base, im=im, roster=[], chat_ids={})
    im.send_post_pres_card.assert_called_once()
    base.update_record.assert_called_once_with("recJOB1", {"fld4zp29Z7": True})

def test_skips_if_card_already_sent():
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    job = {
        "record_id": "recJOB1",
        "fields": {
            "fldJQ9yhx0": yesterday,
            "fld4zp29Z7": True,  # already sent
            "fld6elh0J7": [{"text": "Grab Ramadan"}],
            "fld7MDHHJN": [],
            "fldylh3KLO": [{"id": "ou_account1"}],
        }
    }
    im = MagicMock()
    base = MagicMock()
    handle_post_presentation(job, base=base, im=im, roster=[], chat_ids={})
    im.send_post_pres_card.assert_not_called()

def test_skips_if_pres_date_not_yesterday():
    future = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
    job = {
        "record_id": "recJOB1",
        "fields": {
            "fldJQ9yhx0": future,
            "fld4zp29Z7": False,
            "fld6elh0J7": [{"text": "Grab Ramadan"}],
            "fld7MDHHJN": [],
            "fldylh3KLO": [{"id": "ou_account1"}],
        }
    }
    im = MagicMock()
    base = MagicMock()
    handle_post_presentation(job, base=base, im=im, roster=[], chat_ids={})
    im.send_post_pres_card.assert_not_called()
