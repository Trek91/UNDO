# UNDO V3 — final repair and submission report

Current guide: [UNDO_V3_HANDOFF.md](UNDO_V3_HANDOFF.md).
Execution history, including failures: [BUILD_LOG.md](BUILD_LOG.md).

## Current result — 18 October 2026

PASS: requested source corrections and final original-workspace regression.
PASS: independent clean-archive installation and all21 browser journeys.
The fully tested source cut is ready with the limitations below. The exact final
ZIP receives a further independent post-cut verification, recorded alongside it
in [portable submission verification](SUBMISSION_VERIFICATION.json). That external
record contains its actual SHA-256, commands and outcomes; keeping the digest
external avoids changing the archive whose bytes are being verified.

The corrected app is running locally at http://127.0.0.1:8080. Read-only actual
browser checks passed: current recommendation,5000-path setting, Lab target/refresh,
shared undefined-precision display, mobile overflow and zero page errors. No live
mutation request was made. Previous image is preserved under the local alias
undo:before-final-repair-20261018-d628bf4c; the same undo-demo_undo_data volume remains.
No real payments, commits, pushes, volume/image deletion or external deployment.

## Findings, root causes, changes and regression evidence

| Original finding | Root cause and changed files | Executed regression / outcome |
|---|---|---|
| Wrong proposal recommendation | App.tsx reused latest evaluation without matching the selected request. frontend/src/lib/decisionContext.ts now binds proposal, horizon, paths, seed and action set. Unrelated comparison/chart/explanation is removed; state/engine changes visibly mark saved history stale. | decision-binding.test.tsx A–D: original4 RED, then PASS. Actual repair.spec.ts two proposal/late-A journeys PASS. |
| Lab input race / wrong Save snapshot | ScenarioLab.tsx accepted responses without draft identity. Canonical input/state fingerprint plus monotonic request serial guard success/error/finally/Save; edits invalidate immediately and Save posts the reviewed body. | lab.test.tsx original2 PASS/new3 RED→all5 PASS. Real1000→2000 held-response/payload/ledger browser PASS. Out-of-order, failed current request, edited successful input and exact saved snapshot asserted. |
| Precision inconsistency | Legacy numeric0 was shown despite zero denominator. backend/app/metric_reporting.py provides structured value/defined/numerator/denominator/status/reason/counts; main.py/evidence_types.py/model_evidence.py expose it consistently. MetricValue.tsx is shared by Explanation and ModelEvidence. | test_metric_reporting.py6 RED→PASS; metric-reporting.test.tsx2 RED→PASS; actual API/text/history browser PASS. Independent precision, recall and F1 denominators, zero values with positive denominator and unavailable missing historical counts all tested. |
| Wrong Lab target | Selected context was not passed. App.tsx/decisionContext.ts/ScenarioLab.tsx carry stable proposal/settings, identify supplier/amount/date/source state and persist bounded URL context. Missing target requires explicit replacement. | context unit2 RED→PASS; real POST targets B with inherited14-day/1000-path settings, refresh/direct entry, removed target/reselection and unchanged ledger PASS. |
| Related back/forward regression | Deferred URL effects could coalesce rapid clicks and normalization pushed history entries. Explicit navigation now writes immediately; normalization uses replaceState; wordmark prevents duplicate default navigation. | Added unit1 RED/6 existing PASS→7 PASS; unchanged existing browser back/forward journey PASS. |
| Missing release files / obsolete instructions | Essential V3 modules were untracked; older handoffs conflicted. Explicit submission-manifest.json, deterministic package_submission.py and authoritative handoff now distribute current working bytes. | Missing required report caused actual packaging RED. Missing-source/tamper/missing-member/excluded-path tests3 PASS; full manifest/CRC/hash checks PASS.57 identified missing project files selectively staged;76 pre-existing index entries preserved exactly. |

Metric corrections are read-time presentation only: DecisionRecord.model_statistics
is distinguishable from original evaluation.metadata.model_metrics. Every original
stored evaluation/audit value remains unchanged. Engine, prediction, policy, domain
and synthetic validation artifact match the preserved baseline bytes exactly.
Weights, training data, threshold, financial calculations and ranking are unchanged.
API schema/types and computed synthetic fixtures were regenerated from actual code.

## Executed verification — original workspace versus extracted package

Clean passing candidate SHA256:
2a9beb4fff58a3d70ef45cd31e2ea3fc82fd8d76168fe20b69d77bbb4787a032.
It was extracted outside the workspace to an independent AppData/Local/Temp
undo-submission-clean4 directory. No source/dependency files were copied from the
original checkout. External prerequisites were Python3.12, Node24.12/npm, installed
Chrome, Docker/Buildx, network/cache and documented optional uv0.11.32 installer.
Standard venv/pip installation also passed from the first independent extraction.

| Check | Original workspace Phase7 | Independent clean candidate |
|---|---|---|
| Backend pytest | PASS97 | PASS97 |
| Ruff / mypy | PASS / PASS16 source files | PASS / PASS16 |
| Frontend unit tests | PASS27 | PASS27 |
| Typecheck / ESLint / production build | PASS | PASS |
| Full Playwright browser suite | PASS21 | PASS21 |
| npm audit / pip runtime audit | PASS0 reported advisories | PASS0 reported advisories |
| Packaging regressions | PASS3 | PASS3 |
| Archive manifest / CRC / individual hashes | PASS | PASS115 members /114 indexed files |
| Native and s390x build | PASS from extracted context | PASS independently |
| Native / emulated s390x backend tests | PASS97 each in packaged runtimes | Same exact backend/tests/pins |
| HTTP/static/event/idempotency/SSE/audit/restart | PASS on isolated native and s390x volumes | PASS; backend/static hashes equal extracted production output |
| Existing live database / settings / history | PASS all raw rows exactly unchanged | Only separate temporary DBs/volumes used |

Actual commands (backend working directory):

```powershell
../.venv/Scripts/python.exe -m pytest -q
../.venv/Scripts/python.exe -m ruff check app tests benchmark.py
../.venv/Scripts/python.exe -m mypy app
../.venv/Scripts/python.exe -m pip_audit -r requirements.txt --no-deps --disable-pip
```

Actual commands (frontend working directory):

```powershell
npm test
npm run typecheck
npm run lint
npm run build
npm run e2e
npm audit
```

Clean setup used uv venv --python <Python3.12 executable> --seed .venv,
uv pip install --python .venv/Scripts/python.exe -r backend/requirements-dev.txt,
and npm ci --prefer-offline --no-audit; audit was separately executed afterward.
Root commands: Python scripts/test_package_submission.py and package_submission.py
--verify <actual ZIP>. Docker buildx build --platform linux/amd64 and linux/s390x
-f deploy/Dockerfile --load . executed separately. See handoff for complete runtime
and container-test commands. All command working directories, exit codes and logs
are retained under docs/repair in the engineering workspace. Final exact artifact
commands/results are in the external SHA-bound verification record.

## Failures found during clean validation — retained, diagnosed, repaired

| Attempt | Actual outcome / repair |
|---|---|
| First candidate b14b413d... | Backend97/frontend26/strict/build PASS; browser19 PASS,2 FAIL. Race test's5s UI assertion expired near successful current-response completion; it now holds/asserts the new response too, verifies Save disabled while held, releases/asserts200, and awaits Save response. All original input/body/ledger assertions remain. Second failure reproduced the navigation bug fixed above. |
| Second candidate64aa6740... | INCOMPLETE. New unit selector incorrectly used Testing Library exact option; strict TypeScript and both container builds correctly failed. Corrected to anchored names; type/lint/build passed. Only owned verifier tree stopped during npm installation; no files patched into extraction. |
| Third candidate326d5ae4... | Backend97/frontend27/strict/build/audits/package PASS; browser20 PASS,1 FAIL. Legacy flagship audit selector matched experiments across two retained generations after the race test saved one. It now filters the exact saved generation and asserts the GET opens that saved evaluation ID. Original assertions retained; targeted retry PASS. |
| Fourth candidate2a9beb4f... | Fresh extraction: all15 command gates PASS, including full21 browser journeys. |
| First emulated cold smoke |45s readiness deadline expired before s390x became healthy; failure log retained. Unchanged smoke passed once healthy. Later probes explicitly await Docker health before smoke/restart assertions. |
| External orchestration | First runner could not print Unicode failure log through cp1252; stdout encoding corrected. This did not change application logic or test assertions. |

## Historical integrity and core preservation

Online backup/independent restore passed before changes; another backup was taken
before local update. After update and read-only browser inspection, all raw rows in
all tables equal both preserved snapshots exactly: generations5, settings1,
events7, evaluations27, jobs0, notifications38, audit38. Financial state remains
generation5/version3/cash11,600,000 paise; raw7-day/5000-path/seed20261017 request,
action set and demo cursor3 unchanged. Source diff was reviewed against the298-file
pre-repair snapshot. Changes are limited to required UI/API presentation, regression
fixtures/tests, packaging/config/docs and generated test evidence. Git diff and
staged diff whitespace checks PASS. No unrelated source or user data was changed.

## Submission packaging

Manifest: submission-manifest.json,114 explicit files categorized as runtime,
testing, deployment or documentation; SUBMISSION_CONTENTS.json adds the115th member.
Source is current working-tree bytes, not Git HEAD. No commit/push was made.
Includes frontend/backend/financial/simulation/model source, typed API, tests,
fixtures, pinned specifications and frontend lockfile, deployment/templates,
SQLite schema/demo initialization in source, and synthetic runtime evidence
backend/app/evidence/validation.json. The required evidence artifact is included;
models are deterministic code with no separate private weights asset. Frontend
requires no external public-asset directory. Generated bundles are rebuilt.

Excluded intentionally: live DBs/user state/backups, .env/credentials, .git,
virtual environments, node_modules, caches/bytecode, generated bundles/test logs,
historical screenshot directories and host-specific release helpers. Historical
markdown content remains with superseded notices. Detailed inventory and staging
snapshots remain in the workspace; no sensitive state capture is shipped.

Output: dist/UNDO-V3-SUBMISSION.zip, sibling .zip.sha256, .contents.txt,
.integrity.json and UNDO-V3-VERIFICATION.json. CRC, duplicate/unsafe path checks,
manifest membership and every indexed content hash are verified against actual
archive bytes. Fixed timestamps and sorted entries produce identical SHA256 for
identical input bytes. A missing required file fails closed. The final SHA checksum
and exact post-cut extraction outcomes are external so that recording them does
not invalidate the artifact. All required setup/build/test tools are in the ZIP.

## Limitations / unresolved gates

BLOCKED: real IBM LinuxONE execution — no real target host/access supplied. Native
amd64 and emulated s390x are independently verified claims. Exact pinned Python
3.12.12 slim-bookworm manifest includes s390x; actual images import Pydantic2.11.7
and Core2.33.2 without custom fallback. Docker CLI/engine29.7.2, Buildx0.36.1 and
builder target support were inspected; engine availability is distinct from CLI.

BLOCKED: Docker Scout OS/image-layer scan — exit1 requires Docker login. npm/pip
0-advisory checks do not establish complete security. Existing TestClient/httpx,
ESLint-support and whatwg-encoding deprecation warnings remain non-failing.
ML is experimental synthetic evidence, with no demonstrated incremental decision
uplift over the obligation-aware rule and no real-world accuracy claim. No public/
multi-user authentication/tenant isolation/TLS or real bank connection is supplied.
Multivariable sensitivity and quantile bands remain nonessential unimplemented
enhancements. These are documented limits, not hidden passing requirements.

## Formerly untracked project files — disposition

57 manifest-owned project files were selectively staged. All76 pre-existing index
entries were preserved. No unrelated change was staged, committed or pushed.

- `backend/app/analysis_types.py` — included in manifest; selectively staged.
- `backend/app/decisions.py` — included in manifest; selectively staged.
- `backend/app/evidence/validation.json` — included in manifest; selectively staged.
- `backend/app/evidence_types.py` — included in manifest; selectively staged.
- `backend/app/lab.py` — included in manifest; selectively staged.
- `backend/app/metric_reporting.py` — included in manifest; selectively staged.
- `backend/app/model_evidence.py` — included in manifest; selectively staged.
- `backend/app/policies.py` — included in manifest; selectively staged.
- `backend/app/results.py` — included in manifest; selectively staged.
- `backend/app/robustness.py` — included in manifest; selectively staged.
- `backend/app/scenarios.py` — included in manifest; selectively staged.
- `backend/audit_model.py` — included in manifest; selectively staged.
- `backend/audit_policies.py` — included in manifest; selectively staged.
- `backend/audit_runtime.py` — included in manifest; selectively staged.
- `backend/export_v3.py` — included in manifest; selectively staged.
- `backend/tests/test_deep_audit.py` — included in manifest; selectively staged.
- `backend/tests/test_metric_reporting.py` — included in manifest; selectively staged.
- `backend/tests/test_v3_api.py` — included in manifest; selectively staged.
- `backend/tests/test_v3_contract.py` — included in manifest; selectively staged.
- `backend/tests/test_v3_evidence.py` — included in manifest; selectively staged.
- `backend/tests/test_v3_policies.py` — included in manifest; selectively staged.
- `backend/tests/test_v3_realtime.py` — included in manifest; selectively staged.
- `backend/tests/test_v3_robustness.py` — included in manifest; selectively staged.
- `backend/tests/test_v3_timeline.py` — included in manifest; selectively staged.
- `backend/v3_benchmark.py` — included in manifest; selectively staged.
- `backend/v3_validate_model.py` — included in manifest; selectively staged.
- `docs/AUDIT_HANDOFF.md` — included in manifest; selectively staged.
- `docs/DECISION_CONTRACT.md` — included in manifest; selectively staged.
- `docs/DECISION_ROBUSTNESS.md` — included in manifest; selectively staged.
- `docs/FINAL_REPAIR_REPORT.md` — included in manifest; selectively staged.
- `docs/FINANCIAL_CORRECTNESS.md` — included in manifest; selectively staged.
- `docs/ML_AUDIT.md` — included in manifest; selectively staged.
- `docs/PROTOTYPE_AUDIT.md` — included in manifest; selectively staged.
- `docs/UNDO_V3_HANDOFF.md` — included in manifest; selectively staged.
- `docs/V3_PLAN.md` — included in manifest; selectively staged.
- `docs/V3_RELEASE_NOTES.md` — included in manifest; selectively staged.
- `frontend/e2e/repair.spec.ts` — included in manifest; selectively staged.
- `frontend/e2e/v3.spec.ts` — included in manifest; selectively staged.
- `frontend/scripts/audit-live.mjs` — included in manifest; selectively staged.
- `frontend/scripts/v3-live.mjs` — included in manifest; selectively staged.
- `frontend/src/components/DecisionIntelligence.tsx` — included in manifest; selectively staged.
- `frontend/src/components/MetricValue.tsx` — included in manifest; selectively staged.
- `frontend/src/components/ModelEvidence.tsx` — included in manifest; selectively staged.
- `frontend/src/components/ScenarioLab.tsx` — included in manifest; selectively staged.
- `frontend/src/lib/decisionContext.ts` — included in manifest; selectively staged.
- `frontend/src/lib/decisionLabels.ts` — included in manifest; selectively staged.
- `frontend/tests/decision-binding.test.tsx` — included in manifest; selectively staged.
- `frontend/tests/lab.test.tsx` — included in manifest; selectively staged.
- `frontend/tests/metric-reporting.test.tsx` — included in manifest; selectively staged.
- `frontend/tests/model-evidence-fixture.json` — included in manifest; selectively staged.
- `frontend/tests/v3-fixture.json` — included in manifest; selectively staged.
- `frontend/tests/v3.test.tsx` — included in manifest; selectively staged.
- `frontend/tests/workspace.test.tsx` — included in manifest; selectively staged.
- `scripts/container_tests.py` — included in manifest; selectively staged.
- `scripts/package_submission.py` — included in manifest; selectively staged.
- `scripts/test_package_submission.py` — included in manifest; selectively staged.
- `submission-manifest.json` — included in manifest; selectively staged.
