import { chromium, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'

const url = 'http://127.0.0.1:8080'
const executablePath = ['C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync)
const browser = await chromium.launch(executablePath ? { executablePath } : {})
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' })
const page = await context.newPage()
const errors = []
page.on('pageerror', error => errors.push(error.message))
const before = await (await page.request.get(url+'/api/overview')).json()
expect(before.latest_decision.evaluation.metadata.engine_version).toBe('counterfactual-v3')
const dir = '../docs/v3/screenshots/live'
mkdirSync(dir, { recursive: true })
const checks = []
for (const route of ['overview', 'lab', 'stability', 'policies', 'model']) {
  await page.goto(url+'/#'+route)
  await expect(page.locator('.financial-strip')).toBeVisible()
  if (route === 'overview') {
    await expect(page.getByText('COMPUTED RECOMMENDATION', { exact: true })).toBeVisible()
    await expect(page.getByLabel('Simulation horizon')).toHaveValue(String(before.latest_decision.evaluation.request.horizon_days))
    await expect(page.getByLabel('Simulation paths')).toHaveValue(String(before.latest_decision.evaluation.request.paths))
  }
  if (route === 'model') await expect(page.getByRole('heading', { name: 'Did it improve the decision?' })).toBeVisible()
  if (route === 'lab') {
    // Ephemeral calculations only: no event, save, reset or settings update.
    await page.getByLabel('Receipt delay · days', { exact: true }).fill('5')
    await page.getByLabel('Additional expense · ₹', { exact: true }).fill('10000.01')
    await page.getByRole('button', { name: 'Evaluate experiment', exact: true }).click()
    await expect(page.getByText('The primary recommendation changes.', { exact: true })).toBeVisible({ timeout: 30000 })
  }
  for (const width of [1440, 768, 390]) {
    await page.setViewportSize({ width, height: 1000 })
    if (route === 'overview') await expect.poll(() => page.locator('.chart svg.recharts-surface').evaluate(svg => svg.getBoundingClientRect().right <= innerWidth)).toBe(true)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
    expect(result.violations.map(item => ({ id: item.id, nodes: item.nodes.map(node => ({ target: node.target, summary: node.failureSummary })) }))).toEqual([])
    await page.evaluate(() => { if (document.activeElement instanceof HTMLElement) document.activeElement.blur(); window.scrollTo(0, 0) })
    await expect.poll(() => page.evaluate(() => scrollY)).toBe(0)
    const png = await page.screenshot({ path: `${dir}/${route}-${width}.png`, fullPage: true })
    expect(png.readUInt32BE(16)).toBe(width)
    checks.push({ route, width, axeViolations: 0, documentOverflow: false })
  }
}
const after = await (await page.request.get(url+'/api/overview')).json()
expect(after.state).toEqual(before.state)
expect(after.latest_decision.evaluation.id).toBe(before.latest_decision.evaluation.id)
expect(errors).toEqual([])
writeFileSync('../docs/v3/live-browser.json', JSON.stringify({ url, checks, errors, financialStateUnchanged: true, latestDecisionUnchanged: true, request: after.latest_decision.evaluation.request }, null, 2))
await browser.close()
console.log('PASS: V3 live browser, ephemeral lab, five views at three widths, axe, exact screenshot sizes, no page errors; ledger and live decision unchanged.')
