import os
import pytest
from unittest.mock import MagicMock

os.environ.setdefault("LARK_APP_ID", "cli_test")
os.environ.setdefault("LARK_APP_SECRET", "test_secret")
os.environ.setdefault("BASE_TOKEN", "HH0qb3myka5wPmsyInGlH6l3grd")
os.environ.setdefault("ECD_OPEN_ID", "ou_ecd_test")


@pytest.fixture
def mock_base_client():
    from lark_base import BaseClient

    client = BaseClient.__new__(BaseClient)
    client.base_token = "HH0qb3myka5wPmsyInGlH6l3grd"

    # Inject test data
    client._active_jobs_data = [
        {
            "record_id": "recAAA",
            "fields": {
                "Job Title": [{"text": "Nike AO"}],
                "Account Status": "IN PROGRESS",
                "fld7PcmubU": False,
            },
        },
        {
            "record_id": "recBBB",
            "fields": {
                "Job Title": [{"text": "Old Job"}],
                "Account Status": "DONE",
                "fld7PcmubU": True,
            },
        },
    ]
    client._roster_data = [
        {
            "record_id": "recPPP",
            "fields": {"Name": "Yodha", "fldFrxViIu": "ou_yodha", "fldRbrkboh": ""},
        },
    ]

    # Wire up methods using injected test data
    client.list_active_jobs = lambda: [
        j
        for j in client._active_jobs_data
        if j["fields"].get("Account Status") not in ("DONE", "ON HOLD")
    ]
    client.get_roster = lambda: client._roster_data
    client._patch_record = MagicMock(return_value=True)

    def _update_roster(rec_id, field_name, new_val, current_value=None):
        if current_value == new_val:
            return False
        return client._patch_record("tblmeLyHTfAWvCm3", rec_id, {field_name: new_val})

    client.update_roster_record = _update_roster

    def _update_record(rec_id, fields):
        return client._patch_record("tblpNqjumvstYOnj", rec_id, fields)

    client.update_record = _update_record

    return client
