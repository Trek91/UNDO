# Financial model and assumptions

Amounts are integer paise (INR); API amounts are also paise. Actual balances are nonnegative and change only on confirmed settlements. Forecasts are hypothetical net funding positions and may be negative. Expected/confirmed-but-unsettled receivables never increase actual cash. Timestamps are aware UTC; date-only business deadlines and the ledger baseline midnight use Asia/Kolkata (+05:30). The synthetic simulation reference calendar is fixed at 2026-10-17 and is labelled in the UI; event recording timestamps are actual UTC timestamps. It is not a rolling live bank forecast.

## Three distinct outcomes

1. **Projected cash deficit:** the minimum net cash trajectory is below zero. Report probability and expected peak funding gap (paise). This is a funding requirement, never an actual withdrawal or invented borrowing.
2. **Missed mandatory obligation:** principal remains unpaid at its mandatory deadline, whether because funding is insufficient or the selected schedule postpones payment. Track unpaid amounts per obligation, count each at its first deadline once, and carry it forward for later settlement. Report probability and expected sum of these deadline shortfalls (paise). A late supplier payment is a contractual lateness even when cash is sufficient; report target-obligation lateness probability separately. Payment schedules do not erase the original due date except where a contract explicitly permits the revised schedule.
3. **Desired-reserve breach:** the minimum intraday net cash position falls below the desired reserve. A positive balance can breach the reserve without a cash deficit or missed obligation. Report breach probability, expected peak reserve deficit (paise), and complement probability of maintaining reserve.

Daily chart values are closing net projected cash: available simulated funds minus unpaid due principal and incurred fees. A delayed target's unscheduled but already-due balance remains a liability. Intraday minima include obligations before uncertain receipts. A chart's positive closing balance does not imply all deadlines were met. Do not confuse probability and severity. Expected values use integer division with exact half-even rounding to paise, including negative totals; financial aggregation never divides through a binary float. Probability values are unit fractions.

## Baseline contract

Synthetic business starts with INR 100,000, supplier obligation INR 60,000 due day 0, mandatory operating expense INR 50,000 due day 1, expected customer invoice INR 40,000 on day 1 and desired reserve INR 10,000. Partial payment INR 30,000 now plus remainder on day 3 is explicitly permitted without penalty. Full deferral to day 3 is allowed with a one-time INR 2,000 late fee due day 1. Hold reviews on day 1, offers no extension, and assumes full settlement at review plus the same late fee. All amounts/dates/terms are synthetic assumptions, not market facts.

## Counterfactual policy

Every action uses the same financial snapshot and same sampled receivable arrivals. Immediate payments cannot exceed settled cash. Future funding gaps are projected risks, not fake settlements. Remainders and hold continuation must fall inside the horizon (default 7 days; 1–30 permitted); actions outside it are invalid. No option wins by deleting an unpaid balance. Contract checks precede simulation. Mandatory expenses have priority over supplier payments on the same date. Uncertain receipts arrive after date-only obligations, conservatively. Confirmed settlement timestamps remain separate from this projection convention.

Rank valid actions lexicographically: mandatory-shortfall probability; expected mandatory deadline shortfall; expected penalties; reserve-breach probability; amount-weighted delay; remaining commitment; stable action ID. Hold has no speculative value of information. Explain this limitation. No hard reserve guarantee is offered. Infeasibility is structured; a missing model makes probabilistic evaluation unavailable.

## Prediction

Audit corrections in engine `counterfactual-v2`: immediate plans must fit cash after other
mandatory obligations already due. Contract extensions are measured from the original
due date, including overdue contracts; an extension already in the past is invalid.
An initial portion paid after its original deadline does not erase an incurred fee.
Fees latch when a deadline is missed, before same-day receipts. They are normally payable
the following day (overdue fees immediately), but remain accrued liabilities even if that
payment day lies beyond the horizon. Principal and fees are carried once, never charged
again each day. Existing ledger principal settlements do not represent separate fee
settlements; the projection assumes the specified late fee has not been independently
paid/booked. Record any actual separate expense explicitly rather than inferring it.

The horizon is inclusive day 0 through day H. Other obligations after that window remain
in the immutable snapshot but their subsequent outcomes are outside this evaluation.
No rolling-calendar or unlimited-horizon forecast is claimed. Engine provenance is stored
with new evaluations; historical unversioned calculations are retained and marked stale.

An interpretable logistic regression estimates daily arrival hazard conditional on remaining unpaid. Features: scaled log amount, age, days relative to expected payment, historical late rate and historical mean delay. Synthetic invoice-level records are split before expansion into daily at-risk observations. No IDs or future outcomes are features. Training uses deterministic gradient descent, stable sigmoid, fixed scaling, regularization, and a seed. Held-out daily precision/recall/F1/Brier and invoice-horizon Brier are computed from actual predictions; these are synthetic-data results only. Sequential hazard draws define a survival distribution, not a guaranteed payment date.

Trained coefficients are canonicalized to 12 decimal places before evaluation and hashing. Actual Windows/Linux checks found sub-ULP differences in two coefficients before this normalization. The precision is far smaller than sampling uncertainty and makes model provenance reproducible across the tested architectures. Model metrics and versions are recorded from executed training, not hand-edited. A recorded supplier settlement reduces linked pending proposal amounts to remaining principal; a fully settled proposal closes and does not leave an invalid recalculation job. Historical evaluation snapshots remain unchanged.

Default simulation: 1,000 paths, 7 days, fixed recorded seed. Maximum 5,000 paths / 30 days / 4 actions. Model version, dataset seed, simulation seed, ordering policy, state snapshot and action terms are stored with every evaluation. Correlated customer delays and macroeconomic shocks are not modelled; outcomes are only as credible as the synthetic assumptions.


## V3 decision evidence and primary policy

The existing lexicographic simulated-outcome ranking is unchanged. An eligibility gate
controls whether it may choose the primary action. Without demonstrated downstream ML
benefit, the deterministic obligation-aware rule reserves known separate mandatory
principal through H plus desired reserve, then tries feasible full/split/hold/defer in
that order. If the soft budget cannot be preserved, it holds when feasible; this is not
a solvency guarantee. All alternative forecast outcomes remain visible and experimental.

Cash deficit (minimum projected cash below zero), missed mandatory deadline (unfunded
principal at its required time), supplier lateness (contractual deadline not met) and
reserve breach (projected cash below desired reserve) remain distinct. A receipt later
on the same day can improve closing cash without erasing an earlier missed deadline.
No risk metric is ever written back as settled cash.

Expected total remaining liabilities includes all outstanding principal beyond H and
accrued unpaid contractual fees; expected remaining supplier balance is a narrower
legacy metric. Nearest-rank empirical cash quantiles and sampled worst minimum describe
only the generated paths. Wilson95 intervals quantify finite-path Bernoulli sampling,
not structural/model uncertainty. Sensitivity is bounded one-factor testing, not a joint
probability or confidence score; see DECISION_ROBUSTNESS.md.
