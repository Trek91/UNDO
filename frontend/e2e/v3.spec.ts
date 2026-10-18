import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { mkdir } from 'node:fs/promises'

test.beforeEach(async ({ request }) => { await request.post('/api/demo/reset') })

test('V3 flagship experiment, stability, evidence, save, live update and immutable history', async ({ page, request }) => {
  test.setTimeout(90000)
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await page.goto('/')
  await page.getByLabel('Simulation paths').selectOption('100')
  await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
  await expect(page.getByText('COMPUTED RECOMMENDATION', { exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Obligation-aware rule', exact: true })).toBeVisible()
  const before = (await (await request.get('/api/overview')).json()).state
  await page.getByRole('navigation', { name: 'Decision intelligence' }).getByRole('button', { name: 'Scenario Lab', exact: true }).click()
  await page.getByLabel('Receipt delay · days', { exact: true }).fill('5')
  await page.getByRole('button', { name: 'Evaluate experiment', exact: true }).click()
  await expect(page.getByText('The primary recommendation stays the same.', { exact: true })).toBeVisible({ timeout: 30000 })
  await page.getByLabel('Additional expense · ₹', { exact: true }).fill('10000.01')
  await expect(page.getByRole('button', { name: 'Save experiment', exact: true })).toBeDisabled()
  await page.getByRole('button', { name: 'Evaluate experiment', exact: true }).click()
  await expect(page.getByText('The primary recommendation changes.', { exact: true })).toBeVisible({ timeout: 30000 })
  await expect(page.locator('.lab-comparison article').last()).toContainText('Hold for review')
  await expect(page.getByRole('table', { name: 'Sensitivity cases and recommendation changes' })).toBeVisible()
  await expect(page.getByRole('table', { name: 'Policy outcomes on identical financial futures' }).locator('tbody tr')).toHaveCount(4)
  expect((await (await request.get('/api/overview')).json()).state).toEqual(before)
  const saveResponse = page.waitForResponse(response => response.url().includes('/api/lab/save?'))
  await page.getByRole('button', { name: 'Save experiment', exact: true }).click()
  const response = await saveResponse; expect(response.ok()).toBe(true)
  const savedExperiment = (await response.json()).evaluation
  expect(savedExperiment.generation).toBe(before.generation)
  await expect(page.getByText(/Experiment saved to audit history/)).toBeVisible({ timeout: 30000 })
  expect((await (await request.get('/api/overview')).json()).state).toEqual(before)
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: 'Audit history', exact: true }).click()
  const opened = page.waitForRequest(request => request.url().endsWith('/api/decisions/'+savedExperiment.id))
  await page.locator('.audit-table tbody tr').filter({ hasText: 'experiment saved' })
    .filter({ has: page.getByRole('cell', { name: String(savedExperiment.generation), exact: true }) })
    .getByRole('button', { name: 'Open evaluation' }).click()
  await opened
  await expect(page.getByText(/hypothetical experiment/)).toBeVisible()
  await page.getByRole('button', { name: 'Return to current' }).click()
  await page.getByRole('navigation', { name: 'Decision intelligence' }).getByRole('button', { name: 'Model Evidence Center' }).click()
  await expect(page.getByRole('heading', { name: 'Did it improve the decision?' })).toBeVisible()
  await expect(page.getByText('EXPERIMENTAL', { exact: true })).toBeVisible()
  await expect(page.getByText(/Paired penalty benefit: ₹0/)).toBeVisible()
  const accepted = await request.post('/api/events', { data: { event_id: crypto.randomUUID(), business_id: 'demo', timestamp: new Date().toISOString(), type: 'RECEIVABLE_DELAYED', receivable_id: 'customer', expected_date: '2026-10-29' } })
  expect(accepted.status()).toBe(201)
  await expect.poll(async () => (await (await request.get('/api/overview')).json()).latest_decision?.evaluation.state_version).toBe(1)
  const current = (await (await request.get('/api/overview')).json()).latest_decision.evaluation
  expect(current.decision_evidence.primary_policy).toBe('obligation_rule')
  expect(current.scope).toBe('live')
  expect(errors).toEqual([])
})

test('V3 views are accessible and responsive with actual screenshots', async ({ page, request }) => {
  test.setTimeout(90000)
  await request.post('/api/decisions/evaluate', { data: { paths: 100, include_robustness: true } })
  await mkdir('../docs/v3/screenshots', { recursive: true })
  for (const route of ['overview', 'lab', 'stability', 'policies', 'model']) {
    await page.goto('/#'+route)
    await expect(page.locator('.financial-strip')).toBeVisible()
    if (route === 'model') await expect(page.getByRole('heading', { name: 'Did it improve the decision?' })).toBeVisible()
    for (const width of [1440, 768, 390]) {
      await page.setViewportSize({ width, height: 1000 })
      if (route === 'overview') await expect.poll(() => page.locator('.chart svg.recharts-surface').evaluate(svg => svg.getBoundingClientRect().right <= innerWidth)).toBe(true)
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
      const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
      expect(axe.violations.map(item => ({ id: item.id, nodes: item.nodes.map(node => ({ target: node.target, summary: node.failureSummary })) }))).toEqual([])
      await page.evaluate(() => { if (document.activeElement instanceof HTMLElement) document.activeElement.blur(); window.scrollTo(0, 0) })
      await expect.poll(() => page.evaluate(() => scrollY)).toBe(0)
      await page.screenshot({ path: `../docs/v3/screenshots/${route}-${width}.png`, fullPage: true })
    }
  }
})

test('model evidence loading and failure expose retry paths', async ({ page }) => {
  await page.route('**/api/model/evidence', async route => { await new Promise(resolve => setTimeout(resolve, 500)); await route.fulfill({ status: 503, json: { error: { message: 'Evidence temporarily unavailable' } } }) })
  await page.goto('/#model')
  await expect(page.getByRole('status').filter({ hasText: 'Loading the actual validation evidence' })).toBeVisible()
  await expect(page.getByRole('alert')).toContainText('Evidence temporarily unavailable')
  await page.unroute('**/api/model/evidence')
  await page.getByRole('button', { name: 'Retry model evidence' }).click()
  await expect(page.getByRole('heading', { name: 'Did it improve the decision?' })).toBeVisible()
})
