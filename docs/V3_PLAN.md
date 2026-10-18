> Historical / superseded release instructions and verification snapshot.
> Use [the current V3 handoff](UNDO_V3_HANDOFF.md) and [final repair report](FINAL_REPAIR_REPORT.md)
> for the submitted build. Prior findings and measurements below are preserved.

# UNDO V3 implementation and gates

Keep the ledger, engine objective, SQLite schema, dependency pins, natural design and
single-process deployment. No live financial experiments/reset. Live metadata and a verified
online backup/isolated restore are recorded before implementation. Source ZIP preserves
all tracked and untracked work. Additive evaluation JSON fields preserve old records;
no schema migration or second service is planned.

| Phase | Capability / modules | Executed acceptance strategy |
|---|---|---|
| 0 | Inventory, source/DB backup and isolated restore | Current state, history/settings, Docker and original tests |
| 1 | Decision evidence contract, sampled quantiles and Wilson intervals / engine | Independent money/quantile/interval examples; old regressions |
| 2 | Bounded one-factor sensitivity and grid tipping brackets / robustness | Known switch, infeasible/no-switch, reproducibility, common streams |
| 3 | Balance, obligation/reserve, stress and experimental ML policies / policies | Same actions/state/futures, exact outcomes and ties |
| 4 | Reproduced model evidence and eligibility / evidence, decisions | Class counts, Brier/log loss/calibration, failure gate; rule primary without proven benefit |
| 5 | Decision Room, ephemeral Scenario Lab, stability, policies and evidence / React/API | Actual APIs, explicit save/revert, accessible/responsive loading/error/stale states |
| 6 | Worker/SSE provenance and experiment separation / store/main | Atomicity, concurrent events, out-of-order results, saved experiment never live |
| 7 | Whole product / regression, browser, measured bounded analysis | All tests/static/build, flagship workflow, quantitative checks and screenshots |
| 8 | Native/s390x packaging, state-preserving update, docs | Independent builds/tests/restarts; no real LinuxONE claim |

Each implementation gate records RED, GREEN, REFACTOR and VERIFY in BUILD_LOG. Sensitivity
uses bounded grids and adjacent switch brackets, never unsupported monotonic binary search.
Stability is a share of specified test cases, not confidence. ML remains an explicitly
experimental comparator if held-out decision benefit is not established. Scenario experiments
never mutate the ledger; saving archives an explicitly hypothetical evaluation.
