"""Exercise a running local container through HTTP; probe mode checks restart persistence."""
import argparse
import json
import re
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--url", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--probe", action="store_true")
args = parser.parse_args()
if not args.url.startswith("http://127.0.0.1:"):
    raise SystemExit("Smoke checks are restricted to local loopback servers")


def get(path: str) -> object:
    with urllib.request.urlopen(args.url+path, timeout=15) as response:
        return json.load(response)


def post(path: str, body: object | None = None) -> object:
    request = urllib.request.Request(args.url+path, data=json.dumps(body or {}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


deadline = time.monotonic()+45
while True:
    try:
        health = get("/api/health")
        assert health["status"] == "ok"
        break
    except (OSError, AssertionError):
        if time.monotonic() >= deadline:
            raise
        time.sleep(0.5)
with urllib.request.urlopen(args.url+"/", timeout=10) as response:
    html = response.read().decode()
assert "UNDO" in html
asset = re.search(r'src="(/assets/[^\"]+\.js)"', html).group(1)
with urllib.request.urlopen(args.url+asset, timeout=10) as response:
    assert response.status == 200 and len(response.read()) > 1000

if not args.probe:
    state = post("/api/demo/reset")
    original = post("/api/decisions/evaluate", {"paths": 100})["evaluation"]
    assert original["status"] == "ready"
    receipt_date = (datetime.fromisoformat(state["base_date"])+timedelta(days=5)).date().isoformat()
    event = dict(event_id="container-delay", business_id="demo", timestamp=datetime.now(timezone.utc).isoformat(),
                 type="RECEIVABLE_DELAYED", receivable_id="customer", expected_date=receipt_date)
    accepted = post("/api/events", event)
    assert not accepted["duplicate"]
    assert post("/api/events", event)["duplicate"]
    deadline = time.monotonic()+30
    while True:
        overview = get("/api/overview")
        if overview["latest_decision"] and overview["latest_decision"]["evaluation"]["state_version"] == 1:
            break
        if time.monotonic() >= deadline:
            raise AssertionError("No persisted event-driven recalculation")
        time.sleep(0.1)
    assert get(f"/api/decisions/{original['id']}")["stale"]
    with urllib.request.urlopen(args.url+"/api/events/stream?after=0&once=true", timeout=10) as response:
        stream = response.read().decode()
    assert "EVENT_ACCEPTED" in stream and "EVALUATION_COMPLETED" in stream
else:
    overview = get("/api/overview")
assert overview["state"]["version"] == 1
assert overview["state"]["cash_paise"] == 10000000
assert len(get("/api/events")["items"]) == 1
result = {"checked_at": datetime.now(timezone.utc).isoformat(), "url": args.url, "health": health,
          "static_assets": "PASS", "restart_probe": args.probe, "generation": overview["state"]["generation"],
          "state_version": 1, "cash_paise": overview["state"]["cash_paise"],
          "recommendation": overview["latest_decision"]["evaluation"]["recommendation"],
          "checks": "Persisted state, current evaluation, idempotency, immutable history and SSE" if not args.probe
                    else "State/events/evaluation persisted across container restart"}
Path(args.output).write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
