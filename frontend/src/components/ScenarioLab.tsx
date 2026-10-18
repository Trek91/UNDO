import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { Decision, LabRequest, LabResult, State } from '../lib/api'
import { currency, dateLabel, percent } from '../lib/api'
import type { DecisionContext } from '../lib/decisionContext'
import { PolicyBenchmark, StabilityView } from './DecisionIntelligence'
import { actionName } from '../lib/decisionLabels'

const fields = [
  ['receipt_delay_days', 'Receipt delay · days', 0, 14], ['receipt_probability', 'Receipt probability · 0 to 1', 0, 1],
  ['unexpected_expense_paise', 'Additional expense · ₹', 0], ['mandatory_due_days', 'Mandatory expense · day', 0, 30],
  ['proposed_amount_paise', 'Proposed payment · ₹', 0.01], ['supplier_due_days', 'Supplier deadline · day', -7, 30],
  ['partial_days', 'Split remainder extension · days', 1, 30], ['minimum_partial_paise', 'Minimum partial payment · ₹', 0.01],
  ['penalty_paise', 'Contractual penalty · ₹', 0], ['reserve_paise', 'Desired reserve · ₹', 0],
] as const

export function ScenarioLab({ state, busy, postCurrent, refresh, context, onSelectProposal }: {
  state: State; busy: boolean; postCurrent: <T>(path: string, body?: unknown) => Promise<T>; refresh: () => Promise<void>;
  context?: DecisionContext; onSelectProposal?: (id: string) => void
}) {
  const [values, setValues] = useState<Record<string, string>>({})
  const [partial, setPartial] = useState('')
  const [horizon, setHorizon] = useState(context?.horizon_days ?? 7)
  const [paths, setPaths] = useState(context?.paths ?? 100)
  const [localProposal, setLocalProposal] = useState(() => Object.keys(state.proposals).sort()[0] ?? '')
  const proposalId = context?.proposal_id ?? localProposal
  const proposal = state.proposals[proposalId]
  const supplier = proposal ? state.obligations[proposal.obligation_id] : undefined
  const [result, setResult] = useState<LabResult | null>(null)
  const [reviewed, setReviewed] = useState<{ body: LabRequest; fingerprint: string } | null>(null)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const serial = useRef(0)
  const fingerprint = JSON.stringify([state.generation, state.version, proposalId, context?.seed ?? 20261017, context?.action_ids ?? ['full', 'partial', 'defer', 'hold'], fields.map(([name]) => [name, values[name]?.trim() ?? '']), partial, horizon, paths])
  const latestFingerprint = useRef(fingerprint)
  latestFingerprint.current = fingerprint
  useEffect(() => () => { serial.current++ }, [])
  const dirty = () => { serial.current++; setWorking(false); setResult(null); setReviewed(null); setSaved(false); setError(null) }
  const stale = result && (result.stale || result.baseline.generation !== state.generation || result.baseline.state_version !== state.version)
  const evaluate = async (event?: FormEvent) => {
    event?.preventDefault(); const requestId = ++serial.current
    if (!proposal || !supplier) return
    setWorking(true); setError(null); setSaved(false); setResult(null); setReviewed(null)
    try {
      const changes: Record<string, number | boolean> = {}
      for (const [name] of fields) if (values[name]?.trim()) {
        const raw = values[name].trim()
        if (name.endsWith('_paise')) {
          if (!/^\d+(\.\d{1,2})?$/.test(raw)) throw new Error('Money needs a nonnegative rupee amount with at most two decimals.')
          const [whole, fraction = ''] = raw.split('.')
          changes[name] = Number(whole)*100+Number(fraction.padEnd(2, '0'))
          if (!Number.isSafeInteger(changes[name])) throw new Error('Money amount exceeds the supported integer range.')
        } else changes[name] = Number(raw)
      }
      if (partial) changes.allow_partial = partial === 'yes'
      const body: LabRequest = { changes, simulation: { horizon_days: horizon, paths, seed: context?.seed ?? 20261017, action_ids: context?.action_ids ?? ['full', 'partial', 'defer', 'hold'], include_robustness: true, proposal_id: proposalId } }
      const next = await postCurrent<LabResult>('/lab/evaluate', body)
      if (requestId === serial.current && fingerprint === latestFingerprint.current) {
        setResult(next); setReviewed({ body, fingerprint })
      }
    } catch (reason) { if (requestId === serial.current && fingerprint === latestFingerprint.current) setError(String(reason)) }
    finally { if (requestId === serial.current) setWorking(false) }
  }
  const save = async () => {
    if (!reviewed || !result || stale || working || reviewed.fingerprint !== fingerprint) return
    const requestId = ++serial.current
    setWorking(true); setError(null)
    try { await postCurrent<Decision>('/lab/save', { ...reviewed.body, source_state_digest: result.source_state_digest });
      if (requestId === serial.current && fingerprint === latestFingerprint.current) setSaved(true)
      await refresh()
    }
    catch (reason) { if (requestId === serial.current && fingerprint === latestFingerprint.current) setError(String(reason)) }
    finally { if (requestId === serial.current) setWorking(false) }
  }
  return <section className="scenario-lab" aria-label="Scenario Lab">
    <section className="lab-target" aria-label="Experiment target"><span className="eyebrow">TARGET FROM DECISION CONTEXT</span><label>Experiment proposal<select aria-label="Experiment proposal" value={proposalId} onChange={event => { dirty(); setLocalProposal(event.target.value); onSelectProposal?.(event.target.value) }}>{!proposal && <option value={proposalId}>Unavailable: {proposalId || 'no proposal'}</option>}{Object.values(state.proposals).map(item => <option key={item.id} value={item.id}>{state.obligations[item.obligation_id]?.label} · {item.id}</option>)}</select></label>{proposal && supplier ? <p><strong>{supplier.label}</strong> · proposal {proposal.id} · {currency(proposal.amount_paise)} · due {dateLabel(supplier.due_date)}. Source generation {state.generation}, state {state.version}. {context ? 'Settings inherited from Decision Room or the explicit link.' : 'Direct entry uses the first sorted available proposal, identified above.'}</p> : <p role="alert">Selected proposal {proposalId || '(none)'} is unavailable. Choose an available proposal to evaluate.</p>}</section>
    <div className="lab-intro"><span className="eyebrow">A SAFE SPACE FOR WHAT IF</span><h2>Change an assumption. See the consequence.</h2><p>Experiments use cloned financial snapshots. Save archives the experiment in history. Revert clears these inputs. Neither changes settled cash or the live ledger.</p><p className="method-note">Blank fields keep the original value. Receipt changes affect the first sorted unpaid invoice; mandatory timing affects the first separate mandatory obligation. Day offsets start at the scenario date.</p></div>
    <form onSubmit={event => void evaluate(event)}><div className="lab-fields">{fields.map(([name, label, min, ...rest]) => <label key={name}>{label}<input type="number" min={min} max={rest[0]} step={name === 'receipt_probability' ? '0.01' : name.endsWith('_paise') ? '0.01' : '1'} placeholder="Unchanged" value={values[name] ?? ''} onChange={event => { setValues({ ...values, [name]: event.target.value }); dirty() }}/></label>)}<label>Partial payment permitted<select value={partial} onChange={event => { setPartial(event.target.value); dirty() }}><option value="">Unchanged</option><option value="yes">Yes</option><option value="no">No</option></select></label><label>Experiment horizon<select value={horizon} onChange={event => { setHorizon(Number(event.target.value)); dirty() }}>{[...new Set([horizon, 1, 3, 7, 14, 30])].sort((a,b) => a-b).map(value => <option key={value} value={value}>{value} days</option>)}</select></label><label>Experiment paths<select value={paths} onChange={event => { setPaths(Number(event.target.value)); dirty() }}>{[...new Set([paths, 100, 1000, 5000])].sort((a,b) => a-b).map(value => <option key={value} value={value}>{value}</option>)}</select></label></div><div className="lab-actions"><button className="primary" disabled={busy || working || !proposal || !supplier}>{working ? 'Calculating…' : 'Evaluate experiment'}</button><button type="button" className="secondary" disabled={working} onClick={() => { dirty(); setValues({}); setPartial('') }}>Revert experiment</button><button type="button" className="secondary" disabled={working || busy || !reviewed || !result || Boolean(stale) || !proposal || !supplier || reviewed.fingerprint !== fingerprint || saved} onClick={() => void save()}>Save experiment</button></div></form>
    {error && <p className="message error" role="alert">{error}</p>}{saved && <p className="message notice" role="status">Experiment saved to audit history. Live financial state is unchanged.</p>}
    {result && reviewed?.fingerprint === fingerprint && <><div className="experiment-banner"><strong>{stale ? 'Source state changed. Evaluate again before saving.' : result.recommendation_changed ? 'The primary recommendation changes.' : 'The primary recommendation stays the same.'}</strong><p>Source generation {result.baseline.generation} · state {result.baseline.state_version}. {reviewed ? 'Reviewed experiment' : 'Inputs changed; evaluate again to save.'}</p><small className="mono">{result.source_state_digest}</small></div><div className="lab-comparison">{[result.baseline, result.modified].map((item, index) => { const metrics = item.actions.find(action => action.action.id === item.recommendation)?.metrics; return <article key={index}><span className="eyebrow">{index === 0 ? 'ORIGINAL SNAPSHOT' : 'HYPOTHETICAL SNAPSHOT'}</span><h3>{actionName(item.recommendation)}</h3><dl><div><dt>Settled cash</dt><dd>{currency(item.snapshot.cash_paise)}</dd></div><div><dt>Mandatory miss</dt><dd>{metrics ? percent(metrics.shortfall_probability) : 'Unavailable'}</dd></div><div><dt>Expected penalties</dt><dd>{metrics ? currency(metrics.expected_penalty_paise) : 'Unavailable'}</dd></div><div><dt>Remaining liabilities</dt><dd>{metrics ? currency(metrics.expected_total_remaining_liabilities_paise ?? metrics.expected_remaining_paise) : 'Unavailable'}</dd></div></dl></article> })}</div><StabilityView evaluation={result.modified} busy={working} onAnalyze={() => void evaluate()}/><PolicyBenchmark evaluation={result.modified}/></>}
  </section>
}
