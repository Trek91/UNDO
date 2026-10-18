import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, vi } from 'vitest'
import App from '../src/App'
import type { Decision, Overview } from '../src/lib/api'
import jsonFixture from './v3-fixture.json'
const fixture = jsonFixture as unknown as Decision['evaluation']

vi.mock('../src/hooks/useWorkspace', () => ({ useWorkspace: () => workspace }))
vi.mock('../src/components/CashChart', () => ({ CashChart: () => <div>Calculated chart</div> }))
const state = { ...structuredClone(fixture.snapshot), generation: 1, version: 0,
  obligations: { ...structuredClone(fixture.snapshot.obligations), second: { ...structuredClone(fixture.snapshot.obligations.supplier), id: 'second', label: 'Second supplier', amount_paise: 1000000 } },
  proposals: { ...structuredClone(fixture.snapshot.proposals), other: { id: 'other', obligation_id: 'second', amount_paise: 1000000 } },
} as Overview['state']
const decision = (proposal = 'proposal', recommendation: 'partial' | 'full' = 'partial'): Decision => ({ stale: false, model_statistics: null,
  evaluation: { ...structuredClone(fixture), id: proposal+'-evaluation', snapshot: structuredClone(state), generation: 1, state_version: 0,
    request: { ...fixture.request, proposal_id: proposal, paths: 100, include_robustness: false },
    recommendation, metadata: { ...fixture.metadata, paths: 100 },
  } as Decision['evaluation'],
})
const workspace = {
  overview: {} as Overview, events: { items: [], next_before: null }, history: { items: [], next_before: null }, audit: { items: [], next_before: null },
  error: null, notice: null, busy: false, connection: 'live', lastUpdated: null,
  mutate: vi.fn(), setNotice: vi.fn(), setError: vi.fn(), postCurrent: vi.fn(), refresh: vi.fn(), evaluate: vi.fn(),
}
beforeEach(() => {
  location.hash = '#overview'
  vi.clearAllMocks()
  workspace.overview = { state: structuredClone(state), latest_decision: decision(), notification_cursor: 1, recalculating: false, worker_error: null,
    outstanding_obligations_paise: 12000000, outstanding_receivables_paise: 4000000, near_term_mandatory_paise: 5000000, near_term_horizon_days: 7 }
})
const recommendation = () => screen.queryByRole('heading', { name: 'Split payment. Keep your options clear.' })
const selectProposal = () => screen.getByRole('combobox', { name: /^Proposal/ })

test('A: switching to B removes A evidence until B is evaluated', async () => {
  const user = userEvent.setup(); const view = render(<App/>)
  expect(recommendation()).toBeVisible()
  await user.selectOptions(selectProposal(), 'other')
  expect(screen.getByRole('heading', { name: 'Evaluation required.' })).toBeVisible()
  expect(recommendation()).not.toBeInTheDocument()
  expect(screen.queryByRole('region', { name: 'Recommendation explanation' })).not.toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Evaluate payment' }))
  expect(workspace.evaluate).toHaveBeenCalledWith(expect.objectContaining({ proposal_id: 'other' }))
  workspace.overview = { ...workspace.overview, latest_decision: decision('other', 'full') }; view.rerender(<App/>)
  expect(screen.getByRole('heading', { name: 'Pay in full. Keep your options clear.' })).toBeVisible()
})

test('B: completion of A after switching to B cannot appear as B result', async () => {
  const user = userEvent.setup(); const view = render(<App/>)
  let complete!: () => void
  workspace.evaluate.mockImplementationOnce(() => new Promise<void>(resolve => { complete = resolve }))
  await user.click(screen.getByRole('button', { name: 'Evaluate payment' }))
  await user.selectOptions(selectProposal(), 'other')
  await act(async () => { complete(); workspace.overview = { ...workspace.overview, latest_decision: decision() }; view.rerender(<App/>) })
  expect(screen.getByRole('heading', { name: 'Evaluation required.' })).toBeVisible()
  expect(recommendation()).not.toBeInTheDocument()
  workspace.overview = { ...workspace.overview, latest_decision: decision('other', 'full') }; view.rerender(<App/>)
  expect(screen.getByRole('heading', { name: 'Pay in full. Keep your options clear.' })).toBeVisible()
})

test('C: settings invalidate the result; financial-state changes explicitly mark it historical', async () => {
  const user = userEvent.setup(); const view = render(<App/>)
  await user.selectOptions(screen.getByLabelText('Simulation horizon'), '14')
  expect(screen.getByRole('heading', { name: 'Evaluation required.' })).toBeVisible()
  await user.selectOptions(screen.getByLabelText('Simulation horizon'), '7')
  expect(recommendation()).toBeVisible()
  workspace.overview = { ...workspace.overview, state: { ...state, version: 1 } }; view.rerender(<App/>)
  expect(screen.getByText('SAVED RECOMMENDATION · STALE')).toBeVisible()
})

test('D: returning to A reuses only matching settings and financial state', async () => {
  const user = userEvent.setup(); render(<App/>)
  await user.selectOptions(selectProposal(), 'other')
  expect(recommendation()).not.toBeInTheDocument()
  await user.selectOptions(selectProposal(), 'proposal')
  expect(recommendation()).toBeVisible()
  await user.selectOptions(screen.getByLabelText('Simulation paths'), '1000')
  await user.selectOptions(selectProposal(), 'other'); await user.selectOptions(selectProposal(), 'proposal')
  expect(screen.getByRole('heading', { name: 'Evaluation required.' })).toBeVisible()
})

test('Lab inherits selected stable proposal and settings, visibly identifies target, and does not evaluate live state', async () => {
  const user = userEvent.setup(); render(<App/>)
  await user.selectOptions(selectProposal(), 'other')
  await user.selectOptions(screen.getByLabelText('Simulation horizon'), '14')
  await user.selectOptions(screen.getByLabelText('Simulation paths'), '1000')
  await user.click(screen.getAllByRole('button', { name: 'Scenario Lab' })[0])
  expect(screen.getByRole('region', { name: 'Experiment target' })).toHaveTextContent('Second supplier')
  expect(screen.getByLabelText('Experiment proposal')).toHaveValue('other')
  expect(screen.getByLabelText('Experiment horizon')).toHaveValue('14')
  expect(screen.getByLabelText('Experiment paths')).toHaveValue('1000')
  expect(workspace.evaluate).not.toHaveBeenCalled()
  expect(location.hash).toContain('proposal=other')
})

test('direct Lab link preserves target/settings; missing target requires explicit replacement', async () => {
  location.hash = '#lab?proposal=other&horizon=14&paths=1000&seed=42'
  const user = userEvent.setup(); const view = render(<App/>)
  expect(screen.getByLabelText('Experiment proposal')).toHaveValue('other')
  expect(screen.getByLabelText('Experiment horizon')).toHaveValue('14')
  const next = structuredClone(state); delete next.proposals.other
  workspace.overview = { ...workspace.overview, state: { ...next, version: 1 } }; view.rerender(<App/>)
  expect(screen.getByRole('alert')).toHaveTextContent('Selected proposal other is unavailable')
  expect(screen.getByRole('button', { name: 'Evaluate experiment' })).toBeDisabled()
  await user.selectOptions(screen.getByLabelText('Experiment proposal'), 'proposal')
  expect(screen.getByRole('button', { name: 'Evaluate experiment' })).toBeEnabled()
})

test('URL context normalization replaces an entry while explicit navigation adds exactly one', async () => {
  const initialEntries = window.history.length
  const user = userEvent.setup(); render(<App/>)
  expect(window.history.length).toBe(initialEntries)
  await user.click(screen.getByRole('button', { name: /^Decisions$/ }))
  expect(location.hash).toContain('#decisions?proposal=proposal')
  expect(window.history.length).toBe(initialEntries+1)
  await act(async () => { location.hash = '#events'; window.dispatchEvent(new HashChangeEvent('hashchange')) })
  expect(screen.getByRole('button', { name: /^Event stream$/ })).toHaveAttribute('aria-current', 'page')
  expect(location.hash).toContain('#events?proposal=proposal')
  expect(window.history.length).toBe(initialEntries+2)
})
