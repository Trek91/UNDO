import { Check, CircleAlert } from 'lucide-react'
import type { Evaluation } from '../lib/api'
import { currency, percent } from '../lib/api'

export function Comparison({ evaluation }: { evaluation: Evaluation }) {
  return <div className="table-scroll" tabIndex={0} role="region" aria-label="Scrollable payment comparison"><table className="comparison"><caption className="sr-only">All payment alternatives evaluated against the same simulated futures</caption>
    <thead><tr><th>Payment alternative</th><th>Pay now</th><th>Mandatory shortfall</th><th>Expected shortfall</th><th>Expected penalty</th><th>Reserve breach</th><th>Expected minimum</th><th>Remaining liabilities</th></tr></thead>
    <tbody>{evaluation.actions.map(({ action, metrics, valid, rank }) => <tr key={action.id} className={evaluation.recommendation === action.id ? 'recommended-row' : ''}>
      <th scope="row"><span className="action-label">{evaluation.recommendation === action.id && <Check size={15} aria-hidden="true"/>}{action.label}</span>
        <span className="table-note">{evaluation.recommendation === action.id ? 'Recommended' : valid ? `Experimental rank ${rank ?? '—'}` : 'Unavailable'}</span></th>
      {valid && metrics ? <><td>{currency(action.payments.filter(([day]) => day === 0).reduce((sum, [, amount]) => sum + amount, 0))}</td><td className={metrics.shortfall_probability > 0 ? 'critical-text' : ''}>{percent(metrics.shortfall_probability)}</td><td>{currency(metrics.expected_shortfall_paise)}</td><td>{currency(metrics.expected_penalty_paise)}</td><td>{percent(metrics.reserve_breach_probability)}</td><td>{currency(metrics.expected_minimum_paise)}</td><td>{currency(metrics.expected_total_remaining_liabilities_paise ?? metrics.expected_remaining_paise)}</td></>
        : <td colSpan={7}><span className="invalid-reason"><CircleAlert size={15}/>{action.invalid_reason ?? 'Model unavailable; no probabilistic result.'}</span></td>}
    </tr>)}</tbody></table></div>
}
