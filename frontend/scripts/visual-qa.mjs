import { chromium } from '@playwright/test'
import { existsSync, mkdirSync } from 'node:fs'
const installed = ['C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync)
const browser = await chromium.launch(installed ? { executablePath: installed } : {})
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, reducedMotion: 'reduce' })
const errors = []
page.on('pageerror', error => errors.push(error.message))
mkdirSync('../docs/screenshots', { recursive: true })
await page.goto(process.env.UNDO_PREVIEW_URL ?? 'http://127.0.0.1:5173/')
await page.getByRole('button', { name: 'Evaluate payment', exact: true }).waitFor()
await page.screenshot({ path: '../docs/screenshots/desktop-initial.png', fullPage: true })
await page.getByRole('button', { name: 'Evaluate payment', exact: true }).click()
await page.getByText('COMPUTED RECOMMENDATION', { exact: true }).waitFor()
await page.getByRole('heading', { name: 'See the cash flow.', exact: true }).waitFor()
await page.screenshot({ path: '../docs/screenshots/desktop-evaluated.png', fullPage: true })
await page.setViewportSize({ width: 390, height: 844 })
await page.screenshot({ path: '../docs/screenshots/mobile-evaluated.png', fullPage: true })
const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
console.log(JSON.stringify({ pageErrors: errors, mobileOverflow: overflow, title: await page.title() }))
await browser.close()
if (errors.length || overflow) process.exitCode = 1
