import { ArrowDownLeft, ArrowUpRight, Clock3, FileText } from 'lucide-react'
import type { Event } from '../lib/api'
import { currency, dateLabel, timeLabel } from '../lib/api'

function eventDescription(event: Event): string {
  switch (event.type) {
    case 'RECEIVABLE_DELAYED': return `Payment expected ${dateLabel(event.expected_date)}`
    case 'RECEIVABLE_RECEIVED': return `${currency(event.amount_paise)} received and settled`
    case 'PAYMENT_CONFIRMED': return `${currency(event.amount_paise)} outgoing settlement recorded`
    case 'PAYMENT_PROPOSED': return `${currency(event.proposal.amount_paise)} payment proposed`
    case 'EXPENSE_RECORDED': return `${event.obligation.label} · ${currency(event.obligation.amount_paise)}`
    case 'RECEIVABLE_CREATED': return `${event.receivable.label} · ${currency(event.receivable.amount_paise)}`
    case 'OBLIGATION_UPDATED': return `Contract or amount updated for ${event.obligation_id}`
  }
}
export function Activity({ items, compact = false }: { items: { seq: number; event: Event }[]; compact?: boolean }) {
  if (!items.length) return <div className="empty-state"><Clock3 size={24} strokeWidth={1.3}/><h3>Your ledger is ready.</h3><p>No new events yet. Start the controlled feed or record a specific event.</p></div>
  return <ol className={`activity ${compact ? 'compact' : ''}`}>{items.map(({ seq, event }) => <li key={seq}>
    <span className="event-icon">{event.type === 'RECEIVABLE_RECEIVED' ? <ArrowDownLeft size={18}/> : event.type === 'PAYMENT_CONFIRMED' ? <ArrowUpRight size={18}/> : <FileText size={17}/>}</span>
    <div><strong>{event.type.replaceAll('_', ' ').toLowerCase()}</strong><p>{eventDescription(event)}</p><span className="event-meta">{dateLabel(event.timestamp)} · {timeLabel(event.timestamp)} IST <span className="accepted">Accepted</span></span>{!compact && <code>{event.event_id}</code>}</div>
  </li>)}</ol>
}
