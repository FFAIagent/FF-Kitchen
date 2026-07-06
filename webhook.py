# webhook.py
from __future__ import annotations
import logging
from datetime import date
from flask import Flask, request, current_app
import config

log = logging.getLogger(__name__)

_HTML_DONE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Done</title>
<style>body{{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;background:#f5f5f5}}
.card{{background:white;padding:40px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.1);text-align:center}}
h2{{color:#00b388}}p{{color:#555}}</style></head>
<body><div class="card"><h2>&#x2705; Done!</h2><p>You can close this tab.</p></div></body>
</html>"""


def create_app(base, im) -> Flask:
    app = Flask(__name__)
    app.base = base
    app.im = im

    @app.route("/action", methods=["GET"])
    def action():
        action_name = request.args.get("action", "")
        record_id = request.args.get("record_id", "")
        stage = request.args.get("stage", "")
        job = request.args.get("job", "")
        person = request.args.get("person", "")
        try:
            _handle_action(action_name, record_id, stage, job, person,
                           current_app.base, current_app.im)
        except Exception as e:
            log.error(f"Action error [{action_name}]: {e}", exc_info=True)
        return _HTML_DONE, 200

    return app


def _handle_action(action: str, record_id: str, stage: str, job: str, person: str,
                   base, im) -> None:
    if action == "got_it":
        log.info(f"Got it on record {record_id}")

    elif action == "request_extension":
        _action_request_extension(record_id, stage, base, im)

    elif action == "pres_approved":
        base.update_record(record_id, {config.F_STAGE_STATUS: config.STAGE_PRODUCTION})
        log.info(f"Presentation approved for {record_id}, stage set to Production")

    elif action == "pres_revision":
        log.info(f"Presentation revision for {record_id}")

    elif action in ("feedback_fast", "feedback_normal", "feedback_slow"):
        rating_map = {
            "feedback_fast": "Fast",
            "feedback_normal": "Normal",
            "feedback_slow": "Slow",
        }
        rating = rating_map[action]
        base.create_feedback_record({
            "Rating": rating,
            "Reviewer Type": "Supervisor",
            "Answered At": date.today().strftime("%Y-%m-%d %H:%M:%S"),
            "Used in Calibration": False,
        })
        log.info(f"Feedback recorded: {rating} for {person} on {job}")

    elif action == "feedback_skip":
        log.info(f"Feedback skipped for {person} on {job}")

    else:
        log.warning(f"Unknown action: {action}")


def _action_request_extension(record_id: str, stage: str, base, im) -> None:
    """Find PM for the job and notify them of the extension request."""
    from handlers.brief import _get_text, _resolve_open_ids
    jobs = base.list_active_jobs()
    roster = base.get_roster()
    job = next((j for j in jobs if j["record_id"] == record_id), None)
    if not job:
        log.warning(f"Extension request: job {record_id} not found")
        return
    pm_links = job["fields"].get(config.F_PM_PIC) or []
    pm_people = _resolve_open_ids(pm_links, roster)
    job_title = _get_text(job["fields"].get(config.F_JOB_TITLE))
    for pm_open_id, _ in pm_people:
        im.send_pm_extension_alert(
            pm_open_id, "—", job_title, stage or "milestone", "—",
            f"https://fcn.sg.larksuite.com/base/{config.BASE_TOKEN}"
        )


if __name__ == "__main__":
    from lark_base import BaseClient
    from lark_im import IMClient
    app = create_app(BaseClient(), IMClient())
    app.run(host="0.0.0.0", port=config.WEBHOOK_PORT, debug=False, use_reloader=False)
