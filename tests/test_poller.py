import pytest
from unittest.mock import MagicMock, patch, call
from poller import Poller

@pytest.fixture
def mock_poller(mock_base_client, mocker):
    im = MagicMock()
    poller = Poller.__new__(Poller)
    poller.base = mock_base_client
    poller.im = im
    poller._handlers = []
    # Ensure get_chat_ids and update_last_sync are available
    if not hasattr(poller.base, 'get_chat_ids') or not callable(getattr(poller.base, 'get_chat_ids', None)):
        poller.base.get_chat_ids = MagicMock(return_value={})
    if not hasattr(poller.base, 'update_last_sync') or not callable(getattr(poller.base, 'update_last_sync', None)):
        poller.base.update_last_sync = MagicMock(return_value=True)
    return poller

def test_run_once_calls_all_handlers_for_each_job(mock_poller):
    handler_a = MagicMock()
    handler_b = MagicMock()
    mock_poller._handlers = [handler_a, handler_b]
    mock_poller.run_once()
    active_jobs = mock_poller.base.list_active_jobs()
    assert handler_a.call_count == len(active_jobs)
    assert handler_b.call_count == len(active_jobs)

def test_run_once_updates_last_sync(mock_poller, mocker):
    mock_sync = mocker.patch.object(mock_poller.base, "update_last_sync")
    mock_poller.run_once()
    active_jobs = mock_poller.base.list_active_jobs()
    assert mock_sync.call_count == len(active_jobs)

def test_run_once_continues_after_handler_exception(mock_poller):
    def failing_handler(job, **kw):
        raise RuntimeError("handler exploded")
    mock_poller._handlers = [failing_handler]
    # Should not raise — exceptions are swallowed per-job
    mock_poller.run_once()
