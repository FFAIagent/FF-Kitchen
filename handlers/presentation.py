from __future__ import annotations
import logging
import config
from handlers.brief import _get_text
from handlers.reminder import _is_yesterday

log = logging.getLogger(__name__)


def handle_post_presentation(job: dict, base, im, **_) -> None:
    fields = job["fields"]
    if fields.get(config.F_POST_PRES_CARD_SENT):
        return
    pres_date = fields.get(config.F_CLIENT_PRES_DATE)
    if not _is_yesterday(pres_date):
        return

    job_title = _get_text(fields.get(config.F_JOB_TITLE))
    pres_date_str = str(pres_date)[:10] if pres_date else ""

    # Get Account PIC open_id(s)
    account_pic = fields.get(config.F_ACCOUNT_PIC) or []
    if isinstance(account_pic, list):
        open_ids = [p.get("id") or p.get("open_id") for p in account_pic if isinstance(p, dict)]
    else:
        open_ids = [str(account_pic)] if account_pic else []

    if not open_ids:
        log.warning(f"No Account PIC for post-presentation card on {job['record_id']}")
        return

    # Client name — just use record ID for now (agent can't resolve client names without extra lookup)
    client_name = "the client"

    for open_id in open_ids:
        if open_id:
            im.send_post_pres_card(open_id, job_title, client_name, pres_date_str, job["record_id"])

    base.update_record(job["record_id"], {config.F_POST_PRES_CARD_SENT: True})
    log.info(f"Post-presentation card sent for {job['record_id']} ({job_title})")
