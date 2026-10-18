# V3 robustness and uncertainty

One-factor grids vary receipt delay (0–10 days), prescribed receipt probability (0–1),
additional unexpected expense, mandatory timing, proposal amount, supplier deadline,
partial schedule, penalties and reserve. Default amount grids include cash/budget boundaries
and one-paise neighbors. At most9 dimensions/60 cases, at most200 paths per case, horizon
1–30 days. No exponential Cartesian product. A case uses the same seed/customer uniforms
across actions; changing a factor is explicit and never posts a settlement/event.

Prescribed receipt-probability experiments are user assumptions: the chosen unpaid invoice
arrives once on its expected day clipped to the horizon, or does not arrive. Other customers
retain their modeled paths. No prescribed probability is presented as a learned forecast.

Tipping points are adjacent tested grid brackets where recommendations differ. No binary
search, interpolation or monotonicity assumption. A missing crossing means none found in
the configured range. Prior-action infeasibility and new mandatory miss are distinct flags.
Stability is the unweighted share of these specific test cases preserving the base choice,
not a confidence score or a joint probability. No-change cases count honestly.

Three deterministic seed replicates (base,+1,+2 modulo2^32), with the same case path cap,
test experimental ranking sampling. Different winners report instability; agreement is
only a limited check. Wilson95 intervals concern finite simulated Bernoulli counts,
conditional on the model and assumptions. They exclude calibration/structural uncertainty.
Cash p05/p50/p95 and sampled worst outcomes are empirical simulated values, not guarantees.

Primary deterministic-policy stability and experimental ML ranking are shown separately.
The primary rule can stay unchanged under receipt delays while conditional financial risk
changes substantially. A robust rule is not a guarantee of solvency or reserve maintenance.

## Executed V3 reference result

Canonical7-day/100-path baseline: split payment retained in31/39 cases (79.5%); additional
expense switch bracketINR10,000->10,000.01; proposal bracketINR40,000->40,000.01; reserve
switch bracketINR20,000->30,000. These are actual tested regions, not guarantees. Three
experimental seeds agree in that example, with overlapping mandatory-miss intervals;
this does not establish model confidence or eliminate other ranking/structural uncertainty.
The paired held-out model benchmark still found no reliable incremental benefit, so
primary stability concerns the deterministic policy. Measured repeated results/performance
are in v3/performance.json; generated test fixture and live ephemeral lab provide separate
reproducible examples. New financial events invalidate the old state anchor; saved
experiments remain separate from the live result and original immutable snapshots.
