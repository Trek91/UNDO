import { useState } from 'react'
import type { EventInput, State } from '../lib/api'

function paise(value: FormDataEntryValue | null): number {
  const text = String(value ?? '')
  if (!/^\d+(\.\d{1,2})?$/.test(text)) throw new Error('Enter a nonnegative amount with at most two decimal places.')
  const [whole, fraction = ''] = text.split('.')
  const result = Number(whole) * 100 + Number(fraction.padEnd(2, '0'))
  if (!Number.isSafeInteger(result) || result > 100000000000) throw new Error('Amount exceeds the supported limit.')
  return result
}

export function ScenarioForm({ state, busy, onSubmit }: { state: State; busy: boolean; onSubmit: (body: object) => Promise<unknown> }) {
  const [error, setError] = useState('')
  const terms = state.obligations.supplier?.terms
  return <form className="editor-form" onSubmit={async event => {
    event.preventDefault(); setError('')
    try {
      const data = new FormData(event.currentTarget)
      await onSubmit({ cash_paise: paise(data.get('cash')), reserve_paise: paise(data.get('reserve')),
        supplier_paise: paise(data.get('supplier')), expense_paise: paise(data.get('expense')), receivable_paise: paise(data.get('receivable')),
        supplier_due_days: Number(data.get('supplierDay')), expense_due_days: Number(data.get('expenseDay')), receivable_due_days: Number(data.get('receivableDay')),
        terms: { allow_partial: data.has('partial'), allow_deferral: data.has('defer'),
          minimum_partial_paise: paise(data.get('minimumPartial')), partial_days: Number(data.get('partialDay')),
          defer_days: Number(data.get('deferDay')), late_penalty_paise: paise(data.get('penalty')) } })
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Check the scenario.') }
  }}>
    <div><span className="eyebrow">SYNTHETIC SCENARIO</span><h2>Change the assumptions.</h2><p>Creates a new scenario. Previous events and decisions remain in the audit history.</p></div>
    <div className="form-grid">
      <label>Starting cash (₹)<input name="cash" inputMode="decimal" defaultValue={state.cash_paise / 100} required/></label>
      <label>Desired reserve (₹)<input name="reserve" inputMode="decimal" defaultValue={state.reserve_paise / 100} required/></label>
      <label>Supplier payment (₹)<input name="supplier" inputMode="decimal" defaultValue={(state.obligations.supplier?.amount_paise ?? 6000000) / 100} required/></label>
      <label>Supplier due in days<input name="supplierDay" type="number" min="0" max="30" defaultValue="0" required/></label>
      <label>Mandatory expense (₹)<input name="expense" inputMode="decimal" defaultValue={(state.obligations.operations?.amount_paise ?? 5000000) / 100} required/></label>
      <label>Expense due in days<input name="expenseDay" type="number" min="0" max="30" defaultValue="1" required/></label>
      <label>Expected receivable (₹)<input name="receivable" inputMode="decimal" defaultValue={(state.receivables.customer?.amount_paise ?? 4000000) / 100} required/></label>
      <label>Receivable expected in days<input name="receivableDay" type="number" min="0" max="30" defaultValue="1" required/></label>
      <label>Minimum partial payment (₹)<input name="minimumPartial" inputMode="decimal" defaultValue={(terms?.minimum_partial_paise ?? 3000000) / 100} required/></label>
      <label>Remainder due after original date (days)<input name="partialDay" type="number" min="1" max="30" defaultValue={terms?.partial_days ?? 3} required/></label>
      <label>Deferral after original date (days)<input name="deferDay" type="number" min="1" max="30" defaultValue={terms?.defer_days ?? 3} required/></label>
      <label>One-time late fee (₹)<input name="penalty" inputMode="decimal" defaultValue={(terms?.late_penalty_paise ?? 200000) / 100} required/></label>
    </div>
    <div className="checkbox-row"><label><input type="checkbox" name="partial" defaultChecked={terms?.allow_partial ?? true}/> Contract permits split payment</label><label><input type="checkbox" name="defer" defaultChecked={terms?.allow_deferral ?? true}/> Contract permits deferral with late fee</label></div>
    {error && <p role="alert" className="critical-text">{error}</p>}
    <button className="primary" disabled={busy}>Start scenario</button>
  </form>
}

export function EventForm({ state, busy, onSubmit }: { state: State; busy: boolean; onSubmit: (body: EventInput) => Promise<unknown> }) {
  const [kind, setKind] = useState('RECEIVABLE_DELAYED')
  const [error, setError] = useState('')
  const receivableKind = kind.startsWith('RECEIVABLE_') && kind !== 'RECEIVABLE_CREATED'
  const amountNeeded = kind !== 'RECEIVABLE_DELAYED'
  const dateNeeded = ['RECEIVABLE_DELAYED', 'RECEIVABLE_CREATED', 'EXPENSE_RECORDED', 'OBLIGATION_UPDATED'].includes(kind)
  const first = Object.values(state.receivables).find(item => item.status !== 'settled')
  const newDate = new Date(`${first?.expected_date ?? state.base_date}T12:00:00Z`)
  newDate.setUTCDate(newDate.getUTCDate() + 3)
  return <form className="editor-form event-form" onSubmit={async event => {
    event.preventDefault(); setError('')
    try {
      const data = new FormData(event.currentTarget)
      const identifier = crypto.randomUUID()
      const base = { event_id: identifier, business_id: state.business_id, timestamp: new Date().toISOString(), currency: 'INR' as const }
      const amount = amountNeeded ? paise(data.get('amount')) : 0
      const target = String(data.get('target'))
      const due = String(data.get('date'))
      let payload: EventInput
      switch (kind) {
        case 'RECEIVABLE_DELAYED': payload = { ...base, type: kind, receivable_id: target, expected_date: due }; break
        case 'RECEIVABLE_RECEIVED': payload = { ...base, type: kind, receivable_id: target, amount_paise: amount }; break
        case 'PAYMENT_CONFIRMED': payload = { ...base, type: kind, obligation_id: target, amount_paise: amount }; break
        case 'PAYMENT_PROPOSED': payload = { ...base, type: kind, proposal: { id: 'proposal', obligation_id: target, amount_paise: amount } }; break
        case 'OBLIGATION_UPDATED': payload = { ...base, type: kind, obligation_id: target, amount_paise: amount, due_date: due }; break
        case 'RECEIVABLE_CREATED': payload = { ...base, type: kind, receivable: { id: `invoice-${identifier}`, label: String(data.get('label')), amount_paise: amount, received_paise: 0, status: 'expected', historical_late_rate: 0.35, historical_delay_days: 2, created_date: state.base_date, expected_date: due } }; break
        default: payload = { ...base, type: 'EXPENSE_RECORDED', obligation: { id: `expense-${identifier}`, label: String(data.get('label')), amount_paise: amount, paid_paise: 0, due_date: due, mandatory: true } }
      }
      await onSubmit(payload)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Check the event.') }
  }}>
    <div><span className="eyebrow">CONTROLLED EVENT INPUT</span><h2>Update the financial picture.</h2><p>Record synthetic facts, then watch the current comparison recalculate.</p></div>
    <div className="form-grid">
      <label>Event type<select value={kind} onChange={event => setKind(event.target.value)}>
        <option value="RECEIVABLE_DELAYED">Customer payment delayed</option><option value="EXPENSE_RECORDED">Unexpected expense</option>
        <option value="RECEIVABLE_RECEIVED">Record incoming settlement</option><option value="PAYMENT_CONFIRMED">Record outgoing settlement</option>
        <option value="PAYMENT_PROPOSED">Change payment proposal</option><option value="OBLIGATION_UPDATED">Update obligation</option><option value="RECEIVABLE_CREATED">Create expected receivable</option>
      </select></label>
      {!['EXPENSE_RECORDED', 'RECEIVABLE_CREATED'].includes(kind) && <label>{receivableKind ? 'Customer invoice' : 'Payment obligation'}<select key={receivableKind ? 'invoice' : 'obligation'} name="target" required>
        {receivableKind ? Object.values(state.receivables).filter(item => item.status !== 'settled').map(item => <option value={item.id} key={item.id}>{item.label}</option>) : Object.values(state.obligations).filter(item => item.paid_paise < item.amount_paise).map(item => <option value={item.id} key={item.id}>{item.label}</option>)}
      </select></label>}
      {amountNeeded && <label>Amount (₹)<input name="amount" inputMode="decimal" placeholder="8000.00" required/></label>}
      {dateNeeded && <label>{kind === 'RECEIVABLE_DELAYED' ? 'New expected date' : 'Due / expected date'}<input key={kind} type="date" name="date" defaultValue={kind === 'RECEIVABLE_DELAYED' ? newDate.toISOString().slice(0, 10) : state.base_date} required/></label>}
      {['EXPENSE_RECORDED', 'RECEIVABLE_CREATED'].includes(kind) && <label>Description<input name="label" maxLength={100} placeholder="Equipment repair" required/></label>}
    </div>
    {kind === 'PAYMENT_CONFIRMED' && <p className="form-hint">Records a synthetic settled payment and reduces demo cash. It does not initiate a real transaction.</p>}
    {kind === 'EXPENSE_RECORDED' && <p className="form-hint">Creates an obligation. Cash changes only when an outgoing settlement is recorded.</p>}
    {error && <p role="alert" className="critical-text">{error}</p>}
    <button className="primary" disabled={busy}>Record event</button>
  </form>
}
