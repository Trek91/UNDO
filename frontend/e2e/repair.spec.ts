import { test, expect, type APIRequestContext } from '@playwright/test'

async function twoProposals(request: APIRequestContext) {
  await request.post('/api/demo/reset')
  const base = { business_id: 'demo', timestamp: new Date().toISOString(), currency: 'INR' }
  expect((await request.post('/api/events', { data: { ...base, event_id: crypto.randomUUID(), type: 'EXPENSE_RECORDED',
    obligation: { id: 'second', label: 'Second supplier', amount_paise: 1000000, mandatory: false, due_date: '2026-11-01' } } })).status()).toBe(201)
  expect((await request.post('/api/events', { data: { ...base, event_id: crypto.randomUUID(), type: 'PAYMENT_PROPOSED',
    proposal: { id: 'other', obligation_id: 'second', amount_paise: 1000000 } } })).status()).toBe(201)
  return (await (await request.post('/api/decisions/evaluate', { data: { proposal_id: 'proposal', paths: 100 } })).json()).evaluation
}

test('repair phase1: proposal and configuration changes invalidate unrelated results', async ({ page, request }) => {
  const original = await twoProposals(request)
  expect(original.recommendation).toBe('partial')
  await page.goto('/')
  await expect(page.getByText('COMPUTED RECOMMENDATION', { exact: true })).toBeVisible()
  await page.getByLabel('Proposal', { exact: true }).selectOption('other')
  await expect(page.getByRole('heading', { name: 'Evaluation required.' })).toBeVisible()
  await expect(page.locator('.recommendation-panel')).not.toContainText('Split payment')
  await expect(page.getByRole('region', { name: 'Recommendation explanation' })).toHaveCount(0)
  await page.getByLabel('Proposal', { exact: true }).selectOption('proposal')
  await expect(page.getByText('COMPUTED RECOMMENDATION', { exact: true })).toBeVisible()
  await page.getByLabel('Proposal', { exact: true }).selectOption('other')
  await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Pay in full. Keep your options clear.' })).toBeVisible()
  const current = (await (await request.get('/api/overview')).json()).latest_decision.evaluation
  expect(current.request.proposal_id).toBe('other')
  await page.getByLabel('Simulation horizon').selectOption('14')
  await expect(page.getByRole('heading', { name: 'Evaluation required.' })).toBeVisible()
  await page.getByLabel('Simulation horizon').selectOption('7')
  await expect(page.getByRole('heading', { name: 'Pay in full. Keep your options clear.' })).toBeVisible()
})

test('repair phase1: delayed A completion cannot overwrite selection B', async ({ page, request }) => {
  await twoProposals(request)
  let release!: () => void; let received!: () => void
  const gate = new Promise<void>(resolve => { release = resolve })
  const started = new Promise<void>(resolve => { received = resolve })
  await page.route('**/api/decisions/evaluate?*', async route => {
    const response = await route.fetch(); received(); await gate; await route.fulfill({ response })
  })
  await page.goto('/')
  await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
  await started
  await page.getByLabel('Proposal', { exact: true }).selectOption('other')
  release()
  await expect(page.getByRole('heading', { name: 'Evaluation required.' })).toBeVisible()
  await expect(page.locator('.recommendation-panel')).not.toContainText('Split payment')
  await page.unroute('**/api/decisions/evaluate?*')
  await expect(page.getByRole('button', { name: 'Evaluate payment', exact: true })).toBeEnabled()
  await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Pay in full. Keep your options clear.' })).toBeVisible()
})

test('repair phase2: pending 1000 response cannot enable saving edited 2000 inputs', async ({ page, request }) => {
  test.setTimeout(60000)
  await twoProposals(request)
  const before = (await (await request.get('/api/overview')).json()).state
  let release!: () => void; let received!: () => void
  const gate = new Promise<void>(resolve => { release = resolve })
  const started = new Promise<void>(resolve => { received = resolve })
  await page.route('**/api/lab/evaluate?*', async route => {
    const response = await route.fetch(); received(); await gate; await route.fulfill({ response })
  })
  await page.goto('/#lab')
  const input = page.getByLabel('Additional expense · ₹', { exact: true })
  await input.fill('1000'); await page.getByRole('button', { name: 'Evaluate experiment', exact: true }).click()
  await started; await input.fill('2000')
  const obsoleteCompleted = page.waitForResponse(response => response.url().includes('/api/lab/evaluate?')
    && response.request().postDataJSON().changes.unexpected_expense_paise === 100000)
  release(); expect((await obsoleteCompleted).ok()).toBe(true)
  await expect(input).toHaveValue('2000')
  await expect(page.getByRole('button', { name: 'Save experiment', exact: true })).toBeDisabled()
  await expect(page.locator('.lab-comparison')).toHaveCount(0)
  await page.unroute('**/api/lab/evaluate?*')
  let releaseCurrent!: () => void; let currentReceived!: () => void
  const currentGate = new Promise<void>(resolve => { releaseCurrent = resolve })
  const currentStarted = new Promise<void>(resolve => { currentReceived = resolve })
  await page.route('**/api/lab/evaluate?*', async route => {
    expect(route.request().postDataJSON().changes.unexpected_expense_paise).toBe(200000)
    const response = await route.fetch(); expect(response.ok()).toBe(true)
    currentReceived(); await currentGate; await route.fulfill({ response })
  })
  const completed = page.waitForResponse(response => response.url().includes('/api/lab/evaluate?')
    && response.request().postDataJSON().changes.unexpected_expense_paise === 200000)
  await page.getByRole('button', { name: 'Evaluate experiment', exact: true }).click()
  await currentStarted
  await expect(page.getByRole('button', { name: 'Save experiment', exact: true })).toBeDisabled()
  releaseCurrent(); expect((await completed).ok()).toBe(true)
  await expect(page.getByRole('button', { name: 'Save experiment', exact: true })).toBeEnabled()
  const saved = page.waitForRequest(request => request.url().includes('/api/lab/save?'))
  const savedResponse = page.waitForResponse(response => response.url().includes('/api/lab/save?'))
  await page.getByRole('button', { name: 'Save experiment', exact: true }).click()
  expect((await saved).postDataJSON().changes.unexpected_expense_paise).toBe(200000)
  expect((await savedResponse).ok()).toBe(true)
  await expect(page.getByText(/Experiment saved to audit history/)).toBeVisible()
  expect((await (await request.get('/api/overview')).json()).state).toEqual(before)
  const history = (await (await request.get('/api/decisions')).json()).items
  expect(history.find((row: { evaluation: { scope: string } }) => row.evaluation.scope === 'experiment').evaluation.experiment_changes.unexpected_expense_paise).toBe(200000)
})

test('repair phase3: identical precision reporting while raw historical metadata stays unchanged', async ({ page, request }) => {
  const original = await twoProposals(request)
  const before = await (await request.get('/api/decisions/'+original.id)).json()
  expect(before.evaluation.metadata.model_metrics.precision).toBe(0)
  expect(before.model_statistics.precision.value).toBeNull()
  const text = 'Undefined — no positive predictions (0 predicted positives)'
  await page.goto('/#decisions')
  await expect(page.getByText(text, { exact: true })).toBeVisible()
  await page.getByRole('navigation', { name: 'Decision intelligence' }).getByRole('button', { name: 'Model Evidence Center' }).click()
  await expect(page.getByText(text, { exact: true })).toHaveCount(2)
  const after = await (await request.get('/api/decisions/'+original.id)).json()
  expect(after.evaluation).toEqual(before.evaluation)
})

test('repair phase4: Lab inherits B/settings, survives refresh, and rejects removed target without baseline changes', async ({ page, request }) => {
  test.setTimeout(60000)
  await twoProposals(request)
  const before = (await (await request.get('/api/overview')).json()).state
  await page.goto('/')
  await page.getByLabel('Proposal', { exact: true }).selectOption('other')
  await page.getByLabel('Simulation horizon').selectOption('14')
  await page.getByLabel('Simulation paths').selectOption('1000')
  await page.getByRole('navigation', { name: 'Decision intelligence' }).getByRole('button', { name: 'Scenario Lab', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Experiment target' })).toContainText('Second supplier')
  await expect(page.getByLabel('Experiment proposal', { exact: true })).toHaveValue('other')
  await expect(page.getByLabel('Experiment horizon')).toHaveValue('14')
  await expect(page.getByLabel('Experiment paths')).toHaveValue('1000')
  await page.reload()
  await expect(page.getByLabel('Experiment proposal', { exact: true })).toHaveValue('other')
  await expect(page.getByLabel('Experiment horizon')).toHaveValue('14')
  const calculate = page.waitForRequest(req => req.url().includes('/api/lab/evaluate?'))
  const calculated = page.waitForResponse(res => res.url().includes('/api/lab/evaluate?'))
  await page.getByRole('button', { name: 'Evaluate experiment', exact: true }).click()
  expect((await calculate).postDataJSON().simulation).toMatchObject({ proposal_id: 'other', horizon_days: 14, paths: 1000 })
  const response = await calculated
  expect(response.ok(), await response.text()).toBeTruthy()
  await expect(page.getByRole('button', { name: 'Save experiment', exact: true })).toBeEnabled()
  expect((await (await request.get('/api/overview')).json()).state).toEqual(before)
  const closed = await request.post('/api/events', { data: { event_id: crypto.randomUUID(), business_id: 'demo', timestamp: new Date().toISOString(), type: 'PAYMENT_CONFIRMED', obligation_id: 'second', amount_paise: 1000000 } })
  expect(closed.status()).toBe(201)
  await expect(page.getByRole('alert')).toContainText('Selected proposal other is unavailable')
  await expect(page.getByRole('button', { name: 'Evaluate experiment', exact: true })).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Save experiment', exact: true })).toBeDisabled()
  await page.getByLabel('Experiment proposal', { exact: true }).selectOption('proposal')
  await expect(page.getByRole('button', { name: 'Evaluate experiment', exact: true })).toBeEnabled()
  await page.goto('/#lab?proposal=other&horizon=14&paths=1000&seed=42')
  await expect(page.getByRole('alert')).toContainText('Selected proposal other is unavailable')
})
