import { defineConfig } from '@playwright/test'
import { resolve } from 'node:path'

export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, timeout: 60000,
  use: { baseURL: 'http://127.0.0.1:5173', viewport: { width: 1440, height: 1024 }, trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  webServer: [
    { command: '..\\.venv\\Scripts\\python.exe -m uvicorn revivegraph.main:create_app --factory --app-dir ../backend --host 127.0.0.1 --port 8000', url: 'http://127.0.0.1:8000/api/v1/health', reuseExistingServer: false, env: { REVIVEGRAPH_DB: resolve('../data', `e2e-${Date.now()}.sqlite3`) } },
    { command: 'npm run dev', url: 'http://127.0.0.1:5173', reuseExistingServer: false },
  ],
})
