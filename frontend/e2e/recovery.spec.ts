import { test, expect } from '@playwright/test'
import { mkdir, readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

test('computed recovery, actual donor failure, exact approval, simulated work and audit export', async ({ page, request }) => {
  test.setTimeout(180000)
  const pageErrors: string[] = []
  page.on('pageerror', error => pageErrors.push(error.message))
  await page.goto('/')
  const initial = await (await request.get('/api/v1/state')).json()
  if (!initial.counts.computers) {
    await page.getByRole('button', { name: 'Import CSV', exact: true }).click()
    const dialog = page.getByRole('dialog')
    await dialog.getByRole('button', { name: 'Register synthetic-v1' }).click()
    await expect(dialog.getByText('Registered · v1')).toBeVisible()
    await dialog.getByRole('button', { name: 'Use bundled CSV pair' }).click()
    await dialog.getByRole('button', { name: 'Preview both files' }).click()
    await expect(dialog.getByText('Validation passed', { exact: true })).toBeVisible()
    await dialog.getByRole('button', { name: 'Commit batch', exact: true }).click()
    await expect(dialog.getByText('Batch committed', { exact: false })).toBeVisible()
    await dialog.getByRole('button', { name: 'View imported inventory' }).click()
  }
  await page.getByRole('link', { name: 'Compatibility Graph', exact: true }).click()
  await page.getByLabel('Target computer', { exact: true }).selectOption('RG-PC-06')
  const graph = page.getByRole('region', { name: 'Interactive deterministic compatibility graph', exact: true })
  await expect(graph.locator('.react-flow__node[data-id="RG-RAM-01"]')).toBeVisible()
  await graph.locator('.react-flow__node[data-id="RG-RAM-01"]').click()
  await expect(page.getByRole('region', { name: 'Selected compatibility decision' }).getByRole('heading', { name: 'RG-RAM-01', exact: true })).toBeVisible()
  await graph.getByRole('button', { name: /zoom in/i }).click()
  await graph.getByRole('button', { name: /fit view/i }).click()
  await expect(page.getByRole('region', { name: 'Compatibility decision table' })).toBeVisible()
  await page.getByRole('link', { name: 'Recovery Optimizer', exact: true }).click()
  await expect(page.getByLabel('Repair budget (INR)')).toBeVisible()
  await page.getByRole('button', { name: 'Calculate plan', exact: true }).click()
  const result = page.getByRole('region', { name: 'Computed recovery plan' })
  await expect(result.getByRole('heading', { name: 'Fleet recovery result' })).toBeVisible({ timeout: 90000 })
  await expect(result.getByText('OPTIMAL', { exact: true })).toBeVisible()
  const originalId = await page.getByLabel('Persisted plan revision').inputValue()
  const original = await (await request.get(`/api/v1/plans/${originalId}`)).json()
  expect(original.result.totals.usable_final).toBeGreaterThan(0)
  await mkdir(resolve('../docs/implementation-previews'), { recursive: true })
  // Fixed navigation must be captured from the actual top of the viewport.
  // Otherwise a full-page screenshot can composite fixed layers at the old
  // scroll position left by the graph interaction.
  await page.evaluate(() => scrollTo(0, 0))
  await expect.poll(() => page.evaluate(() => scrollY)).toBe(0)
  await expect.poll(() => page.locator('.sidebar').evaluate(el => el.getBoundingClientRect().top)).toBe(0)
  await expect.poll(() => page.locator('.brand').evaluate(el => el.getBoundingClientRect().top)).toBe(20)
  expect(await page.locator('.skip-link').evaluate(el => el.getBoundingClientRect().bottom)).toBeLessThan(0)
  await page.screenshot({ path: resolve('../docs/implementation-previews/optimizer-computed-desktop.png'), fullPage: false })
  await page.getByRole('link', { name: 'Live Recovery Simulation', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Inject failure and replan' })).toBeEnabled()
  const failureId = await page.getByLabel('Failure component').inputValue()
  expect(original.result.allocations.some((a: { ram_component_ids: string[]; storage_component_id: string }) => [...a.ram_component_ids, a.storage_component_id].includes(failureId))).toBe(true)
  await page.getByRole('button', { name: 'Inject failure and replan' }).click()
  await expect(page.getByRole('region', { name: 'Before and after comparison' })).toBeVisible({ timeout: 90000 })
  const revisedId = await page.getByLabel('Persisted plan revision').inputValue()
  expect(revisedId).not.toBe(originalId)
  const revised = await (await request.get(`/api/v1/plans/${revisedId}`)).json()
  expect(revised.result.allocations.some((a: { ram_component_ids: string[]; storage_component_id: string }) => [...a.ram_component_ids, a.storage_component_id].includes(failureId))).toBe(false)
  // The preserved original is visibly stale and cannot authorize new work.
  await page.getByLabel('Persisted plan revision').selectOption(originalId)
  await expect(page.getByRole('button', { name: 'Review approval', exact: true })).toBeDisabled()
  await page.getByLabel('Persisted plan revision').selectOption(revisedId)
  await page.getByRole('button', { name: 'Review approval', exact: true }).click()
  await page.getByRole('checkbox', { name: 'I reviewed this exact revision and authorize simulated work only.' }).check()
  await page.getByLabel('Persisted plan revision').selectOption(originalId)
  await expect(page.getByRole('button', { name: 'Review approval', exact: true })).toBeDisabled()
  await page.getByLabel('Persisted plan revision').selectOption(revisedId)
  await page.getByRole('button', { name: 'Review approval', exact: true }).click()
  await expect(page.getByRole('checkbox', { name: 'I reviewed this exact revision and authorize simulated work only.' })).not.toBeChecked()
  await page.getByRole('checkbox', { name: 'I reviewed this exact revision and authorize simulated work only.' }).check()
  await page.getByRole('button', { name: 'Approve exact simulation plan' }).click()
  await expect(page.getByRole('button', { name: 'Create simulation work orders' })).toBeEnabled()
  await page.getByRole('button', { name: 'Create simulation work orders' }).click()
  const orders = page.getByRole('region', { name: 'Simulation work orders' })
  await expect(orders).toBeVisible()

  // Execute browser controls in dependency order; each checkbox and authored
  // evidence reference is supplied explicitly. No physical measurements are claimed.
  let verified = false
  for (let iteration = 0; iteration < 120 && !verified; iteration++) {
    const current = await (await request.get(`/api/v1/plans/${revisedId}`)).json()
    const completed = new Set<string>(current.work_orders.flatMap((o: { steps: { id: string; status: string }[] }) => o.steps.filter(s => ['done', 'completed'].includes(s.status)).map(s => s.id)))
    let acted = false
    for (const order of current.work_orders) {
      const work = orders.getByTestId('work-order').filter({ has: page.locator('summary', { hasText: order.target_asset_id }) })
      const summary = work.locator('summary').first()
      if (!(await work.evaluate(el => (el as HTMLDetailsElement).open))) await summary.click()
      const pending = order.steps.find((s: { id: string; operation: string; status: string; depends_on: string[] }) => s.operation !== 'verify_target' && !completed.has(s.id) && s.depends_on.every(id => completed.has(id)))
      if (pending) {
        const step = work.locator('.order-step').filter({ has: page.getByRole('heading', { name: `${pending.operation.replaceAll('_', ' ')} ${pending.component_id ?? ''}`.trim(), exact: true }) }).first()
        for (const checkbox of await step.getByRole('checkbox').all()) await checkbox.check()
        await step.getByRole('textbox').fill(`synthetic:e2e-${pending.id}`)
        await step.getByRole('button', { name: `Record ${pending.operation.replaceAll('_', ' ')}`, exact: true }).click()
        await expect(page.getByText('Saving simulated work progress…', { exact: true })).toHaveCount(0)
        await expect(step.getByRole('button', { name: `Record ${pending.operation.replaceAll('_', ' ')}`, exact: true })).toBeDisabled()
        acted = true; break
      }
      if (!order.verification && order.steps.filter((s: { operation: string }) => s.operation !== 'verify_target').every((s: { id: string }) => completed.has(s.id))) {
        const verification = work.locator('.order-step').filter({ has: page.getByRole('heading', { name: 'Simulated verification', exact: true }) })
        for (const checkbox of await verification.getByRole('checkbox').all()) await checkbox.check()
        await verification.getByRole('textbox').fill(`synthetic:e2e-verification-${order.id}`)
        await verification.getByRole('button', { name: 'Record simulated verification', exact: true }).click()
        await expect(work.getByText('Simulated verification: pass', { exact: true })).toBeVisible()
        verified = true; acted = true; break
      }
    }
    expect(acted, 'A prerequisite-ready work step or verification must be available').toBe(true)
  }
  expect(verified).toBe(true)
  const finalState = await (await request.get('/api/v1/state')).json()
  expect(finalState.recovery.simulated_passes).toBeGreaterThan(0)
  expect(finalState.recovery.physical_passes).toBe(0)
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export audit report' }).click()
  const download = await downloadPromise
  const reportPath = await download.path()
  const report = JSON.parse(await readFile(reportPath!, 'utf-8'))
  expect(JSON.stringify(report)).toContain(revisedId)
  expect(JSON.stringify(report)).toContain('synthetic:e2e-verification')
  const verifiedOrder = orders.getByTestId('work-order').filter({ has: page.getByText('Simulated verification: pass', { exact: true }) }).first()
  await verifiedOrder.screenshot({ path: resolve('../docs/implementation-previews/simulation-verification-checklist.png') })
  await orders.getByTestId('work-order').evaluateAll(elements => elements.forEach(el => { (el as HTMLDetailsElement).open = false }))
  await page.evaluate(() => scrollTo(0, 0))
  await page.screenshot({ path: resolve('../docs/implementation-previews/simulation-verified-desktop.png'), fullPage: true })
  await page.setViewportSize({ width: 390, height: 844 })
  // Resizing from desktop animates the existing navigation drawer out over
  // 150ms. Capture only once it has fully cleared the content, rather than
  // recording a mid-transition drawer covering the first letters.
  await expect.poll(() => page.locator('.sidebar').evaluate(el => el.getBoundingClientRect().right)).toBeLessThanOrEqual(0)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.evaluate(() => scrollTo(0, 0))
  // Check actual text geometry, not only document overflow: local scroll
  // offsets must never crop the banner, heading or plan controls on mobile.
  const mobileGeometry = await page.evaluate(() => {
    const selectors = ['.mode-strip strong', '.header-title h1', '.recovery-workspace > .filter-bar', '.constraints-panel']
    return { scrollX, elements: selectors.map(selector => {
      const element = document.querySelector(selector)!
      const bounds = element.getBoundingClientRect()
      return { selector, left: bounds.left, right: bounds.right, scrollLeft: element.scrollLeft }
    }) }
  })
  expect(mobileGeometry.scrollX).toBe(0)
  for (const element of mobileGeometry.elements) {
    expect(element.left, `${element.selector} starts within mobile padding`).toBeGreaterThanOrEqual(16)
    expect(element.right, `${element.selector} ends within mobile padding`).toBeLessThanOrEqual(374)
    expect(element.scrollLeft, `${element.selector} is not scrolled horizontally`).toBe(0)
  }
  await page.screenshot({ path: resolve('../docs/implementation-previews/simulation-mobile-viewport.png'), fullPage: false })
  await page.screenshot({ path: resolve('../docs/implementation-previews/simulation-verified-mobile.png'), fullPage: true })
  expect(pageErrors).toEqual([])
})
