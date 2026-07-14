#!/usr/bin/env python3
"""WonderLab Voucher Sync — auto-marks voucher codes as Redeemed when a
Redemption Request is confirmed.

Run on a schedule (every 10 min via launchd) or manually:
    python3 scripts/wonderlab_voucher_sync.py

Idempotent: safe to run multiple times. Skips codes already marked Redeemed.

Base: XvkybPhKyaUQoBszNM6l3Av4g6b (WonderLab)
Tables:
  - Voucher Codes:               tblkScdoHVo73Vis
  - Voucher Redemption Requests: tblmuoWxTLkMIlvv
"""
from __future__ import annotations
import json
import logging
import subprocess
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

BASE_TOKEN  = "XvkybPhKyaUQoBszNM6l3Av4g6b"

# Voucher Codes table
CODES_TABLE  = "tblkScdoHVo73Vis"
C_CODE       = "fldTrHLauw"   # Code (text)  e.g. "WL2026.0001"
C_STATUS     = "fldoSppXyV"   # Status (select)
C_REDEEMED   = "fldFMPZQDX"   # Redeemed In Transaction (text)

STATUS_AVAILABLE = "✅ Available"
STATUS_REDEEMED  = "🔴 Redeemed"
STATUS_ASSIGNED  = "🔒 Assigned"

# Voucher Redemption Requests table
REQ_TABLE    = "tblmuoWxTLkMIlvv"
R_NAME       = "fldW28wYid"   # Full Name (primary text)
R_STATUS     = "fldl46Z7NM"   # Status (select)
R_CODES_DONE = "fldOoQas7k"   # Codes Marked (checkbox)
R_START_REG  = "fldjgToa38"   # Code — Start Regular (text)
R_QTY_REG    = "fldw9HxzJF"   # Quantity Regular (number)
R_START_COMP = "fldvwRZKQf"   # Code — Start Companion (text)
R_QTY_COMP   = "fldXwpzIHQ"   # Quantity Companion (number)

STATUS_CONFIRMED = "✅ Confirmed"

RATE_LIMIT_SLEEP = 0.15   # seconds between writes


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run(cmd: list[str]) -> dict:
    res = subprocess.run(cmd, capture_output=True, text=True)
    raw = res.stdout
    lines = [l for l in raw.splitlines() if not l.startswith("warning:")]
    return json.loads("\n".join(lines)) if lines else {}


def _unwrap(v):
    """Single-element list → scalar (lark-cli columnar format)."""
    if isinstance(v, list) and len(v) == 1 and isinstance(v[0], str):
        return v[0]
    return v


def list_records(table_id: str) -> list[dict]:
    """Fetch all records from a table, returning [{record_id, fields}]."""
    records = []
    offset  = 0
    has_more = True
    while has_more:
        cmd = [
            "lark-cli", "base", "+record-list",
            "--base-token", BASE_TOKEN,
            "--table-id",   table_id,
            "--as", "user",
            "--format", "json",
            "--limit", "200",
            "--offset", str(offset),
        ]
        d     = _run(cmd)
        inner = d.get("data", d)
        fids  = inner.get("field_id_list", [])
        rids  = inner.get("record_id_list", [])
        rows  = inner.get("data", [])
        has_more = inner.get("has_more", False)

        for i, rid in enumerate(rids):
            row = rows[i]
            fields = {
                fids[j]: _unwrap(row[j])
                for j in range(min(len(fids), len(row)))
                if row[j] is not None
            }
            records.append({"record_id": rid, "fields": fields})

        offset += len(rows)
        if not has_more or not rows:
            break

    return records


def update_code_record(record_id: str, status: str, redeemed_in: str) -> bool:
    """Set Status + Redeemed In Transaction on a single Voucher Code record."""
    patch = {C_STATUS: status, C_REDEEMED: redeemed_in}
    cmd = [
        "lark-cli", "base", "+record-upsert",
        "--base-token", BASE_TOKEN,
        "--table-id",   CODES_TABLE,
        "--record-id",  record_id,
        "--as", "user",
        "--json", json.dumps(patch),
    ]
    d = _run(cmd)
    return bool(d.get("ok"))


def parse_code_number(code: str) -> int | None:
    """'WL2026.0042' → 42. Returns None if unparseable."""
    try:
        return int(code.split(".")[-1])
    except Exception:
        return None


def code_from_number(n: int) -> str:
    """42 → 'WL2026.0042'."""
    return f"WL2026.{n:04d}"


# ── Main logic ────────────────────────────────────────────────────────────────

def run_sync() -> None:
    log.info("WonderLab Voucher Sync — starting")

    # 1. Load all Voucher Codes into a lookup: code_str → {record_id, status}
    log.info("Loading voucher codes...")
    all_codes = list_records(CODES_TABLE)
    code_map: dict[str, dict] = {}
    for r in all_codes:
        f = r["fields"]
        code = f.get(C_CODE, "")
        if code:
            code_map[code] = {"record_id": r["record_id"], "status": f.get(C_STATUS, "")}

    log.info(f"  {len(code_map)} codes loaded")

    # 2. Load Redemption Requests with Status = Confirmed
    log.info("Loading confirmed redemption requests...")
    all_requests = list_records(REQ_TABLE)
    confirmed = [
        r for r in all_requests
        if r["fields"].get(R_STATUS) == STATUS_CONFIRMED
    ]
    log.info(f"  {len(confirmed)} confirmed requests")

    # 3. For each confirmed request, mark its code range
    total_updated = 0

    for req in confirmed:
        f       = req["fields"]
        name    = f.get(R_NAME, "Unknown")
        ref_tag = f"📥 {name}"

        # Regular codes
        start_reg = f.get(R_START_REG, "")
        qty_reg   = int(f.get(R_QTY_REG) or 0)

        # Companion codes
        start_comp = f.get(R_START_COMP, "")
        qty_comp   = int(f.get(R_QTY_COMP) or 0)

        ranges_to_process = []
        if start_reg and qty_reg > 0:
            start_n = parse_code_number(start_reg)
            if start_n is not None:
                ranges_to_process.append((start_n, qty_reg))

        if start_comp and qty_comp > 0:
            start_n = parse_code_number(start_comp)
            if start_n is not None:
                ranges_to_process.append((start_n, qty_comp))

        if not ranges_to_process:
            log.info(f"  [{name}] — no code range found, skipping")
            continue

        req_updated = 0
        for start_n, qty in ranges_to_process:
            for n in range(start_n, start_n + qty):
                code = code_from_number(n)
                entry = code_map.get(code)
                if not entry:
                    log.warning(f"  Code {code} not found in Voucher Codes table")
                    continue
                if entry["status"] == STATUS_REDEEMED:
                    continue  # already done — idempotent skip

                ok = update_code_record(entry["record_id"], STATUS_REDEEMED, ref_tag)
                if ok:
                    entry["status"] = STATUS_REDEEMED  # update local cache
                    req_updated += 1
                    total_updated += 1
                else:
                    log.error(f"  Failed to update {code}")

                time.sleep(RATE_LIMIT_SLEEP)

        if req_updated:
            log.info(f"  [{name}] — marked {req_updated} codes as Redeemed")
        else:
            log.info(f"  [{name}] — all codes already Redeemed (nothing to do)")

    log.info(f"Sync complete — {total_updated} codes updated across {len(confirmed)} confirmed requests")


if __name__ == "__main__":
    run_sync()
