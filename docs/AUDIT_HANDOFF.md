> Historical / superseded release instructions and verification snapshot.
> Use [the current V3 handoff](UNDO_V3_HANDOFF.md) and [final repair report](FINAL_REPAIR_REPORT.md)
> for the submitted build. Prior findings and measurements below are preserved.

# UNDO — audited engineering handoff, 17 October 2026

## A. Overall status

**READY WITH DOCUMENTED LIMITATIONS.** Working local synthetic demonstration, repaired
against reproduced financial/concurrency defects. All achievable local/native/emulated
functional gates passed. Real-world model usefulness, public production security and real
LinuxONE execution are not established. No known unresolved critical defect in exercised
prototype workflows; passing tests are not proof of universal correctness.

## B. Live application

[Open UNDO](http://127.0.0.1:8080/). Compose service `undo-demo-undo-1` is healthy, one
Uvicorn process, UID10001, read-only root filesystem, capabilities dropped and loopback
binding. Existing volume `undo-demo_undo_data` retained.

Original generation **4**, version **0**, settled cash **10,000,000 paise / ₹100,000**
preserved. No live reset, scenario replacement or synthetic cash event was injected.
Original 3-day/100-path evaluation settings restored; baseline now has a current computed
split recommendation under engine `counterfactual-v2`, with conditional risks displayed.
Live audit evaluations added four evaluations/notifications/audit rows: original tables
4 generations/2 events/7 evaluations/12 notifications/12 audit rows; closing
4/2/11/16/16. All original rows/financial states verified against the baseline backup.

Actual Chrome smoke passed after final update: five views, evaluation/backend values,
desktop/mobile layout, no page exceptions or document overflow. Exact chart values,
legend toggles, keyboard, axe checks, stale tabs and pagination are tested in isolated
browser journeys. Current screenshots: audit/screenshots/live-desktop.png and live-mobile.png.

## C. Financial correctness

Settled cash remains separate from projections; expected invoices never become available
cash. INR integer paise, strict event validation, aware UTC timestamps, business dates,
atomic writes, global logical idempotency, chronological replay and immutable evaluations
are retained. No real payment integration/execution exists.

Funding deficits, unpaid mandatory principal at its deadline, target contractual lateness,
desired-reserve breaches, severity and accrued fees are measured separately. Original-date
extensions, prior mandatory affordability, same-day receipt ordering, horizon-boundary fees
and exact half-even monetary averages now have regression coverage. The Windows clock
fix waits one measured tick and retains strict future rejection. Details/hand calculations
are in [FINANCIAL_CORRECTNESS.md](FINANCIAL_CORRECTNESS.md).

## D. ML findings

Model/seed/data/split/epochs/weights/threshold unchanged. Daily conditional arrival hazard:
1,125 held-out observations, 94 positives, TP0/TN1031/FP0/FN94 at threshold 0.5.
Maximum score 0.248181 explains zero predicted positives. Precision is undefined and
numeric zero is now explicitly identified as a convention; recall/F1 are zero.
Counts/defined flags are published. Daily Brier **0.073974** versus training-prevalence
baseline **0.076997** is a modest synthetic improvement. Day-7 horizon is a separate target
(Brier 0.234075; precision 0.5909 / recall 0.2407 / F1 0.3421).

Training loss improves from 0.252915 to 0.219233; two fresh processes and both packaged
architectures reproduce the model version/weights. Deterministic training occurs at startup,
cached per process; no serialized artifact or artifact reload is claimed. Missing/malformed
models return unavailable. See [ML_AUDIT.md](ML_AUDIT.md) and raw predictions/calibration.

## E. Simulation and recommendations

Real alternative schedules, permitted minimum portions, retained remainders, deadlines,
fees and hold continuation use the same immutable snapshot and shared random futures.
Recommendation is computed by the unchanged risk-first lexicographic objective, rendered
by React. Engine provenance, model version, paths, seed, horizon and scenario digest persist.

Paired evaluation on the same 120 held-out realized futures compared balance-only,
obligation/reserve rule, worst-case rule and ML. Mandatory misses: 95.833% balance-only,
0% both stronger rule and ML. Rule/ML mean penalties both 186,667 paise; reserve-gap severity
slightly worse with ML. ML picked split 109 / hold 11 versus rule split 120, but **no incremental
outcome benefit over the stronger rule is established**. The UI discloses this limitation.

## F. Executed tests

| Environment/check | Actual final result |
|---|---|
| Windows Python 3.12.13 backend | 74 PASS, 9.63s |
| Packaged Linux amd64 Python 3.12.12 | 74 PASS, 9.75s |
| Packaged Linux s390x, emulated | 74 PASS, 57.61s |
| Frontend Vitest | 10 PASS, 2 files |
| Complete real browser suite | 13 PASS, 42.4s |
| Strict types, ESLint, Ruff, mypy, frontend production build | PASS |
| Python/npm known dependency audits, pip consistency | PASS; unchanged pins |
| Both final HTTP/static/event/SSE smoke and actual container restarts | PASS |
| Online backup, original-row comparison, separate restored original image/database | PASS |

No skips. One upstream Starlette/httpx TestClient deprecation warning remains.
Commands from backend: `../.venv/Scripts/python.exe -m pytest -q`,
`../.venv/Scripts/python.exe -m ruff check app tests benchmark.py lock_requirements.py audit_*.py`,
`../.venv/Scripts/python.exe -m mypy app`.
From frontend: `npm test`, `npm run typecheck`, `npm run lint`, `npm run build`, `npm run e2e`.
Root packaged/runtime commands and complete RED/failure/fix/rerun records are in
[BUILD_LOG.md](BUILD_LOG.md); final JUnit/log/Playwright evidence is under audit/.

Measured small local workload: warm evaluation median 138.27 ms / P95 185.05 ms;
event-to-persisted-recalculation median 308.61 ms / P95 368.09 ms. In-process ASGI; excludes
network/browser rendering, and predates the final narrow Windows HTTP clock wait.
No public capacity or performance SLA claimed.

## G. Docker and platform readiness

CLI/engine 29.7.2 available. Buildx 0.36.1 / BuildKit 0.32.2 running, s390x advertised and
actually built/executed under emulation. Exact pinned Python image index includes s390x;
real installs downloaded Pydantic Core 2.33.2 s390x wheels. Pydantic 2.11.7/Core 2.33.2 and
packaged source hashes verified. No compatible dependency replaced or custom fallback added.

Final image indexes:

- Native `undo:native` / `undo:audit-final-native`:
  `sha256:87b0928e38d5612fa568350e497da5eaa585112e2eb4ace9d002d134dcad9e24`.
- Target `undo:audit-final-s390x`:
  `sha256:737cd22ea67b377c47766c5e398816f2b7a9a97dbc46143e8821069ab1805d6f`.

**BLOCKED:** real LinuxONE execution, no host/access supplied.
**BLOCKED:** installed Docker Scout requires login before OS-image scanning; no clean
OS-CVE claim. No login/account change attempted. Native testing, emulated packaging and
real host deployment remain separate claims.

## H. Corrections and preservation

Fixed schedule affordability, overdue date arithmetic, mandatory-target miss accounting,
fee accrual/carry-forward, exact monetary means, cross-reset retry and receipt identity,
stale write guards, invoice chronology, malformed models, misleading metric presentation,
history cursor ties, response ordering/generation consistency, page retention/gap recovery,
inspected staleness, browser navigation, engine provenance and Windows clock precision.
The finding table in [PROTOTYPE_AUDIT.md](PROTOTYPE_AUDIT.md) identifies severity/evidence.

Original native image preserved as `undo:pre-audit-20261017`; original `undo:s390x` and
intermediate audit images retained. Original source snapshot:
`.runtime/audit/source-before.patch`. Original online DB backup:
`.runtime/audit/live-baseline.db`. Closing verified backup:
`.runtime/audit/live-handoff-final.db`, SHA256
`1ebba66135436893cded093d94fb1351088bdc2e8dd42810309ba77c7ca4bd66`.
No commits, pushes, external deployments or discarded user work.

Restore proof started the original image against the original backup in a NEW isolated
volume, verified original state/evaluation/all 12 audit rows, then stopped it. Live volume
and original backup unchanged (audit/restore-verification.json). Old software should use
its matching restored backup, since versioned evaluation metadata may exceed its schema.
Do not overwrite the current volume as a rollback shortcut; preserve both histories.

The audit also records a backup-check false positive that did not stop its first shell
sequence, transient startup probe failure, a TypeScript failure and repeated browser failures.
Each was diagnosed/repaired and rerun; none is reported as a pass.

## I. Outstanding risks and operating instructions

Use `docker compose up -d --no-build`, `docker compose ps`, and `docker compose stop`
from the repository root. Stop retains the current volume. Keep one worker. Do not run
the destructive container_smoke.py against the live URL; it intentionally resets its target.
Audit runtime tools use isolated volumes/ports; these test containers are stopped and their
volumes/images retained. Native dev instructions are in README; tests use isolated 8001/5174.

Synthetic data, weak calibration, no proven incremental ML benefit, independent customer
shocks, finite paths, fixed calendar, simplified one-time fees and 15–30-day extrapolation
remain explicit. No public authentication/authorization, multi-business isolation, TLS,
load qualification, penetration test, drift monitoring or real financial connectors are
implemented. No real-world accuracy or production/LinuxONE deployment claim is made.
