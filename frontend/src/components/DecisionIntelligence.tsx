import { ArrowRight, FlaskConical, ShieldCheck } from 'lucide-react'
import type { Evaluation } from '../lib/api'
import { currency, percent } from '../lib/api'

import { actionName, dimensionName } from '../lib/decisionLabels'
const valueLabel = (value: number, unit: string) => unit === 'paise' ? currency(value) : unit === 'probability' ? percent(value) : `${value} days`

export function DecisionInsights({ evaluation }: { evaluation: Evaluation }) {
  const evidence = evaluation.decision_evidence
  const chosen = evaluation.actions.find(item => item.action.id === evaluation.recommendation)
  if (!evidence) return <p className="stale-note">Legacy calculation. Evaluate again to create V3 decision evidence.</p>
  const metrics = chosen?.metrics
  const interval = metrics?.probability_intervals.shortfall_probability
  return <section className="intelligence-panel" aria-label="Decision policy and uncertainty">
    <div className="evidence-heading"><span className="policy-icon"><ShieldCheck size={20}/></span><div><span className="eyebrow">THE BASIS FOR THIS DECISION</span><h2>{evidence.primary_policy === 'obligation_rule' ? 'Obligation-aware rule' : 'ML-informed policy'}</h2></div><span className="evidence-badge">{evidence.model_gate.status}</span></div>
    <p>{evidence.model_gate.reason}</p>
    <div className="basis-row"><span>Known mandatory budget <strong>{currency(evidence.known_mandatory_budget_paise)}</strong></span><span>Desired reserve <strong>{currency(evidence.desired_reserve_paise)}</strong></span><a href="#model">Inspect model evidence <ArrowRight size={13}/></a></div>
    <p className="assumption-note"><FlaskConical size={14}/>{evidence.forecast_basis === 'prescribed_stress' ? 'Prescribed no-receipt stress. Frequencies are scenario outcomes, not learned probabilities.' : 'Conditional forecasts remain experimental. Future outcomes can differ; the primary policy is disclosed separately.'}</p>
    {metrics?.cash_outcomes && <div className="outcome-grid"><div><span>Sampled worst minimum</span><strong>{currency(metrics.cash_outcomes.sampled_worst_minimum_paise)}</strong><small>Within these simulated paths</small></div><div><span>5th percentile minimum</span><strong>{currency(metrics.cash_outcomes.minimum_p05_paise)}</strong><small>Empirical downside, not a guarantee</small></div><div><span>Expected remaining liabilities</span><strong>{currency(metrics.expected_total_remaining_liabilities_paise ?? metrics.expected_remaining_paise)}</strong><small>Principal and accrued unpaid fees</small></div></div>}
    {interval && <p className="evidence-footnote">Mandatory-miss estimate: {percent(metrics!.shortfall_probability)}. Wilson 95% sampling interval {percent(interval.lower)}–{percent(interval.upper)}, {interval.trials} paths. This excludes uncertainty about the model itself.</p>}
    <details><summary>What would make us reevaluate?</summary><ul className="trigger-list">{evidence.reevaluate_when.map(text => <li key={text}>{text}</li>)}</ul></details>
  </section>
}

export function StabilityView({ evaluation, onAnalyze, busy }: { evaluation?: Evaluation; onAnalyze: () => void; busy: boolean }) {
  const report = evaluation?.robustness
  if (!report) return <section className="v3-empty"><span className="eyebrow">RECOMMENDATION STABILITY</span><h2>Test the assumptions behind the action.</h2><p>Run bounded one-factor experiments to find where the preferred action changes. No confidence score is invented.</p><button className="primary" disabled={busy || !evaluation} onClick={onAnalyze}>{busy ? 'Calculating sensitivity…' : 'Test recommendation stability'}<ArrowRight size={15}/></button></section>
  return <section className="stability-view" aria-label="Recommendation stability results">
    <div className="section-title"><div><span className="eyebrow">WHAT CHANGES THE DECISION?</span><h2>Steady where it matters. Sensitive where it should be.</h2></div><button className="secondary" disabled={busy} onClick={onAnalyze}>{busy ? 'Analyzing…' : 'Run sensitivity again'}</button></div>
    <div className="stability-summary"><div><span className="eyebrow">TESTED SCENARIO SHARE</span><strong>{report.stability_share === null ? 'Not available' : percent(report.stability_share)}</strong><p>{report.stable_cases} of {report.evaluated_cases} tested cases retain <b>{actionName(report.base_recommendation)}</b>.</p></div><div><h3>Sensitivity, not model confidence.</h3><p>{report.method}</p><p>{report.grid_paths} paths/case · {report.horizon_days}-day horizon · seed {report.seed}. Base calculation: {report.baseline_paths} paths.</p></div></div>
    <div className={`sampling-note ${report.sampling_status === 'unstable' ? 'sensitive' : ''}`}><strong>{report.sampling_status === 'unstable' ? 'Experimental ranking changes across sampling seeds.' : report.sampling_status === 'unavailable' ? 'ML sampling check unavailable.' : 'Three sampling seeds agree; this is a limited check.'}</strong><p>{report.experimental_seed_recommendations.map(actionName).join(' · ')}. {report.ranking_intervals_overlap ? 'Leading mandatory-miss intervals overlap; these intervals alone cannot establish a distinct ranking.' : 'The reported sampling check is separate from uncertain future outcomes.'}</p></div>
    <h3 className="subsection-title">Calculated switching regions</h3>
    {report.tipping_points.length ? <div className="tipping-list">{report.tipping_points.map((point, index) => <article key={index}><span>{dimensionName[point.dimension]}</span><strong>{valueLabel(point.lower_value, point.unit)} → {valueLabel(point.upper_value, point.unit)}</strong><p>{actionName(point.before_action)} → {actionName(point.after_action)}</p><small>{point.method}</small></article>)}</div> : <p className="method-note">No primary-policy switch found within these tested ranges. This is not proof of stability outside the grid.</p>}
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Scrollable sensitivity matrix"><table className="sensitivity-table"><caption>Sensitivity cases and recommendation changes</caption><thead><tr><th>Assumption</th><th>Tested value</th><th>Primary action</th><th>Experimental action</th><th>Observed effect</th></tr></thead><tbody>{report.cases.map((row, index) => <tr key={index} className={row.changed ? 'switch-row' : ''}><th scope="row">{dimensionName[row.dimension]}</th><td>{valueLabel(row.value, row.unit)}</td><td>{actionName(row.recommendation)}</td><td>{actionName(row.experimental_recommendation)}</td><td>{row.status}{row.previous_action_infeasible && ' · prior action infeasible'}{row.new_mandatory_shortfall && ' · new mandatory miss risk'}{row.constraints.length > 0 && <details><summary>Contract constraints</summary><ul>{row.constraints.map(text => <li key={text}>{text}</li>)}</ul></details>}</td></tr>)}</tbody></table></div>
    {report.skipped_dimensions.map(text => <p key={text} className="method-note">Not applicable: {text}</p>)}
    <ul className="method-limits">{report.limitations.map(text => <li key={text}>{text}</li>)}</ul>
  </section>
}

const conclusions = { no_difference: 'No financial difference on this sample.', ml_better: 'Experimental ML has lower measured risk or cost on this sample.', ml_worse: 'Experimental ML has higher measured risk or cost on this sample.', mixed_tradeoffs: 'The results show trade-offs; neither policy wins every outcome.', insufficient_evidence: 'Insufficient evidence for an ML comparison.' }
export function PolicyBenchmark({ evaluation }: { evaluation?: Evaluation }) {
  const comparison = evaluation?.decision_evidence?.policy_comparison
  if (!comparison) return <section className="v3-empty"><h2>Compare the policies behind the choice.</h2><p>Evaluate a payment to compare feasible actions against the same futures.</p></section>
  return <section className="policy-benchmark"><div className="section-title"><div><span className="eyebrow">SAME FACTS. SAME FUTURES. DIFFERENT POLICIES.</span><h2>What is doing the useful work?</h2></div></div>
    <div className="benchmark-conclusion"><strong>{conclusions[comparison.conclusion]}</strong><p>Current planning simulations, not held-out effectiveness evidence. These are conditional on <span className="mono">{comparison.outcome_basis}</span>. <a href="#model">Inspect the held-out validation.</a></p></div>
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Scrollable policy benchmark"><table className="policy-table"><caption>Policy outcomes on identical financial futures</caption><thead><tr><th>Policy & action</th><th>Mandatory miss</th><th>Expected shortfall</th><th>Expected penalty</th><th>Reserve breach</th><th>Expected minimum</th><th>Remaining liabilities</th></tr></thead><tbody>{comparison.policies.map(row => <tr key={row.id} className={row.id === evaluation?.decision_evidence?.primary_policy ? 'recommended-row' : ''}><th scope="row">{row.label}<span className="table-note">{actionName(row.action_id)}</span></th>{row.metrics ? <><td>{percent(row.metrics.shortfall_probability)}</td><td>{currency(row.metrics.expected_shortfall_paise)}</td><td>{currency(row.metrics.expected_penalty_paise)}</td><td>{percent(row.metrics.reserve_breach_probability)}</td><td>{currency(row.metrics.expected_minimum_paise)}</td><td>{currency(row.metrics.expected_total_remaining_liabilities_paise ?? row.metrics.expected_remaining_paise)}</td></> : <td colSpan={6}>{row.status}</td>}</tr>)}</tbody></table></div>
    <div className="policy-definitions">{comparison.policies.map(row => <details key={row.id}><summary>{row.label}: decision rule</summary><p>{row.reason}</p><p>Contractual feasibility at decision time: {percent(row.contractual_feasibility_rate)}. Shared scenario digest: <span className="mono">{row.scenario_digest}</span>.</p></details>)}</div>
    <ul className="method-limits">{comparison.limitations.map(text => <li key={text}>{text}</li>)}</ul>
  </section>
}
