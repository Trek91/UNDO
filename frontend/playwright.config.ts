import { defineConfig } from '@playwright/test'
import { existsSync } from 'node:fs'
const installed = ['C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'].find(existsSync)
export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, timeout: 30000,
  reporter: [['list'], ['json', { outputFile: '../docs/e2e-results.json' }]],
  use: { baseURL: 'http://127.0.0.1:5174', viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce',
    launchOptions: installed ? { executablePath: installed } : {}, trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  webServer: [
    { command: 'node scripts/start-test-backend.mjs', url: 'http://127.0.0.1:8001/api/health', timeout: 30000 },
    { command: 'npm run dev -- --port 5174', url: 'http://127.0.0.1:5174', env: { UNDO_API_URL: 'http://127.0.0.1:8001' }, timeout: 30000 },
  ],
})
