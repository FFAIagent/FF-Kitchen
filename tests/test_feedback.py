# tests/test_feedback.py
import pytest
from unittest.mock import MagicMock
from handlers.feedback import (
    should_ask_supervisor, should_ask_ecd,
    compute_speed_index, classify_speed_trend
)
from datetime import date, timedelta


def make_done_job(actual_hours=3.0, days_since_done=3):
    done_date = (date.today() - timedelta(days=days_since_done)).strftime("%Y-%m-%d")
    return {
        "record_id": "recJOB1",
        "fields": {
            "fldxhKL0x0": "DONE",
            "fldF3smRP5": actual_hours,
            "fldOxFaNTn": done_date,  # using Last Agent Sync as proxy for done date
        }
    }


def test_should_ask_supervisor_after_3_days():
    job = make_done_job(days_since_done=3)
    assert should_ask_supervisor(job) is True


def test_should_not_ask_supervisor_before_3_days():
    job = make_done_job(days_since_done=1)
    assert should_ask_supervisor(job) is False


def test_should_ask_ecd_after_7_days():
    job = make_done_job(days_since_done=7)
    assert should_ask_ecd(job) is True


def test_should_not_ask_ecd_before_7_days():
    job = make_done_job(days_since_done=5)
    assert should_ask_ecd(job) is False


def test_compute_speed_index_all_normal():
    ratings = ["Normal", "Normal", "Normal"]
    assert compute_speed_index(ratings) == pytest.approx(1.0)


def test_compute_speed_index_all_fast():
    ratings = ["Fast", "Fast", "Fast"]
    assert compute_speed_index(ratings) == pytest.approx(0.85)


def test_compute_speed_index_mixed_recent_weighted():
    # Recent ratings count 2x — recent Fast pulls index down
    ratings = ["Slow", "Slow", "Normal", "Fast", "Fast"]
    index = compute_speed_index(ratings)
    assert index < 1.0  # Fast recent ratings dominate


def test_classify_speed_trend_getting_faster():
    assert classify_speed_trend([0.9, 0.85, 0.82]) == "Getting Faster"


def test_classify_speed_trend_stable():
    assert classify_speed_trend([1.0, 0.95, 1.05]) == "Stable"


def test_classify_speed_trend_getting_slower():
    assert classify_speed_trend([1.0, 1.1, 1.2]) == "Getting Slower"
