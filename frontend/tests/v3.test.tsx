import { render, screen } from '@testing-library/react'
import type { Evaluation } from '../src/lib/api'
import { DecisionInsights, PolicyBenchmark, StabilityView } from '../src/components/DecisionIntelligence'
import fixture from './v3-fixture.json'

const evaluation = fixture as unknown as Evaluation
test('primary policy and experimental model status remain distinct', () => {
  render(<DecisionInsights evaluation={evaluation}/>)
  expect(screen.getByText('Obligation-aware rule')).toBeVisible()
  expect(screen.getByText('EXPERIMENTAL')).toBeVisible()
  expect(screen.getByText(/Conditional forecasts/)).toBeVisible()
})
test('stability is actual grid evidence rather than confidence', () => {
  render(<StabilityView evaluation={evaluation} onAnalyze={() => {}} busy={false}/>)
  expect(screen.getByRole('table', { name: 'Sensitivity cases and recommendation changes' })).toBeVisible()
  expect(screen.getByRole('heading', { name: /not model confidence/ })).toBeVisible()
  expect(screen.getAllByText(/proposed payment/i).length).toBeGreaterThan(0)
})
test('policy benchmark includes all actual policy rows and limitations', () => {
  render(<PolicyBenchmark evaluation={evaluation}/>)
  expect(screen.getByRole('rowheader', { name: /Balance-only/ })).toBeVisible()
  expect(screen.getByRole('rowheader', { name: /Obligation-aware rule/ })).toBeVisible()
  expect(screen.getByText(/not held-out effectiveness evidence/)).toBeVisible()
})
