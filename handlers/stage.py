from __future__ import annotations
import logging
import config
from handlers.brief import _resolve_open_ids, _get_text

log = logging.getLogger(__name__)


def handle_stage_advance(job: dict, base, im, roster: list, **_) -> None:
    fields = job["fields"]
    stage = fields.get(config.F_STAGE_STATUS)
    if stage not in config.INTERNAL_REVIEW_STAGES:
        return

    revision_count = fields.get(config.F_REVISION_COUNT) or 0
    if isinstance(revision_count, float):
        revision_count = int(revision_count)

    job_title = _get_text(fields.get(config.F_JOB_TITLE))
    pm_links = fields.get(config.F_PM_PIC) or []
    pm_people = _resolve_open_ids(pm_links, roster)

    if revision_count == 0:
        base.update_record(job["record_id"], {config.F_STAGE_STATUS: config.STAGE_CLIENT_PRES})
        log.info(f"Auto-advanced {job['record_id']} ({job_title}) to Client Presentation")
    else:
        msg = (
            f"Revision flagged on {job_title}\n"
            f"Revision Count: {revision_count}\n"
            f"Please set the next Internal Review date in the Base record."
        )
        for open_id, _ in pm_people:
            im.send_text(open_id, msg)
        log.info(f"Notified PM about revision on {job['record_id']} ({job_title})")
