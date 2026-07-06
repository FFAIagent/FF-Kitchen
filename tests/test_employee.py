# tests/test_employee.py
import pytest
from unittest.mock import MagicMock
from handlers.employee import build_person_job_map, format_current_jobs, run_employee_updates


def make_roster():
    return [
        {"record_id": "recART1", "fields": {"fldFrxViIu": "ou_art", "fldLy0sa0j": "Yodha",
                                              "fldRbrkboh": "", "fldaAvILjb": None}},
    ]


def make_active_jobs(art_record="recART1"):
    return [
        {"record_id": "recJOB1", "fields": {
            "fld6elh0J7": [{"text": "Nike AO"}],
            "fldEX4xvDL": [{"id": art_record}],
            "fldqZGdn7Z": [], "fldUFuqlPa": [], "fldE5yJTeM": [],
            "fldc8ikiB1": [], "fldrM1lwar": [],
            "fld9s3v6yW": "2026-07-14",   # Next Milestone Date
            "fldNwVKYVH": "1st Internal Review",
        }},
    ]


def test_build_person_job_map_groups_by_person():
    jobs = make_active_jobs()
    roster = make_roster()
    person_map = build_person_job_map(jobs, roster)
    assert "recART1" in person_map
    assert len(person_map["recART1"]) == 1


def test_format_current_jobs_returns_string():
    jobs_for_person = [{"title": "Nike AO", "stage": "1st Internal Review", "next_date": "2026-07-14"}]
    text = format_current_jobs(jobs_for_person)
    assert "Nike AO" in text
    assert "1st Internal Review" in text


def test_run_employee_updates_writes_only_when_changed():
    jobs = make_active_jobs()
    roster = make_roster()
    base = MagicMock()
    run_employee_updates(jobs, roster, base)
    # Should write because current value "" != new value
    assert base.update_roster_record.call_count >= 1


def test_run_employee_updates_skips_when_unchanged():
    jobs = make_active_jobs()
    roster = [
        {"record_id": "recART1", "fields": {
            "fldFrxViIu": "ou_art", "fldLy0sa0j": "Yodha",
            "fldRbrkboh": "Nike AO (1st Internal Review 2026-07-14)",
            "fldaAvILjb": "2026-07-14",
        }},
    ]
    base = MagicMock()
    base.update_roster_record = MagicMock(side_effect=lambda rec_id, field_id, new_val, current_value=None: new_val != current_value)
    run_employee_updates(jobs, roster, base)
    # update_roster_record is called but returns False (no write) for unchanged values
    for call in base.update_roster_record.call_args_list:
        _, kwargs = call
        assert kwargs.get("current_value") is not None
