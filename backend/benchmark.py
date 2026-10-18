"""Repeatable local measurements; no production-scale or external latency claims."""
import json
import math
import platform
import statistics
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.domain import baseline
from app.engine import EvaluationRequest, evaluate
from app.main import create_app
from app.prediction import load_model


def summary(samples: list[float]) -> dict[str, float | int]:
    ordered = sorted(samples)
    return {"trials": len(samples), "median_ms": statistics.median(samples),
            "p95_ms": ordered[math.ceil(len(ordered)*0.95)-1], "min_ms": min(samples), "max_ms": max(samples)}


def measure() -> dict[str, object]:
    started = time.perf_counter()
    load_model()
    training_ms = (time.perf_counter()-started)*1000
    timings = []
    request = EvaluationRequest()
    for _ in range(20):
        start = time.perf_counter()
        evaluate(baseline(), request)
        timings.append((time.perf_counter()-start)*1000)
    events = []
    live = []
    with tempfile.TemporaryDirectory() as directory:
        with TestClient(create_app(str(Path(directory)/"benchmark.db"))) as client:
            client.post("/api/decisions/evaluate", json={"paths": 1000})
            for index in range(10):
                # Distinct small actual cash movements; same bounded workload, no demo DB writes.
                payload = dict(event_id=f"bench-{index}", business_id="demo", timestamp=datetime.now(timezone.utc).isoformat(),
                    type="PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=100)
                start = time.perf_counter()
                response = client.post("/api/events", json=payload)
                response.raise_for_status()
                events.append((time.perf_counter()-start)*1000)
                version = response.json()["state_version"]
                deadline = time.monotonic()+10
                while time.monotonic() < deadline:
                    overview = client.get("/api/overview").json()
                    if overview["latest_decision"] and overview["latest_decision"]["evaluation"]["state_version"] == version:
                        break
                    time.sleep(0.01)
                else:
                    raise RuntimeError("Recalculation exceeded benchmark observation window")
                live.append((time.perf_counter()-start)*1000)
    return {"recorded_at": datetime.now(timezone.utc).isoformat(), "os": platform.platform(), "architecture": platform.machine(),
        "python": platform.python_version(), "workload": "1 proposal, 4 alternatives, 1000 paths, 7-day horizon, 1 receivable, 2 obligations",
        "method": "Warm engine measured directly; event/refresh measured through in-process real HTTP ASGI client. Includes 150ms worker polling; excludes network/browser rendering. P95 nearest-rank order statistic.",
        "model_initialization_ms": training_ms, "evaluation": summary(timings), "http_event_commit": summary(events),
        "event_to_persisted_recalculation": summary(live)}


if __name__ == "__main__":
    result = measure()
    output = Path("../docs/benchmark.json")
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
