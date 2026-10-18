import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { Comparison } from '../src/components/Comparison'
import { EventForm, ScenarioForm } from '../src/components/Forms'
import { currency, percent } from '../src/lib/api'
import type { Evaluation } from '../src/lib/api'
import fixture from './fixture.json'

const evaluation = fixture as unknown as Evaluation

test('comparison renders actual backend results and a unique recommendation', () => {
  render(<Comparison evaluation={evaluation}/>)
  expect(screen.getAllByText('Recommended')).toHaveLength(1)
  expect(screen.getByText('Split payment')).toBeVisible()
  expect(screen.getAllByText(percent(evaluation.actions[0].metrics!.shortfall_probability)).length).toBeGreaterThan(0)
})

test('invalid contract displays reason instead of invented metrics', () => {
  const changed = structuredClone(evaluation)
  changed.actions[1].valid = false
  changed.actions[1].metrics = null
  changed.actions[1].action.invalid_reason = 'Partial payments are prohibited by this contract.'
  render(<Comparison evaluation={changed}/>)
  expect(screen.getByText('Partial payments are prohibited by this contract.')).toBeVisible()
})

test('INR formatting preserves paise and negative projections', () => {
  expect(currency(12345678)).toBe('₹1,23,456.78')
  expect(currency(-1000000)).toBe('-₹10,000')
})

test('delay form creates typed event without touching actual cash', async () => {
  const submit = vi.fn().mockResolvedValue(undefined)
  render(<EventForm state={evaluation.snapshot} busy={false} onSubmit={submit}/>)
  await userEvent.clear(screen.getByLabelText('New expected date'))
  await userEvent.type(screen.getByLabelText('New expected date'), '2026-10-25')
  await userEvent.click(screen.getByRole('button', { name: 'Record event' }))
  expect(submit).toHaveBeenCalledWith(expect.objectContaining({ type: 'RECEIVABLE_DELAYED', receivable_id: 'customer', expected_date: '2026-10-25' }))
})

test('scenario editor sends amounts in integer paise and explicit terms', async () => {
  const submit = vi.fn().mockResolvedValue(undefined)
  render(<ScenarioForm state={evaluation.snapshot} busy={false} onSubmit={submit}/>)
  await userEvent.clear(screen.getByLabelText('Starting cash (₹)'))
  await userEvent.type(screen.getByLabelText('Starting cash (₹)'), '150000.25')
  await userEvent.click(screen.getByRole('button', { name: 'Start scenario' }))
  expect(submit).toHaveBeenCalledWith(expect.objectContaining({ cash_paise: 15000025, terms: expect.objectContaining({ allow_partial: true }) }))
})
