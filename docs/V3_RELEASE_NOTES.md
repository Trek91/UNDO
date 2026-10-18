> Historical / superseded release instructions and verification snapshot.
> Use [the current V3 handoff](UNDO_V3_HANDOFF.md) and [final repair report](FINAL_REPAIR_REPORT.md)
> for the submitted build. Prior findings and measurements below are preserved.

# UNDO V3 — engineering handoff

17 October 2026 · **READY WITH DOCUMENTED LIMITATIONS**

## A. Version 3 overview

V3 is running locally at [UNDO](http://127.0.0.1:8080/#overview). It extends the existing
React/FastAPI/SQLite application with a Decision Room, a snapshot-only Scenario Lab,
recommendation stability and switching regions, four-policy comparisons, an evidence-gated
primary policy, and a Model Evidence Center. No service, external AI requirement, payment
integration or database table migration was added. Existing user source changes were
preserved; no commits, pushes, public deployment or real payments occurred.

Scenario Lab Evaluate is ephemeral. Save archives an explicitly hypothetical immutable
evaluation, never applies assumptions to the ledger, changes live calculation settings,
completes a pending live job or replaces the overview's live recommendation. Revert
discards local inputs. The existing scenario editor remains a separate generation workflow.

## B. Decision-quality results

The original hard constraints and lexicographic experimental objective are preserved.
Without demonstrated held-out ML decision benefit, the primary action follows the
obligation-aware deterministic rule: reserve known separate mandatory principal through
the horizon plus the desired reserve, then consider feasible full/split/hold/defer in
order. If the soft budget cannot be preserved, hold when feasible. This is a disclosed
decision rule, not a claim of globally optimal or risk-free behavior.

Sensitivity varies nine supported dimensions using bounded one-factor grids, at most60
cases and200 paths/case, with common seeds/customer draws across alternatives. The canonical
7-day/100-path example retained split payment in31 of39 cases (79.5%). That is a share of
specified test cases, **not model confidence**. The unexpected-expense switch is bracketed
between INR10,000 and10,000.01; proposed-payment and reserve switching regions are also
computed. Receipt delay can leave the deterministic primary action unchanged while
changing financial risk. Prior-action infeasibility, new mandatory miss risk and cases
with no detected switch are reported explicitly. No monotonicity or joint-likelihood
assumption is used.

Three seed replicates disclose experimental ranking instability or limited agreement.
Wilson95 intervals quantify finite-path sampling of four distinct probabilities; cash
quantiles and sampled worst minima are actual simulation outputs. Remaining liabilities
include all outstanding principal, even beyond the horizon, and accrued unpaid fees.
The selected action's own downside and the actual leading alternative drive explanations.

Balance-only, obligation-aware, experimental ML and prescribed no-receipt stress policies
are scored on the same actions, state, horizon and futures. Policy choices never receive
held-out realized futures. Current planning results are labelled separately from held-out
validation; ties and mixed trade-offs remain visible. See DECISION_CONTRACT.md,
DECISION_ROBUSTNESS.md and v3/heldout-policy-records.json.

## C. ML evidence

Unchanged model: `synthetic-logistic-hazard-v1-8dfd5f3ab9ed`. Conditional daily arrival
hazard is combined into cumulative receipt probability using survival from day0 through
H inclusive. Training480/held-out120 invoices; zero invoice overlap. Held-out daily
observations1125, positives94, negatives1031. At threshold0.5: TP0/TN1031/FP0/FN94,
zero predicted positives, **precision undefined**, recall0/F1=0. Threshold, weights and
training data were not changed to force positive classifications.

Daily Brier0.07397396463575107 vs training-prevalence baseline0.07699681538133897;
day7 receipt Brier0.23407548600545616 vs0.25969184027777775. Actual log loss, probability
distribution and calibration counts are available in v3/model-evidence.json and the UI.

The downstream benchmark used120 untouched held-out synthetic invoices, three prespecified
forecast seeds,100 paths per decision, then one realized future per invoice. A1000-replicate
invoice-cluster bootstrap retained dependence across repeated seed choices. Paired penalty
benefit0 paise,95% interval[0,0]; some ML funding-gap outcomes are worse. **No reliable
incremental decision benefit was established.** The source/model-bound eligibility gate
therefore remains **EXPERIMENTAL**, with the deterministic rule primary. Missing/invalid
models report UNAVAILABLE and use labelled prescribed stress without invented probabilities.
These results establish no real-world predictive accuracy or financial benefit.

## D. UI verification

Sixteen isolated browser journeys pass, including all13 prior journeys and the V3 flagship
experiment/save/history/live-event workflow, model failure/retry and new-view accessibility.
The flagship verified unchanged action after receipt delay, a changed action after the
INR10,000.01 expense, a saved experiment without ledger mutation, then a real synthetic
event producing a new live evaluation. Historical snapshots remain inspectable.

Five V3 views were checked at1440/768/390 widths, with automated WCAG A/AA axe checks,
no document overflow, keyboard focus/reduced-motion checks and actual screenshots. A
4.43:1 label-contrast defect was repaired; the affected checks and full suite passed.
Live packaged-browser verification repeated five views/three widths, tested an ephemeral
lab calculation, matched persisted14-day/100-path controls, and verified no financial or
latest-decision mutation. Actual screenshots are under v3/screenshots/live. Desktop
Decision Room/Scenario Lab/Model Evidence and mobile stability were visually inspected.
Automated checks are not a comprehensive manual assistive-technology certification.

## E. Executed tests and commands

All commands below completed successfully except the explicitly identified blockers and
captured/repaired attempts. Backend commands run from backend using the project venv;
frontend commands run from frontend.

| Check | Command / evidence | Result |
|---|---|---|
| Windows backend | `../.venv/Scripts/python.exe -m pytest -q --junitxml=../docs/v3/final-backend.xml` |91 passed,0 failed,0 skipped;12.91s |
| Static backend | `../.venv/Scripts/python.exe -m ruff check app tests`; `... -m mypy app` |PASS,15 sources checked by mypy |
| Frontend | `npm test` |15 passed,0 failed,0 skipped |
| Static/build frontend | `npm run typecheck`; `npm run lint`; `npm run build` |PASS |
| Browser | `npm run e2e` |16 passed,0 failed,0 skipped; v3/phase7-browser.log, v3/e2e-final.json |
| Native Linux packaged suite | `.venv/Scripts/python.exe scripts/v3_container_tests.py` from root |91 passed,0 failed,0 skipped;11.58s |
| Emulated s390x packaged suite | Same script, separate target runtime |91 passed,0 failed,0 skipped;111.60s |
| Live packaged browser | `node scripts/v3-live.mjs` |PASS;15 route/viewport combinations,0 axe violations/page errors/overflow |
| Model protocol | `../.venv/Scripts/python.exe v3_validate_model.py` |PASS; measured no reliable uplift |
| Reproducibility/performance | `../.venv/Scripts/python.exe v3_benchmark.py` |PASS; two identical-output runs/workload |
| Dependency audits | `npm audit --json`; `... -m pip_audit -r requirements.txt --no-deps --disable-pip --format json` |0 known reported dependency vulnerabilities |

Comparable baseline reconfirmed at Phase0:74 backend,10 frontend; previous browser suite13
was rerun as part of the current16. Additions are17 backend,5 frontend and3 browser tests;
packaged repetitions are separate executions of the same91 backend tests. One upstream
Starlette/httpx deprecation warning remains; no tests were skipped or weakened for green.

Measured Windows3.12.13 workloads:100 paths/H7 with39 sensitivity cases ~0.79–0.84s;
1000/H14 ~3.16–3.27s;5000/H30 ~8.82–9.32s. Case paths cap at200; four alternatives share
scenarios. Timings are observations on this machine, not an SLA or a claimed speedup.
Exact measurements: v3/performance.json.

Repairs and failed attempts are retained in BUILD_LOG.md: backup-handle cleanup, strict
typing, missing API/UI contracts, test-fixture assumptions, contrast, Windows runner
encoding, interrupted network downloads and explicit browser-context setup. Offline
packaged tests install exact pure-Python test-tool wheels with networking disabled and
use each image's original production dependency graph. Wheel hashes are recorded.

## F. Data preservation and recovery

Authoritative volume `undo-demo_undo_data`, database `/app/data/undo.db`.
Before implementation: online SQLite backup, integrity check, isolated Store restore,
source ZIP `.runtime/v3/source-before.zip`, preserved image `undo:v3-baseline-native`.
The actual baseline was generation4/version0/cash10,000,000 paise,14-day/100-path settings,
15 evaluations,2 events,20 audit records, demo cursor0. Earlier reported3-day settings
were not assumed current.

Pre-release backup was restored onto a **fresh isolated volume** and served successfully
under both the preserved V2 and V3 images. V3 recalculation and actual restart preserved
the restored state. SQLite schema1 is unchanged; old evaluations load with additive defaults.
Rollback requires the verified pre-release database with the old image: old strict V2
models cannot consume newly appended V3 JSON. Restore in isolation first and retain the
current database; do not blindly overwrite data.

After the local update and live browser checks: generation4/version0/cash10,000,000 paise,
original raw request settings and demo cursor0 verified unchanged. Every original row in
generations/events/evaluations/notifications/audit remains byte-for-byte present. One
V3 recalculation appended a16th evaluation and21st audit/notification record; no financial
events were added. Final and delivery backups also passed integrity and isolated restore.
Evidence: v3/baseline.json, pre-release.json, recovery.json, final.json, delivery.json.

## G. Deployment status

| Target | Actual verification |
|---|---|
| Windows native development |Python3.12.13;91 backend tests and frontend/browser gates PASS |
| Native Linux amd64 |`undo:v3-native`; image build, Python3.12.12 imports,91 tests, HTTP/SSE/static assets/idempotency and actual restart PASS |
| Linux s390x packaging |`undo:v3-s390x`; separate build and actual emulated Python/Pydantic/Core imports PASS |
| Emulated s390x runtime |91 tests and HTTP/SSE/static assets/idempotency/actual restart PASS |
| Real IBM LinuxONE |**BLOCKED / NOT VERIFIED**: no real target host/access available |
| Local service |Healthy at127.0.0.1:8080, native V3 image, original volume preserved |

Pinned Python3.12.12-slim-bookworm index
`sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c`
supports both architectures. Actual runtimes retain Pydantic2.11.7/Core2.33.2; no custom
dependency fallback was needed. Native and target source hashes/model weights match.
Docker CLI/engine29.7.2 and Buildx/BuildKit were rechecked; output in v3/docker-environment.log.

Final native image index: `sha256:78e481c7ed9657e45e56b64235d69ad0ebf6d69f7eb4d537e97223be5e5cb14f`.
Final s390x index: `sha256:9ea9cb788b85bfb4c6bf0dfc97cc00e8e9415621b9465939c930ac23e5a82f98`.
Exact runtime evidence: v3/container-runtime-v3-verified.json. Local activation used
`docker tag undo:v3-native undo:native` and `docker compose up -d --no-build`, then the
guarded recalculation endpoint, which queues original settings without rewriting them.
Temporary verification containers were stopped/removed; their isolated volumes remain.
No external deployment occurred.

## H. Limitations and blocked checks

- **ML experimental:** no demonstrated downstream advantage; no real-customer validation.
- **Finite synthetic scenarios:** independent customer draws, no correlated macro shocks;
  day15–30 extrapolates beyond training. Wilson intervals exclude model/structural error.
- **Bounded one-factor sensitivity:** grid brackets, not exact/general thresholds; no joint
  scenario likelihood, multivariable optimizer or unsupported confidence score.
- **Model probability overrides:** prescribed assumptions on the first sorted unpaid invoice,
  with arrival day clipped into the experiment horizon; not learned forecasts.
- **Scope:** single-process, loopback synthetic decision-support deployment. Public production
  access controls, real payment rails, real-data calibration and availability certification
  are outside this release; no claim that these are implemented.
- **Docker Scout BLOCKED:** `docker scout cves undo:v3-native --only-severity critical,high`
  exited1 because login is required. OS/image-layer vulnerability scanning is unverified;
  dependency audits are a separate successful check.
- **Real LinuxONE BLOCKED:** no host/access. Emulated execution must not be represented as
  real IBM infrastructure deployment.
- **Nonessential enhancements not implemented:** multivariable sensitivity/interactive
  quantile bands are deferred; actual one-factor evidence and accessible tables are working.

## I. Readiness

**READY WITH DOCUMENTED LIMITATIONS** for the controlled synthetic workflow. The core V3
calculation, evidence, experimentation, persistence and UI requirements are implemented
and exercised. No known unresolved critical financial/data-integrity defect was found by
the executed gates. This is not certification of arbitrary portfolios, real-world ML
accuracy, public financial operations or actual LinuxONE deployment.
