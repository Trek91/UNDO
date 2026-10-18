# V3 decision quality contract

Hard feasibility uses remaining principal, settled cash after prior mandatory deadlines,
explicit contract permissions/minimum portions and in-horizon schedules. Desired reserve
is a soft target, never cash or a hard payment prohibition. No synthetic receipt settles
the ledger. All monetary aggregates use integer paise and exact half-even means.

The simulation objective is unchanged: mandatory-miss probability, expected missed principal,
expected accrued fees, reserve-breach probability, amount-weighted delay, remaining target
principal and stable action ID. It is lexicographic; no hidden weighted score.

Evidence now includes all remaining principal (including obligations beyond the horizon)
and accrued unpaid fees, sampled worst intraday net funding, nearest-rank p05/p50/p95
minimum and daily closing outcomes. Sampled worst is not a guaranteed worst possible outcome.
Wilson95 intervals describe finite-path Bernoulli sampling conditional on assumptions;
they do not measure model accuracy, calibration uncertainty or scenario confidence.
Legacy records have absent evidence, not invented zeroes or reconstructed quantiles.

V3 will distinguish primary policy choice from the experimental ML objective ranking.
The evidence gate chooses the validated obligation/reserve rule when ML decision benefit
is insufficient. Experimental forecast metrics still carry their model provenance; prescribed
stress results are labelled as such, never as learned probabilities. Policy comparisons
share candidates, state, horizon and realized future paths. Rule reasoning is explicit.
Sensitivity will report the chosen primary and experimental policy separately; a stable
rule under receipt delays does not imply future outcomes are certain.
