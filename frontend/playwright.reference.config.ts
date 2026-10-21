import { defineConfig } from '@playwright/test'
import { resolve } from 'node:path'
import base from './playwright.config'

// The user's normal local application can stay open on 8000/5173.
export default defineConfig({
  ...base,
  use: { ...base.use, baseURL: 'http://127.0.0.1:15173' },
  webServer: [
    { command: '..\\.venv\\Scripts\\python.exe -m uvicorn revivegraph.main:create_app --factory --app-dir ../backend --host 127.0.0.1 --port 18100', url: 'http://127.0.0.1:18100/api/v1/health', reuseExistingServer: false, env: { REVIVEGRAPH_DB: resolve('../data', `reference-e2e-${Date.now()}.sqlite3`) } },
    { command: 'npm run dev -- --port 15173', url: 'http://127.0.0.1:15173', reuseExistingServer: false, env: { REVIVEGRAPH_API_TARGET: 'http://127.0.0.1:18100' } },
  ],
})
