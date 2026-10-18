import { chromium, expect } from '@playwright/test'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
const url = process.env.UNDO_PREVIEW_URL ?? 'http://127.0.0.1:8080'
const executablePath = ['C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync)
const browser = await chromium.launch(executablePath ? { executablePath } : {})
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, reducedMotion: 'reduce' })
const errors = []
page.on('pageerror', error => errors.push(error.message))
const before = await (await page.request.get(`${url}/api/overview`)).json()
const currency = paise => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: paise % 100 === 0 ? 0 : 2 }).format(paise/100)
const dir = '../docs/audit/screenshots'
mkdirSync(dir, { recursive: true })
await page.goto(url)
await expect(page.getByRole('button', { name: 'Evaluate payment', exact: true })).toBeVisible()
await expect(page.locator('.financial-strip')).toContainText('₹1,00,000')
await page.screenshot({ path: `${dir}/live-before.png`, fullPage: true })
// Evaluation appends a decision/audit record; it never changes financial state.
if (process.env.UNDO_AUDIT_READ_ONLY !== '1') await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
await expect(page.getByText('COMPUTED RECOMMENDATION', { exact: true })).toBeVisible()
const after = await (await page.request.get(`${url}/api/overview`)).json()
expect(after.state).toEqual(before.state)
const decision = after.latest_decision.evaluation
const chosen = decision.actions.find(a => a.action.id === decision.recommendation)
await expect(page.locator('.recommendation-panel')).toContainText(chosen.action.label)
const table = page.getByRole('table', { name: 'All payment alternatives evaluated against the same simulated futures' })
for (const result of decision.actions.filter(action => action.metrics)) {
  await expect(table.getByRole('row').filter({ hasText: result.action.label })).toContainText(currency(result.metrics.expected_penalty_paise))
}
for (const nav of ['Decisions', 'Cash flow', 'Event stream', 'Audit history', 'Overview']) {
  await page.getByRole('button', { name: nav, exact: true }).click()
  await expect(page.getByRole('button', { name: nav, exact: true })).toHaveAttribute('aria-current', 'page')
}
await expect(page.getByRole('heading', { name: 'See the cash flow.', exact: true })).toBeVisible()
await page.screenshot({ path: `${dir}/live-desktop.png`, fullPage: true })
await page.setViewportSize({ width: 390, height: 844 })
await expect.poll(() => page.locator('.chart svg.recharts-surface').evaluate(svg => svg.getBoundingClientRect().right <= innerWidth)).toBe(true)
const mobileImage = await page.screenshot({ path: `${dir}/live-mobile.png`, fullPage: true })
expect(mobileImage.readUInt32BE(16)).toBe(390)
const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
expect(overflow).toBe(false)
expect(errors).toEqual([])
writeFileSync(`../docs/audit/live-browser${process.env.UNDO_AUDIT_LABEL ? '-'+process.env.UNDO_AUDIT_LABEL : ''}.json`, JSON.stringify({ url, financialStateUnchanged: true, generation: after.state.generation, version: after.state.version, engine_version: decision.metadata.engine_version ?? 'legacy-unversioned', recommendation: decision.recommendation, metrics: chosen.metrics, pageErrors: errors, mobileOverflow: overflow }, null, 2))
await browser.close()
console.log('PASS: live evaluation, five navigation views, API recommendation match, ledger preserved, desktop/mobile screenshots, no page errors or overflow.')
