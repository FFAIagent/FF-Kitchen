import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta
import pytz
from handlers.reminder import handle_deadline_reminders, _is_tomorrow

WIB = pytz.timezone("Asia/Jakarta")

def test_is_tomorrow_true():
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    assert _is_tomorrow(tomorrow) is True

def test_is_tomorrow_false_today():
    today = date.today().strftime("%Y-%m-%d")
    assert _is_tomorrow(today) is False

def test_is_tomorrow_false_past():
    past = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert _is_tomorrow(past) is False

def test_sends_card_when_milestone_is_tomorrow_and_flag_false():
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    job = {
        "record_id": "recJOB1",
        "fields": {
            "fld6elh0J7": [{"text": "Nike AO"}],
            "fldFcsIm6z": tomorrow,              # 1st Internal Review Date = tomorrow
            "fld8gu09fN": False,                 # 1st Review Reminder Sent = false
            "fldZvsitPG": None,                  # Job Brief Date = null
            "fldILWcToS": False,
            "fldJQ9yhx0": None,
            "fldTECKIZi": False,
            "fldD9v82lp": None,
            "fldBOfqiLk": False,
            "fldEX4xvDL": [{"id": "recART1"}],
            "fldqZGdn7Z": [],
            "fldUFuqlPa": [],
            "fldE5yJTeM": [],
            "fldc8ikiB1": [],
            "fldrM1lwar": [],
            "fldH4QtERK": [{"id": "recPM1"}],
        }
    }
    im = MagicMock()
    base = MagicMock()
    roster = [
        {"record_id": "recART1", "fields": {"fldFrxViIu": "ou_art", "fldLy0sa0j": "Yodha"}},
        {"record_id": "recPM1",  "fields": {"fldFrxViIu": "ou_pm",  "fldLy0sa0j": "Billie"}},
    ]
    handle_deadline_reminders(job, base=base, im=im, roster=roster, chat_ids={})
    im.send_reminder_card.assert_called_once()
    base.update_record.assert_called_once_with("recJOB1", {"fld8gu09fN": True})

def test_skips_when_flag_already_set():
    tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    job = {
        "record_id": "recJOB1",
        "fields": {
            "fld6elh0J7": [{"text": "Nike AO"}],
            "fldFcsIm6z": tomorrow,
            "fld8gu09fN": True,  # already sent
            "fldZvsitPG": None, "fldILWcToS": False,
            "fldJQ9yhx0": None, "fldTECKIZi": False,
            "fldD9v82lp": None, "fldBOfqiLk": False,
            "fldEX4xvDL": [{"id": "recART1"}],
            "fldqZGdn7Z": [], "fldUFuqlPa": [], "fldE5yJTeM": [],
            "fldc8ikiB1": [], "fldrM1lwar": [], "fldH4QtERK": [],
        }
    }
    im = MagicMock()
    base = MagicMock()
    handle_deadline_reminders(job, base=base, im=im, roster=[], chat_ids={})
    im.send_reminder_card.assert_not_called()
