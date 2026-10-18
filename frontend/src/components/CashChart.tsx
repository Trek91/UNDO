import { useState } from 'react'
import { CartesianGrid, Line, LineChart, ReferenceDot, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Evaluation } from '../lib/api'
import { currency, dateLabel } from '../lib/api'

const colors: Record<string, string> = { full: '#B54743', partial: '#246B54', defer: '#4778CB', hold: '#9A692C' }
export function CashChart({ evaluation }: { evaluation: Evaluation }) {
  const [hidden, setHidden] = useState<string[]>([])
  const [showData, setShowData] = useState(false)
  const valid = evaluation.actions.filter(result => result.metrics)
  const data = Array.from({ length: evaluation.metadata.horizon_days + 1 }, (_, day) => {
    const date = new Date(`${evaluation.snapshot.base_date}T12:00:00Z`)
    date.setUTCDate(date.getUTCDate() + day)
    return { date: date.toISOString().slice(0, 10), ...Object.fromEntries(valid.map(result => [result.action.id, (result.metrics?.daily_paise[day] ?? 0) / 100])) }
  })
  return <section className="chart-section" aria-labelledby="cash-chart-title">
    <div className="section-title"><div><span className="eyebrow">THE NEXT {evaluation.metadata.horizon_days} DAYS</span><h2 id="cash-chart-title">See the cash flow.</h2></div><button className="text-button" onClick={() => setShowData(value => !value)} aria-expanded={showData}>{showData ? 'Hide data' : 'View data'}</button></div>
    <p className="section-description">Expected closing balances across the same {evaluation.metadata.paths.toLocaleString('en-IN')} simulated futures.</p>
    <p className="settled-anchor">Settled cash at decision time: <strong>{currency(evaluation.snapshot.cash_paise)}</strong> · projections begin after scheduled actions.</p>
    <div className="chart-legend">{valid.map(result => <button key={result.action.id} aria-pressed={!hidden.includes(result.action.id)} onClick={() => setHidden(previous => previous.includes(result.action.id) ? previous.filter(id => id !== result.action.id) : [...previous, result.action.id])}><span style={{ background: colors[result.action.id] }}/>{result.action.label}</button>)}</div>
    <div className="chart" role="img" aria-label="Projected closing cash by payment alternative. Reserve threshold and zero funding line shown. Exact values are available using View data.">
      <ResponsiveContainer width="100%" height={290}><LineChart data={data} margin={{ top: 20, right: 18, left: 4, bottom: 10 }} accessibilityLayer>
        <CartesianGrid stroke="#E1E5DF" strokeDasharray="3 5" vertical={false}/>
        <XAxis dataKey="date" tickFormatter={dateLabel} axisLine={false} tickLine={false} minTickGap={20} tick={{ fill: '#5E6B61', fontSize: 11 }} dy={10}/>
        <YAxis tickFormatter={value => `${value < 0 ? '−' : ''}₹${Math.abs(Number(value) / 1000)}k`} axisLine={false} tickLine={false} tick={{ fill: '#5E6B61', fontSize: 11 }} width={60}/>
        <ReferenceLine y={0} stroke="#B54743" strokeOpacity={0.5}/>
        <ReferenceDot x={evaluation.snapshot.base_date} y={evaluation.snapshot.cash_paise / 100} r={4} fill="#17231E" stroke="#fff" ifOverflow="extendDomain"/>
        <ReferenceLine y={evaluation.snapshot.reserve_paise / 100} stroke="#5E6B61" strokeDasharray="5 5" label={{ value: 'Desired reserve', fill: '#5E6B61', fontSize: 10, position: 'insideTopRight' }}/>
        <Tooltip labelFormatter={label => dateLabel(String(label))} formatter={(value, name) => [currency(Number(value) * 100), valid.find(result => result.action.id === name)?.action.label ?? name]} contentStyle={{ border: '1px solid #E1E5DF', borderRadius: 8, fontSize: 12 }}/>
        {valid.filter(result => !hidden.includes(result.action.id)).map(result => <Line key={result.action.id} name={result.action.id} dataKey={result.action.id} stroke={colors[result.action.id]} strokeWidth={evaluation.recommendation === result.action.id ? 3 : 1.5} strokeDasharray={result.action.id === 'hold' ? '5 4' : undefined} dot={false} activeDot={{ r: 4 }} isAnimationActive={false}/>)}
      </LineChart></ResponsiveContainer>
    </div>
    <p className="chart-footnote">Projection, not settled cash. Intraday deadlines can be missed even when closing cash is positive.</p>
    {evaluation.timeline.length > 0 && <details className="cash-timeline"><summary>Known deadlines and uncertain incoming payments</summary><ol>{evaluation.timeline.map((item, index) => <li key={index}><span>Day {item.day} · {item.kind === 'uncertain_receipt' ? 'Uncertain receipt' : item.kind === 'mandatory' ? 'Mandatory deadline' : 'Supplier deadline'}</span><strong>{item.label}</strong><span>{currency(item.amount_paise)}{item.kind === 'uncertain_receipt' ? ' · expected date, not guaranteed' : ' · remaining principal'}</span></li>)}</ol></details>}
    {showData && <div className="table-scroll" tabIndex={0} role="region" aria-label="Scrollable cash-flow data"><table><caption>Expected closing cash · INR</caption><thead><tr><th>Date</th>{valid.map(result => <th key={result.action.id}>{result.action.label}</th>)}</tr></thead><tbody>{data.map(row => <tr key={row.date}><th>{dateLabel(row.date)}</th>{valid.map(result => <td key={result.action.id}>{currency(Number(row[result.action.id as keyof typeof row]) * 100)}</td>)}</tr>)}</tbody></table></div>}
  </section>
}
