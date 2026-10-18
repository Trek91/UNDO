import json
from pathlib import Path

from app.decisions import assess
from app.domain import baseline
from app.engine import EvaluationRequest
from app.main import create_app
from app.prediction import load_model
from app.model_evidence import model_evidence

Path('../docs/openapi.json').write_text(json.dumps(create_app().openapi(), indent=2))
result = assess(baseline(), EvaluationRequest(paths=30, include_robustness=True), load_model())
Path('../frontend/tests/v3-fixture.json').write_text(result.model_dump_json(indent=2))
Path('../frontend/tests/model-evidence-fixture.json').write_text(model_evidence(load_model()).model_dump_json(indent=2), encoding='utf-8')
print('Exported actual OpenAPI and computed V3 test fixture; no live database access.')
