> Historical / superseded release instructions and verification snapshot.
> Use [the current V3 handoff](UNDO_V3_HANDOFF.md) and [final repair report](FINAL_REPAIR_REPORT.md)
> for the submitted build. Prior findings and measurements below are preserved.

# Financial correctness audit

## V3 additions — PASS for executed cases

All previous invariants remain covered by the final91-test Windows backend suite.
V3 adds exact rounded integer-paise remaining liabilities (all outstanding principal,
including beyond horizon, plus accrued unpaid fees), sampled minimum/daily cash quantiles,
and Wilson95 intervals for distinct mandatory miss, late supplier, cash deficit and
reserve breach frequencies. Quantiles and intervals are conditional simulation evidence.

The primary eligibility-gated obligation/reserve rule is distinct from the unchanged
lexicographic experimental ranking. Hard contractual/affordability constraints remain
separate from the desired reserve. Hypothetical changes clone typed state; neither
Evaluate nor Save experiment emits a financial event or modifies settled cash. Saved
experiments cannot complete a live queued job or become the overview's live decision.
Stale source hashes/version guards reject outdated saves. Old evaluations remain immutable.
The selected action's own downside and actual leading alternative now drive its explanation.
See test_v3_contract, test_v3_api, test_v3_realtime and test_v3_timeline.

Status: PASS for the exercised invariants and counterexamples; bounded synthetic decision
support, not certification of arbitrary financial portfolios. See the exact definitions in
[financial-model.md](financial-model.md) and actual tests in `backend/tests`.

## Ledger and temporal integrity

Integer paise, INR, nonnegative settled cash, aware UTC events and Asia/Kolkata date
boundaries are enforced. Expected/delayed invoices and recorded obligations do not credit
cash. Only confirmed synthetic receipts/payments change settled funds. Projections operate
on copies. Payments cannot exceed remaining principal or cash; receipts cannot exceed
remaining invoices. Paid principal cannot be erased by an update. Fully paid proposals
close. Duplicate and conflicting events, invalid chronological dependencies, unknown IDs,
wrong business/currency, fractional/negative/oversized amounts and naive dates are rejected.

SQLite event/state/job/notification/audit writes share one transaction. Failure injection
rolls them back. Concurrent distinct events retain all updates; duplicate acceptance is
logical and global across generations. A retry returns its original acceptance version,
even after reset, without applying cash twice. Legacy duplicate rows are preserved.
Generation/version guards reject stale client mutations atomically; unguarded API callers
explicitly request operations against the current state, so external clients should supply
both guards. React supplies both for events, evaluation, feed, scenario changes and reset.

Replay sorts aware timestamps stably; an invalid earlier dependency rejects the whole
event. Invoice creation cannot postdate its recording event. Reset/scenario operations
archive generations, never wipe the database. Live ledger was not used for destructive tests.

## Independently checked outcomes

| Scenario | Expected result | Verification |
|---|---|---|
| Baseline, full payment, no receipt | day 0 ₹40,000; day 1 −₹10,000; mandatory miss ₹10,000 | PASS, hand calculation |
| ₹115,000 initial cash, same full plan | no cash deficit/miss; reserve deficit ₹5,000 | PASS, separate reserve test |
| High cash, permitted full deferral | no funding miss, supplier late, fee ₹2,000 | PASS, lateness independent of liquidity |
| Same-day incoming receipt after a mandatory deadline | closing balance cures; measured deadline miss persists | PASS |
| Mandatory target held despite sufficient cash | missed principal ₹60,000; cash deficit probability zero | PASS, new regression |
| Split remainder unpaid at day 3 | target late; incurred fee ₹2,000 and peak gap ₹12,000 | PASS |
| Horizon ends on that day 3 | fee remains a liability, closing net −₹12,000 | PASS, no truncation advantage |
| Other supplier cured by a receipt later on due date | missed deadline still incurs its fee once | PASS, new regression |
| Mandatory ₹50,000 due today, cash ₹100,000 | full ₹60,000 invalid; permitted ₹30,000 split valid | PASS, no silently underpaid full plan |
| Original deadline yesterday, extension 3 days | remainder/defer day 2; already incurred fee retained | PASS |
| Original deadline 10 days ago, extension 3 days | past schedules invalid | PASS |
| Large aggregate / 5,000 paths | −10,000,000,999,999 paise, exact Fraction reference | PASS; old float mean lost one paise |

The RED run recorded 13 failures/1 pass before the first repairs. Subsequent regressions
also reproduced timestamp pagination loss, absent HTTP generation guards, missing diagnostic
counts, a malformed model with no invoices being ranked, and absent engine provenance.
The final Windows suite has 74 passing tests. Full native/emulated container verification
is separately recorded in BUILD_LOG and the audit XML/log files.

## Counterfactual discipline

Each action changes payment timing/amounts against the same immutable state and same
random invoice-arrival scenarios. The seed, paths, inclusive horizon, model version,
engine version and scenario digest are stored. Remainders are retained; contract
permissions, minimum portions and horizon restrictions are checked before ranking.
Mandatory obligations precede supplier schedules; uncertain receipts arrive afterward.
Unscheduled but due target liabilities are included in net funding positions.

The lexicographic objective is unchanged: mandatory miss probability, miss severity,
incurred penalties, reserve breach probability, amount-weighted delay, remaining target
principal, stable action ID. It is a stated preference, not a proven universal optimum.
Hold assumes full settlement tomorrow and offers no speculative information benefit.
No model means no probabilistic ranking; malformed/nonfinite coefficients also fail closed.

## Limits retained explicitly

Fees are a simplified one-time contractual assumption, not jurisdictional advice. There
is no credit facility, interest, tax treatment, partial receipt arrival process, currency
conversion or payment execution. Each unpaid invoice's remaining amount arrives once in
a sampled path. Customer shocks are independent. The scenario calendar is fixed, and
the horizon is bounded to 30 days; 15–30-day model use extrapolates beyond training follow-up.
Unobserved earlier fee settlements cannot be inferred from principal-only records.

Native Windows Python 3.12 reports a 15.625ms wall-clock resolution. The HTTP handler waits
one measured tick (maximum50ms) for an apparently current browser timestamp before invoking
the reducer. The reducer's strict future rejection is unchanged: settlement is accepted only
after the backend clock reaches its timestamp. Deterministic tests verify both the wait and
rejection of a genuinely future event. No timestamp backdating or tolerance waiver is used.
