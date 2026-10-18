import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { mkdir } from 'node:fs/promises'

test.beforeEach(async ({ request }) => { await request.post('/api/demo/reset') })

test('complete decision, delay, recalculation, audit and reset journey', async ({ page, request }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await page.goto('/')
  await expect(page.getByText('₹1,00,000', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
  await expect(page.getByText('COMPUTED RECOMMENDATION', { exact: true })).toBeVisible()
  const original = await (await request.get('/api/overview')).json()
  await expect(page.getByRole('table', { name: 'All payment alternatives evaluated against the same simulated futures' }).getByRole('row')).toHaveCount(5)
  await page.getByRole('button', { name: 'Understand the recommendation' }).click()
  await expect(page.getByText('A decision you can inspect.')).toBeVisible()
  await page.getByRole('button', { name: 'Record event', exact: true }).click()
  await page.getByLabel('New expected date').fill('2026-10-26')
  await page.getByRole('button', { name: 'Record event', exact: true }).last().click()
  await expect.poll(async () => {
    const value = await (await request.get('/api/overview')).json()
    return value.latest_decision?.evaluation.state_version
  }).toBe(1)
  const updated = await (await request.get('/api/overview')).json()
  expect(updated.state.cash_paise).toBe(10000000)
  expect(updated.latest_decision.evaluation.actions).not.toEqual(original.latest_decision.evaluation.actions)
  await page.getByRole('button', { name: 'Audit history', exact: true }).click()
  await expect(page.getByText('evaluation completed', { exact: true }).first()).toBeVisible()
  await page.getByRole('button', { name: 'Open evaluation' }).last().click()
  await expect(page.getByText(/This evaluation is historical/)).toBeVisible()
  await page.getByRole('button', { name: 'Reset demo', exact: true }).click()
  const baseline = await (await request.get('/api/overview')).json()
  expect(baseline.state.version).toBe(0)
  expect(baseline.state.cash_paise).toBe(10000000)
  expect(errors).toEqual([])
})

test('unexpected expense, duplicate delivery and invalid input remain safe', async ({ page, request }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
  await expect(page.getByText('COMPUTED RECOMMENDATION', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Record event', exact: true }).click()
  await page.getByLabel('Event type').selectOption('EXPENSE_RECORDED')
  await page.getByLabel('Amount (₹)', { exact: true }).fill('8000')
  await page.getByLabel('Description', { exact: true }).fill('Emergency repair')
  await page.getByRole('button', { name: 'Record event', exact: true }).last().click()
  await expect.poll(async () => (await (await request.get('/api/overview')).json()).state.version).toBe(1)
  const state = await (await request.get('/api/overview')).json()
  expect(state.state.cash_paise).toBe(10000000)
  expect(state.outstanding_obligations_paise).toBe(11800000)
  const accepted = (await (await request.get('/api/events')).json()).items[0].event
  const retry = await request.post('/api/events', { data: accepted })
  expect(retry.status()).toBe(200)
  expect((await retry.json()).duplicate).toBe(true)
  const invalid = await request.post('/api/events', { data: { ...accepted, event_id: 'invalid', obligation: { ...accepted.obligation, amount_paise: -1 } } })
  expect(invalid.status()).toBe(422)
  expect((await (await request.get('/api/overview')).json()).state.version).toBe(1)
})

test('feed start pause resume has observable persisted outcomes', async ({ page, request }) => {
  await page.goto('/#events')
  await page.getByRole('button', { name: 'Start demo feed' }).click()
  await expect(page.getByRole('button', { name: 'Pause feed' })).toBeVisible()
  await expect.poll(async () => (await (await request.get('/api/events')).json()).items.length, { timeout: 10000 }).toBe(1)
  await page.getByRole('button', { name: 'Pause feed' }).click()
  const paused = (await (await request.get('/api/events')).json()).items.length
  await page.waitForTimeout(5300)
  expect((await (await request.get('/api/events')).json()).items.length).toBe(paused)
  await page.getByRole('button', { name: 'Start demo feed' }).click()
  await expect.poll(async () => (await (await request.get('/api/events')).json()).items.length, { timeout: 10000 }).toBe(2)
  await page.getByRole('button', { name: 'Pause feed' }).click()
})

test('scenario controls derive a different recommendation from changed facts', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Edit synthetic scenario' }).click()
  await page.getByLabel('Starting cash (₹)').fill('200000')
  await page.getByLabel('Supplier payment (₹)').fill('10000')
  await page.getByRole('button', { name: 'Start scenario', exact: true }).click()
  await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Pay in full. Keep your options clear.', exact: true })).toBeVisible()
})

test('infeasible actions are disclosed without forcing a recommendation', async ({ page, request }) => {
  await request.post('/api/demo/scenario', { data: { cash_paise: 0, terms: { allow_partial: false, allow_deferral: false } } })
  await page.goto('/')
  // Evaluate an explicitly selected, immediately unaffordable action through the real API.
  const response = await request.post('/api/decisions/evaluate', { data: { action_ids: ['full'], paths: 100 } })
  expect((await response.json()).evaluation.status).toBe('infeasible')
  await page.reload()
  await expect(page.getByText('No feasible action.', { exact: true })).toBeVisible()
  await expect(page.getByRole('cell').getByText('Immediate payment exceeds settled cash after prior mandatory deadlines.')).toBeVisible()
})

test('disconnect and backend errors have recovery paths', async ({ page }) => {
  await page.route('**/api/events/stream*', route => route.abort())
  await page.goto('/')
  await expect(page.getByText(/Live updates are reconnecting/)).toBeVisible()
  await page.route('**/api/decisions/evaluate*', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: { code: 'database_unavailable', message: 'Storage is unavailable. Retry shortly.' } }) }))
  await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('Storage is unavailable.')
  await mkdir('../docs/screenshots', { recursive: true })
  await page.screenshot({ path: '../docs/screenshots/error-recovery.png', fullPage: true })
  await page.unroute('**/api/decisions/evaluate*')
  await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
  await expect(page.getByText('COMPUTED RECOMMENDATION', { exact: true })).toBeVisible()
})

test('responsive layout, keyboard access, contrast and reduced motion', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
  await expect(page.getByText('COMPUTED RECOMMENDATION', { exact: true })).toBeVisible()
  const desktop = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
  expect(desktop.violations.map(item => ({ id: item.id, nodes: item.nodes.map(node => ({ target: node.target, summary: node.failureSummary })) }))).toEqual([])
  for (const width of [1440, 768, 390]) {
    await page.setViewportSize({ width, height: 900 })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  }
  const mobile = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
  expect(mobile.violations.map(item => ({ id: item.id, nodes: item.nodes.map(node => ({ target: node.target, summary: node.failureSummary })) }))).toEqual([])
  await page.reload()
  await expect(page.getByRole('button', { name: 'Evaluate payment', exact: true })).toBeVisible()
  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused()
  expect(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(true)
})

test('loading and empty states are real and usable', async ({ page }) => {
  await page.route('**/api/overview', async route => { await new Promise(resolve => setTimeout(resolve, 700)); await route.continue() })
  await page.goto('/')
  await expect(page.getByText('Opening your workspace')).toBeVisible()
  await page.screenshot({ path: '../docs/screenshots/loading.png', fullPage: true })
  await expect(page.getByRole('button', { name: 'Evaluate payment', exact: true })).toBeVisible()
  await expect(page.getByText('Your ledger is ready.')).toBeVisible()
})

test('open saved evaluation becomes historical when a live event arrives', async ({ page, request }) => {
  await page.goto('/#decisions')
  await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
  await expect(page.getByText('COMPUTED RECOMMENDATION', { exact: true })).toBeVisible()
  await page.locator('.history-list button').first().click()
  await expect(page.getByText(/This evaluation matches current state/)).toBeVisible()
  const result = await request.post('/api/events', { data: { event_id: crypto.randomUUID(), business_id: 'demo',
    timestamp: new Date().toISOString(), type: 'RECEIVABLE_DELAYED', receivable_id: 'customer', expected_date: '2026-10-29' } })
  expect(result.status()).toBe(201)
  await expect(page.getByText(/This evaluation is historical/)).toBeVisible()
})

test('stale browser mutation after another client resets is rejected without ledger changes', async ({ page, request }) => {
  const original = await (await request.get('/api/overview')).json()
  await page.route('**/api/overview', route => route.fulfill({ json: original }))
  await page.route('**/api/events/stream*', route => route.abort())
  await page.goto('/')
  await page.getByRole('button', { name: 'Record event', exact: true }).click()
  await page.getByLabel('New expected date').fill('2026-10-27')
  await request.post('/api/demo/reset')
  await page.getByRole('button', { name: 'Record event', exact: true }).last().click()
  await expect(page.getByRole('alert')).toContainText('Financial state changed')
  const current = await (await request.get('/api/overview')).json()
  expect(current.state.generation).toBe(original.state.generation+1)
  expect(current.state.version).toBe(0)
  expect(current.state.cash_paise).toBe(original.state.cash_paise)
})

test('browser back and forward stay synchronized with navigation', async ({ page }) => {
  await page.goto('/#overview')
  await page.getByRole('button', { name: 'Decisions', exact: true }).click()
  await page.getByRole('button', { name: 'Event stream', exact: true }).click()
  await page.goBack()
  await expect(page.getByRole('button', { name: 'Decisions', exact: true })).toHaveAttribute('aria-current', 'page')
  await page.goForward()
  await expect(page.getByRole('button', { name: 'Event stream', exact: true })).toHaveAttribute('aria-current', 'page')
})

test('chart data, legend and simulation controls reflect backend calculations', async ({ page, request }) => {
  await page.goto('/')
  await page.getByLabel('Simulation horizon').selectOption('14')
  await page.getByLabel('Simulation paths').selectOption('100')
  await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
  await expect(page.getByText('COMPUTED RECOMMENDATION', { exact: true })).toBeVisible()
  const result = (await (await request.get('/api/overview')).json()).latest_decision.evaluation
  expect(result.metadata.horizon_days).toBe(14)
  expect(result.metadata.paths).toBe(100)
  await page.getByRole('button', { name: 'View data', exact: true }).click()
  const table = page.getByRole('table', { name: 'Expected closing cash · INR', exact: true })
  const rows = table.locator('tbody tr')
  await expect(rows).toHaveCount(15)
  const format = (paise: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: paise % 100 === 0 ? 0 : 2 }).format(paise/100)
  const valid = result.actions.filter((action: { metrics: unknown }) => action.metrics)
  for (let day = 0; day <= 14; day++) {
    expect(await rows.nth(day).locator('td').allTextContents()).toEqual(valid.map((action: { metrics: { daily_paise: number[] } }) => format(action.metrics.daily_paise[day])))
  }
  const legend = page.locator('.chart-legend button').first()
  await legend.click()
  await expect(legend).toHaveAttribute('aria-pressed', 'false')
  await legend.click()
  await expect(legend).toHaveAttribute('aria-pressed', 'true')
})

test('event, evaluation and audit pagination expose every retained record', async ({ page, request }) => {
  for (let index = 0; index < 51; index++) {
    const accepted = await request.post('/api/events', { data: { event_id: crypto.randomUUID(), business_id: 'demo',
      timestamp: new Date().toISOString(), type: 'PAYMENT_CONFIRMED', obligation_id: 'supplier', amount_paise: 1 } })
    expect(accepted.status()).toBe(201)
  }
  for (let index = 0; index < 31; index++) expect((await request.post('/api/decisions/evaluate', { data: { paths: 1 } })).status()).toBe(200)
  const expectedAuditCount = (await (await request.get('/api/audit?limit=100')).json()).items.length
  await page.goto('/#events')
  await expect(page.locator('ol.activity > li')).toHaveCount(50)
  await page.getByRole('button', { name: 'Load earlier events', exact: true }).click()
  await expect(page.locator('ol.activity > li')).toHaveCount(51)
  await page.getByRole('button', { name: 'Decisions', exact: true }).click()
  await expect(page.locator('.history-list > button')).toHaveCount(30)
  await page.getByRole('button', { name: 'Load earlier comparisons', exact: true }).click()
  await expect(page.locator('.history-list > button')).toHaveCount(31)
  await page.getByRole('button', { name: 'Audit history', exact: true }).click()
  await expect(page.locator('.audit-table tbody tr')).toHaveCount(50)
  await page.getByRole('button', { name: 'Load earlier audit records', exact: true }).click()
  await expect(page.locator('.audit-table tbody tr')).toHaveCount(expectedAuditCount)
  // A new persisted update refreshes the page without discarding loaded historical pages.
  await request.post('/api/decisions/evaluate', { data: { paths: 1 } })
  await expect(page.locator('.audit-table tbody tr')).toHaveCount(expectedAuditCount+1)
})
