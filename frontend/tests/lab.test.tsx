import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { ScenarioLab } from '../src/components/ScenarioLab'
import type { LabResult, State } from '../src/lib/api'
import fixture from './v3-fixture.json'

test('saving requires a reviewed experiment and edits invalidate that review', async () => {
  const user = userEvent.setup()
  const result = { baseline: fixture, modified: { ...fixture, scope: 'experiment' }, source_state_digest: 'a'.repeat(64), recommendation_changed: false, stale: false, semantics: '' } as unknown as LabResult
  const post = vi.fn().mockResolvedValue(result)
  render(<ScenarioLab state={fixture.snapshot as State} busy={false} postCurrent={post} refresh={vi.fn()}/>)
  expect(screen.getByRole('button', { name: 'Save experiment' })).toBeDisabled()
  await user.type(screen.getByLabelText('Additional expense · ₹'), '10000.01')
  await user.click(screen.getByRole('button', { name: 'Evaluate experiment' }))
  expect(post.mock.calls[0][1].changes.unexpected_expense_paise).toBe(1000001)
  expect(screen.getByRole('button', { name: 'Save experiment' })).toBeEnabled()
  await user.click(screen.getByRole('button', { name: 'Save experiment' }))
  expect(post.mock.calls[1][0]).toBe('/lab/save')
  expect(post.mock.calls[1][1].source_state_digest).toBe('a'.repeat(64))
  expect(await screen.findByText(/Experiment saved to audit history/)).toBeVisible()
  await user.type(screen.getByLabelText('Receipt delay · days'), '5')
  expect(screen.getByRole('button', { name: 'Save experiment' })).toBeDisabled()
  await user.click(screen.getByRole('button', { name: 'Revert experiment' }))
  expect(screen.queryByText('The primary recommendation stays the same.')).not.toBeInTheDocument()
  expect(screen.getByRole('region', { name: 'Experiment target' })).toBeVisible()
  expect(post).toHaveBeenCalledTimes(2)
})

test('lab failure exposes retryable error and never offers an unreviewed save', async () => {
  const post = vi.fn().mockRejectedValue(new Error('Source changed'))
  render(<ScenarioLab state={fixture.snapshot as State} busy={false} postCurrent={post} refresh={vi.fn()}/>)
  await userEvent.click(screen.getByRole('button', { name: 'Evaluate experiment' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Source changed')
  expect(screen.getByRole('button', { name: 'Save experiment' })).toBeDisabled()
})

const response = (marker: string): LabResult => ({ baseline: fixture, modified: { ...fixture, scope: 'experiment' }, source_state_digest: marker.repeat(64), recommendation_changed: false, stale: false, semantics: '' }) as unknown as LabResult
function pending<T>() { let resolve!: (value: T) => void; let reject!: (error: Error) => void; const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no }); return { promise, resolve, reject } }

test('race: edited 2000 draft cannot accept or save pending 1000 result; current save payload is 2000', async () => {
  const user = userEvent.setup(); const first = pending<LabResult>(); const second = pending<LabResult>()
  const post = vi.fn().mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise).mockResolvedValue({})
  render(<ScenarioLab state={fixture.snapshot as State} busy={false} postCurrent={post} refresh={vi.fn()}/>)
  const input = screen.getByLabelText('Additional expense · ₹')
  await user.type(input, '1000'); await user.click(screen.getByRole('button', { name: 'Evaluate experiment' }))
  await user.clear(input); await user.type(input, '2000')
  await act(async () => first.resolve(response('a')))
  expect(input).toHaveValue(2000)
  expect(screen.queryByText('Reviewed experiment')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Save experiment' })).toBeDisabled()
  await user.click(screen.getByRole('button', { name: 'Evaluate experiment' }))
  await act(async () => second.resolve(response('b')))
  expect(screen.getByRole('button', { name: 'Save experiment' })).toBeEnabled()
  await user.click(screen.getByRole('button', { name: 'Save experiment' }))
  expect(post.mock.calls[2][1].changes.unexpected_expense_paise).toBe(200000)
  expect(post.mock.calls[2][1].source_state_digest).toBe('b'.repeat(64))
})

test('newer response wins when older evaluation resolves last', async () => {
  const user = userEvent.setup(); const first = pending<LabResult>(); const second = pending<LabResult>()
  const post = vi.fn().mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise)
  render(<ScenarioLab state={fixture.snapshot as State} busy={false} postCurrent={post} refresh={vi.fn()}/>)
  const input = screen.getByLabelText('Additional expense · ₹')
  await user.type(input, '1000'); await user.click(screen.getByRole('button', { name: 'Evaluate experiment' }))
  await user.clear(input); await user.type(input, '2000')
  await user.click(screen.getByRole('button', { name: 'Evaluate experiment' }))
  expect(post).toHaveBeenCalledTimes(2)
  await act(async () => second.resolve(response('b')))
  await act(async () => first.resolve(response('a')))
  expect(screen.getByText('b'.repeat(64))).toBeVisible()
  expect(screen.queryByText('a'.repeat(64))).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Save experiment' })).toBeEnabled()
})

test('a failed current request cannot be rescued by an older success', async () => {
  const user = userEvent.setup(); const old = pending<LabResult>(); const current = pending<LabResult>()
  const post = vi.fn().mockReturnValueOnce(old.promise).mockReturnValueOnce(current.promise)
  render(<ScenarioLab state={fixture.snapshot as State} busy={false} postCurrent={post} refresh={vi.fn()}/>)
  await user.click(screen.getByRole('button', { name: 'Evaluate experiment' }))
  await user.type(screen.getByLabelText('Receipt delay · days'), '2')
  await user.click(screen.getByRole('button', { name: 'Evaluate experiment' }))
  await act(async () => current.reject(new Error('Current calculation failed')))
  await act(async () => old.resolve(response('a')))
  expect(screen.getByRole('alert')).toHaveTextContent('Current calculation failed')
  expect(screen.getByRole('button', { name: 'Save experiment' })).toBeDisabled()
})
