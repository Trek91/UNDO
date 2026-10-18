# UNDO V3 — current submission handoff

This is the authoritative setup and submission guide. Earlier handoffs and audit
counts describe earlier builds; consult FINAL_REPAIR_REPORT.md and BUILD_LOG.md
for executed repair evidence. The final ZIP has an external, SHA-bound verification
record so that recording its checksum cannot change the ZIP being verified.

## Product and architecture

UNDO is a local, single-business synthetic cash-flow decision-support demonstration.
React/Vite renders calculations returned by FastAPI. SQLite stores typed events,
settled state, immutable evaluations, hypothetical experiments and audit history.
One Uvicorn worker runs the durable recalculation queue and SSE event stream.
No workflow executes a real payment. Currency is INR, money is integer paise,
timestamps are timezone-aware, and the synthetic reference date is 17 October 2026.

The overview and cash-flow screens separate settled cash, expected receipts,
obligations and desired reserves. Decision Room evaluates full payment, contractual
partial payment, contractual deferral and hold when allowed. Shared seeded random
scenarios make alternatives comparable. Projected cash deficits, missed/late
contractual obligations and desired-reserve breaches are distinct measures; see
financial-model.md. Recommendations and explanation drivers come from the backend.
Decision intelligence compares four policies and computes one-factor sensitivity,
switching brackets and recommendation stability. These are bounded analyses,
not guarantees or exhaustive multivariable optimization.

Scenario Lab inherits the selected stable proposal ID and simulation settings,
shows the supplier and source state, and evaluates hypothetical inputs without
changing the ledger. Save archives the exact reviewed experiment; Revert discards
the draft. Changing an input invalidates the result, including in-flight responses.
URL hash parameters preserve selected proposal/settings on refresh. An unavailable
target requires explicit selection. The separate scenario editor creates a new
synthetic generation. Event recording, settlements and the deterministic demo feed
produce versioned updates, recalculation and stale historical evaluations. Audit
history retains original snapshots across generations. Reset is an explicit demo
operation; never use it against a demo whose records must be preserved.

Model Evidence compares experimental synthetic predictions against baselines.
The obligation-aware deterministic rule remains primary: synthetic validation did
not establish incremental ML decision benefit or real-world predictive accuracy.
Weights, training data and threshold are unchanged by this repair. Shared metric
reports derive precision/recall/F1 from TP/FP/FN with independent denominators.
Undefined values are null with reasons; historical missing counts are unavailable.
DecisionRecord.model_statistics is a read-time presentation. Raw historical
evaluation metadata remains distinguishable and is never rewritten for display.

## Prerequisites and configuration

Install Python 3.12 (tested local 3.12.13), Node.js 24.12 with npm, and optionally
Docker Engine with Buildx. Internet or a populated dependency cache is needed for
declared package installation and image pulls. Browser tests use installed Chrome
or Edge on Windows, otherwise install Playwright Chromium. Git is optional for
running the archive. No database, secret, global Python library or original checkout
is required. Linux uses .venv/bin/python in place of .venv/Scripts/python.exe.

.env.example documents environment variables; it is not automatically loaded by
Python. UNDO_DB defaults to data/undo.db relative to the backend working directory.
UNDO_STATIC defaults to ../frontend/dist; set an absolute path when using another
working directory. UNDO_ORIGINS is a comma-separated exact browser-origin list.
UNDO_API_URL configures Vite's backend proxy (default http://127.0.0.1:8000).
Docker Compose additionally accepts UNDO_IMAGE and UNDO_PORT. Use a separate
Compose project name and port for isolated validation to create a separate volume.

## Clean native installation (PowerShell, extracted project root)

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
Set-Location frontend
npm ci
```

For repeated isolated verification, uv0.11.32 is an optional installer prerequisite:
`uv venv --python 3.12 --seed .venv`, then
`uv pip install --python .venv/Scripts/python.exe -r backend/requirements-dev.txt`.
This installs the same declared specifications without using workspace packages.
`npm ci --prefer-offline --no-audit` may use the npm dependency cache; run the
separate npm audit command afterward. Standard pip/npm installation above was
also executed from an independent archive extraction.

Backend terminal from project root:

```powershell
Set-Location backend
../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Frontend terminal from project root:

```powershell
Set-Location frontend
npm run dev
```

Open http://127.0.0.1:5173; API documentation is http://127.0.0.1:8000/docs
and health is http://127.0.0.1:8000/api/health. The demo initializes once and persists.
For one-process serving, run npm run build from frontend, then start the backend
as above and open http://127.0.0.1:8000. Keep one worker. On Linux create the
environment with python3.12 -m venv .venv and use its bin/python executable.

## Verification commands

From backend:

```powershell
../.venv/Scripts/python.exe -m pytest -q
../.venv/Scripts/python.exe -m ruff check app tests benchmark.py
../.venv/Scripts/python.exe -m mypy app
../.venv/Scripts/python.exe -m pip_audit -r requirements.txt --no-deps --disable-pip
```

From frontend:

```powershell
npm test
npm run typecheck
npm run lint
npm run build
npm run e2e
npm audit
```

If no installed browser is available, first run npx playwright install chromium
(Linux may need browser system libraries). Browser tests start independent servers
on 8001/5174 and an extracted-copy .runtime/e2e.db. Those ports must be free.
The repair browser suite uses real isolated APIs and held responses for the races.
Verified source-cut checks in both the original workspace and independent archive
extraction: backend97, frontend27, full browser21, typecheck/lint/build and npm/pip
runtime audits (0 reported advisories) PASS. Packaging regressions3 PASS. Both
architectures passed97 backend tests and isolated runtime/restart checks. The
source-bound model/financial artifact is unchanged. Precise final ZIP post-cut
results are in dist/UNDO-V3-VERIFICATION.json; see FINAL_REPAIR_REPORT.md for the
full original/extracted distinction and earlier failures/fixes.

## Isolated Docker build and runtime

From the extracted root, with a functioning Linux Docker engine:

```powershell
docker version
docker info
docker buildx version
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64 -f deploy/Dockerfile -t undo:submission-native --load .
$env:UNDO_IMAGE='undo:submission-native'
$env:UNDO_PORT='8085'
docker compose -p undo-submission-check up -d --no-build
.venv/Scripts/python.exe scripts/container_smoke.py --url http://127.0.0.1:8085 --output .runtime/native-smoke.json
docker compose -p undo-submission-check restart
.venv/Scripts/python.exe scripts/container_smoke.py --url http://127.0.0.1:8085 --output .runtime/native-restart.json --probe
```

The smoke script deliberately resets its target: use only the isolated validation
project/port, never an existing preserved application. Restart uses the same volume.
Choose another unused project/port for each independent clean verification.
To stop the owned check, use docker compose -p undo-submission-check stop;
do not remove existing volumes. Native here means the tested amd64 Docker host.

Separately package the target architecture:

```powershell
docker buildx build --platform linux/s390x -f deploy/Dockerfile -t undo:submission-s390x --load .
```

The exact pinned Python 3.12.12 slim-bookworm manifest supports s390x. Pydantic
2.11.7 and Core2.33.2 install in the image without a custom fallback. The frontend
Node build runs on BUILDPLATFORM. Native success, emulated s390x packaging/runtime
and actual IBM LinuxONE execution are independent claims. Real LinuxONE execution
is BLOCKED: no target host/access is supplied. No external deployment is claimed.

For offline container regression tools, prepare declared pure-Python wheels from
the extracted root (production dependencies remain those installed in the image):

```powershell
.venv/Scripts/python.exe -m pip download --only-binary=:all: --no-deps --dest .runtime/test-wheels pytest==9.1.1 httpx==0.28.1 httpcore==1.0.9 certifi==2026.7.22 pluggy==1.7.0 iniconfig==2.3.1 packaging==26.3 pygments==2.21.0
.venv/Scripts/python.exe scripts/container_tests.py --image undo:submission-native --platform linux/amd64
.venv/Scripts/python.exe scripts/container_tests.py --image undo:submission-s390x --platform linux/s390x
```

## Submission

submission-manifest.json explicitly classifies runtime/testing/deployment/docs files.
The packager reads current bytes, including explicitly included formerly untracked
V3 modules. No Git HEAD snapshot is used. backend/app/evidence/validation.json is
required synthetic model-validation evidence and is included; do not delete it as
an arbitrary generated asset. Models are deterministic code, with no separate
private weights file. SQLite schema and demo initialization live in backend source.
The frontend has no external public asset directory requirement. Declared package
lockfiles, source, tests, fixtures, Dockerfiles and documentation are shipped.

Live databases, .env, credentials, backups, caches, installed packages, generated
bundles, host-specific release helpers and historical screenshot/log directories
are excluded. Historical markdown is retained with superseded notices. Detailed
repair execution logs remain in the engineering workspace, not in the distributable.

From root:

```powershell
.venv/Scripts/python.exe scripts/test_package_submission.py
.venv/Scripts/python.exe scripts/package_submission.py
.venv/Scripts/python.exe scripts/package_submission.py --verify dist/UNDO-V3-SUBMISSION.zip
Get-FileHash dist/UNDO-V3-SUBMISSION.zip -Algorithm SHA256
```

The deterministic ZIP contains SUBMISSION_CONTENTS.json with per-file hashes and
sizes. Its sibling .zip.sha256, .contents.txt and .integrity.json are generated from
actual bytes. dist/UNDO-V3-VERIFICATION.json records verification of the exact final
ZIP from an independent temporary extraction. A checksum is an integrity identifier,
not an authentication signature. Repeat tests using only the extracted source and
declared prerequisites; do not repair extraction by copying workspace files.

## Limits and troubleshooting

Local synthetic use only. Multi-user public hosting needs authentication, tenant
isolation, TLS and operational controls not implemented here. No real-bank integration.
OS/image-layer Docker Scout scanning is BLOCKED without Docker login; npm/pip
dependency audits are separate checks. Starlette TestClient emits a non-failing
httpx deprecation warning. Multivariable sensitivity and quantile bands remain
nonessential enhancements, not implemented functionality. Numeric outcomes depend
on the selected snapshot, horizon and simulated receipt assumptions.

For origin errors configure UNDO_ORIGINS; for proxy errors check the backend health
and UNDO_API_URL. For unavailable targets select a valid proposal explicitly.
For stale results reevaluate the current context. Keep a writable private database
directory, one worker and the same volume across restart. Preserve data when
diagnosing errors rather than deleting it.

## Public repository evidence

See [SUBMISSION_VERIFICATION.md](SUBMISSION_VERIFICATION.md) and the accompanying
JSON for portable copies of the executed final-archive results. Machine-specific
paths are explicitly redacted. Generated ZIPs remain outside Git; the original
tested artifact checksum is preserved in the verification record.
