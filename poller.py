from __future__ import annotations
import logging
from lark_base import BaseClient
from lark_im import IMClient

log = logging.getLogger(__name__)

class Poller:
    def __init__(self):
        self.base = BaseClient()
        self.im = IMClient()
        # Handlers registered in scheduler.py after all modules import
        self._handlers: list = []

    def register(self, handler_fn) -> None:
        self._handlers.append(handler_fn)

    def run_once(self) -> None:
        log.info("Poll cycle starting")
        jobs = self.base.list_active_jobs()
        roster = self.base.get_roster()
        chat_ids = self.base.get_chat_ids() if hasattr(self.base, 'get_chat_ids') else {}
        # Pre-fetch Clients once per poll cycle so handle_client_link_bridge
        # doesn't make a separate API call per job.
        clients = self.base.get_clients() if hasattr(self.base, 'get_clients') else []
        context = {"roster": roster, "chat_ids": chat_ids, "base": self.base, "im": self.im, "clients": clients}
        for job in jobs:
            for handler in self._handlers:
                try:
                    handler(job, **context)
                except Exception as e:
                    log.error(f"Handler {getattr(handler, '__name__', repr(handler))} failed on {job['record_id']}: {e}")
            try:
                self.base.update_last_sync(job["record_id"])
            except Exception as e:
                log.error(f"Sync update failed on {job['record_id']}: {e}")
        log.info(f"Poll cycle complete: {len(jobs)} jobs processed")
