import json
import sqlite3
import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.store import Store


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "api.db"))
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def payload(**changes):
    return dict(event_id="api-event", business_id="demo", timestamp="2026-10-17T08:00:00Z",
                type="RECEIVABLE_DELAYED", receivable_id="customer", expected_date="2026-10-23", **changes)


def test_actual_http_contract_and_validation(client):
    assert client.get("/api/health").json()["status"] == "ok"
    overview = client.get("/api/overview").json()
    assert overview["state"]["cash_paise"] == 10000000
    assert client.get("/api/obligations").status_code == 200
    assert client.get("/api/receivables").status_code == 200
    assert client.get("/api/decisions/missing").status_code == 404
    assert client.post("/api/events", json={"bypass": True}).status_code == 422
    assert client.post("/api/decisions/evaluate", json={"paths": 5001}).status_code == 422
    assert client.post("/api/decisions/evaluate", json={"proposal_id": "missing"}).status_code == 404
    assert client.get("/api/events?limit=1000").status_code == 422
    assert client.get("/openapi.json").json()["paths"]["/api/events"]["post"]


def test_event_duplicate_conflict_and_db_failure(client):
    response = client.post("/api/events", json=payload())
    assert response.status_code == 201
    assert client.post("/api/events", json=payload()).json()["duplicate"] is True
    changed = payload()
    changed["expected_date"] = "2026-10-24"
    assert client.post("/api/events", json=changed).status_code == 409
    with sqlite3.connect(client.app.state.store.path) as conn:
        conn.execute("CREATE TRIGGER fail_api BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT, 'failure'); END")
    changed["event_id"] = "new-id"
    failed = client.post("/api/events", json=changed)
    assert failed.status_code == 503
    assert "Traceback" not in failed.text and "failure" not in failed.text
    assert len(client.get("/api/events").json()["items"]) == 1


def test_evaluation_event_recalculation_and_stream_replay(client):
    response = client.post("/api/decisions/evaluate", json={"paths": 100})
    assert response.status_code == 200
    original = response.json()["evaluation"]
    assert original["recommendation"] in [item["action"]["id"] for item in original["actions"] if item["valid"]]
    accepted = client.post("/api/events", json=payload()).json()
    deadline = time.monotonic()+8
    while time.monotonic() < deadline:
        overview = client.get("/api/overview").json()
        if overview["latest_decision"] and overview["latest_decision"]["evaluation"]["state_version"] == accepted["state_version"]:
            break
        time.sleep(0.05)
    else:
        pytest.fail("Accepted event did not trigger a persisted recalculation")
    assert overview["state"]["cash_paise"] == 10000000
    previous = client.get(f"/api/decisions/{original['id']}").json()
    assert previous["stale"] is True
    assert previous["evaluation"] == original
    stream = client.get("/api/events/stream?after=0&once=true")
    assert stream.status_code == 200
    data = [json.loads(line[6:]) for line in stream.text.splitlines() if line.startswith("data: ")]
    updates = [item for item in data if "kind" in item]
    assert any(item["kind"] == "EVENT_ACCEPTED" for item in updates)
    assert any(item["kind"] == "EVALUATION_COMPLETED" for item in updates)
    cursor = updates[0]["seq"]
    replay = client.get("/api/events/stream", headers={"Last-Event-ID": str(cursor)}, params={"once": "true"})
    assert f'"seq": {cursor},' not in replay.text
    assert client.get("/api/audit").json()["items"]


def test_reset_and_feed_and_request_limits(client):
    first = client.post("/api/decisions/evaluate", json={"paths": 10}).json()["evaluation"]
    assert client.post("/api/demo/events/next").status_code == 200
    assert client.post("/api/demo/reset").json()["generation"] == 2
    assert client.get("/api/overview").json()["state"]["version"] == 0
    assert client.get(f"/api/decisions/{first['id']}").json()["stale"] is True
    assert client.post("/api/events", content="x"*70000, headers={"Content-Type": "application/json"}).status_code == 413
    assert client.post("/api/demo/reset", headers={"Origin": "https://untrusted.example"}).status_code == 403


def test_pending_work_recovers_on_restart(tmp_path):
    path = tmp_path / "recovery.db"
    store = Store(path)
    store.schedule({"paths": 10})
    with TestClient(create_app(str(path))) as client:
        deadline = time.monotonic()+8
        while time.monotonic() < deadline:
            if client.get("/api/decisions").json()["items"]:
                break
            time.sleep(0.05)
        else:
            pytest.fail("Durable evaluation work was not recovered")
        assert client.app.state.store.pending() is None


def test_editable_scenario_is_archived_and_recomputed(client):
    response = client.post("/api/demo/scenario", json={"cash_paise": 20000000, "supplier_paise": 1000000})
    assert response.status_code == 200
    assert response.json()["cash_paise"] == 20000000
    assert response.json()["generation"] == 2
    decision = client.post("/api/decisions/evaluate", json={"paths": 20}).json()["evaluation"]
    assert decision["snapshot"]["proposals"]["proposal"]["amount_paise"] == 1000000
    assert decision["recommendation"] == "full"
    assert client.post("/api/demo/scenario", json={"cash_paise": -1}).status_code == 422
    client.post("/api/demo/reset")
    assert client.get("/api/overview").json()["state"]["cash_paise"] == 10000000


def test_cors_invalid_cursor_and_state_conflict(client):
    allowed = client.options("/api/events", headers={"Origin": "http://127.0.0.1:5173",
        "Access-Control-Request-Method": "POST"})
    assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    denied = client.options("/api/events", headers={"Origin": "https://untrusted.example",
        "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in denied.headers
    assert client.get("/api/events/stream?once=true", headers={"Last-Event-ID": "invalid"}).status_code == 422
    assert client.post("/api/events?expected_version=5", json=payload()).status_code == 409
    assert client.get("/api/overview").json()["state"]["version"] == 0
