# tests/test_scheduler.py
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import pytz


def test_in_polling_window_during_hours():
    """in_polling_window() returns True during 08:00–21:59 WIB."""
    import scheduler
    wib = pytz.timezone("Asia/Jakarta")
    mock_dt = wib.localize(datetime(2026, 7, 6, 10, 0, 0))  # 10:00 WIB
    with patch("scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_dt
        assert scheduler.in_polling_window() is True


def test_in_polling_window_before_start():
    """in_polling_window() returns False before 08:00 WIB."""
    import scheduler
    wib = pytz.timezone("Asia/Jakarta")
    mock_dt = wib.localize(datetime(2026, 7, 6, 6, 0, 0))  # 06:00 WIB
    with patch("scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_dt
        assert scheduler.in_polling_window() is False


def test_in_polling_window_after_end():
    """in_polling_window() returns False at 22:00 WIB."""
    import scheduler
    wib = pytz.timezone("Asia/Jakarta")
    mock_dt = wib.localize(datetime(2026, 7, 6, 22, 0, 0))  # 22:00 WIB
    with patch("scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_dt
        assert scheduler.in_polling_window() is False


def test_poll_job_skips_outside_window():
    """poll_job() does not call poller.run_once() outside polling hours."""
    import scheduler
    poller = MagicMock()
    with patch("scheduler.in_polling_window", return_value=False):
        scheduler.poll_job(poller)
    poller.run_once.assert_not_called()


def test_poll_job_runs_inside_window():
    """poll_job() calls poller.run_once() inside polling hours."""
    import scheduler
    poller = MagicMock()
    poller.base.list_active_jobs.return_value = []
    poller.base.get_roster.return_value = []
    poller.base.list_feedback_records.return_value = []
    with patch("scheduler.in_polling_window", return_value=True):
        scheduler.poll_job(poller)
    poller.run_once.assert_called_once()
