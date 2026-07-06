# tests/test_webhook.py
import pytest
from unittest.mock import MagicMock
from webhook import create_app


@pytest.fixture
def app():
    base = MagicMock()
    im = MagicMock()
    flask_app = create_app(base, im)
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def test_got_it_returns_200(client):
    resp = client.get("/action?action=got_it&record_id=recJOB1")
    assert resp.status_code == 200


def test_got_it_response_contains_done(client):
    resp = client.get("/action?action=got_it&record_id=recJOB1")
    assert b"Done" in resp.data or b"close" in resp.data.lower()


def test_request_extension_calls_pm_alert(app):
    app.base.list_active_jobs.return_value = [{
        "record_id": "recJOB1",
        "fields": {
            "fldH4QtERK": [{"id": "recPM1"}],
            "fld6elh0J7": [{"text": "Nike AO"}],
        }
    }]
    app.base.get_roster.return_value = [
        {"record_id": "recPM1", "fields": {"fldFrxViIu": "ou_pm", "fldLy0sa0j": "Billie"}}
    ]
    client = app.test_client()
    resp = client.get("/action?action=request_extension&record_id=recJOB1&stage=1st+Internal+Review")
    assert resp.status_code == 200
    app.im.send_pm_extension_alert.assert_called_once()


def test_pres_approved_sets_stage_to_production(app):
    client = app.test_client()
    resp = client.get("/action?action=pres_approved&record_id=recJOB1")
    assert resp.status_code == 200
    app.base.update_record.assert_called_with("recJOB1", {"fldNwVKYVH": "Production"})


def test_feedback_fast_creates_feedback_record(app):
    client = app.test_client()
    resp = client.get("/action?action=feedback_fast&record_id=recJOB1&person=Yodha&job=Nike+AO")
    assert resp.status_code == 200
    app.base.create_feedback_record.assert_called_once()
    call_fields = app.base.create_feedback_record.call_args[0][0]
    assert call_fields["Rating"] == "Fast"


def test_feedback_normal_creates_feedback_record(app):
    client = app.test_client()
    resp = client.get("/action?action=feedback_normal&record_id=recJOB1")
    assert resp.status_code == 200
    app.base.create_feedback_record.assert_called_once()
    call_fields = app.base.create_feedback_record.call_args[0][0]
    assert call_fields["Rating"] == "Normal"


def test_feedback_slow_creates_feedback_record(app):
    client = app.test_client()
    resp = client.get("/action?action=feedback_slow&record_id=recJOB1")
    assert resp.status_code == 200
    app.base.create_feedback_record.assert_called_once()
    call_fields = app.base.create_feedback_record.call_args[0][0]
    assert call_fields["Rating"] == "Slow"


def test_feedback_skip_returns_200(client):
    resp = client.get("/action?action=feedback_skip")
    assert resp.status_code == 200


def test_unknown_action_returns_200_gracefully(client):
    resp = client.get("/action?action=unknown_action_xyz")
    assert resp.status_code == 200
