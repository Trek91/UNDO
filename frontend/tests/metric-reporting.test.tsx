import { cleanup, render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import { Explanation } from '../src/components/Explanation'
import { ModelEvidenceView } from '../src/components/ModelEvidence'
import { api } from '../src/lib/api'
import type { Evaluation, ModelEvidence } from '../src/lib/api'
import evaluationJson from './v3-fixture.json'
import evidenceJson from './model-evidence-fixture.json'

vi.mock('../src/lib/api', async original => ({ ...await original<typeof import('../src/lib/api')>(), api: vi.fn() }))
const evaluation = evaluationJson as unknown as Evaluation
const report = evidenceJson as unknown as ModelEvidence

test('explanation and evidence center display the identical denominator-aware precision', async () => {
  const text = 'Undefined — no positive predictions (0 predicted positives)'
  render(<Explanation evaluation={evaluation} expanded statistics={report.daily!.classification}/>)
  expect(screen.getByText(text)).toBeVisible()
  cleanup()
  vi.mocked(api).mockResolvedValue(report)
  render(<ModelEvidenceView/>)
  expect((await screen.findAllByText(text)).length).toBe(2)
})

test('historical missing denominators display unavailable instead of guessing a corrected zero', () => {
  render(<Explanation evaluation={evaluation} expanded/>)
  expect(screen.getAllByText(/Unavailable — stored denominator counts unavailable/)).toHaveLength(3)
})
