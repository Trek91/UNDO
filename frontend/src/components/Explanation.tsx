import { ArrowUpRight, CircleAlert, Fingerprint } from 'lucide-react'
import type { Decision, Evaluation } from '../lib/api'
import { MetricValue } from './MetricValue'
import { currency, dateLabel, percent } from '../lib/api'

const metricNames: Record<string, string> = { shortfall_probability: 'lower mandatory-shortfall probability', expected_shortfall_paise: 'lower expected mandatory shortfall', expected_penalty_paise: 'lower expected contractual penalties', reserve_breach_probability: 'lower reserve-breach probability', payment_delay: 'less payment delay' }
export function Explanation({ evaluation, expanded = false, statistics }: { evaluation: Evaluation; expanded?: boolean; statistics?: Decision['model_statistics'] }) {
  const recommended = evaluation.actions.find(result => result.action.id === evaluation.recommendation)
  const alternative = evaluation.actions.find(result => result.action.id === evaluation.explanation.alternative_id)
  const metric = evaluation.explanation.principal_metric
  return <section className="explanation" aria-label="Recommendation explanation">
    <div className="section-title"><div><span className="eyebrow">THE REASONING</span><h2>A decision you can inspect.</h2></div><Fingerprint size={23} strokeWidth={1.3} aria-hidden="true"/></div>
    <p className="explanation-lead">{evaluation.explanation.reason}</p>
    {!evaluation.decision_evidence && recommended && alternative && <p>{recommended.action.label} ranks ahead of {alternative.action.label} through {metricNames[metric ?? ''] ?? 'the documented ranking order'}.</p>}
    {recommended?.metrics && alternative?.metrics && <div className="reason-comparison"><div><span>{recommended.action.label}</span><strong>{percent(recommended.metrics.shortfall_probability)}</strong><small>mandatory shortfall · {currency(recommended.metrics.expected_penalty_paise)} expected penalties</small></div><ArrowUpRight size={18} aria-hidden="true"/><div><span>{alternative.action.label}</span><strong>{percent(alternative.metrics.shortfall_probability)}</strong><small>mandatory shortfall · {currency(alternative.metrics.expected_penalty_paise)} expected penalties</small></div></div>}
    <p className="downside"><CircleAlert size={17} aria-hidden="true"/>{evaluation.explanation.downside}</p>
    <details open={expanded || undefined}><summary>Assumptions, model & reproducibility</summary><div className="assumptions">
      <dl><div><dt>State</dt><dd>Generation {evaluation.generation} · version {evaluation.state_version}</dd></div><div><dt>Reference date</dt><dd>{dateLabel(evaluation.snapshot.base_date)} · {evaluation.snapshot.timezone}</dd></div><div><dt>Simulation</dt><dd>{evaluation.metadata.paths.toLocaleString('en-IN')} paths · {evaluation.metadata.horizon_days} days · seed {evaluation.metadata.seed}</dd></div><div><dt>Scenario digest</dt><dd className="mono">{evaluation.metadata.scenario_digest ?? 'Unavailable'}</dd></div><div><dt>Model</dt><dd className="mono">{evaluation.metadata.model_version ?? 'Unavailable'}</dd></div></dl>
      <p>{evaluation.metadata.ordering}</p>
      <p>Calculation engine: {evaluation.metadata.engine_version}. Older stored evaluations retain their original calculations and are marked stale after an engine change.</p>
      <ul>{evaluation.metadata.assumptions.map(text => <li key={text}>{text}</li>)}</ul>
      <p>{evaluation.explanation.sensitivity_note}</p>
      <h3>Synthetic-data evaluation</h3><p>These measurements describe generated data. They do not establish real-world accuracy.</p>
      <p>The model estimates a conditional daily arrival probability. Precision, recall and F1 use a fixed daily threshold of 0.5; the simulation uses the probabilities directly. When predicted positives are zero, precision is undefined; legacy numeric zeros are a reporting convention. The Model Evidence Center reports undefined denominators explicitly. A low Brier score alone does not establish useful decisions.</p>
      <p>Classification display is derived from stored confusion counts. Original raw metadata is preserved; missing denominators remain unverified.</p>
      <dl>{(['precision', 'recall', 'f1'] as const).map(key => <div key={key}><dt>{key === 'f1' ? 'F1' : key === 'precision' ? 'Precision' : 'Recall'}</dt><dd><MetricValue metric={statistics?.[key]}/></dd></div>)}</dl>
      <dl>{Object.entries(evaluation.metadata.model_metrics).filter(([key]) => !['precision', 'recall', 'f1', 'precision_defined', 'recall_defined'].includes(key)).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{Number.isInteger(value) ? value : value.toFixed(4)}</dd></div>)}</dl>
      <ul>{evaluation.explanation.limitations.map(text => <li key={text}>{text}</li>)}</ul>
      <h3>Contractual payment schedules</h3>{evaluation.actions.map(({ action, metrics }) => <div key={action.id} className="contract-line"><strong>{action.label}</strong><p>{action.valid ? action.description : action.invalid_reason}</p>{action.valid && <p>{action.payments.map(([day, amount]) => `${currency(amount)} on day ${day}`).join(' + ')}{action.reconsider_day !== null ? ` · review on day ${action.reconsider_day}` : ''}</p>}{metrics && <p>Cash deficit: {percent(metrics.cash_deficit_probability)} · expected peak funding gap {currency(metrics.expected_peak_cash_deficit_paise)} · supplier late: {percent(metrics.late_payment_probability)} · expected remaining supplier balance {currency(metrics.expected_remaining_paise)}</p>}</div>)}
    </div></details>
  </section>
}
