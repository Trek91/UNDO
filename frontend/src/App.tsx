import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Activity as ActivityIcon, ArrowDownLeft, ArrowRight, ArrowUpRight, ChartNoAxesCombined, Check, ChevronRight, CircleHelp, Clock3, FileClock, LayoutDashboard, LoaderCircle, Pause, Play, Plus, RotateCcw, Settings2, ShieldCheck, X } from 'lucide-react'
import { DecisionInsights, StabilityView, PolicyBenchmark } from './components/DecisionIntelligence'
import { ScenarioLab } from './components/ScenarioLab'
import { ModelEvidenceView } from './components/ModelEvidence'
import { Activity } from './components/Activity'
import { Comparison } from './components/Comparison'
import { Explanation } from './components/Explanation'
import { EventForm, ScenarioForm } from './components/Forms'
import { useWorkspace } from './hooks/useWorkspace'
import { api, currency, dateLabel, percent, timeLabel } from './lib/api'
import type { Decision, Evaluation, EventInput, State } from './lib/api'
import { decisionLink, matchesDecision, readDecisionLink } from './lib/decisionContext'

const LazyCashChart = lazy(() => import('./components/CashChart').then(module => ({ default: module.CashChart })))
function CashChart({ evaluation }: { evaluation: Evaluation }) {
  return <Suspense fallback={<div className="chart-placeholder" role="status">Loading the calculated cash-flow chart…</div>}><LazyCashChart evaluation={evaluation}/></Suspense>
}

const navigation = [
  { id: 'overview', label: 'Overview', Icon: LayoutDashboard }, { id: 'decisions', label: 'Decisions', Icon: ChartNoAxesCombined },
  { id: 'cash-flow', label: 'Cash flow', Icon: ActivityIcon }, { id: 'events', label: 'Event stream', Icon: Clock3 },
  { id: 'lab', label: 'Scenario Lab', Icon: Settings2 }, { id: 'model', label: 'Model evidence', Icon: ShieldCheck },
  { id: 'audit', label: 'Audit history', Icon: FileClock },
]

const routes = [...navigation, { id: 'stability', label: 'Recommendation stability' }, { id: 'policies', label: 'Policy benchmark' }]

export default function App() {
  const workspace = useWorkspace()
  const { overview, events, history, audit, error, notice, busy, connection, lastUpdated } = workspace
  const initialLink = useRef(readDecisionLink(location.hash))
  const [view, setView] = useState(() => routes.some(item => item.id === initialLink.current.view) ? initialLink.current.view : 'overview')
  const [editor, setEditor] = useState<'event' | 'scenario' | null>(null)
  const [running, setRunning] = useState(false)
  const [inspected, setInspected] = useState<Decision | null>(null)
  const [horizon, setHorizon] = useState(initialLink.current.horizon_days ?? 7)
  const [paths, setPaths] = useState(initialLink.current.paths ?? 1000)
  const [proposalId, setProposalId] = useState(initialLink.current.proposal_id ?? 'proposal')
  const [seed, setSeed] = useState(initialLink.current.seed ?? 20261017)
  const [actionIds, setActionIds] = useState<Evaluation['request']['action_ids']>(initialLink.current.action_ids ?? ['full', 'partial', 'defer', 'hold'])
  const [contextReady, setContextReady] = useState(false)
  const initializedGeneration = useRef<number | null>(null)
  useEffect(() => {
    if (!overview || initializedGeneration.current === overview.state.generation) return
    initializedGeneration.current = overview.state.generation
    const request = overview.latest_decision?.evaluation.request
    const link = initialLink.current
    setHorizon(link.horizon_days ?? request?.horizon_days ?? 7)
    setPaths(link.paths ?? request?.paths ?? 1000)
    setProposalId(link.proposal_id ?? request?.proposal_id ?? Object.keys(overview.state.proposals).sort()[0] ?? '')
    setSeed(link.seed ?? request?.seed ?? 20261017)
    setActionIds(link.action_ids ?? request?.action_ids ?? ['full', 'partial', 'defer', 'hold'])
    initialLink.current = { view: link.view }
    setContextReady(true)
  }, [overview])
  useEffect(() => {
    const sync = () => {
      const link = readDecisionLink(location.hash)
      if (routes.some(item => item.id === link.view)) setView(link.view)
      if (link.proposal_id !== undefined) setProposalId(link.proposal_id)
      if (link.horizon_days !== undefined) setHorizon(link.horizon_days)
      if (link.paths !== undefined) setPaths(link.paths)
      if (link.seed !== undefined) setSeed(link.seed)
      if (link.action_ids !== undefined) setActionIds(link.action_ids)
    }
    window.addEventListener('hashchange', sync)
    return () => window.removeEventListener('hashchange', sync)
  }, [])
  useEffect(() => {
    if (contextReady) {
      const next = decisionLink(view, { proposal_id: proposalId, horizon_days: horizon, paths, seed, action_ids: actionIds })
      if (location.hash.slice(1) !== next) window.history.replaceState(null, '', `#${next}`)
    }
  }, [view, proposalId, horizon, paths, seed, actionIds, contextReady])
  const { mutate, setNotice, postCurrent } = workspace
  useEffect(() => {
    if (!running) return
    const timer = setInterval(async () => {
      const result = await mutate(() => postCurrent<{ completed: boolean }>('/demo/events/next'), 'Demo event processed; current comparison will refresh.')
      if (!result || result.completed) { setRunning(false); if (result?.completed) setNotice('The deterministic feed is complete. Reset the demo to replay it.') }
    }, 5000)
    return () => clearInterval(timer)
  }, [running, mutate, setNotice, postCurrent])
  const state = overview?.state
  const saved = inspected ?? overview?.latest_decision
  const active = saved ? { ...saved, stale: saved.stale || saved.evaluation.generation !== state?.generation || saved.evaluation.state_version !== state?.version } : saved
  const context = { proposal_id: proposalId, horizon_days: horizon, paths, seed, action_ids: actionIds }
  const evaluation = active && (inspected || matchesDecision(active.evaluation, context)) ? active.evaluation : undefined
  const decisionState = inspected ? inspected.evaluation.snapshot : state
  const proposal = decisionState?.proposals[inspected?.evaluation.request.proposal_id ?? proposalId]
  const supplier = proposal ? decisionState?.obligations[proposal.obligation_id] : undefined
  const chosen = evaluation?.actions.find(result => result.action.id === evaluation.recommendation)
  const navigate = (next: string) => {
    setView(next); setInspected(null); setEditor(null)
    // Record navigation immediately, even before the initial context effect runs.
    const link = decisionLink(next, context)
    if (location.hash.slice(1) !== link) location.hash = link
  }
  const recordEvent = (body: EventInput) => mutate(() => postCurrent('/events', body), 'Event accepted. The ledger and affected comparisons are updating.')
  const startScenario = async (body: object) => {
    setRunning(false)
    const result = await mutate(() => postCurrent<State>('/demo/scenario', body), 'New synthetic scenario started. Evaluate its payment to compare outcomes.')
    if (result) { setEditor(null); setInspected(null); setProposalId('proposal') }
  }
  const reset = async () => {
    setRunning(false)
    const result = await mutate(() => postCurrent<State>('/demo/reset'), 'Baseline restored. Previous generations remain in the audit history.')
    if (result) { setInspected(null); setEditor(null); setProposalId('proposal') }
  }
  const inspect = async (identifier: string) => {
    const result = await mutate(() => api<Decision>(`/decisions/${identifier}`), 'Stored evaluation opened with its original financial snapshot.')
    if (result) setInspected(result)
  }

  return <div className="app-shell">
    <a className="skip-link" href="#main">Skip to content</a>
    <aside className="sidebar"><a className="wordmark" href="#overview" onClick={event => { event.preventDefault(); navigate('overview') }} aria-label="UNDO overview"><span className="brand-mark">↶</span>UNDO<span className="wordmark-dot">.</span></a>
      <div className="workspace-label">YOUR WORKSPACE</div>
      <nav aria-label="Main navigation">{navigation.map(({ id, label, Icon }) => <button key={id} aria-label={label} onClick={() => navigate(id)} className={view === id ? 'selected' : ''} aria-current={view === id ? 'page' : undefined}><Icon size={18} strokeWidth={1.6}/><span>{label}</span>{view === id && <span className="nav-indicator"/>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="local-note"><ShieldCheck size={19}/><div><strong>A space to think ahead.</strong><p>Simulate decisions.<br/>No real money moves.</p></div></div><button className="help-link" onClick={() => { navigate('decisions'); if (!evaluation) workspace.setNotice('Evaluate a payment to inspect the model, contractual terms and reproducibility details.') }}><CircleHelp size={16}/>How UNDO works<ArrowUpRight size={14}/></button><div className="profile"><span>MS</span><div><strong>{state?.business_name ?? 'Morrow Studio'}</strong><small>Synthetic workspace</small></div></div></div>
    </aside>
    <div className="workspace-main"><header className="topbar"><div className="breadcrumb">Workspace <ChevronRight size={12}/> <strong>{routes.find(item => item.id === view)?.label}</strong></div><div className="topbar-status"><span className={`connection ${connection}`}><i/>{connection === 'live' ? 'Connected' : connection === 'reconnecting' ? 'Reconnecting' : 'Connecting'}</span><span className="demo-badge">DEMO DATA{state && ` · STATE ${state.version}`}</span><button className="icon-button" aria-label="Edit synthetic scenario" aria-expanded={editor === 'scenario'} onClick={() => setEditor(editor === 'scenario' ? null : 'scenario')}><Settings2 size={18}/></button></div></header>
    <main id="main" tabIndex={-1}>
      {error && <div className="message error" role="alert"><span>{error}</span><button onClick={() => void workspace.refresh()}>Retry</button><button className="icon-button" onClick={() => workspace.setError(null)} aria-label="Dismiss error"><X size={16}/></button></div>}
      {notice && <div className="message notice" role="status"><Check size={16}/><span>{notice}</span><button className="icon-button" onClick={() => workspace.setNotice(null)} aria-label="Dismiss notification"><X size={16}/></button></div>}
      {connection === 'reconnecting' && <p className="connection-warning" role="status">Live updates are reconnecting. The page refreshes periodically; saved financial state is preserved.</p>}
      {!state ? <div className="initial-loading" aria-busy="true"><LoaderCircle className="spin" size={28}/><h1>{error ? 'Workspace unavailable' : 'Opening your workspace'}</h1><p>{error ? 'Retry the connection to load the persisted financial state.' : 'Loading the financial ledger and saved decisions.'}</p></div> : <>
      <div className="page-heading"><div><span className="eyebrow">DECISION INTELLIGENCE, IN REAL TIME</span><h1>{view === 'overview' ? <>Decision Room.<br/><span>A better next move.</span></> : view === 'decisions' ? 'Consider every move.' : view === 'cash-flow' ? 'Follow the possibilities.' : view === 'events' ? 'As the picture changes.' : view === 'lab' ? 'Explore the what if.' : view === 'model' ? 'Evidence before confidence.' : view === 'stability' ? 'When does the answer change?' : view === 'policies' ? 'Compare the approaches.' : 'Every decision, traceable.'}</h1><p>{view === 'overview' ? 'See the consequences before you commit.' : view === 'audit' ? 'The facts, assumptions and calculations behind each recommendation.' : 'A clear view of your cash, commitments and choices.'}</p></div><div className="heading-actions"><span className="as-of">SCENARIO DATE · {dateLabel(state.base_date).toUpperCase()}</span><button className="secondary" onClick={() => setEditor(editor === 'event' ? null : 'event')} aria-expanded={editor === 'event'}><Plus size={16}/>Record event</button></div></div>
      {editor && <div className="editor"><button className="icon-button editor-close" onClick={() => setEditor(null)} aria-label="Close editor"><X size={18}/></button>{editor === 'event' ? <EventForm key={`${state.generation}-${state.version}`} state={state} busy={busy} onSubmit={recordEvent}/> : <ScenarioForm key={`${state.generation}-${state.version}`} state={state} busy={busy} onSubmit={startScenario}/>}</div>}
      <div className="financial-strip"><div><span>Available cash <span className="settled-dot"/></span><strong>{currency(state.cash_paise)}</strong><small>Settled · available now</small></div><div><span>Near-term mandatory</span><strong>{currency(overview.near_term_mandatory_paise)}</strong><small>Known dues · next {overview.near_term_horizon_days} days</small></div><div><span>Expected incoming</span><strong>{currency(overview.outstanding_receivables_paise)}</strong><small>Not yet available cash</small></div><div><span>Desired reserve</span><strong>{currency(state.reserve_paise)}</strong><small>Risk target · not a guarantee</small></div></div>
      {inspected && <div className="historical-banner"><FileClock size={18}/><span>Viewing {inspected.evaluation.scope === 'experiment' ? 'hypothetical experiment ·' : 'saved'} generation {inspected.evaluation.generation}, state {inspected.evaluation.state_version}. {active?.stale ? 'This evaluation is historical.' : 'This evaluation matches current state.'}</span><button className="text-button" onClick={() => setInspected(null)}>Return to current</button></div>}
      <nav className="intelligence-nav" aria-label="Decision intelligence">{[['overview', 'Decision Room'], ['lab', 'Scenario Lab'], ['stability', 'Recommendation stability'], ['policies', 'Policy benchmark'], ['model', 'Model Evidence Center']].map(([id, label]) => <button key={id} className={view === id ? 'active' : ''} onClick={() => navigate(id)}>{label}</button>)}</nav>
      {view === 'lab' && <ScenarioLab key={`${state.generation}:${proposalId}:${horizon}:${paths}:${seed}:${actionIds.join(',')}`} state={state} context={context} onSelectProposal={setProposalId} busy={busy} postCurrent={postCurrent} refresh={workspace.refresh}/>}
      {view === 'model' && <ModelEvidenceView/>}
      {view === 'stability' && <StabilityView evaluation={evaluation} busy={busy || Boolean(active?.stale) || Boolean(inspected)} onAnalyze={() => void workspace.evaluate({ ...context, include_robustness: true })}/>}
      {view === 'policies' && <PolicyBenchmark evaluation={evaluation}/>}
      {['overview', 'decisions'].includes(view) && <>
        <section className="decision-panel" aria-labelledby="payment-title"><div className="payment-summary"><span className="eyebrow">YOUR NEXT DECISION</span><div className="payment-header"><span className="supplier-avatar"><ArrowUpRight size={22}/></span><div><h2 id="payment-title">{supplier?.label ?? 'No pending obligation'}</h2><p>Supplier payment {supplier && <>· due {dateLabel(supplier.due_date)}</>}</p></div><span className="status-tag">PROPOSED</span></div><div className="proposed-amount">{currency(proposal?.amount_paise ?? 0)}</div><p className="payment-note">A payment is more than a balance check.<br/>Compare its effect on the days ahead.</p><div className="evaluation-controls"><label>Horizon<select aria-label="Simulation horizon" disabled={Boolean(inspected)} value={inspected?.evaluation.request.horizon_days ?? horizon} onChange={event => setHorizon(Number(event.target.value))}>{[...new Set([inspected?.evaluation.request.horizon_days ?? horizon, 1, 3, 7, 14, 30])].sort((a,b) => a-b).map(days => <option key={days} value={days}>{days} days</option>)}</select></label><label>Paths<select aria-label="Simulation paths" disabled={Boolean(inspected)} value={inspected?.evaluation.request.paths ?? paths} onChange={event => setPaths(Number(event.target.value))}>{[...new Set([inspected?.evaluation.request.paths ?? paths, 100, 1000, 5000])].sort((a,b) => a-b).map(count => <option key={count} value={count}>{count.toLocaleString('en-IN')}</option>)}</select></label>{Object.keys(decisionState?.proposals ?? {}).length > 1 && <label>Proposal<select aria-label="Proposal" disabled={Boolean(inspected)} value={inspected?.evaluation.request.proposal_id ?? proposalId} onChange={event => setProposalId(event.target.value)}>{Object.values(decisionState?.proposals ?? {}).map(item => <option key={item.id} value={item.id}>{item.id}</option>)}</select></label>}</div><button className="primary evaluate-button" disabled={busy || !proposal || Boolean(inspected)} onClick={() => { setInspected(null); void workspace.evaluate(context) }}>{busy ? <LoaderCircle size={17} className="spin"/> : <ChartNoAxesCombined size={17}/>}Evaluate payment<ArrowRight size={16}/></button></div>
        <div className={`recommendation-panel ${chosen ? 'has-recommendation' : ''}`}>{chosen?.metrics ? <><div className="recommendation-eyebrow"><span className="recommendation-symbol"><Check size={17}/></span>{active?.stale ? 'SAVED RECOMMENDATION · STALE' : 'COMPUTED RECOMMENDATION'}</div><h2>{chosen.action.label}.<br/><span>Keep your options clear.</span></h2><p>{chosen.action.description}</p><div className="recommendation-metrics"><div><strong>{percent(chosen.metrics.shortfall_probability)}</strong><span>Mandatory shortfall</span></div><div><strong>{currency(chosen.metrics.expected_penalty_paise)}</strong><span>Expected penalties</span></div></div><p className="risk-disclosure">Reserve breach: {percent(chosen.metrics.reserve_breach_probability)}. {evaluation?.explanation.downside}</p><button className="text-button" onClick={() => document.getElementById('reasoning')?.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' })}>Understand the recommendation<ArrowRight size={15}/></button></> : <><div className="orbital-mark" aria-hidden="true"><span/><span/><ArrowUpRight size={38} strokeWidth={1}/></div><span className="eyebrow">BEFORE YOU COMMIT</span><h2>{evaluation?.status === 'infeasible' ? 'No feasible action.' : evaluation?.status === 'unavailable' ? 'Model unavailable.' : 'Evaluation required.'}</h2><p>{evaluation ? evaluation.explanation.reason : 'Evaluate this selected payment and settings to view its recommendation. Results for another payment or configuration are not shown.'}</p><div className="method-label"><ShieldCheck size={15}/>Real calculations. Inspectable assumptions.</div></>}</div></section>
        {overview.recalculating && <p className="recalculation" role="status"><LoaderCircle size={15} className="spin"/>New facts received. Recalculating against financial state {state.version}…</p>}
        {overview.worker_error && <p role="alert" className="critical-text">{overview.worker_error}</p>}
        {evaluation && active?.stale && !inspected && <p className="stale-note" role="status">The saved comparison uses an older financial state or calculation engine. Evaluate again or wait for recalculation.</p>}
        {evaluation && <DecisionInsights evaluation={evaluation}/>}
        {evaluation && <section className="comparison-section"><div className="section-title"><div><span className="eyebrow">SAME STARTING POINT. DIFFERENT CHOICES.</span><h2>Consider the alternatives.</h2></div><span className="section-meta">{evaluation.metadata.paths.toLocaleString('en-IN')} paths · state {evaluation.state_version}</span></div><Comparison evaluation={evaluation}/></section>}
      </>}
      {view === 'overview' && <div className="insight-grid"><div>{evaluation ? <CashChart evaluation={evaluation}/> : <section className="chart-placeholder"><span className="eyebrow">CASH-FLOW OUTLOOK</span><h2>The possibilities start here.</h2><div className="placeholder-lines" aria-hidden="true"><span/><span/><span/></div><p>Evaluate the proposed payment to calculate comparable cash trajectories.</p></section>}</div><section className="activity-section"><div className="section-title"><h2>Live activity</h2><span className="live-dot"/></div><p className="section-description">Accepted changes to your financial picture.</p><Activity items={events.items.slice(0, 3)} compact/><button className="text-button" onClick={() => navigate('events')}>Open event stream<ArrowRight size={14}/></button></section></div>}
      {view === 'cash-flow' && (evaluation ? <CashChart evaluation={evaluation}/> : <section className="empty-state"><ChartNoAxesCombined size={32}/><h2>A forecast needs a decision.</h2><p>Evaluate a payment to generate its cash-flow alternatives.</p><button className="primary" onClick={() => navigate('decisions')}>Open decisions<ArrowRight size={15}/></button></section>)}
      {view === 'events' && <section><div className="section-title"><div><span className="eyebrow">PERSISTED FINANCIAL EVENTS</span><h2>The story as it happens.</h2></div><button className={running ? 'secondary' : 'primary'} disabled={busy} onClick={() => setRunning(value => !value)}>{running ? <Pause size={15}/> : <Play size={15}/>} {running ? 'Pause feed' : 'Start demo feed'}</button></div><p className="section-description">Three deterministic events, five seconds apart. Pause anytime or record a specific event above.</p><Activity items={events.items}/>{events.next_before && <button className="secondary" onClick={() => void workspace.loadMoreEvents()}>Load earlier events</button>}</section>}
      {view === 'audit' && <section><div className="section-title"><div><span className="eyebrow">DURABLE HISTORY</span><h2>Nothing behind the curtain.</h2></div><span className="section-meta">Current generation {state.generation}</span></div><p className="section-description">Reset and scenario changes archive earlier records. Open any saved evaluation from the trail.</p><div className="table-scroll" tabIndex={0} role="region" aria-label="Scrollable audit history"><table className="audit-table"><caption className="sr-only">Audit records across synthetic generations</caption><thead><tr><th>Time · IST</th><th>Generation</th><th>Recorded action</th><th>Details</th></tr></thead><tbody>{audit.items.map(row => <tr key={row.seq}><td>{dateLabel(row.created_at)} · {timeLabel(row.created_at)}</td><td>{row.generation}</td><td>{row.kind.replaceAll('_', ' ').toLowerCase()}</td><td>{['EVALUATION_COMPLETED', 'EXPERIMENT_SAVED'].includes(row.kind) ? <button className="text-button" onClick={() => void inspect(String(row.detail.evaluation_id))}>Open evaluation<ArrowUpRight size={14}/></button> : <span>{row.kind === 'DEMO_RESET' || row.kind === 'SCENARIO_CREATED' ? `Previous generation ${row.detail.previous_generation}` : String(row.detail.type ?? row.detail.event_id ?? 'Financial state updated')}</span>}</td></tr>)}</tbody></table></div>{!audit.items.length && <div className="empty-state"><FileClock size={26}/><h3>A clean starting point.</h3><p>Events, comparisons and resets will appear here.</p></div>}{audit.next_before && <button className="secondary" onClick={() => void workspace.loadMoreAudit()}>Load earlier audit records</button>}</section>}
      {evaluation && (['overview', 'decisions'].includes(view) || inspected) && <div id="reasoning"><Explanation evaluation={evaluation} statistics={active?.model_statistics} expanded={view === 'decisions' || Boolean(inspected)}/></div>}
      {view === 'decisions' && <section className="decision-history"><div className="section-title"><h2>Saved comparisons</h2><span className="section-meta">This scenario generation</span></div>{history.items.length ? <div className="history-list">{history.items.map(record => <button key={record.evaluation.id} onClick={() => void inspect(record.evaluation.id)}><FileClock size={19}/><div><strong>{record.evaluation.actions.find(item => item.action.id === record.evaluation.recommendation)?.action.label ?? record.evaluation.status}</strong><small>{record.evaluation.scope === 'experiment' ? 'Experiment · ' : ''}State {record.evaluation.state_version} · {record.evaluation.metadata.paths} paths · {record.stale ? 'Historical' : 'Current state'}</small></div><ArrowUpRight size={17}/></button>)}</div> : <p className="muted">Your first evaluation will be saved here.</p>}{history.next_before && <button className="secondary" onClick={() => void workspace.loadMoreHistory()}>Load earlier comparisons</button>}</section>}
      {['overview', 'cash-flow'].includes(view) && <div className="ledger-grid"><section><div className="section-title"><h2>What’s due</h2><ArrowUpRight size={18}/></div>{Object.values(state.obligations).map(item => <div key={item.id} className="ledger-row"><div><strong>{item.label}</strong><small>{dateLabel(item.due_date)} · {item.mandatory ? 'Mandatory expense' : 'Supplier commitment'}</small></div><div><strong>{currency(item.amount_paise - item.paid_paise)}</strong><small>{item.amount_paise === item.paid_paise ? 'Settled' : 'Outstanding'}</small></div></div>)}</section><section><div className="section-title"><h2>Expected incoming</h2><ArrowDownLeft size={18}/></div>{Object.values(state.receivables).map(item => <div key={item.id} className="ledger-row"><div><strong>{item.label}</strong><small>Expected {dateLabel(item.expected_date)} · {item.status}</small></div><div><strong>{currency(item.amount_paise - item.received_paise)}</strong><small>{item.status === 'settled' ? 'Settled into cash' : 'Not available cash'}</small></div></div>)}</section></div>}
      <footer className="footer"><div><span className="footer-wordmark">UNDO</span><span>Simulated decision support. Future outcomes are uncertain.</span></div><div><span>{lastUpdated ? `Updated ${timeLabel(lastUpdated)} IST` : 'Connecting…'}</span><button className="text-button" disabled={busy} onClick={() => void reset()}><RotateCcw size={13}/>Reset demo</button></div></footer>
      </>}
    </main></div>
  </div>
}
