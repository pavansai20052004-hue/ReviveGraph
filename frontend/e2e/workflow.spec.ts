import { test, expect } from '@playwright/test'
import { mkdir, readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

test('guided recovery, current-plan navigation, ready queue and saved evidence survive reload', async ({ page, request }) => {
  test.setTimeout(180000)
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  const headers = () => ({ 'X-Actor-ID': 'workflow-browser-test', 'Idempotency-Key': crypto.randomUUID() })
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
  // A separate context makes this case independent of existing browser runs.
  const originalResponse = await request.post('/api/v1/plans', { headers: headers(), data: { context_id: `workflow-${crypto.randomUUID()}`, budget_paise: 250000, time_minutes: 330 } })
  expect(originalResponse.ok()).toBe(true)
  const original = await originalResponse.json()
  const donor = original.result.operations.find((op: { operation: string; target_asset_id?: string; asset_id: string }) => op.operation.startsWith('remove_') && op.target_asset_id && op.target_asset_id !== op.asset_id)
  const failureResponse = await request.post(`/api/v1/plans/${original.id}/failures`, { headers: headers(), data: { component_id: donor.component_id } })
  expect(failureResponse.ok()).toBe(true)
  const revised = await failureResponse.json()
  await page.setViewportSize({ width: 1672, height: 941 })
  await page.goto('/#dashboard')
  // A stale saved selection must not override the dashboard's current-plan CTA.
  await page.evaluate(id => sessionStorage.setItem('revivegraph-plan', id), original.id)
  await page.getByRole('region', { name: 'Recovery next action' }).getByRole('button', { name: 'Review revised plan', exact: true }).click()
  await expect(page.getByLabel('Persisted plan revision')).toHaveValue(revised.id)
  const comparison = page.getByRole('region', { name: 'Before and after comparison' })
  const changed = revised.result.allocations.filter((after: { target_asset_id: string; ram_component_ids: string[]; storage_component_id: string }) => {
    const before = original.result.allocations.find((a: { target_asset_id: string }) => a.target_asset_id === after.target_asset_id)
    return !before || JSON.stringify([...before.ram_component_ids, before.storage_component_id].sort()) !== JSON.stringify([...after.ram_component_ids, after.storage_component_id].sort())
  }).length
  expect(changed).toBeGreaterThan(0)
  await expect(comparison.locator('.allocation-diff li')).toHaveCount(changed)
  await comparison.getByRole('button', { name: /Show all \d+ allocations/ }).click()
  await expect(comparison.locator('.allocation-diff li')).toHaveCount(revised.result.allocations.length)
  await comparison.getByRole('button', { name: 'Show changed allocations only' }).click()
  await mkdir(resolve('../docs/implementation-previews'), { recursive: true })
  await comparison.screenshot({ path: resolve('../docs/implementation-previews/effective-allocation-changes.png') })
  await page.getByRole('button', { name: 'Review approval', exact: true }).click()
  await page.getByRole('checkbox', { name: 'I reviewed this exact revision and authorize simulated work only.' }).check()
  await page.getByRole('button', { name: 'Approve exact simulation plan' }).click()
  await page.getByRole('button', { name: 'Create simulation work orders' }).click()
  const queue = page.getByRole('region', { name: 'Simulation work orders' })
  await expect(queue.getByTestId('work-order')).toHaveCount(revised.result.allocations.length)
  await queue.getByLabel('Work order search').fill('RG-PC-01')
  await expect(queue.getByTestId('work-order')).toHaveCount(1)
  await queue.getByRole('button', { name: 'Show next available task' }).click()
  await expect(queue.getByLabel('Work order search')).toHaveValue('')
  const focused = queue.locator('.focused-work-step')
  await expect(focused).toHaveCount(1)
  await expect(focused).toBeFocused()
  const stepId = await focused.getAttribute('data-step-id')
  expect(stepId).toBeTruthy()
  const order = focused.locator('xpath=..')
  const orderId = await order.getAttribute('id')
  for (const checkbox of await focused.getByRole('checkbox').all()) await checkbox.check()
  const evidence = `synthetic:workflow-browser-${stepId}`
  await focused.getByRole('textbox').fill(evidence)
  await focused.getByRole('button', { name: /^Record / }).click()
  await expect(focused.getByText('Saved simulation record', { exact: false })).toBeVisible()
  await page.reload()
  await expect(queue).toBeVisible()
  const savedOrder = page.locator(`[id="${orderId}"]`)
  await savedOrder.locator('summary').click()
  const saved = savedOrder.locator(`[data-step-id="${stepId}"]`)
  await expect(saved.getByRole('textbox')).toHaveValue(evidence)
  await expect(saved.getByRole('textbox')).toBeDisabled()
  for (const checkbox of await saved.getByRole('checkbox').all()) {
    await expect(checkbox).toBeChecked()
    await expect(checkbox).toBeDisabled()
  }
  await expect(saved.getByText('Saved simulation record', { exact: false })).toBeVisible()
  // Work takes visual priority over a second failure once execution starts.
  await expect(page.getByRole('button', { name: 'Inject failure and replan' })).not.toBeVisible()
  await queue.getByTestId('work-order').evaluateAll(elements => elements.forEach(el => { (el as HTMLDetailsElement).open = false }))
  await page.evaluate(() => scrollTo(0, 0))
  await page.screenshot({ path: resolve('../docs/implementation-previews/effective-simulation-desktop.png') })
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Continue simulated work', exact: true })).toBeVisible()
  await page.screenshot({ path: resolve('../docs/implementation-previews/effective-dashboard-desktop.png') })
  await page.setViewportSize({ width: 390, height: 844 })
  await expect.poll(() => page.locator('.sidebar').evaluate(el => el.getBoundingClientRect().right)).toBeLessThanOrEqual(0)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.screenshot({ path: resolve('../docs/implementation-previews/effective-dashboard-mobile.png') })
  await page.getByRole('button', { name: 'Continue simulated work', exact: true }).click()
  await expect(queue).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.evaluate(() => scrollTo(0, 0))
  const queueTop = await queue.evaluate(el => el.getBoundingClientRect().top)
  const controlsTop = await page.locator('.constraints-panel').evaluate(el => el.getBoundingClientRect().top)
  expect(queueTop).toBeLessThan(controlsTop)
  await page.screenshot({ path: resolve('../docs/implementation-previews/effective-simulation-mobile.png') })
  expect(errors).toEqual([])
})
