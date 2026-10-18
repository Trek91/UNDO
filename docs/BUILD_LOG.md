# UNDO build evidence

## Current V3 delivery — PASS with documented external blockers

Local V3 is healthy at http://127.0.0.1:8080. Final verification:91 Windows backend,
91 native Linux and91 emulated s390x backend tests;15 frontend tests;16 browser journeys.
No failures/skips in these final runs. Actual build/runtime/source/persistence records
are under docs/v3; complete A–I handoff: V3_RELEASE_NOTES.md. LinuxONE real-host execution
and Docker Scout are BLOCKED for the exact reasons below. Earlier phases/audits retain
historical counts and are not overwritten as current results.

### V3 Phases 3–4 gates — PASS

Phase3 RED: new policies module absent, collection ERROR. Targeted GREEN3 PASS;
mypy literal-key issues repaired without casts/relaxed checks. VERIFY full82 PASS,
Ruff/mypy PASS. Policy selection is separate from scoring: held-out futures cannot enter
choice functions. All outcomes share actions, starting state, horizons and futures;
observed ties/tradeoffs remain explicit, no hidden composite weights.
Phase4 RED: model evidence/orchestration absent, collection ERROR. GREEN2 PASS;
full VERIFY84 PASS, Ruff/mypy PASS. Legacy engine-version assertion now uses the actual
ENGINE_VERSION constant; old unversioned provenance check remains intact.
`../.venv/Scripts/python.exe v3_validate_model.py` PASS: untouched120 held-out invoices,
three prespecified simulation seeds,100 forecast paths/decision, one realized future
per invoice,1000 invoice-cluster bootstrap replicates. Paired fee benefit0 paise,
CI[0,0]; no reliable uplift. Version/source/weight-bound artifact packaged under
app/evidence/validation.json. Current daily Brier/counts/undefined precision reproduced
from actual forecasts; gate remains EXPERIMENTAL and primary is validated obligation rule.
Model absent/invalid: explicit UNAVAILABLE, rule still works under labelled no-receipt
stress; no heuristic probabilities invented. Production fitting/threshold/data unchanged.

### V3 Phases 1–2 gates — PASS

Phase1 RED: test_v3_contract.py 2 FAIL (new evidence absent). GREEN/VERIFY: full76 PASS,
Ruff/mypy PASS. Added real nearest-rank sampled quantiles, Wilson95 sampling intervals,
all remaining principal including out-of-window obligations and accrued unpaid fees.
Refactored shared objective_key without changing the lexicographic objective.
Phase2 RED: test_v3_robustness.py collection ERROR (service absent). GREEN targeted5 PASS;
static gate found unused import and optional scenario typing, repaired and rerun.
Full VERIFY79 PASS (phase2-verify.xml), Ruff/mypy PASS. Bounded one-factor grid,
adjacent switch brackets, no-switch/infeasible cases and common random streams verified.
Contract/ranges/method: DECISION_CONTRACT.md, DECISION_ROBUSTNESS.md. Live financial state
and current14-day/100-path settings remain untouched; APIs not yet switched to V3.

## V3 execution — Phase 0 PASS (2026-10-17)

V3 request inspected in full, existing source/Git/AGENTS/architecture/financial/ML reports
reviewed. Plan: V3_PLAN.md, phases0–8. No app implementation changed before this gate.
Docker Compose healthy at8080, authoritative volume undo-demo_undo_data /app/data/undo.db;
CLI/engine29.7.2, Buildx builder running BuildKit0.32.2 advertises s390x. Actual source
snapshot `.runtime/v3/source-before.zip`, original image alias undo:v3-baseline-native.
`scripts/v3_preserve.py baseline`: online backup written, isolated restore worked but
temporary cleanup failed because SQLite context managers had not closed handles on Windows.
Fixed with explicit closing contexts, reran `baseline --existing` without replacing backup:
PASS integrity, isolated Store restore, live state equality and original settings captured.
Current baseline is in docs/v3/baseline.json; all original rows preserved.
Backend baseline: `../.venv/Scripts/python.exe -m pytest -q --junitxml=../docs/audit/v3-baseline.xml`
PASS74 in13.83s, zero skips; Ruff/mypy PASS (six sources). Frontend `npm test` PASS10;
`npm run typecheck` PASS. One upstream TestClient deprecation warning remains.
Phase0 RED/GREEN: failed backup cleanup fixed and reverified; refactor explicit resource
closure. No live reset, event, configuration change or external deployment.

Date: 2026-10-17 (Asia/Kolkata). No pre-existing files, Git repository or user changes were present. Host: Windows x64, PowerShell 7.6.5, Python 3.14.2, Node 24.12.0, npm 11.18.0, uv 0.11.32, Git 2.52.0. No application implementation existed.

## Phase 0 — PASS

Discovery performed before implementation. Approved stack: React/TypeScript/Vite; FastAPI/Pydantic; standard-library SQLite; small trained logistic model; shared-draw simulation; SSE. Python 3.12 is the isolated project runtime. Dependency and architecture checks are in progress.

### Docker checks actually executed

- `docker version`: sandbox exit 1 (named-pipe permission denied); elevated retry exit 0. Client 29.7.2 windows/amd64; Docker Desktop 4.89.0; engine 29.7.2 linux/amd64.
- `docker info`: sandbox exit 1 (permission denied); elevated retry exit 0. Engine reachable, Linux/WSL2 x86_64, 16 CPUs, 7.612 GiB memory.
- `docker buildx version`: exit 0; v0.36.1-desktop.1.
- `docker buildx inspect --bootstrap`: sandbox exit 1 (.docker/buildx lock access denied); elevated retry exit 0. desktop-linux builder, docker driver, running BuildKit v0.32.2. Advertised platforms include linux/amd64 and linux/s390x.

Advertised build support is not an image build, dependency installation, or LinuxONE deployment. Exact base image under inspection: python:3.12.12-slim-bookworm. No target compatibility claim yet.

An initial `uv python find 3.12` encountered sandbox cache permission errors. This does not establish that Python 3.12 is unavailable; retry with an authorized cache/runtime installation follows.

### Dependency verification results

- `docker buildx imagetools inspect python:3.12.12-slim-bookworm`: exit 0; index digest sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c includes linux/amd64 and linux/s390x (target manifest sha256:1f4da44a940d41c7cc5929a37921b2e0425533735f5efbf616c2f6a46633848e).
- `docker buildx build --platform linux/amd64 -f deploy/Dockerfile.dependencies -t undo-deps:native --load --progress plain .`: exit 0; installed and imported FastAPI 0.115.12, Pydantic 2.11.7, Pydantic Core 2.33.2 on x86_64.
- `docker buildx build --platform linux/s390x -f deploy/Dockerfile.dependencies -t undo-deps:s390x --load --progress plain .`: initial request was interrupted/rejected before launch; resumed after access change, exit 0. Installed the actual manylinux s390x Pydantic Core wheel and imported all three packages; output `s390x 0.115.12 2.11.7 2.33.2`. This is emulated container execution, not a real LinuxONE host.
- `uv venv --python 3.12 .venv`: created isolated CPython 3.12.13. uv package installation stalled; stopped only the owned installers and used standard `python -m ensurepip` then `python -m pip install -r backend/requirements-dev.txt`. Native package installation is in progress.
- `git init`: exit 0; initialized the previously empty directory, no commits. Architecture, financial assumptions, testing strategy and engineering rules documented. Runtime Python patch differs (local 3.12.13 vs image 3.12.12); both use Python 3.12 ABI and are verified separately.

Discovery gate passed: empty baseline preserved, architecture/sequence/rules documented, exact base image and native/target dependencies actually verified. Native developer tooling and frontend dependencies continue installing; application tests will wait for their runners. No application behavior claimed.

## Phase 1 — PASS

RED: native import assertion exited 1 with missing `app.domain`. Added contract tests alongside implementation. Replay test then ran under Pytest and exited 1 with missing `replay` import (collection error, no tests executed in that RED run). GREEN: pure validated reducer and replay implemented. REFACTOR: identity checks centralized in replay; database layer will enforce them atomically. VERIFY: from backend, `../.venv/Scripts/python.exe -m pytest -q tests/test_domain.py`: 21 passed, exit 0 (earlier subset: 20 passed). `... -m ruff check app tests`: exit 0. `... -m mypy app`: 2 source files, exit 0. No skips. Native dependency installation via pip completed successfully.

## Phase 2 — PASS

RED: `... -m pytest -q tests/test_store.py` exited 1, missing app.store (collection error). GREEN: transactional SQLite ledger, stable historical replay, immutable event history, generation reset, audit and durable notification/job tables. VERIFY: `... -m pytest -q`: 26 passed, exit 0. Initial mypy found two inferred dictionary-value type errors in demo event payloads; explicitly typed the heterogeneous boundary payload, reran full 26 tests, ruff and mypy: all exit 0, no skips. Database-trigger failure test proves no event or notification survives a failed state write; concurrent duplicate delivery applies once. Reset archives history.

## Phase 3 — PASS

RED: `... -m pytest -q tests/test_engine.py` exited 1, missing app.engine (collection error). GREEN: trained standard-library logistic daily hazard model, invoice-group split, shared scenario draws, candidate contract validation, funding/mandatory/reserve/lateness metrics, penalty accrual and lexicographic ranking. REFACTOR: penalty IDs use reserved namespaces; all supplier obligations can accrue their contractual fees; mandatory target deadlines remain represented. Added regression for a missed split remainder (INR 12,000 peak gap including fee), distinct from mandatory expense shortfall. VERIFY: `... -m pytest -q`: 37 passed, exit 0. Initial ruff unused import and mypy default-factory typing errors repaired; full regression, ruff and mypy then exit 0 (5 source files). No skips. Hand examples verify INR 10,000 gap after full payment, INR 5,000 reserve-only deficit with greater starting cash, and same-day receipts that cannot erase a missed deadline.

Actual model: synthetic-logistic-hazard-v1-09d9f8b98a86, seed 20261017; 480 training and 120 held-out invoices; 1,125 held-out daily observations. Daily precision=0, recall=0, F1=0 at threshold 0.5 (daily arrival is sparse); daily Brier=0.0739739646357492, day-7 horizon Brier=0.23407548600543285. These results are honest synthetic evaluation and demonstrate no real-world accuracy. Written by executed model evaluation to model-evaluation.json. Default 1,000-path evaluation computed split payment as first-ranked; this is an observed result, never a hard-coded recommendation.

Frontend setup completed with 351 packages; initial npm audit reports 15 vulnerabilities. Recorded in npm-audit-initial.json; dependency upgrades are in progress and must be verified before frontend acceptance.

## Phase 4 — PASS

RED: `... -m pytest -q tests/test_api.py` exited 1 (missing app.main). GREEN: typed HTTP API, bounded requests/pagination, consistent errors, durable worker, immutable decision snapshots, SSE cursor replay and restart recovery. First full run: 41 passed / 1 failed. Feed timestamp was incorrectly rejected because validation truncated current-time microseconds; removed truncation. Focused test: 1 passed. Full regression: 42 passed, exit 0, one third-party Starlette/AnyIO deprecation warning, no skips. Ruff exit 0; mypy exit 0 (6 source files). Generated actual FastAPI OpenAPI schema into docs/openapi.json. HTTP tests cover rollback/503, idempotency/conflict, automatic recalculation, stale snapshots, SSE reconnection/replay, origin restrictions, 64 KiB request bound and persisted work recovery. No endpoint integrates with payment rails; PAYMENT_CONFIRMED accepts a synthetic ledger fact.

## Phase 5 — PASS

RED: `npm test` exited 1 because Forms did not yet exist (0 tests run). GREEN: complete dashboard/navigation, editable scenario/events, backend comparison metrics/chart, structured explanations, feed controls, historical views, reset and responsive design. Initial TypeScript check failed because output defaults were not required in OpenAPI; fixed the serialization schema contract and regenerated types rather than suppressing strict checks. Request forms now use generated input contracts. Initial lint warnings (hook dependencies/component exports) corrected. VERIFY: `npm test`: 5 passed; `npm run typecheck`, `npm run lint`, `npm run build`: exit 0. Production bundle generated (588.38 kB JS, 174.77 kB gzip); bundle-size advisory noted for optimization, not suppressed.

Dependencies: upgrade initially hit npm peer-resolution conflicts. A generated-dependency cleanup command was blocked by policy before execution. Safer alternative kept files and reconciled explicit compatible root pins via npm; `npm ls --depth=0` exit 0 with no invalid dependencies; `npm audit` exit 0, 0 vulnerabilities. No source deleted. Original vulnerability report preserved.

Browser QA: in-app automation failed before launch (`failed to write kernel assets`, OS error 3). Used installed Chrome with actual Playwright browser automation instead: `node scripts/visual-qa.mjs` exit 0, no page errors, no mobile document overflow. Captured and visually inspected actual desktop/mobile screenshots under docs/screenshots. API health and frontend HTTP both returned successful responses. Running UI renders real 1,000-path results; critical full-payment risk is visible, event empty state visible. New editable scenario API and OpenAPI contracts reverified with 43 backend tests plus static checks. Added accessible names for mobile navigation and corrected normalized durable-job request completion during review; regression checks follow in Phase 6.

## Phase 6 — PASS

Backend regression: 48 tests passed, exit 0, one third-party deprecation warning; ruff and mypy exit 0. Added concurrent distinct cash updates, stale evaluation preserving newer work, invalid model status, multiple mandatory shortfalls, high-cash changed recommendation, CORS and cursor/conflict tests. Durable worker now completes raw queued requests even when default fields were omitted.

Browser RED/repair: first `npm run e2e` ran 8 tests: 5 passed, 3 failed. Two selectors were ambiguous/too exact (actual correct results present in snapshots); corrected selectors. Axe found real secondary-text contrast issues; darkened muted colors. Focused rerun found a missing keyboard focus target for horizontally scrolling mobile tables; added named focusable regions. A diagnostics edit briefly caused a syntax error (0 tests ran); fixed immediately without weakening assertions. Final `npm run e2e`: 8 passed in 34.6s, exit 0, no skips. Desktop/mobile WCAG 2 A/AA and 2.1 AA axe checks found zero violations in the tested evaluated state. Tested 1440/768/390 widths, reduced motion and keyboard skip link. This is practical automated accessibility review, not accessibility certification.

Real workflows verified: initial state, evaluation/all alternatives, explanation, delayed receivable, persisted event, unchanged actual cash, recalculated projections, archived evaluation/audit, reset, unexpected expense, duplicate/invalid input, controlled feed pause/resume, changed scenario, infeasibility, disconnected SSE and injected backend errors with recovery. Loading/error screenshots captured and visually inspected. Error response test deliberately simulates storage failure at the HTTP boundary; database rollback is separately tested with a real SQLite trigger. Frontend 5 tests, strict typecheck, lint and production build pass. No commits/pushes/external deployment performed.

## Phase 7 — BLOCKED (real LinuxONE host execution only)

All achievable local and emulated checks are PASS. No IBM LinuxONE host or access details were supplied, so real host deployment/execution is BLOCKED and is not claimed. Exact remaining host checks are in deployment.md. The application is running locally in the native production container at http://127.0.0.1:8080.

### Final review and repairs

- `python -m pip_audit --format json --output docs/python-audit-initial.json` (isolated interpreter, root): exit 1, 28 advisory entries across pip, pytest and Starlette. Updated FastAPI to 0.143.3, Starlette to 1.8.0, pip to 26.2.1, pytest to 9.1.1 after inspecting actual package metadata. Preserved compatible Pydantic 2.11.7 / Pydantic Core 2.33.2; no fallback introduced. Froze the complete installed production dependency graph with `../.venv/Scripts/python.exe lock_requirements.py` from backend. Final environment and runtime-only audits both exit 0 with no known vulnerabilities (JSON evidence retained). These are dependency advisory scans, not an OS image scan or full security audit.
- Inspected actual Windows/Linux model weights: two coefficients differed below 1e-16 because of platform math. Canonicalized trained coefficients to 12 decimals before evaluation/hash. Final model on Windows, native Linux and emulated s390x: **synthetic-logistic-hazard-v1-8dfd5f3ab9ed**. Final held-out daily Brier 0.07397396463575107; day-7 Brier 0.23407548600545616; precision/recall/F1 remain zero at threshold 0.5. Sparse daily positive predictions and synthetic-only provenance are explicit limitations. model-evaluation.json was regenerated by executing training/evaluation.
- Corrected baseline midnight from UTC to Asia/Kolkata, with a regression test for an event in the preceding UTC date. Supplier settlements now reduce pending proposal principal and close fully settled proposals; closed proposals do not leave impossible recalculation jobs. Unknown database schema versions are rejected without downgrading the file. All changes were followed by full regression and image rebuilds.
- Lazy-loaded the chart module: production initial JS 230.59 kB (71.70 kB gzip), chart chunk 359.52 kB (104.59 kB gzip). Build-size warning resolved through actual splitting, not threshold suppression.
- Reviewed the source/diff for inert controls, hard-coded recommendation outcomes, secrets, duplicate frontend financial ranking and fake functionality. Before-evaluation chart space is explicitly an empty state; input placeholders are labelled inputs. No real banking integration, credentials, remote publishing, commits or pushes. Git index contains intent-to-add entries only, enabling review of the complete new-file diff. Added LF guidance and ignored generated TypeScript build-info. Build logs retain observed output; line endings and trailing whitespace may be normalized for clean-diff review without changing substantive output.

### Exact final verification commands and observed results

Backend working directory (`backend`):

| Command | Observed result |
|---|---|
| `../.venv/Scripts/python.exe -m pytest -q` | 52 passed, exit 0, no skips; 1 upstream httpx/TestClient deprecation warning |
| `../.venv/Scripts/python.exe -m ruff check app tests benchmark.py lock_requirements.py` | exit 0 |
| `../.venv/Scripts/python.exe -m mypy app` | 6 source files, exit 0 |
| `../.venv/Scripts/python.exe benchmark.py` | exit 0, measured 20 evaluation and 10 event/recalculation trials; docs/benchmark.json |

Frontend working directory (`frontend`):

| Command | Observed result |
|---|---|
| `npm run generate:api` | exit 0, generated from actual current OpenAPI schema |
| `npm run typecheck` | exit 0 |
| `npm run lint` | exit 0, no warnings |
| `npm test` | 5 tests passed, 1 file, exit 0, no skips |
| `npm run build` | exit 0, production HTML/CSS and split JS assets |
| `npm run e2e` | 8 tests passed in 34.3s, exit 0, no skips; full real UI/API workflow and accessibility assertions |
| `npm audit` | exit 0, zero known vulnerabilities |
| `node scripts/visual-qa.mjs` with `UNDO_PREVIEW_URL=http://127.0.0.1:8080` | exit 0, real production UI, zero page errors, no 390px document overflow; desktop/mobile screenshots captured and inspected |

Root working directory:

| Command | Observed result |
|---|---|
| `.venv/Scripts/python.exe -m pip_audit --format json --output docs/python-audit-final.json` | exit 0, no known vulnerabilities |
| `.venv/Scripts/python.exe -m pip_audit -r backend/requirements.txt --no-deps --disable-pip --format json --output docs/python-runtime-audit.json` | exit 0, no known vulnerabilities; tool advises optional hash locking |
| `.venv/Scripts/python.exe -m pip check` | exit 0, no broken requirements |
| `docker compose -p undo-demo config --quiet` | exit 0 |
| `docker buildx build --platform linux/amd64 -f deploy/Dockerfile -t undo:native --load --progress plain .` | exit 0; final native image index sha256:65edc81d7c5d4a9b8d1e756d4d0bcfe92f0a01549cccfa6cbe20174fd1251400 |
| `docker buildx build --platform linux/s390x -f deploy/Dockerfile -t undo:s390x --load --progress plain .` | exit 0; final target image index sha256:e192e6f35fc84ceff91a4de7612632f8c60b272eaecbda0aeb35e5afeff5a23c |
| `docker image inspect undo:native undo:s390x --format '{{.RepoTags}} {{.Architecture}} {{.Id}}'` | verified amd64 and s390x independently |

Full tests executed against packaged application code (only tests bind-mounted read-only), with ephemeral containers:

```powershell
docker run --rm --name undo-test-native --user 0 --platform linux/amd64 --mount type=bind,source=C:/Users/<local-user>\OneDrive\Desktop\UNDO\backend\tests,target=/verify/tests,readonly undo:native sh -c "python -m pip install --no-cache-dir pytest==9.1.1 httpx==0.28.1 && python -m pytest -q -p no:cacheprovider /verify/tests"
docker run --rm --name undo-test-s390x --user 0 --platform linux/s390x --mount type=bind,source=C:/Users/<local-user>\OneDrive\Desktop\UNDO\backend\tests,target=/verify/tests,readonly undo:s390x sh -c "python -m pip install --no-cache-dir pytest==9.1.1 httpx==0.28.1 && python -m pytest -q -p no:cacheprovider /verify/tests"
```

Native: **52 passed in 3.30s**, exit 0. Emulated s390x: **52 passed in 39.32s**, exit 0. Both have one upstream TestClient deprecation warning; no skips. Raw output in container-tests-native.log / container-tests-s390x.log. Earlier 49-test image runs also passed before the three final-review regressions were added; final 52-test runs supersede them.

Runtime smoke and actual restart verification:

```powershell
docker compose -p undo-demo up -d --no-build
.venv/Scripts/python.exe scripts/container_smoke.py --url http://127.0.0.1:8080 --output docs/native-smoke.json
docker compose -p undo-demo restart
.venv/Scripts/python.exe scripts/container_smoke.py --url http://127.0.0.1:8080 --output docs/native-restart.json --probe
docker run -d --name undo-target-final --platform linux/s390x --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges --mount source=undo-target-check-data,target=/app/data -p 127.0.0.1:8081:8000 -e UNDO_ORIGINS=http://127.0.0.1:8081 undo:s390x
.venv/Scripts/python.exe scripts/container_smoke.py --url http://127.0.0.1:8081 --output docs/s390x-smoke.json
docker restart undo-target-final
.venv/Scripts/python.exe scripts/container_smoke.py --url http://127.0.0.1:8081 --output docs/s390x-restart.json --probe
```

All exited 0. Real HTTP health/static assets/evaluation/idempotency/event recalculation/immutable audit/SSE passed. Both retained generation 3, state version 1, one event, settled cash 10,000,000 paise and the stored evaluation after restart. Model version matched all three tested environments. Native Compose reported healthy; target container also became healthy. Afterwards native demo was explicitly reset to a clean baseline and evaluated for user handoff, preserving prior audit generations.

### Actual benchmark (final run)

Windows AMD64, Python 3.12.13, one invoice/two obligations/four alternatives, 1,000 paths, 7 days. 20 warm engine trials: median **87.59 ms**, P95 **96.08 ms**. 10 in-process HTTP event commits: median **7.00 ms**, P95 **8.07 ms**. Event to persisted recalculation: median **245.06 ms**, P95 **273.89 ms**. Model initialization **1,158.96 ms**. Includes worker polling, excludes network/browser rendering; not a production capacity benchmark. Data and method saved in benchmark.json.

### Remaining limits

Real LinuxONE execution: BLOCKED by absent host/access. In-app CUA kernel initialization: BLOCKED, compensated with actual Chrome/Playwright verification. No OS-image vulnerability scan, penetration test, public authentication or multi-node validation claimed. Synthetic model/classification limitations, fixed scenario calendar and single-process deployment are documented. Current functional local and emulated workflows have no known unresolved critical defect.

Final handoff: native Compose remains healthy on loopback port 8080 with a freshly reset, evaluated baseline; previous generations retained. Development backend restarted with the final code. Emulated test runtime containers were stopped/removed after successful verification; target images and persistent test volume retained. Ephemeral unit-test containers removed themselves. `git diff --check` initially found three whitespace-only Docker log lines; normalized log whitespace and reran: exit 0. Full new-file diff is reviewable via intent-to-add entries; no staged content, commits or pushes. Final actual production screenshot was inspected after these checks. Full A–I handoff is in HANDOFF.md.

The obsolete initial "Not started" placeholder was removed during the subsequent audit;
the chronological execution records above remain the original build evidence.

## Final prototype audit — 2026-10-17, baseline and RED/GREEN

This is a new audit of the existing application. All original source, image tags,
volumes and databases were preserved. `git status --short` inspected intent-to-add
source and untracked audit tools; no commits/pushes. The live service was identified
using `docker compose ps`, inspect and read-only HTTP probes. Backup commands:
`git diff --binary --output=.runtime/audit/source-before.patch` and
`.venv/Scripts/python.exe scripts/audit_baseline.py` (PASS, online SQLite backup,
integrity `ok`, live state equals backup; SHA256/table counts in baseline-state.json).
An earlier container-tmpfs backup copy failed because `docker cp` could not see the
tmpfs file; a subsequent inline Python command hit PowerShell quoting errors.
The standalone backup utility corrected both issues. No live ledger mutations.

Docker recheck before repairs: `docker version`, `docker info`, `docker buildx version`,
`docker buildx inspect --bootstrap` all exit 0. CLI/engine 29.7.2 available,
Desktop 4.89, Linux amd64 engine; Buildx 0.36.1, BuildKit 0.32.2 running;
linux/s390x advertised. Packaging and host execution remain separate gates.

Baseline commands (backend cwd, project Python):
`../.venv/Scripts/python.exe -m pytest -q --junitxml=../docs/audit/backend-baseline.xml`
PASS 52; Ruff `check app tests benchmark.py lock_requirements.py` PASS;
mypy `app` PASS, six sources. Frontend cwd: `npm test` PASS 5,
`npm run typecheck`, `npm run lint`, `npm run build` PASS;
`npm run e2e` PASS 8 in 34.5s (isolated DB/ports, archived e2e-baseline.json).
`npm audit --json` PASS zero known vulnerabilities; root
`.venv/Scripts/python.exe -m pip_audit --format json --output docs/audit/python-baseline.json`
and `-m pip check` PASS. One upstream Starlette/httpx TestClient deprecation warning.

Live pre-repair browser: `node scripts/audit-live.mjs` (frontend cwd), PASS:
actual Chrome, evaluation saved, all five views, backend recommendation matched,
desktop/390px screenshots, no page exceptions/document overflow, full financial state
equal before/after (generation 4/version 0/cash 10,000,000). No reset or event injected.

ML diagnosis: `../.venv/Scripts/python.exe audit_model.py`, exit 0.
Unchanged original seed/split/epochs/threshold. 1,125 held-out daily observations,
94 positives, predicted positives zero, max probability 0.24818, Brier 0.07397396
versus training-prevalence baseline 0.07699682. Precision is mathematically undefined;
original helper substitutes zero. Raw predictions and calibration evidence retained.

Financial RED: `../.venv/Scripts/python.exe -m pytest tests/test_deep_audit.py -q
--junitxml=../docs/audit/regressions-red.xml`: 13 FAIL, 1 PASS (XML/raw log).
The wrapper's trailing Get-Content masked the process exit; pytest output/XML explicitly
record the failures. Confirmed deadline, schedule, fee, malformed-model, reset-retry,
acceptance-version, generation-guard, creation-date and monetary-mean defects.
GREEN after repairs: same targeted cases plus test_engine.py: 27 PASS.
REFACTOR: exact integer half-even mean; latched accrued fees and separate scheduled
payment/deadline liabilities; atomic reusable generation/version guard.

Persistence/API RED: `pytest tests/test_deep_audit.py -k 'history_cursor or http_stale'
-q --junitxml=../docs/audit/concurrency-red.xml`: 2 FAIL, exit 1.
Equal-timestamp history records were skipped; stale-generation HTTP events were accepted.
Repair: compound timestamp/rowid cursor, generation guards on all mutations,
transactional overview read snapshot, global event retry lookup preserving legacy rows.
VERIFY: full `pytest -q --junitxml=../docs/audit/backend-green.xml`: 68 PASS,
one upstream warning; Ruff (including audit_model.py) and mypy PASS.

Frontend RED: `npm test -- --reporter=verbose`: 3 FAIL / 5 PASS, exit 1,
raw frontend-red.log. Confirmed unscoped history fetch, financial state regression,
and absent evaluation mutation token. Repairs now being verified.

### Audit continuation — completed verification and further self-repair

This section supersedes earlier counts/image IDs for the current application; earlier
execution records remain historical evidence.

Frontend GREEN initially: `npm test` 8 PASS, typecheck/lint/build PASS; original eight
browser journeys PASS in 35.3s. Guarded event/reset/scenario/feed/evaluation calls,
generation-scoped lists and monotone responses were implemented. Inspected staleness is
derived from current state; hash navigation synchronizes browser back/forward.

Model RED: `pytest tests/test_deep_audit.py -k 'metrics_publish or without_forecasts'
-q --junitxml=../docs/audit/model-red.xml`: 2 FAIL. Repair: diagnostic class counts,
threshold/defined flags and validation before draws even without unpaid invoices.
Model fitting, weights, seed, data, epochs and threshold unchanged. GREEN full suite 70 PASS.
Provenance RED: `pytest ... -k legacy_evaluation -q --junitxml=../docs/audit/provenance-red.xml`:
1 FAIL. New metadata engine `counterfactual-v2`, legacy default `legacy-unversioned`;
old stored JSON retained and displayed stale. Full GREEN 71 PASS, Ruff/mypy PASS.

`../.venv/Scripts/python.exe audit_runtime.py`: PASS, two fresh-process models identical;
OpenAPI exported. Frontend `npm run generate:api`: PASS, generated strict types updated.
`../.venv/Scripts/python.exe audit_policies.py`: PASS, all 120 untouched held-out invoices
and paired realized futures, 1,000 ML paths each; balance-only, obligation/reserve rule,
worst-case rule and ML all computed. No incremental ML outcome benefit over the stronger
obligation-aware rule established. Exact results in policy-comparison.json / ML_AUDIT.md.
`audit_model.py` rerun PASS with training loss reconstruction: initial 0.25291537,
final 0.21923283, constant training-prevalence loss 0.23512650; unchanged predictions.
`benchmark.py`: PASS, actual measurements saved (see PROTOTYPE_AUDIT.md for scope/timing).

Added transient worker failure/recovery and CDF sampling coverage: full Windows suite
73 PASS. Browser additions for inspected staleness, stale-tab rejection, hash navigation
and exact chart/legend/controls: 12 PASS in 40.3s. Unit suite initially 8 PASS.

Initial audited images built independently:
`docker buildx build --platform linux/amd64 -f deploy/Dockerfile -t undo:audit-native --load --progress plain .`
and analogous `linux/s390x` / `undo:audit-s390x`: both exit 0. Logs build-native.log /
build-s390x.log. New tags preserve original images. Original native tagged
`undo:pre-audit-20261017` before replacing the operational `undo:native` alias.
Full production requirements were FORCE REINSTALLED in ephemeral containers on both
platforms, plus pytest==9.1.1/httpx==0.28.1; pip check PASS, 73 tests PASS each.
Raw logs contain actual x86_64 and s390x Pydantic Core 2.33.2 wheel downloads.
No dependency replacement or custom compatibility fallback was necessary.
Initial `scripts/audit_containers.py`: PASS packaged source hashes, exact versions,
model/weights, read-only UID10001 runtime, isolated HTTP/SSE smoke and actual restarts.

#### Late frontend RED / repair / verification

An isolated pagination browser check PASS (1 in 9.0s), but the complete 13-test run
returned 12 PASS/1 FAIL. Its immediate count assertion checked before the request completed;
investigation also found refresh replacing loaded pages. Archived report
e2e-pagination-failure.json; trace .runtime/audit/pagination-failure.zip.
New unit reproduction: `npm test`, 1 FAIL/8 PASS, pagination-refresh-red.log.
Repair retains/deduplicates loaded pages across overlapping refreshes and validates cursor
and generation before appending. Browser assertion now awaits the exact backend record
count and verifies retention after a new persisted update (stronger assertion).
A transitional TypeScript error TS2345 (optional state) was repaired using an explicit
state guard, keeping strict checking. No type/test requirements relaxed.
Additional burst-gap RED: `npm test`, 1 FAIL/9 PASS, pagination-burst-red.log.
Repair uses the server cursor when a disconnected burst has no overlap with loaded pages,
so missing records can be fetched rather than silently skipped. GREEN 10 unit tests.

Repeated full browser runs then returned 12 PASS/1 FAIL with HTTP 422 during rapid current
timestamp events. Trace/response retained in timestamp-failure.json and
.runtime/audit/timestamp-failure.zip. Actual response: future-event rejection.
`time.get_clock_info('time')` on Windows Python 3.12: GetSystemTimeAsFileTime,
resolution 0.015625s. Browser current UTC could lead that coarse clock within one tick.
Deterministic RED: `pytest tests/test_deep_audit.py -k coarse_clock -q
--junitxml=../docs/audit/clock-red.xml`: 1 FAIL. Repair waits at most one measured tick
(capped at 50ms) before the unchanged strict reducer future check. It does not backdate
events or accept future settlements. Regression also proves a genuinely future event
still rejects without changing cash.

Final native Windows commands, backend cwd:

| Command | Result |
|---|---|
| `../.venv/Scripts/python.exe -m pytest -q --junitxml=../docs/audit/backend-final.xml` | PASS 74, 9.63s, no skips |
| `../.venv/Scripts/python.exe -m ruff check app tests benchmark.py lock_requirements.py audit_*.py` | PASS |
| `../.venv/Scripts/python.exe -m mypy app` | PASS, six sources |

Final frontend cwd, stop-on-error command sequence:
`npm test` PASS 10 (two files); `npm run typecheck` PASS; `npm run lint` PASS;
`npm run build` PASS; `npm run e2e` PASS **13 in 42.4s**, no skips.
JSON report e2e-results.json and audit/e2e-final.json. Production initial JS 232.86kB /
72.48kB gzip, separate chart chunk 359.52kB /104.59kB gzip. Accessibility checks are
actual axe checks of exercised desktop/mobile states, not a blanket certification.

#### Final packaging and platform gates

Both final builds exit 0, root cwd:

```text
docker buildx build --platform linux/amd64 -f deploy/Dockerfile -t undo:audit-final-native --load --progress plain .
docker buildx build --platform linux/s390x -f deploy/Dockerfile -t undo:audit-final-s390x --load --progress plain .
```

Final native index: sha256:87b0928e38d5612fa568350e497da5eaa585112e2eb4ace9d002d134dcad9e24.
Final s390x index: sha256:737cd22ea67b377c47766c5e398816f2b7a9a97dbc46143e8821069ab1805d6f.
Exact Python base manifest rechecked using `docker buildx imagetools inspect
python:3.12.12-slim-bookworm`, exit 0; original pinned index and s390x manifest retained.

Final container tests (root cwd; arch/image/name/XML changed independently per platform):

```powershell
docker run --rm --name undo-audit-final-tests-native --user 0 --platform linux/amd64 --mount type=bind,source=C:/Users/<local-user>/OneDrive/Desktop/UNDO/backend/tests,target=/verify/tests,readonly --mount type=bind,source=C:/Users/<local-user>/OneDrive/Desktop/UNDO/docs/audit,target=/evidence undo:audit-final-native sh -c 'python -m pip install --no-cache-dir pytest==9.1.1 httpx==0.28.1 && python -m pip check && python -m pytest -q -p no:cacheprovider --junitxml=/evidence/container-final-native.xml /verify/tests'
docker run --rm --name undo-audit-final-tests-s390x --user 0 --platform linux/s390x --mount type=bind,source=C:/Users/<local-user>/OneDrive/Desktop/UNDO/backend/tests,target=/verify/tests,readonly --mount type=bind,source=C:/Users/<local-user>/OneDrive/Desktop/UNDO/docs/audit,target=/evidence undo:audit-final-s390x sh -c 'python -m pip install --no-cache-dir pytest==9.1.1 httpx==0.28.1 && python -m pip check && python -m pytest -q -p no:cacheprovider --junitxml=/evidence/container-final-s390x.xml /verify/tests'
```

Native PASS **74 in 9.75s**. Emulated s390x PASS **74 in 57.61s**. Both pip check PASS,
one upstream TestClient warning, no skips. Logs/XML under audit/container-tests-final-*.
`.venv/Scripts/python.exe scripts/audit_containers.py --label final --image-prefix audit-final`:
PASS actual runtime/source hashes/model weights, Python 3.12.12, Pydantic 2.11.7/Core 2.33.2,
health/static/API/event/idempotency/immutable history/SSE and restart persistence for both.
Final isolated ports8082/8083, volumes undo-audit-native-final / undo-audit-s390x-final.
Those test containers were stopped afterward; all volumes/images retained.

#### Live preservation and final local update

Verified online backups before both local updates. The first pre-upgrade verifier falsely
failed on generations.request changing from the original 3 days/100 paths to the browser
audit's 7/1,000; ledger state was equal. The PowerShell sequence continued after the
assertion. The valid pre-upgrade backup was preserved, the comparison corrected to check
immutable history separately from mutable active request, and verification rerun PASS.
Original evaluation settings restored by guarded evaluation; no live reset/cash event.

Final update (each command explicitly checked before proceeding):
`scripts/audit_baseline.py --label before-final-upgrade` PASS; Compose config PASS;
`docker tag undo:audit-final-native undo:native`; `docker compose up -d --no-build` PASS.
An immediate finalizer GET hit RemoteDisconnected while Uvicorn was starting; the utility
now waits on healthy readiness (bounded 30s). Rerun PASS; this was a startup probe, not a
successful check falsely reported. No ledger mutation occurred on that failed GET.

`scripts/audit_finalize.py` PASS restores original 3-day/100-path config, evaluates final
engine, checks unchanged state, persisted SSE replay/no duplicates, healthy model/database.
Frontend `UNDO_AUDIT_READ_ONLY=1 UNDO_AUDIT_LABEL=final node scripts/audit-live.mjs` PASS
after final update: five views, backend result match, desktop/mobile, no page exceptions or
overflow. Screenshots audit/screenshots/live-desktop.png and live-mobile.png inspected.
`scripts/audit_baseline.py --label handoff-final` PASS: integrity ok, full original financial
state and all original history rows retained, evaluation settings unchanged.
Closing tables: generations4/events2/evaluations11/notifications16/audit16; active generation4,
version0, cash10,000,000 paise. Snapshot/hash in audit/handoff-final-state.json.
`docker compose ps`: healthy; native primary remains http://127.0.0.1:8080.

#### Blockers and claims

`docker scout version`: installed v1.24.0. `docker scout cves --format sarif --output
docs/audit/scout-native.sarif --only-severity critical,high undo:audit-native`: BLOCKED,
exit 1, requires Docker login. No scan result/zero-CVE claim and no account change.
Known Python/npm dependency audit baseline passed; pins unchanged throughout this audit.
Real LinuxONE host execution: BLOCKED, no supplied host/access. Public security testing,
load/capacity qualification and real-world model validation: NOT RUN. No unresolved critical
defect found in exercised local workflows; readiness has the documented synthetic limits.

Phase mapping: Phase0 discovery/architecture PASS; Phase1 domain PASS; Phase2 persistence
PASS; Phase3 model/simulation correctness PASS with predictive usefulness PARTIAL; Phase4
API/SSE PASS; Phase5 frontend PASS; Phase6 reliability/browser PASS; Phase7 native/emulated
packaging PASS, real host/OS scan BLOCKED. Audit RED/GREEN/REFACTOR/VERIFY evidence above
extends the original ordered phase records. No commits, pushes, external deployment or
real payments. Current reports: PROTOTYPE_AUDIT.md, ML_AUDIT.md, FINANCIAL_CORRECTNESS.md.

### Closing audit checks — PASS, with documented blockers

`.venv/Scripts/python.exe scripts/audit_restore.py`: PASS, restored the original image/database
pair in NEW volume undo-audit-restore-proof-final, served original state/evaluation/all12
audit rows on isolated8084, verified original backup hash unchanged and live state untouched,
then stopped the proof container. No overwrite of the live volume. See restore-verification.json.

Final-gates XML/JSON aggregation: PASS, 74 tests with zero failures/errors/skips in each of
Windows/native/emulated suites; 13 expected browser passes, zero unexpected/flaky/skipped.
Every final served JS/CSS byte matched frontend/dist; both final packages' app source hashes
matched current source. Actual SHA256 values recorded in audit/final-gates.json.

Visual review found the mobile screenshot was captured before Recharts finished resizing:
PNG869px wide although the subsequently measured document had settled to390px. This was
a screenshot-timing defect. Preserved mobile-before-chart-settle.png, updated the capture
utility to await SVG bounds and assert PNG width390, reran live read-only smoke PASS, and
inspected the corrected390px screenshot. Final desktop/mobile images are actual captures.

`git diff --check`: exit0; existing CRLF-to-LF informational warnings, no whitespace errors.
Git status still contains original intent-to-add source plus untracked audit work; no staged
content, commit or push. Local app remains healthy at8080. Current A–I report:
AUDIT_HANDOFF.md. Final readiness: READY WITH DOCUMENTED LIMITATIONS; real LinuxONE and
Docker Scout OS scan remain BLOCKED, model incremental usefulness remains unestablished.

Maximum permitted configuration probe (backend cwd, project Python, inline read-only
engine invocation): PASS, 5,000 paths/30 days/four alternatives, one warm execution
2,036.82ms; every series31 entries, all floating metrics finite, source state unchanged.
Actual record audit/maximum-configuration.json. This is a boundary check on the small
baseline, not a multi-user/load benchmark; the long horizon extrapolates beyond training.
Final `git diff --check` exit0 and Compose healthy rechecked after documentation updates.

### V3 Phase 5 — PASS

RED: lab endpoints returned 404/405 (2 failed); new UI modules initially absent
(transform error). Timeline evidence test failed with missing Evaluation.timeline.
GREEN: snapshot-only lab APIs, guarded explicit experiment save, evidence center,
Decision Room, sensitivity matrix/tipping regions, policy benchmark, cash quantiles,
settled-cash anchor and backend deadline timeline implemented. UI test initially found
an ambiguous duplicate text selector; repaired to target the intended heading.
TypeScript caught an invalid proposal_id access; corrected to the actual request/current
proposal contract. A PowerShell/Python default-encoding edit introduced one non-UTF8
separator; recovered the bytes and explicitly saved UTF8. REFACTOR: shared display labels
moved out of React component modules; no lint warnings suppressed. Primary downside now
comes from the actual selected action instead of retaining an experimental rank's downside.
VERIFY backend: 87 passed (phase5-backend.xml), Ruff/mypy PASS15 sources. Frontend:
15 passed; strict typecheck/lint PASS. Actual OpenAPI/types/fixture regenerated.
Source-bound held-out model artifact rerun after engine schema change; no ML uplift,
primary rule unchanged. No live ledger, request settings or existing records modified.

### V3 Phase 6 — PASS

RED: provenance regression exposed absent affected_evaluation_ids; two new test fixtures
incorrectly used an unsupported RESERVE_UPDATED event and an existing 200 vs201 contract.
Fixtures corrected to supported RECEIVABLE_DELAYED /201 without changing the API.
GREEN: accepted-event notifications/audit now link affected live evaluation IDs,
new state version and whether recalculation was scheduled. Completed decisions retain
snapshot/policy/recommendation provenance; experiment notifications are distinct.
REFACTOR: common atomic evaluation writer indentation normalized; no schema migration.
VERIFY: full90 backend tests PASS (phase6-backend.xml), Ruff/mypy PASS15 sources.
Tests cover stale-source conflicts, missing-model prescribed stress with primary rule,
experiments preserving pending jobs and latest live result, out-of-order old completions,
plus all prior atomicity/idempotency/concurrency/restart/SSE regressions. Live untouched.

### V3 Phase 7 — PASS

RED: first complete browser run14 PASS/2 FAIL; axe identified eyebrow contrast4.43:1
on new pale surface. GREEN: darkened label, no accessibility rule disabled. Affected2
browser tests PASS; full rerun16 PASS,0 FAIL/0 SKIP (phase7-browser.log/e2e-results.json).
Includes original13 journeys and3 V3 workflows, explicit save/revert/history, stale input,
API-linked charts and live event refresh, failure/loading/retry, keyboard/reduced motion,
WCAG A/AA automated checks and widths1440/768/390 on all five V3 views.
REFACTOR: reuse shared labels, display persisted settings on initial generation load,
explicit experiment history labels, version3.0.0. Actual screenshots in v3/screenshots;
visually inspected desktop Decision Room and mobile stability; no document overflow.
VERIFY: frontend15 tests PASS, typecheck/lint/build PASS; backend90 tests/static gates
passed in Phase6 with unchanged backend. `v3_benchmark.py` PASS: two exact repeated
calculations per workload, paths100/H7 ~0.79–0.84s;1000/H14 ~3.16–3.27s;
5000/H30 ~8.82–9.32s,39 cases capped200 paths. Measurements, not a performance SLA.
`pip_audit -r requirements.txt --no-deps --disable-pip --format json` exit0,
no known runtime dependency vulnerabilities. No synthetic benefit/accuracy claim.

### V3 Phase 8 — PASS for achievable gates; external checks BLOCKED

RED: preserved baseline image printed counterfactual-v2 and failed the actual assertion
that V3 packaging requires counterfactual-v3 (phase8-red.log). GREEN: actual native and
s390x buildx builds --load passed, retaining pinned Python3.12.12-slim-bookworm index,
Pydantic2.11.7/Core2.33.2 and the existing production graph; no dependency fallback.
`docker version`, `docker info`, `docker buildx version`, `docker buildx inspect --bootstrap`
all exited0 (docker-environment.log): CLI/engine29.7.2 available; running builder advertises
s390x. Advertising alone was not used as proof: both images were built and actually run.

Late explanation review: leading alternative now comes from actual experimental ranking,
with a computed reason when its immediate commitment consumes the known mandatory/reserve
budget, or the disclosed rule order otherwise. First added test assumed full was the
leading alternative, but it was hold for that sample; corrected that mistaken fixture
and added a separate full/partial-only budget counterexample. Final Windows91 tests PASS,
Ruff/mypy PASS15 sources, actual API/fixture re-exported. Both images rebuilt after repair.
No eligibility-model core source or weights changed; source-bound benchmark remains valid.

REFACTOR/repairs: packaged test runner initially failed Windows stdout decoding, then
stdout encoding, before completing report collection. Explicit UTF8 fixed both. Native
networked rerun91 passed; intermittent PyPI downloads slowed the target install. Stopped
only the identified owned target installer (exit137; no target test success claimed for
that run). Downloaded the exact pure-Python test wheels through host pip cache; hashes in
test-wheels.json. Runner now installs them --no-index/--no-deps with --network none, using
each image's original production dependencies. No incompatible dependency substitution.
One attempted log redirection hit an existing running process's file lock; retried with
a separate offline output path, no result inferred from the failed launch.

VERIFY commands from root:
- `docker buildx build --platform linux/amd64 -f deploy/Dockerfile -t undo:v3-native --load --progress plain .`: exit0.
- Same with linux/s390x /undo:v3-s390x: exit0.
- `.venv/Scripts/python.exe scripts/v3_container_tests.py`: exit0; native91 PASS/0 FAIL/0 SKIP11.58s;
  emulated s390x91 PASS/0 FAIL/0 SKIP111.60s. container-tests-offline.log and per-arch logs.
- `.venv/Scripts/python.exe scripts/audit_containers.py --label v3-verified --image-prefix v3 --expected-engine counterfactual-v3 --evidence-dir docs/v3`:
  exit0. Current native/s390x source hashes match host; model weights/version match each other;
  Python3.12.12 /Pydantic2.11.7 /Core2.33.2 imports; pip check; actual HTTP/static assets/SSE,
  idempotency/historical evaluation/recalculation, persisted events/state/evaluation across
  actual container restart PASS independently. Initial v3-final candidate output retained;
  v3-verified records identify the final rebuilt images.
- `.venv/Scripts/python.exe scripts/v3_recovery.py`: exit0; pre-release backup on fresh
  isolated volume served under preserved V2 and V3; V3 recalc/restart preserved state.
  Schema1 unchanged. Rollback requires backup with old image because strict V2 models
  cannot consume new JSON fields; recovery.json and deployment.md explain procedure.
- `.venv/Scripts/python.exe scripts/v3_activate.py`: exit0; docker tag then compose up
  --no-build, healthy; guarded recalculate queues the original request verbatim.
- `node scripts/v3-live.mjs` from frontend: initial runner failed axe's explicit-context
  requirement; changed browser.newPage to browser.newContext/newPage and reran. PASS
  five views x three widths (1440/768/390), including populated ephemeral lab;0 axe
  violations/page errors/document overflow. Actual PNG widths asserted. Reset scroll/focus
  after accessibility analysis to avoid sticky-sidebar capture offset; screenshots refreshed.
  Browser checks never saved an experiment, posted an event/reset or changed settings.
- `.venv/Scripts/python.exe scripts/v3_preserve.py final` and `... delivery`: exit0;
  online backups/integrity/isolated restore PASS. Generation4/version0/10,000,000 paise,
  raw14-day/100-path request and demo cursor0 unchanged. Every original generation/event/
  evaluation/notification/audit row retained. Evaluations15->16, notifications/audit20->21
  due solely to the V3 calculation; events remain2. Current ledger/snapshots/settings verified.

Current native image index78e481c7ed9657e45e56b64235d69ad0ebf6d69f7eb4d537e97223be5e5cb14f;
s390x9ea9cb788b85bfb4c6bf0dfc97cc00e8e9415621b9465939c930ac23e5a82f98.
Preserved pre-V3 image alias undo:v3-baseline-native; original volumes/source kept.
Only owned temporary verification containers stopped/removed; no Docker volume removed.
No commits, pushes, external deployment/publication, paid infrastructure or real payments.

BLOCKED: actual IBM LinuxONE execution — no real target host/access available. Emulated
s390x success is a separate claim. BLOCKED: `docker scout cves undo:v3-native --only-severity
critical,high` exit1, requires Docker login. Dependency npm/pip audits passed with0 reported
vulnerabilities; OS/image-layer scanning remains unverified. Original deprecation warning
in Starlette/httpx persists without failing tests. No hidden P0 issue observed in executed
gates. Nonessential multivariable sensitivity/quantile-band enhancements are not implemented;
bounded one-factor calculations, accessible evidence and all core V3 workflows are working.

Required docs updated: README, PROTOTYPE_AUDIT, FINANCIAL_CORRECTNESS, ML_AUDIT,
DECISION_ROBUSTNESS, V3_RELEASE_NOTES, financial-model, architecture and deployment.
Readiness: READY WITH DOCUMENTED LIMITATIONS for the controlled synthetic environment.

## Final defect repair — Phase 0 preservation PASS

2026-10-17. Full repair directive, AGENTS, current source/tests/config/docs and Git
staged/unstaged/untracked status inspected. No staged content existed; original index
entries include intent-to-add files, with essential V3 modules still untracked. Captured
original index/status/staged diff and298-source-file ZIP under .runtime/final-repair.
Live Compose remains healthy at8080; authoritative volume undo-demo_undo_data unchanged.
Actual baseline: generation5/version3/cash11,600,000 paise,7-day/5000-path request,
demo cursor3; generations5/events7/evaluations27/notifications38/audit38/jobs0.
Online SQLite backup .runtime/final-repair/before.db, integrity and independent temporary
restore PASS, live API state matches. Source and DB preservation performed before app edits.
Baseline commands: backend pytest91 PASS; frontend npm test15 PASS (actual output checked).
RED/GREEN/REFACTOR: prior review reproduced UI defects using isolated response fixtures;
current preservation uses explicit closed SQLite connections and never overwrites backups.
VERIFY preservation PASS. No live reset/event/evaluation/settings write; no staged changes.

### Final repair Phase 1 — PASS

RED: decision-binding.test.tsx4 FAIL against original UI. GREEN: immutable evaluation
request association checks proposal/horizon/paths/seed/action set; unrelated result,
comparison/chart/explanation removed with Evaluation required. Same-input old-state
results remain explicitly STALE; dependent analysis disabled. Historical snapshot uses
its own proposal/settings with controls disabled. REFACTOR: shared decisionContext helper;
no financial calculations added to React. Initial strict check caught fixture tuple/
literal types and an invalid Testing Library option; corrected typed fixture boundaries.
VERIFY:4 targeted tests PASS; typecheck/lint PASS; frontend19 PASS. Browser2 PASS against
isolated actual APIs: two distinct proposals/recommendations, settings invalidation,
return-to-A and delayed-A completion. Commands: vitest decision-binding; npm test;
playwright e2e/repair.spec.ts --grep phase1. Evidence: docs/repair/phase1-*.log.

### Final repair Phase 2 — PASS

RED: new exact race/out-of-order/failure tests3 FAIL (existing2 PASS). GREEN: canonical
ordered input/state fingerprint plus monotonic request serial associates every completed
result with its originating draft; dirty drafts hide results and invalidate in-flight
responses. Only matching successful reviewed snapshots can Save. Older success/failure/
finally callbacks cannot replace newer state; save payload is the reviewed immutable body.
REFACTOR: shared invalidation handles form edits and Revert; unmount invalidates requests.
VERIFY: lab5 tests PASS, typecheck/lint PASS; browser exact1000->2000 race PASS using real
isolated backend calculations/save, persisted experiment contains200000 paise; live ledger
untouched. Evidence: phase2-red.log, phase2-browser.log. Failure/out-of-order cases are
exercised with held promises, not timing sleeps or favorable network assumptions.

### Final repair Phase 3 — PASS

RED:6 backend historical/shared-representation API tests FAIL,2 UI display tests FAIL.
GREEN: one denominator-aware classification report (value/defined/numerator/denominator/
status/reason/counts) serves Model Evidence and read-time DecisionRecord presentation.
Zero-denominator precision/recall/F1 are independently undefined; positive denominators
with numerator0 remain0. Historical missing/invalid counts are unverified/unavailable.
Raw evaluation metadata and audit rows are not rewritten. REFACTOR: shared MetricValue
component formats both views; raw classification zero values removed from user-facing
metric lists while API raw history retained separately. Training/weights/threshold/core
ranking untouched, source-bound validation artifact remains valid.
VERIFY:97 backend PASS, Ruff/mypy16 PASS; frontend24 PASS, typecheck/lint PASS; browser
phase3 actual API/display consistency and unchanged raw historical evaluation PASS.
OpenAPI/types and computed fixtures regenerated; evidence in phase3-red/ui-red/browser logs.

### Final repair Phase 4 — PASS

RED:2 context/direct-link tests FAIL against pre-fix implementation (prior4 association
checks PASS). GREEN: stable proposal, seed, action set and horizon/path context passes
from Decision Room into Lab. Target supplier/ID/amount/date/source state are visible;
explicit selector replaces silent first-proposal fallback. URL hash query preserves
selected context over refresh/direct entry/back/forward. Invalid or removed target shows
selection error, disables evaluation/save and requires explicit replacement. Draft changes
remain hypothetical. REFACTOR: bounded link parser/serializer shares existing routing;
no state-management library. Existing API settings outside preset dropdowns now display
as explicit values rather than blank selections. Canonical Lab fingerprint includes target
and inherited simulation settings. Regression Revert selector updated to distinguish
persistent target context from the cleared result (assertion retained that result is gone).
Browser's initial5-second save assertion expired during real1000-path14-day analysis;
now awaits and asserts the actual successful response before checking Save, with no
relaxed result assertion. VERIFY:26 frontend tests PASS, strict checks/lint/build PASS;
phase4 browser PASS including real correct-proposal POST, refresh, removed target,
explicit reselection and no implicit financial-state mutation. Live unchanged.

### Final repair Phase 5 — PASS

RED: package_submission.py failed on missing required FINAL_REPAIR_REPORT.md.
GREEN: explicit114-file curated manifest (plus generated hash index) ships current
working bytes, including synthetic validation runtime asset, source/test/deployment/
docs pins, without relying on HEAD. README directs to current UNDO_V3_HANDOFF;
older release instructions retain content with superseded notices. Compose accepts
isolated port/image overrides; default existing project/volume are preserved.
REFACTOR: deterministic stable ZIP order/timestamps, CRC/hash/complete-inventory
verification; forbidden paths/credentials/missing files fail closed.
VERIFY: scripts/test_package_submission.py3 PASS (missing source, tampered/missing
archive member, excluded paths). scripts/package_submission.py PASS,115 members,
114 content hashes verified. Inventory and explicit selective-staging list recorded
under docs/repair; only new manifest-listed project files staged, all pre-existing
index entries preserved byte-for-byte. No commit/push. Exclusions are local state,
secrets, caches/bundles and host-specific historical logs/helpers. Clean extraction
remains NOT RUN until Phase6. Repeat-build determinism is checked below.

### Final repair Phase 6 — initial candidate FAIL; diagnosed and repaired

Candidate SHA256 b14b413d1af3f58e274fe5969fd2128ff81efcbdaad4b7cecd02cf8b4db109c7
extracted independently under AppData/Local/Temp/undo-submission-candidate-l7m0gs47.
No workspace source/dependencies copied. Fresh venv/pip requirements-dev install,
npm ci PASS. Backend97, frontend26, Ruff, mypy16, typecheck/lint/build PASS.
Full browser21 executed:19 PASS,2 FAIL (retained clean-browser.log and traces).
Race test's5s Save assertion expired near a successful real response; changed to
explicitly hold/assert the current200000-paise response, verify Save disabled while
held, then assert successful Evaluate/Save HTTP responses and the original UI/body/
ledger checks. Added60s whole-journey budget; no result assertion weakened.
Second failure was a related Phase4 navigation regression: deferred effect URL writes
coalesced rapid clicks; normalization also pushed redundant history. New unit RED1/7
then GREEN7/7 after immediate explicit-navigation writes and replaceState normalization,
wordmark prevents duplicate default entry. Original frontend27 PASS. Targeted browser
retry2 PASS including unchanged back/forward case; typecheck/lint/build PASS.
Runtime native/s390x builds from extracted context PASS; actual imports x86_64/s390x,
Python3.12.12/Pydantic2.11.7/Core2.33.2; source hashes match extracted app. Both
container test suites97 PASS. Native smoke/restart PASS; s390x initial cold readiness
45s timeout FAIL preserved, healthy retry and health-awaited restart PASS unchanged
smoke assertions. Only fresh isolated volumes/8085/8086; no live reset or writes.
Docker CLI/engine29.7.2 and Buildx0.36.1 available; builder supports linux/s390x;
exact pinned Python manifest independently inspected, s390x present. Scout exit1
requires Docker login; actual LinuxONE execution BLOCKED without host/access.
First orchestrator printed Unicode failure log through cp1252 and stopped; fixed
its external stdout encoding. No application code bypassed. Remaining audits and
regenerated archive verification follow; Phase6 is not yet a passing gate.

Phase6 retry candidate64aa6740b2b475af51601ebeb8225aa6144c5c2d9fbb1a70e2c766adbe9a906b:
uv0.11.32 fresh environment/declared dependency install PASS. Candidate INCOMPLETE:
new navigation test used Testing Library's unsupported exact option; original
typecheck/build and both extracted Docker builds FAIL (no image replaced). Corrected
new test selectors to anchored names; original typecheck/lint/build rerun PASS.
Stopped only owned clean2 verifier process tree during npm install, preserving temp
files/logs; no unrelated process or live application touched. Will extract a corrected
archive again; no source is patched into an extracted verification directory.

Phase6 corrected candidate326d5ae425512c7f0c85e53ea6736bc7003f862dd71278a647f7a31a3122a969:
fresh uv environment/pins/npm lock installation PASS; backend97, frontend27, Ruff,
mypy16, typecheck/lint/build, npm audit0 advisories, pip runtime audit0 advisories,
packaging3 and archive115-member integrity PASS. Browser20 PASS,1 FAIL: legacy
flagship audit selector assumed only one experiment across all retained generations.
The newly passing race/save test legitimately added another retained experiment.
No history was deleted. Updated flagship test awaits/asserts actual Save response,
filters exact saved generation and verifies the GET uses the saved evaluation ID;
all original model/ledger/history assertions retained. Targeted flagship retry1 PASS;
typecheck/lint PASS. New archive/extraction required for this test-only correction.
Native/s390x rebuilt corrected UI images PASS; native runtime/restart PASS, target
verification continues with explicit health readiness. Production screenshots from
clean archive inspected: mobile Lab390 and desktop overview1440 preserve design.

### Final repair Phase 6 — PASS after repair and fresh extraction

Verified archive SHA2562a9beb4fff58a3d70ef45cd31e2ea3fc82fd8d76168fe20b69d77bbb4787a032
extracted independently to AppData/Local/Temp/undo-submission-clean4-iax3p3o0.
All15 executed command gates PASS: fresh uv/Python3.12.13 declared dependency install,
npm ci --prefer-offline --no-audit, backend97, Ruff, mypy16, frontend27, typecheck,
lint, production build, full browser21, npm audit0 advisories, pip runtime audit0
advisories, packaging3 and actual archive115-member/114-content-hash verification.
Commands, working directories, exit codes and actual logs: docs/repair/clean4-*.
No file copied from workspace into extraction, no original environment packages used.
Native and s390x image builds from this extraction PASS. Both verified runtimes'
backend hashes and static asset hashes equal this extraction's production build;
native/s390x HTTP/static/events/audit/SSE and actual restart probes PASS. Earlier
97-test native/emulated suites remain applicable to byte-identical backend/tests
and pinned runtime; model/core financial sources and validation asset match the
preserved source-before.zip exactly. Stage6 failures/retries remain in prior entries.
Proceeding to Phase7 final original-workspace regression and data preservation.

### Final repair Phase 7 — PASS for all achievable source-cut gates

18 October2026. Original workspace rerun: backend97, Ruff, mypy16, frontend27,
typecheck/lint/build, full browser21, npm audit0 advisories, pip runtime audit0
advisories, packaging regressions3 and actual archive-integrity check PASS.
Actual commands/cwd/exit codes: docs/repair/phase7-original.json and phase7-*.log.
Read-only pre-upgrade online backup showed all raw rows exactly equal to Phase0.
Verified native image activated locally using same undo-demo_undo_data volume;
previous image preserved as undo:before-final-repair-20261018-d628bf4c. New running
image8f5b31941645c5f396fa61123a957ff8011a1254cca8085824abef5b22d238bd healthy.
Read-only actual8080 browser PASS: current recommendation/cash,5000 paths, correct
Lab supplier/refresh, same undefined precision in both views, mobile overflow and
zero page errors; no POST/mutation requests. Post-upgrade online backup integrity
and exact comparisons to both earlier backups PASS: all7 tables/raw rows/settings/
request/demo cursor preserved (generation5/version3/cash11600000paise,7events,
27evaluations,38audit,38notifications,0jobs). Core engine/prediction/policies/domain
and synthetic validation artifact byte-identical to original source snapshot.
Source diff reviewed: only targeted UI/metric API presentation, fixtures/tests,
packaging/config/docs and generated test evidence. Git diff/check and staged check
PASS.57 explicitly identified missing manifest project files selectively staged;
all76 pre-existing index entries retained. No commit/push/external deployment,
real payment, live reset, volume/image deletion or unrelated infrastructure.

Final documentation cut includes current handoff and repair report. The regenerated
final artifact's exact checksum/listing/integrity and independent post-cut execution
record are in dist/UNDO-V3-SUBMISSION.* and dist/UNDO-V3-VERIFICATION.json. This
external record is the authoritative continuation for commands after the ZIP cut;
putting the ZIP's own checksum inside itself would change it. Production source and
tests are frozen at this fully verified cut; post-cut checks do not assume success.
Remaining BLOCKED gates: real LinuxONE host execution (no host/access), Docker Scout
OS-layer scan (login required). Synthetic ML has no established decision uplift.

## GitHub publication preparation — user authorized public repository UNDO

The user explicitly authorized GitHub upload and selected a PUBLIC repository named
UNDO. This supersedes the earlier no-commit/no-push restriction for this publication.
Inspection: local master branch has no commits or remote; existing staging and all
local files were captured under .runtime/github-publication before changes. GitHub
CLI2.86.0 is installed, but saved credentials were invalid; browser device login
was started. Publication remains pending until successful authorization.

The upload is curated from submission-manifest.json rather than git add -A. Live
financial databases/backups, .env, caches, installed dependencies and machine-specific
historical evidence directories are excluded. Absolute Windows user-profile names
were redacted from this public log; original bytes are retained privately. Published
verification documents identify redacted machine paths explicitly, preserve actual
results/checksum and do not introduce new test claims. Financial/application source
is unchanged. The earlier verified submission ZIP and checksum remain unchanged.

GitHub authorization PASS: active account Trek91 via browser device login. Target
Trek91/UNDO did not exist. Curated116-file scan PASS: no detected credentials or
unredacted local profile paths; no databases/.env/caches in selected paths. Commit
author will use Trek91's GitHub noreply address; existing global Git identity remains
unchanged. No application code/pins or original verified ZIP bytes changed.
