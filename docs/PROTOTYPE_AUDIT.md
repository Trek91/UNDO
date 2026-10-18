> Historical / superseded release instructions and verification snapshot.
> Use [the current V3 handoff](UNDO_V3_HANDOFF.md) and [final repair report](FINAL_REPAIR_REPORT.md)
> for the submitted build. Prior findings and measurements below are preserved.

# UNDO prototype audit — 17 October 2026

## V3 current verification

V3 extends the existing service and ledger; it does not rebuild or reset the application.
Phase0 online backup and isolated restore protected the actual generation4/state0/cash
10,000,000 paise baseline, with14-day/100-path settings and15 existing evaluations.
Source ZIP and preserved baseline image are available under the documented local paths.

Implemented and exercised: ephemeral experiments, explicit archive/revert, primary-rule
and experimental forecast separation, common-future policy comparison, sensitivity matrix,
Wilson intervals, cash quantiles, actual model evidence and traceable live updates.
Windows91 backend tests pass;15 frontend tests and16 browser journeys pass. Initial browser
contrast failure was repaired and the affected checks plus complete suite rerun.
Five V3 views passed automated WCAG A/AA checks at1440/768/390; real screenshots were inspected.

Current deployment/preservation evidence and remaining limits are maintained in
[V3_RELEASE_NOTES.md](V3_RELEASE_NOTES.md) and [BUILD_LOG.md](BUILD_LOG.md). The sections below
record the preceding V2 audit and retain their original dates/counts.

## Baseline before repairs

PASS: source inspected with all existing uncommitted files preserved. No commits or pushes.
Live Compose service `undo-demo-undo-1` is healthy at http://127.0.0.1:8080,
using `undo:native` and persistent volume `undo-demo_undo_data`.
Generation 4, version 0, settled cash 10,000,000 paise. No live reset authorized or performed in this audit.

PASS: read-only SQLite online backup captured to `.runtime/audit/live-baseline.db`;
integrity check `ok`; SHA256 and table counts in `audit/baseline-state.json`.
Source snapshot `.runtime/audit/source-before.patch` preserves pre-audit work.

Executed baseline: backend pytest 52 passed; Ruff and mypy passed;
frontend Vitest 5 passed, typecheck/lint/build passed; isolated Playwright 8 passed.
Python dependency consistency and Python/npm vulnerability audits passed.
These results establish the existing suite baseline, not complete correctness.

Docker CLI and engine 29.7.2 available; Buildx 0.36.1 / BuildKit 0.32.2.
Running Docker Desktop Linux amd64 builder advertises linux/s390x.
This is emulation capability, not real LinuxONE execution.

Independent unchanged-model diagnostic reproduced 94 held-out positive daily observations,
zero predicted positives at threshold 0.5, maximum probability 0.24818.
Full raw diagnostics: `audit/ml-diagnostics.json`, `audit/heldout-predictions.csv`.
Financial, concurrency, pagination and model-failure edge cases remain under investigation.
No hypothesis is treated as a confirmed defect until reproduced.

Overall at baseline: AUDIT INCOMPLETE.

## Findings and self-repair

The original passing suite missed material defects. The audit added 22 backend cases,
five frontend hook cases and five browser journeys. RED artifacts retain failures before
repairs. Source-inspection findings were also verified; no unexecuted pre-fix failure is claimed.

| Finding | Severity | Repair | Status |
|---|---|---|---|
| Full plan silently underpaid after mandatory costs | High | Validate immediate affordability after mandatory priority | PASS |
| Overdue extensions restarted; past schedules valid | High | Original-date arithmetic and elapsed-schedule rejection | PASS |
| Delayed mandatory target missed no recorded deadline | High | Measure unpaid principal independently of schedule | PASS |
| Same-day cure erased other supplier fee | High | Latch breach before receipts; accrue once | PASS |
| Last-day breach hid next-day fee | High | Carry incurred fee liability beyond horizon | PASS |
| Reset retry applied cash again | High | Global logical identity, original acceptance receipt | PASS |
| Duplicate reported newer acceptance version | Medium | Original insertion-count version | PASS |
| Stale generation HTTP mutations accepted | High | Atomic generation/version guards; client tokens | PASS |
| Future invoice recorded before creation | Medium | Business-date chronology validation | PASS |
| Float averaging lost a paise | Medium | Exact integer half-even mean, Fraction reference | PASS |
| Empty/short model weights ranked; no-invoice bypass | High | Shape/finiteness validation before draws | PASS |
| Undefined precision displayed without class counts | Medium | Counts, defined flags and daily-target explanation | PASS |
| Equal-timestamp decision history skipped rows | Medium | Timestamp/rowid cursor | PASS |
| Refresh could mix/regress financial state | High | Consistent overview snapshot and monotone generation-scoped client reads | PASS |
| Live refresh lost pages or skipped burst gaps | Medium | Deduplicated overlapping merges; recoverable gap cursor | PASS |
| Inspected staleness/navigation became outdated | Medium | Current-state display check and hash synchronization | PASS |
| Legacy calculations lacked engine provenance | Medium | Version new engine, preserve/mark legacy calculations stale | PASS |
| Coarse Windows clock rejected current browser events | Medium | Wait one measured clock tick, retain strict future validation | PASS |

Reproduction names/analytic results are in FINANCIAL_CORRECTNESS.md and test_deep_audit.py.
Training data, seed, fitting and threshold were not changed to improve the metrics.

## Functional and reliability gates

PASS: Windows backend 74 tests, frontend 10 tests, complete browser suite 13 tests.
TypeScript, ESLint, Ruff, mypy and production frontend build pass. No skips.
Journeys cover evaluation, changed recommendations, delays/expenses, duplicates, invalid
input, reset, feed pause/resume, scenarios, immutable history, stale tabs, infeasibility,
loading/empty/error states, network recovery, keyboard/reduced motion, desktop/mobile axe,
back/forward navigation, exact chart cells/legend and persistent pagination after a live update.

PASS: database rollback, concurrent acceptance, replay, durable work recovery, transient
worker failure/degraded health/retry, stale-work preservation, SSE replay and duplicate-free
cursor resumption. Overview facts share one SQLite snapshot. Superseded client responses
cannot overwrite newer financial state.

PASS: deterministic training/draws and two fresh model processes; sampling check against
hazard CDF. PARTIAL: synthetic model usefulness, with no demonstrated incremental outcome
benefit over the stronger transparent obligation-aware rule. See ML_AUDIT.md.

PASS: npm/Python dependency audits and consistency. BLOCKED: Docker Scout image scan
requires account login and returned exit 1 before a scan. No account modification or clean
OS-image CVE claim. Public security/penetration/multi-user checks are NOT RUN and outside
the loopback prototype's scope. Real LinuxONE execution is BLOCKED by absent host/access.

Actual benchmark, 1,000 paths/7 days/one invoice/two obligations: 20 warm evaluations
median 138.27 ms/P95 185.05 ms; 10 in-process event commits median 9.94 ms/P95 19.09 ms;
event-to-persisted-recalculation median 308.61 ms/P95 368.09 ms. Cold model 1,125.00 ms.
This predates the final narrow HTTP clock wait; engine unchanged, Windows commits may
add one tick. No production capacity or browser-rendering SLA claimed.

## Preservation

No live reset, scenario change or cash event was injected. Live evaluations appended
records. Original 3-day/100-path settings were restored. Generation 4/version 0/cash
₹100,000 remain intact. Original generations, events, evaluation JSON, notifications and
audit rows were compared against the baseline SQLite backup; see audit/handoff-final-state.json.

The first backup verifier treated mutable evaluation settings as immutable history and
failed despite a valid online backup/unchanged ledger. The PowerShell sequence continued
to the tested local image update. The comparison was corrected and rerun; all original
financial/history rows and settings were preserved. Final commands stop on errors.

Original native image remains `undo:pre-audit-20261017`; original target `undo:s390x`
remains. Intermediate images/test volumes retained. No commits, pushes, external deployment
or real payments. Final package/runtime gates and readiness are in BUILD_LOG and the audit handoff.

Final status: **READY WITH DOCUMENTED LIMITATIONS**. Both final packaged suites pass 74
tests; native/emulated smoke and restart gates pass. Final served CSS/JS bytes equal the
local production build; both packages' backend hashes equal current source. Original
image/backup restore was actually run in a new volume and passed; live storage untouched.
Public production, real-world model value, OS-image scanning and real LinuxONE execution
retain the explicit limitations/blockers described above.
