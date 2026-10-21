import { test, expect } from '@playwright/test'
import { mkdir, readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

test('reference dashboard, real comparisons/activity, reports, search and all 390px workspaces', async ({ page, request }) => {
  test.setTimeout(120000)
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  const headers = () => ({ 'X-Actor-ID': 'visual-check-operator', 'Idempotency-Key': crypto.randomUUID() })
  const state = await (await request.get('/api/v1/state')).json()
  if (!state.counts.computers) {
    const reg = await (await request.post('/api/v1/fixture-registrations', { headers: headers(), data: {} })).json()
    const batch = await (await request.post('/api/v1/imports/preview', { headers: headers(), multipart: {
      registration_id: reg.id,
      computers_file: { name: 'computers.csv', mimeType: 'text/csv', buffer: await readFile(resolve('../datasets/synthetic-v1/computers.csv')) },
      components_file: { name: 'components.csv', mimeType: 'text/csv', buffer: await readFile(resolve('../datasets/synthetic-v1/components.csv')) },
    } })).json()
    expect((await request.post(`/api/v1/imports/${batch.batch_id}/commit`, { headers: headers(), data: { preview_hash: batch.preview_hash, expected_revision: batch.expected_revision } })).ok()).toBe(true)
  }
  let plans = (await (await request.get('/api/v1/plans')).json()).items
  if (!plans.length) {
    const response = await request.post('/api/v1/plans', { headers: headers(), data: { context_id: `reference-${crypto.randomUUID()}`, budget_paise: 250000, time_minutes: 330 } })
    expect(response.ok()).toBe(true)
    const original = await response.json()
    const donor = original.result.operations.find((o: { operation: string; target_asset_id?: string; asset_id: string }) => o.operation.startsWith('remove_') && o.target_asset_id && o.target_asset_id !== o.asset_id)
    const revised = await request.post(`/api/v1/plans/${original.id}/failures`, { headers: headers(), data: { component_id: donor.component_id } })
    expect(revised.ok()).toBe(true)
    plans = (await (await request.get('/api/v1/plans')).json()).items
  }
  await mkdir(resolve('../docs/implementation-previews'), { recursive: true })
  await page.setViewportSize({ width: 1672, height: 941 })
  await page.goto('/#dashboard')
  await expect(page.getByRole('heading', { name: 'Recovery overview', exact: true })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Actual recovery plan comparisons' }).getByText('Greedy baseline', { exact: true }).first()).toBeVisible()
  await expect(page.locator('.overview-metric')).toHaveCount(5)
  await expect(page.locator('.overview-machine')).toHaveCount(12)
  const activity = await (await request.get('/api/v1/audit-events?limit=8')).json()
  expect(activity.total).toBeGreaterThan(0)
  await expect(page.getByRole('region', { name: 'Real system activity' }).getByText(activity.items[0].action.replaceAll('_', ' '), { exact: true }).first()).toBeVisible()
  await page.screenshot({ path: resolve('../docs/implementation-previews/reference-dashboard-desktop.png') })

  await page.getByLabel('Search fleet inventory').fill('RG-RAM-07')
  await page.getByRole('button', { name: 'Search inventory', exact: true }).click()
  await expect(page.getByRole('tab', { name: 'Components · 31' })).toHaveAttribute('aria-selected', 'true')
  await expect(page.getByRole('button', { name: 'RG-RAM-07', exact: true })).toBeVisible()
  await page.getByLabel('Search asset or part ID').fill('')
  await page.getByRole('tab', { name: 'Computers · 12' }).click()
  await page.getByRole('button', { name: 'RG-PC-04', exact: true }).click()
  await page.screenshot({ path: resolve('../docs/implementation-previews/reference-inventory-desktop.png') })
  await page.getByRole('link', { name: 'Compatibility Graph', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Interactive deterministic compatibility graph' })).toBeVisible()
  await page.screenshot({ path: resolve('../docs/implementation-previews/reference-compatibility-desktop.png') })
  await page.getByRole('link', { name: 'Recovery Optimizer', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Computed recovery plan' })).toBeVisible()
  await page.screenshot({ path: resolve('../docs/implementation-previews/reference-optimizer-desktop.png') })
  await page.getByRole('link', { name: 'Live Recovery Simulation', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Computed recovery plan' })).toBeVisible()
  await page.screenshot({ path: resolve('../docs/implementation-previews/reference-simulation-desktop.png') })
  await page.getByRole('link', { name: 'Reports', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Recovery record', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Export audit JSON', exact: true })).toBeEnabled()
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export audit JSON', exact: true }).click()
  const exported = JSON.parse(await readFile((await (await downloadPromise).path())!, 'utf-8'))
  expect(exported.plan.id).toBe(plans[0].id)
  expect(exported.mode).toBe('simulation')
  expect(exported.physical_verified_repairs).toBe(0)
  await page.screenshot({ path: resolve('../docs/implementation-previews/reference-reports-desktop.png') })
  const auditType = page.getByLabel('Audit event type')
  await expect(auditType.locator('option')).not.toHaveCount(1)
  const option = (await auditType.locator('option').all()).at(1)!
  await auditType.selectOption((await option.getAttribute('value'))!)
  await expect(page.locator('.reports-activity-list article')).not.toHaveCount(0)
  await auditType.selectOption('')

  await page.setViewportSize({ width: 390, height: 844 })
  for (const [route, title] of [['dashboard', 'Recovery overview'], ['inventory', 'Computer Inventory'], ['compatibility', 'Compatibility Graph'], ['optimizer', 'Recovery Optimizer'], ['simulation', 'Live Recovery Simulation'], ['reports', 'Reports']]) {
    await page.goto(`/#${route}`)
    await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible()
    await expect(page.locator('.loading')).toHaveCount(0)
    if (route === 'dashboard') await expect(page.getByRole('region', { name: 'Actual recovery plan comparisons' }).getByText('Greedy baseline', { exact: true }).first()).toBeVisible()
    if (route === 'reports') await expect(page.getByRole('heading', { name: 'Recovery record', exact: true })).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${route} fits 390px`).toBe(true)
    await expect.poll(() => page.locator('.sidebar').evaluate(el => el.getBoundingClientRect().right)).toBeLessThanOrEqual(0)
    await page.screenshot({ path: resolve(`../docs/implementation-previews/reference-${route}-mobile.png`), fullPage: route === 'dashboard' })
  }
  await page.getByRole('button', { name: 'Open navigation' }).click()
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Recovery overview', exact: true })).toBeVisible()
  expect(errors).toEqual([])
})
