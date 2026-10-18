> Historical / superseded release instructions and verification snapshot.
> Use [the current V3 handoff](UNDO_V3_HANDOFF.md) and [final repair report](FINAL_REPAIR_REPORT.md)
> for the submitted build. Prior findings and measurements below are preserved.

# ML audit — unchanged model, honest decision evidence

## V3 evidence gate — evaluated, EXPERIMENTAL

The unchanged model is synthetic-logistic-hazard-v1-8dfd5f3ab9ed. The target is conditional
daily arrival hazard, with survival multiplied from day0 through H inclusive. This is
separate from receipt-by-horizon probability. Training remains480 invoices, held out120,
zero invoice overlap; diagnostics reconstruct actual forecasts without refitting weights.

Held-out daily:1125 at-risk days,94 positives,1031 negatives; TP0/TN1031/FP0/FN94 at0.5.
Precision is **undefined** (no predicted positives), recall0/F1=0. Daily Brier
0.07397396463575107 vs training-prevalence baseline0.0769968153813; lower Brier alone does
not qualify ML for primary policy use. Full log loss, prediction distribution, counts,
fixed-bin calibration and day7 horizon diagnostics: v3/model-evidence.json / live API.
No weights, thresholds or training data were changed to force positive classifications.

`backend/v3_validate_model.py` ran an untouched120-invoice paired downstream benchmark with
three prespecified forecast seeds,100 forecast paths per decision, then one realized
synthetic future per invoice. Selection never sees realized futures. Invoice-cluster
bootstrap1000 replicates avoids treating three forecasts of one invoice as independent.
Paired expected-penalty benefit:0 paise,95% interval[0,0]. Some funding-gap outcomes are
worse for ML; no reliable downstream advantage was established. See raw paired records
v3/heldout-policy-records.json and source/model-bound app/evidence/validation.json.

Eligibility requires valid artifact/split, probabilistic baseline improvement and verified
held-out decision improvement across seeds. It currently fails closed. Primary decisions
use the obligation-aware rule; ML is an experimental comparator. Absent/invalid models
show UNAVAILABLE with a labelled prescribed no-receipt stress, not invented probabilities.
All evidence is synthetic; real-world predictive accuracy and financial benefit remain
unverified. Horizon15–30 extrapolates beyond the training days0–14. The earlier audit below
is historical, and its PARTIAL label is superseded by this explicit V3 evidence status.

Status: PARTIAL. The model is a working deterministic synthetic daily hazard estimator.
The tested application does not establish incremental decision benefit over a transparent
obligation-aware rule, or real-world predictive accuracy.

## Reproduction and root cause

`../.venv/Scripts/python.exe audit_model.py` from backend reconstructs the existing dataset
and split and independently computes metrics from predictions. Seed 20261017, 600 invoices,
480 training/120 held out, 240 gradient steps, threshold 0.5 and all original data/weights
were retained. Version: `synthetic-logistic-hazard-v1-8dfd5f3ab9ed`.

The target is **arrival on this day conditional on still being unpaid**, not receipt by
day 7. Only at-risk days are expanded, ending at arrival or day 14 censoring. Train/test
split happens at invoice level before expansion; overlap is empty. Invoice IDs, future
arrival days and settlement labels are not features. Predefined scaling uses amount,
age, relative expected date, historical late rate and historical delay. No fitted
preprocessing uses held-out labels. The synthetic generator's latent noise is unavailable
to the model. Stable sigmoid, finite coefficients and deterministic gradients are tested.

| Held-out daily quantity | Actual result |
|---|---:|
| Observations | 1,125 |
| Positive / negative labels | 94 / 1,031 |
| Positive prevalence | 8.3556% |
| Training daily prevalence | 6.2994% (319/5,064) |
| Predicted positives at 0.5 | 0 |
| TP / TN / FP / FN | 0 / 1,031 / 0 / 94 |
| Probability min / median / max | 0.009303 / 0.053123 / 0.248181 |
| Mean probability | 0.062274 |
| Precision | undefined, because TP+FP=0 |
| Recall / F1 | 0 / 0 |
| Model Brier | 0.0739739646 |
| Training-prevalence baseline Brier | 0.0769968154 |
| Calibration error, 10 fixed bins | 0.0212815809 |

Every daily score is below the existing threshold. This explains the zero predictions;
there are positive test labels, and no inverted-class or missing-positive-label defect
was found. The original metric helper used zero for undefined precision without counts.
It now also publishes confusion counts, threshold, positives and defined flags, and the UI
explains the convention. Raw audit precision remains JSON null. The threshold is unchanged.
Simulation consumes probabilities directly, so a 0.5 daily classifier is not the decision rule.

The daily Brier improvement over the *training* prevalence predictor is about 0.00302
(3.93% relative), a modest synthetic proper-score improvement, not evidence of useful
classification or production accuracy. Calibration bins underpredict observed rates;
the highest occupied bin has only 9 observations. No certainty claim is supported.

For arrival by day 7 (days 0–7 inclusive): 54/120 positive invoices; model TP13/TN57/FP9/FN41,
precision 0.5909, recall 0.2407, F1 0.3421, Brier 0.2340754860.
The training-horizon-prevalence baseline Brier is 0.2596918403. This is a distinct target,
not a replacement selected to hide poor daily classification.

Training-loss verification reconstructs the original inputs/weights without refitting:
initial log loss 0.25291537, final 0.21923283, training-prevalence constant 0.23512650.
This confirms the training objective improved; it does not establish optimal fitting or
generalization. Coefficients, held-out predictions and original model version are unchanged.

## Decision policy comparison

`../.venv/Scripts/python.exe audit_policies.py` uses all 120 original held-out invoices.
Dates translate to the scenario calendar while preserving all relative input features.
For every invoice, all policies face identical realized arrival day/amount (or no arrival)
and identical starting cash/obligations/terms. The ML simulation uses 1,000 common paths,
the unchanged model/seed/objective, and never sees that held-out future when choosing.

Policies:

- Balance-only: full payment if affordable now.
- Obligation rule: reserve all mandatory principal due within the horizon plus desired
  reserve; choose full if it fits, otherwise permitted split if its immediate portion fits,
  otherwise hold. It does not use predictive probabilities.
- Worst-case rule: rank actual alternatives with the existing objective under no receipts.
  Included as an additional conservative comparator, not the only non-ML baseline.
- ML: production risk-first recommendation from shared stochastic scenarios.

| Realized outcome, 120 paired cases | Balance | Obligation rule | Worst-case rule | ML |
|---|---:|---:|---:|---:|
| Choices | full 120 | split 120 | hold 120 | split 109, hold 11 |
| Mandatory miss rate | 95.833% | 0% | 0% | 0% |
| Expected mandatory miss, paise | 958,333 | 0 | 0 | 0 |
| Cash deficit / reserve breach rate | 95.833% | 93.333% | 95.833% | 93.333% |
| Target late rate | 0% | 93.333% | 100% | 93.333% |
| Mean penalties, paise | 0 | 186,667 | 200,000 | 186,667 |
| Mean peak reserve deficit, paise | 1,916,667 | 2,050,632 | 2,108,333 | 2,053,333 |
| Mean remaining target principal, paise | 0 | 574,334 | 574,334 | 574,334 |

The obligation-aware policies avoid mandatory misses by allowing supplier delay and
penalties: a real tradeoff, not a free improvement in every metric. ML improves on the
weak balance check and the conservative worst-case rule in some metrics. It **does not
beat the stronger transparent obligation rule** on mandatory misses, fees, funding
deficits or remaining principal in this sample; reserve-gap severity is slightly worse.
Its probabilities do influence choices (11 differing decisions), but influence alone is
not usefulness. The UI now states the lack of established incremental outcome benefit.
No seed, threshold, future or data was changed to manufacture uplift.

## Runtime and limitations

`audit_runtime.py` compares two fresh processes. Training is deterministic at startup and
cached per process; there is no serialized model artifact, and no artifact reload claim.
Native and emulated packaged runtime versions/weights/source hashes are checked separately
by `scripts/audit_containers.py`. Missing models and malformed/nonfinite coefficient arrays
return unavailable, including the no-invoice case. No heuristic probability fallback exists.

Training observations span days 0–14. Longer UI horizons extrapolate; customer delays are
independent, historical rates are synthetic, the generator is simplified, and there is no
real customer data, external validation, temporal backtest, production drift monitoring or
proof of financial outcome improvement. Additional fitting or threshold tuning would need
training/validation data and a fresh untouched test set. None was silently introduced.

Evidence: `audit/ml-diagnostics.json`, `audit/heldout-predictions.csv`,
`audit/policy-comparison.json`, `audit/fresh-process-model.json`, runtime logs and regression XML.
