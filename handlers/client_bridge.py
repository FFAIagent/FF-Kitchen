# handlers/client_bridge.py
"""Bridge DAPUR Client Name (select) → Client (link field).

WHY THIS EXISTS
---------------
The Job Submission Form fills in 'Client Name' (a select field, fldzr8aih0)
because Lark Base Forms cannot show link-type fields as questions (platform
limitation, confirmed by Riri 2026-07-07).

The 'Client' field (fld7MDHHJN) is a LINK to the Clients table. It drives:
  - 'Auto-fill Team from Client Card' automation (fires on Client field change)
  - Billing Tier, Pressure Weight, and all other lookups from the Clients table

Until Client (link) is written, those automations and lookups are dead.

HOW IT WORKS
------------
On every poll cycle this handler:
1. Checks if Client (link) is empty for the current job.
2. If empty AND Client Name (select) has a value, looks up the Clients table
   for a matching record (case-insensitive name match).
3. Writes the matching record_id into the Client (link) field.
4. Logs a warning if no match is found (typo or new client not yet in Clients table).

Once the link is written, Lark's own 'Auto-fill Team' workflow fires and
fills the assignment fields — no further agent action needed.
"""
from __future__ import annotations
import logging
import config

log = logging.getLogger(__name__)


def _normalize(name: str) -> str:
    """Lowercase and strip for case-insensitive name matching."""
    return name.strip().lower()


def handle_client_link_bridge(job: dict, base, clients: list, **_) -> None:
    """Write Client (link) if it is missing but Client Name (select) is set.

    Registered as a per-job handler in scheduler.py. Runs on every poll cycle
    so any backlog of unlinked jobs gets cleaned up automatically.

    Args:
        job:     DAPUR record dict {record_id, fields}
        base:    BaseClient instance (used to write the update)
        clients: list of Clients table records, pre-fetched once per poll cycle
                 by poller.run_once() to avoid a fetch-per-job pattern.
    """
    fields = job["fields"]

    # Already linked — nothing to do.
    if fields.get(config.F_CLIENT_LINK):
        return

    # No Client Name either — nothing to match against.
    client_name_raw = fields.get(config.F_CLIENT_NAME)
    if not client_name_raw:
        return

    # Client Name is a single-select field — lark-cli may return str or [str]
    if isinstance(client_name_raw, list):
        client_name = client_name_raw[0] if client_name_raw else ""
    else:
        client_name = str(client_name_raw)

    if not client_name:
        return

    # Find matching Client record (case-insensitive name match)
    name_norm = _normalize(client_name)
    match = next(
        (
            c for c in clients
            if _normalize(str(c["fields"].get(config.CL_CLIENT_NAME, ""))) == name_norm
        ),
        None,
    )

    if not match:
        log.warning(
            "client_bridge: no Clients record found for name '%s' "
            "(job %s) — check spelling or add client to Clients table",
            client_name, job["record_id"],
        )
        return

    # Link field format for +record-upsert: list of {record_id} dicts
    linked_rec_id = match["record_id"]
    ok = base.update_record(
        job["record_id"],
        {config.F_CLIENT_LINK: [{"record_id": linked_rec_id}]},
    )
    if ok:
        log.info(
            "client_bridge: linked job %s ('%s') → Client record %s",
            job["record_id"], client_name, linked_rec_id,
        )
