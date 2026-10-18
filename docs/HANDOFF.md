> Historical / superseded release instructions and verification snapshot.
> Use [the current V3 handoff](UNDO_V3_HANDOFF.md) and [final repair report](FINAL_REPAIR_REPORT.md)
> for the submitted build. Prior findings and measurements below are preserved.

# UNDO engineering handoff

> Historical original-build handoff. The current audited application, corrected findings,
> final counts/image IDs and readiness are in [AUDIT_HANDOFF.md](AUDIT_HANDOFF.md).
> The material below records the earlier build and is retained as history.

## A. Product delivered

UNDO is running at **http://127.0.0.1:8080/** in a native production container. It has a complete responsive React dashboard, current financial position, obligations/receivables, payment evaluation, four contract-aware alternatives, real risk/cost comparisons, cash-flow charts and exact data tables, computed recommendations/explanations, controlled event feed, event entry, editable synthetic scenarios, stale/historical evaluations, persistent audit history and intentional demo reset. No real payments are initiated.

## B. Architecture

React 19 / strict TypeScript / Vite 8 with Lucide and Recharts 3. Generated OpenAPI types connect the frontend to FastAPI 0.143.3 / Starlette 1.8.0 / Pydantic 2.11.7 / Pydantic Core 2.33.2 / Uvicorn. SQLite uses atomic financial writes, idempotent event IDs, validated chronological replay, immutable initial generations and evaluation snapshots. A durable pending-work table, single calculation worker and persisted SSE cursors support event-driven recalculation and reconnection. Only confirmed synthetic settlements change actual cash.

Prediction is a trained standard-library logistic daily hazard model. The simulator uses common random scenarios and integer-paise cash arithmetic, separately measures funding deficits, mandatory deadline shortfalls, supplier lateness and desired-reserve breaches, applies contractual schedules/penalties and ranks feasible candidates with the documented lexicographic objective. No external LLM, paid API or financial connector is required.

## C. Implementation phases

| Phase | Status | Evidence |
|---|---|---|
| 0 Discovery | PASS | Empty repository preserved; runtimes, four Docker checks, exact base manifests and native/target dependencies verified |
| 1 Domain | PASS | Monetary/time/cash/settlement/event invariants and identity conflicts tested |
| 2 Persistence | PASS | Restart, replay, rollback, concurrent acceptance, reset and preserved audit tested |
| 3 Prediction/simulation | PASS | Deterministic training/draws, held-out metrics, hand examples, terms, penalties, ranking and infeasibility tested |
| 4 API/live integration | PASS | Actual HTTP validation/errors, stored decisions, durable recovery, stale work and SSE replay tested |
| 5 Frontend | PASS | Component tests, strict types, lint, production build and actual visual inspection |
| 6 End-to-end/reliability | PASS | Eight real browser journeys, a11y/contrast, keyboard/mobile/reduced motion, invalid/duplicate/disconnected/error cases |
| 7 Delivery/LinuxONE | BLOCKED for real host execution | All achievable native and emulated packaging/tests/smoke/restart checks PASS; no IBM host supplied |

## D. Verification results

- Windows Python 3.12.13: **52 backend tests passed**, no skips.
- Packaged Linux amd64 Python 3.12.12: **52 backend tests passed**, no skips.
- Packaged Linux s390x under emulation: **52 backend tests passed**, no skips.
- `npm test`: **5 passed**; `npm run e2e`: **8 passed**, no skips.
- `npm run typecheck`, `npm run lint`, `npm run build`: PASS.
- Backend Ruff/Mypy: PASS. `pip check`: PASS.
- `npm audit`, full Python environment audit and pinned Python runtime audit: zero known dependency vulnerabilities.
- Compose validation, both separate image builds, real HTTP static/API/event/SSE smoke tests and actual container restart persistence: PASS.
- Desktop and mobile axe checks: no violations in tested states. No document overflow at 1440/768/390 widths. Actual initial/evaluated/error/loading screenshots inspected.
- One upstream Starlette TestClient/httpx deprecation warning remains; it does not skip tests. No accessibility certification, OS image security scan or full security audit is claimed.

Exact executed commands, failures, repairs, exit statuses and artifact paths are in [BUILD_LOG.md](BUILD_LOG.md). Container test logs and the Playwright JSON report contain actual results. No test was treated as passing because it merely existed.

Measured local workload: four alternatives, one invoice, two obligations, 1,000 paths, seven days. Twenty warm evaluations: median 87.59 ms / P95 96.08 ms. Ten event commits: median 7.00 ms; event to stored recalculation: median 245.06 ms / P95 273.89 ms. In-process ASGI, excludes network and browser rendering; see [benchmark.json](benchmark.json).

## E. AI/ML evaluation

Active version: **synthetic-logistic-hazard-v1-8dfd5f3ab9ed**, confirmed on Windows, native Linux and emulated s390x after canonicalizing coefficients to 12 decimals. Fixed dataset seed 20261017; 600 synthetic invoices split into 480 training / 120 held-out before daily observation expansion. Held-out daily observations: 1,125.

Executed metrics: daily Brier **0.07397396463575107**; day-7 horizon Brier **0.23407548600545616**. Precision, recall and F1 at probability threshold 0.5 are **0**: daily arrival positives are sparse and the model does not cross that threshold on held-out positives. These limitations are displayed honestly. Metrics are synthetic-data evaluation, not real-world accuracy or a financial guarantee. Sequential hazards generate possible arrival dates; probability is not an exact promised arrival date. Missing/invalid models return unavailable status.

## F. LinuxONE readiness

The exact Python image tag/digest includes a real s390x manifest. Native amd64 and target s390x images were built independently. The target actually installed/imported pinned Pydantic/Pydantic Core wheels, ran all 52 packaged backend tests, served the full application, evaluated decisions, processed an event, replayed SSE and preserved SQLite data through restart under emulation.

**No real IBM LinuxONE deployment occurred.** Remaining host architecture, runtime, storage, access, networking, health, workflow and restart checks are listed in [deployment.md](deployment.md).

Final image indexes:

- Native: `sha256:65edc81d7c5d4a9b8d1e756d4d0bcfe92f0a01549cccfa6cbe20174fd1251400`
- s390x: `sha256:e192e6f35fc84ceff91a4de7612632f8c60b272eaecbda0aeb35e5afeff5a23c`

## G. How to run

Already running: **http://127.0.0.1:8080/**. From the repository root, `docker compose up -d --no-build` starts the built native image; `docker compose ps` checks health and `docker compose stop` preserves storage. API health: `http://127.0.0.1:8080/api/health`.

Native developer setup and commands are in [README.md](../README.md). Backend: from backend, `../.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`; frontend: from frontend, `npm run dev`. Local UI: http://127.0.0.1:5173/. Use `.venv/bin/python` equivalents on Linux. Development does not require Docker.

Use the UI's **Reset demo** or POST `/api/demo/reset`. Reset deliberately creates a new generation; older audit history remains. Scenario settings also preserve the previous generation. The synthetic reference calendar is fixed at 17 October 2026 and labelled in the interface. Configuration is via process environment; `.env.example` is reference documentation and is not silently autoloaded.

## H. Known issues and boundaries

- Real LinuxONE host execution is blocked by absent host access.
- Single-process, single-business synthetic demo; no public authentication, authorization, multi-tenant isolation or payment execution.
- Model quality is limited by synthetic assumptions; daily classification metrics are zero at the chosen threshold. Finite-path risk estimates and independent customer arrivals do not establish real-world predictive accuracy.
- Fixed synthetic calendar, conservative same-day outflow ordering and explicit hold continuation are assumptions, inspectable with every evaluation.
- One upstream TestClient deprecation warning. No OS-image vulnerability scan or penetration test performed.
- No known unresolved critical defect in tested local workflows. Public/production operation requires additional security and operational work documented in README/deployment.

## I. Evidence and files

- [Build evidence](BUILD_LOG.md), [architecture](architecture.md), [financial model](financial-model.md), [test instructions](testing.md), [deployment procedure](deployment.md).
- [Model evaluation](model-evaluation.json), [benchmark](benchmark.json), [OpenAPI](openapi.json), [browser results](e2e-results.json).
- Native/target build and test logs: `container-native.log`, `container-s390x.log`, `container-tests-native.log`, `container-tests-s390x.log`.
- Runtime smoke and restart JSON records for both architectures; before/after dependency audit reports; actual screenshots under `screenshots/`.
- Domain, persistence, model/simulator and HTTP tests in backend/tests; frontend component tests and real browser journeys in frontend/tests and frontend/e2e.

Readiness: a working, verified local synthetic demonstration with independently tested native and emulated s390x packaging. Real LinuxONE deployment and public production readiness remain unverified.
