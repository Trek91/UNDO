"""Fresh-process model provenance and generated API contract verification."""
import json
import platform
import subprocess
import sys
from pathlib import Path

from app.main import create_app

code = """import json,platform,pydantic,pydantic_core
from app.prediction import load_model
m=load_model()
print(json.dumps(dict(python=platform.python_version(),architecture=platform.machine(),pydantic=pydantic.__version__,pydantic_core=pydantic_core.__version__,version=m.version,weights=m.weights,metrics=m.metrics)))
"""
records = [json.loads(subprocess.run([sys.executable, '-c', code], capture_output=True, check=True,
                                   text=True).stdout) for _ in range(2)]
assert records[0] == records[1]
Path('../docs/audit/fresh-process-model.json').write_text(json.dumps(dict(
    host=platform.platform(), identical_fresh_processes=True, processes=records,
    loading='Deterministic training at startup, cached per process; no serialized artifact is claimed.'), indent=2))
Path('../docs/openapi.json').write_text(json.dumps(create_app().openapi(), indent=2))
print('PASS: two independent fresh-process models match; API contract exported.')
