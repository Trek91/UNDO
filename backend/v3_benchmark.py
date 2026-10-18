"""Measured local bounded workload; no live database or predictive-accuracy claim."""
import json
import platform
import time
from pathlib import Path

from app.decisions import assess
from app.domain import baseline
from app.engine import EvaluationRequest
from app.prediction import load_model

model = load_model()
state = baseline()
records = []
for paths, horizon in [(100, 7), (1000, 14), (5000, 30)]:
    request = EvaluationRequest(paths=paths, horizon_days=horizon, include_robustness=True)
    results = []
    timings = []
    for _ in range(2):
        start = time.perf_counter()
        result = assess(state, request, model)
        timings.append(time.perf_counter()-start)
        dump = result.model_dump()
        dump.pop('id')
        results.append(dump)
    assert results[0] == results[1], 'Repeated same-seed computation changed'
    assert result.robustness is not None
    records.append(dict(paths=paths, horizon=horizon, sensitivity_paths=result.robustness.grid_paths,
        cases=result.robustness.evaluated_cases, seconds=timings, reproducible=True,
        recommendation=result.recommendation, stability=result.robustness.stability_share,
        serialized_bytes=len(result.model_dump_json().encode())))
output = dict(platform=platform.platform(), python=platform.python_version(), scope='isolated baseline, sequential single-process local runs; timings are observations, not an SLA', records=records)
Path('../docs/v3/performance.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
print(json.dumps(output, indent=2))
