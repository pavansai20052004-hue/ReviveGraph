import { useCallback, useEffect, useRef, useState } from 'react'
import { api, jsonMutation, publicDemo } from '../api'
import type { Component, Plan, WorkOrder, WorkStep } from '../types'
import { Button } from './ui/button'
import { Badge, EmptyState, ErrorNotice, Loading, Panel } from './ui/primitives'
import { Icon } from './ui/Icon'
import './recovery-flow.css'
import { ContinuationAccounting, ReconciliationPanel } from './ReconciliationPanel'

export const money = (paise: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(paise / 100)
const ids = (allocation: Plan['result']['allocations'][number]) => [...allocation.ram_component_ids, allocation.storage_component_id]
const human = (value: string) => value.replaceAll('_', ' ')
const isDone = (step: WorkStep) => step.status === 'done' || step.status === 'completed'
type RecordedStep = WorkStep & { checks?: string[]; actor?: string; completed_at?: string; recorded_at?: string }
type QueueTask = { order: WorkOrder; step: WorkStep }

function readyWork(orders: WorkOrder[]): QueueTask[] {
  const completed = new Set(orders.flatMap(order => order.steps.filter(isDone).map(step => step.id)))
  return [...orders].sort((a, b) => a.target_asset_id.localeCompare(b.target_asset_id)).flatMap(order =>
    order.status === 'paused' ? [] : order.steps.filter(step => !isDone(step) && step.status === 'pending'
      && (step.operation !== 'verify_target' || !order.verification)
      && step.depends_on.every(id => completed.has(id))).map(step => ({ order, step })))
}
const signed = (value: number, suffix = '') => `${value > 0 ? '+' : value < 0 ? '−' : ''}${Math.abs(value)}${suffix}`


export function RecoveryWorkspace({ simulation, components, inventoryRevision, onChanged }: { simulation: boolean; components: Component[]; inventoryRevision: number; onChanged: () => Promise<void> }) {
  const [plans, setPlans] = useState<Plan[]>([])
  const [selected, setSelected] = useState(() => sessionStorage.getItem('revivegraph-plan') ?? '')
  const [plan, setPlan] = useState<Plan | null>(null)
  const [parent, setParent] = useState<Plan | null>(null)
  const [execution, setExecution] = useState<'local' | 'nodus'>('local')
  const [orchestration, setOrchestration] = useState<'local' | 'render'>('local')
  const [budget, setBudget] = useState('2500')
  const [minutes, setMinutes] = useState('330')
  const [contextId, setContextId] = useState('demo')
  const [failure, setFailure] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [review, setReview] = useState(false)
  const [reviewCheck, setReviewCheck] = useState(false)
  const [showAllChanges, setShowAllChanges] = useState(false)
  const [orderFilter, setOrderFilter] = useState('All')
  const [orderSearch, setOrderSearch] = useState('')
  const [focusTask, setFocusTask] = useState<QueueTask | null>(null)
  const requestKeys = useRef(new Map<string, string>())
  function post<T>(path: string, body: unknown): Promise<T> {
    const fingerprint = `${inventoryRevision}:${path === '/plans' ? plan?.scenario_id ?? 'initial' : ''}:${path}:${JSON.stringify(body)}`
    let key = requestKeys.current.get(fingerprint)
    if (!key) { key = crypto.randomUUID(); requestKeys.current.set(fingerprint, key) }
    return api<T>(path, { ...jsonMutation(body, key), signal: AbortSignal.timeout(orchestration === 'render' || plan?.execution?.workflow?.orchestrator === 'render-workflows' ? 1260000 : 420000) })
  }

  const load = useCallback(async (selection?: string) => {
    const response = await api<{ items: Plan[] }>('/plans')
    response.items.sort((a, b) => (a.created_at ?? '').localeCompare(b.created_at ?? ''))
    setPlans(response.items)
    const next = selection ?? selected ?? ''
    const chosen = response.items.some(p => p.id === next) ? next : response.items[response.items.length - 1]?.id
    if (!chosen) { setPlan(null); setParent(null); return }
    const current = await api<Plan>(`/plans/${chosen}`)
    setPlan(current); setSelected(chosen); sessionStorage.setItem('revivegraph-plan', chosen)
    setParent(current.parent_plan_id ? await api<Plan>(`/plans/${current.parent_plan_id}`) : null)
  }, [selected])
  useEffect(() => { let active = true; setBusy('Loading persisted plans…'); load().catch(e => active && setError((e as Error).message)).finally(() => active && setBusy('')); return () => { active = false } }, []) // Initial restore only; explicit actions refresh the chosen revision.
  useEffect(() => { setReview(false); setReviewCheck(false); setShowAllChanges(false); setOrderFilter('All'); setOrderSearch(''); setFocusTask(null) }, [plan?.id, plan?.input_hash])
  useEffect(() => {
    if (!focusTask) return
    const order = document.getElementById(`work-order-${focusTask.order.id}`) as HTMLDetailsElement | null
    if (order) order.open = true
    const step = document.getElementById(`work-step-${focusTask.step.id}`)
    if (step) { step.scrollIntoView({ behavior: 'smooth', block: 'center' }); step.focus({ preventScroll: true }) }
  }, [focusTask])

  const run = async (label: string, action: () => Promise<unknown>) => {
    if (busy) return
    setError(''); setBusy(label)
    try { await action() } catch (e) { setError((e as Error).message); await load().catch(() => {}) } finally { setBusy('') }
  }
  const partById = new Map((plan?.snapshot?.components ?? components).map(p => [p.component_id, p]))
  const transfers = plan?.result.allocations.flatMap(a => ids(a).filter(id => partById.get(id)?.location_asset_id !== a.target_asset_id)) ?? []
  const failureCandidates = [...new Set(transfers)].sort((a, b) => Number(!partById.get(a)?.location_asset_id) - Number(!partById.get(b)?.location_asset_id) || a.localeCompare(b))
  const chosenFailure = failureCandidates.includes(failure) ? failure : failureCandidates[0] ?? ''
  const stale = plan && (plan.status === 'stale' || plan.inventory_revision !== inventoryRevision)
  const canApprove = !!plan && !stale && plan.status === 'validated'
  const baseline = plan?.result.baseline?.totals
  const refresh = async (id?: string) => { await load(id); await onChanged() }
  const allOrders = plan?.work_orders ?? []
  const allSteps = allOrders.flatMap(order => order.steps)
  const completedIds = allSteps.filter(isDone).map(step => step.id)
  const readyTasks = readyWork(allOrders)
  const remainingSteps = allSteps.filter(step => !isDone(step)).length
  const passedOrders = allOrders.filter(order => order.verification?.outcome === 'pass').length
  const filteredOrders = allOrders.filter(order => order.target_asset_id.toLowerCase().includes(orderSearch.trim().toLowerCase())
    && (orderFilter === 'All' || orderFilter === 'Verified' && order.verification?.outcome === 'pass'
      || orderFilter === 'Paused' && order.status === 'paused'
      || orderFilter === 'Needs action' && order.verification?.outcome !== 'pass' && order.status !== 'paused'))
  const cashRemaining = plan ? plan.budget_paise - plan.result.totals.cost_paise : 0
  const timeRemaining = plan ? plan.time_minutes - plan.result.totals.technician_minutes : 0
  const allocationChanges = parent && plan ? [...new Set([...parent.result.allocations, ...plan.result.allocations].map(a => a.target_asset_id))].sort().map(target => {
    const before = parent.result.allocations.find(a => a.target_asset_id === target)
    const after = plan.result.allocations.find(a => a.target_asset_id === target)
    const changed = !before || !after || JSON.stringify(ids(before).slice().sort()) !== JSON.stringify(ids(after).slice().sort())
    return { target, before, after, changed }
  }) : []
  const changedCount = allocationChanges.filter(change => change.changed).length

  function revealNextTask() {
    const task = readyTasks[0]
    if (!task || stale || plan?.status === 'paused' || busy) return
    setOrderFilter('All'); setOrderSearch(''); setFocusTask({ ...task })
  }
  function revealSection(section: string) {
    document.getElementById(section)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  const nextAction = !plan ? {
    title: 'Calculate the fleet before choosing transfers', text: 'Set a budget and technician time. The backend will select complete configurations and validate every allocated part.', label: 'Go to resource limits', section: 'recovery-inputs',
  } : stale || plan.status === 'paused' || plan.status === 'rejected' ? {
    title: plan.status === 'paused' ? 'This rehearsal is paused' : plan.status === 'rejected' ? 'This plan was rejected' : 'Choose a current plan revision',
    text: plan.status === 'paused' ? 'Review saved simulated locations, recorded charges and remaining limits. Calculate a continuation, then approve its exact new revision before recording more work.' : 'Earlier results stay in history, but cannot authorize new work. Select a current revision or calculate a new rehearsal.', label: plan.status === 'paused' ? 'Review reconciliation' : 'Review plan selection', section: plan.status === 'paused' ? 'recovery-reconciliation' : 'recovery-plan-picker',
  } : !plan.result.operations.length ? {
    title: plan.result.allocations.length ? 'No repair operations are required' : 'No recoverable configuration within these limits',
    text: plan.result.allocations.length ? 'The selected configurations are retained without new repair work. They are not newly completed repairs.' : 'Review exclusions, evidence and hard resource limits. No work orders or simulated passes have been created.', label: 'Review plan inputs', section: 'recovery-inputs',
  } : plan.status === 'validated' ? {
    title: plan.parent_plan_id ? 'Review the revised plan before execution' : 'Your computed plan is ready to review',
    text: plan.parent_plan_id ? 'Check the highlighted allocation changes, remaining resources and exact revision, then choose approval or rejection.' : 'Inspect the allocations and proof. In Simulation you can test an actual allocated donor failure before approving work.', label: 'Review exact plan', section: 'recovery-approval',
  } : !allOrders.length ? {
    title: 'Approval recorded. Create the work checklist next.', text: 'The plan has reserved its target computers and components in this simulation context. Work orders preserve the extraction-before-installation dependencies.', label: 'Go to work-order creation', section: 'recovery-approval',
  } : passedOrders === allOrders.length ? {
    title: 'This simulated rehearsal is complete', text: `${passedOrders} authored simulation passes are recorded. Export the traceable history; physical repair counts remain zero.`, label: 'Export this record', section: 'recovery-export',
  } : {
    title: readyTasks.length ? 'Continue with a prerequisite-ready task' : 'Review the remaining work',
    text: readyTasks.length ? `${readyTasks.length} tasks are ready now. ${remainingSteps} total steps remain; completion still requires your explicit checklist and evidence.` : 'No task can advance right now. Inspect dependency or unresolved verification records; do not repeat completed work.', label: 'Open work queue', section: 'recovery-work-orders',
  }


  async function calculate() {
    const raw = Number(budget), time = Number(minutes), paise = Math.round(raw * 100)
    if (!Number.isFinite(raw) || raw < 0 || Math.abs(raw * 100 - paise) > 0.00001 || !Number.isSafeInteger(paise) || !Number.isSafeInteger(time) || time < 0) throw new Error('Enter a nonnegative INR budget with at most two decimal places and whole technician minutes.')
    if (!/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(contextId)) throw new Error('Use 1–64 letters, digits, underscores or hyphens for the execution context, starting with a letter or digit.')
    const next = await post<Plan>('/plans', { fleet_id: 'RG-DEMO-12', budget_paise: paise, time_minutes: time, context_id: contextId, execution, orchestration })
    await refresh(next.id); setReview(false); setReviewCheck(false)
  }
  async function exportReport() {
    if (!plan) return
    const report = await api<unknown>(`/plans/${plan.id}/report`)
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }))
    const link = document.createElement('a'); link.href = url; link.download = `revivegraph-${plan.id}-audit.json`; link.click(); URL.revokeObjectURL(url)
  }
  return <div className="recovery-workspace stack">
    {error && <ErrorNotice message={error}><Button variant="secondary" disabled={!!busy} onClick={() => void run('Refreshing plan…', () => refresh())}>Refresh plan and retry</Button></ErrorNotice>}
    {busy && <Loading text={busy} />}
    <Panel className={`recovery-action-banner ${stale || plan?.status === 'paused' ? 'recovery-action-caution' : ''}`} aria-label="Recovery next action"><span className="recovery-action-icon"><Icon name={plan?.status === 'paused' || stale ? 'alert' : 'arrow'} size={22} /></span><div><span className="eyebrow">YOUR NEXT STEP</span><h2>{nextAction.title}</h2><p>{nextAction.text}</p></div><Button variant="secondary" disabled={!!busy} onClick={() => revealSection(nextAction.section)}>{nextAction.label}<Icon name="arrow" size={15} /></Button></Panel>
    <div className="filter-bar" id="recovery-plan-picker"><label className="plan-picker">Persisted plan revision<select aria-label="Persisted plan revision" value={selected} disabled={!!busy || !plans.length} onChange={e => void run('Loading revision…', () => refresh(e.target.value))}><option value="" disabled>No plan calculated</option>{plans.map(p => <option key={p.id} value={p.id}>{p.id.slice(0, 12)} · {p.parent_plan_id ? 'replanned' : 'original'} · {p.status}</option>)}</select></label><Button variant="secondary" disabled={!!busy} onClick={() => void run('Refreshing plan…', () => refresh())}>Refresh plan</Button></div>
    {plan?.status === 'paused' && <ReconciliationPanel key={plan.id} planId={plan.id} onChanged={refresh} />}
    {plan && <ContinuationAccounting plan={plan} />}
    <div className={simulation ? `simulation-workspace${allOrders.length ? ' has-work-orders' : ''}` : 'optimizer-workspace'}>
      <Panel className="p-5 stack constraints-panel" id="recovery-inputs"><span className="eyebrow">{simulation ? 'SCENARIO OVERLAY' : 'PLAN INPUTS'}</span><h2>{simulation ? allOrders.length ? 'Scenario controls' : 'Stress the computed plan' : 'Resource limits'}</h2>
        {simulation ? <>{allOrders.length ? <><p className="caption">Your approved work queue is ready. Continue recorded steps before exploring another scenario.</p><details className="secondary-failure-controls"><summary>Simulate another failure</summary><div className="stack"><p className="caption">A failure excludes a selected part from this scenario. Physical locations and health evidence stay unchanged.</p><hr /><label>Allocated donor or stock part<select aria-label="Failure component" value={chosenFailure} disabled={!failureCandidates.length || !!busy} onChange={e => setFailure(e.target.value)}>{!failureCandidates.length && <option value="">No transferred component in this plan</option>}{failureCandidates.map(id => <option key={id} value={id}>{id} · {partById.get(id)?.location_asset_id ?? 'Stock'}</option>)}</select></label><p className="caption">Chosen from actual allocations. Installed donor parts appear first.</p><Button variant={allOrders.length ? 'secondary' : undefined} disabled={!plan || !chosenFailure || !!busy || !!stale || plan.status === 'rejected' || plan.status === 'paused'} onClick={() => void run('Applying simulated failure and recalculating…', async () => { const next = await post<Plan>(`/plans/${plan!.id}/failures`, { component_id: chosenFailure }); await refresh(next.id); setReview(false); setReviewCheck(false) })}>Inject failure and replan</Button></div></details><p className="caption warning-copy">After work starts, failure pauses execution. Follow the reconciliation message before continuing.</p></> : <><p className="caption">A failure excludes a selected part from this scenario. Physical locations and health evidence stay unchanged.</p><hr /><label>Allocated donor or stock part<select aria-label="Failure component" value={chosenFailure} disabled={!failureCandidates.length || !!busy} onChange={e => setFailure(e.target.value)}>{!failureCandidates.length && <option value="">No transferred component in this plan</option>}{failureCandidates.map(id => <option key={id} value={id}>{id} · {partById.get(id)?.location_asset_id ?? 'Stock'}</option>)}</select></label><p className="caption">Chosen from actual allocations. Installed donor parts appear first.</p><Button variant={allOrders.length ? 'secondary' : undefined} disabled={!plan || !chosenFailure || !!busy || !!stale || plan.status === 'rejected' || plan.status === 'paused'} onClick={() => void run('Applying simulated failure and recalculating…', async () => { const next = await post<Plan>(`/plans/${plan!.id}/failures`, { component_id: chosenFailure }); await refresh(next.id); setReview(false); setReviewCheck(false) })}>Inject failure and replan</Button><p className="caption warning-copy">After work starts, failure pauses execution. Follow the reconciliation message before continuing.</p></>}</> : <><p className="caption">The optimizer and greedy baseline use the same pinned snapshot and hard limits.</p><hr /><label>New calculation context<input aria-label="Simulation execution context" value={contextId} maxLength={64} onChange={e => setContextId(e.target.value)} /></label><Button variant="secondary" disabled={!!busy} onClick={() => setContextId(`rehearsal-${Date.now()}`)}>Use a new rehearsal context</Button><p className="caption">{plan ? `Displayed plan uses context “${plan.context_id}”. ` : ''}New contexts start from imported inventory and keep earlier plans, reservations and progress separate. Use reconciliation to continue paused work; a new rehearsal context is independent and starts over from imported inventory.</p><label>Workflow orchestration<select aria-label="Workflow orchestration" value={orchestration} disabled={!!busy} onChange={e => setOrchestration(e.target.value as 'local' | 'render')}><option value="local">Local validated pipeline</option><option value="render">Hosted Render Workflows (requires deployment)</option></select></label>{orchestration === 'render' && <p className="caption">Runs validation, execution, result validation and audit generation on the configured Render workflow. Hosted compute may incur charges. No automatic resubmission or local fallback.</p>}<label>Calculation runs on<select aria-label="Calculation execution" value={execution} disabled={!!busy} onChange={e => setExecution(e.target.value as 'local' | 'nodus')}><option value="local">{orchestration === 'render' ? 'Render worker CPU' : publicDemo ? 'Render demo CPU' : 'Local laptop CPU'}</option><option value="nodus">Nodus cloud CPU (up to US$0.10)</option></select></label>{execution === 'nodus' && <p className="caption">Uses event credits. Five-minute job limit; returned allocations are validated locally. No automatic paid retry or local fallback.</p>}<label>Repair budget (INR)<input aria-label="Repair budget (INR)" inputMode="decimal" type="number" min="0" step="0.01" value={budget} onChange={e => setBudget(e.target.value)} /></label><label>Technician minutes<input aria-label="Technician minutes" inputMode="numeric" type="number" min="0" step="1" value={minutes} onChange={e => setMinutes(e.target.value)} /></label><dl><dt>Minimum RAM</dt><dd>8 GiB · desktop UDIMM</dd><dt>Minimum storage</dt><dd>240 GB · 2.5-inch SATA</dd><dt>Zero limits</dt><dd>Hard zero, never unlimited</dd><dt>Inventory</dt><dd>Revision {inventoryRevision} · simulation only</dd></dl><Button disabled={!!busy || !components.length} onClick={() => void run('Calculating complete fleet configurations…', calculate)}>Calculate plan</Button></>}
        <hr /><p className="caption">Synthetic prices, durations and health assertions. This is planning, not a physical repair result.</p>
      </Panel>
      <div className="stack result-column">{plan ? <>
        {!!plan.work_orders?.length && <Panel className="p-5 stack" aria-label="Simulation work orders" id="recovery-work-orders"><div className="step-heading"><div><span className="eyebrow">PERSISTED EXECUTION</span><h2>Simulation work orders</h2></div><Badge tone="cyan">{completedIds.length} / {allSteps.length} steps recorded</Badge></div><p className="caption">Check each required item and enter authored simulation evidence. No physical inventory is moved.</p><div className="work-queue-summary" aria-label="Prerequisite-ready work queue"><div><Icon name="list" /><span><strong>{!stale && plan.status !== 'paused' ? readyTasks.length : 0} ready tasks</strong><small>{passedOrders} / {allOrders.length} simulated passes · {remainingSteps} steps remaining</small></span></div><Button variant="secondary" disabled={!!busy || !!stale || plan.status === 'paused' || !readyTasks.length} onClick={revealNextTask}>Show next available task<Icon name="arrow" size={15} /></Button>{readyTasks[0] && !stale && plan.status !== 'paused' && <p className="caption">Next: <strong>{readyTasks[0].order.target_asset_id}</strong> · {human(readyTasks[0].step.operation)} {readyTasks[0].step.component_id ?? ''}</p>}</div><div className="work-queue-controls"><div role="group" aria-label="Work order filter">{['All', 'Needs action', 'Verified', 'Paused'].map(value => <button key={value} className={orderFilter === value ? 'active' : ''} aria-pressed={orderFilter === value} onClick={() => setOrderFilter(value)}>{value}</button>)}</div><label><span className="sr-only">Work order search</span><input aria-label="Work order search" placeholder="Find computer ID…" value={orderSearch} onChange={event => setOrderSearch(event.target.value)} /></label></div><p className="caption">{filteredOrders.length} of {allOrders.length} work orders · verification is simulated only</p>{filteredOrders.map(order => <OrderView key={order.id} order={order} completedSteps={completedIds} focusedStep={focusTask?.step.id} allOrders={allOrders} onRevealDependency={(task) => { setOrderFilter('All'); setOrderSearch(''); setFocusTask({ ...task }) }} disabled={!!busy || !!stale || plan.status === 'paused'} onStep={(step, body) => run('Saving simulated work progress…', async () => { await post(`/work-orders/${order.id}/steps/${step.id}`, body); await refresh(plan.id) })} onVerify={body => run('Recording simulated verification…', async () => { await post(`/work-orders/${order.id}/verification`, body); await refresh(plan.id) })} />)}{!filteredOrders.length && <p className="queue-empty">No work orders match this view. Choose All or clear the computer search.</p>}</Panel>}
        <Panel className="p-5 stack" aria-label="Computed recovery plan"><div className="step-heading"><div><span className="eyebrow">{plan.parent_plan_id ? 'REVISED PLAN' : 'COMPUTED PLAN'}</span><h2>Fleet recovery result</h2></div><Badge tone={plan.result.solver.status === 'OPTIMAL' ? 'success' : 'warning'}>{plan.result.solver.status}</Badge></div><p className="caption mono plan-id">{plan.id}</p><p className="caption">Inventory revision {plan.inventory_revision} · {plan.mode} · {plan.result.solver.engine_version ?? 'CP-SAT'} · {plan.status} · {plan.execution?.provider === 'nodus' ? `Nodus CPU · job ${plan.execution.job_id}` : plan.execution?.workflow?.orchestrator === 'render-workflows' ? 'Render worker CPU' : 'Local CPU'} · {plan.execution?.workflow?.orchestrator === 'render-workflows' ? `Render Workflows · task ${plan.execution.workflow.task_run_id ?? 'unavailable'}` : plan.execution?.workflow ? 'Local validated pipeline' : 'Workflow trace not recorded'}</p>
          {plan.execution?.workflow && <details><summary>Validated workflow stages</summary><ol className="reason-list">{plan.execution.workflow.stages.map(step => <li key={step.stage}><strong>{step.stage.replaceAll('_', ' ')} · {step.status}</strong><span className="hash">Input {step.input_hash}<br />Output {step.output_hash}</span></li>)}</ol><p className="hash">Audit artifact {plan.execution.workflow.artifact_hash}</p></details>}
          {stale && <ErrorNotice message="This plan is stale. Approval and new work orders are disabled. Select the revised plan or calculate from the current snapshot." />}
          {plan.status === 'paused' && <ErrorNotice message="Execution paused after failure. Existing progress is preserved and cannot be advanced until reconciled." />}
          <hr /><div className="result-metrics">{[['Usable final', plan.result.totals.usable_final], ['Newly recovered', plan.result.totals.newly_recovered], ['Assumed cash', money(plan.result.totals.cost_paise)], ['Technician effort', `${plan.result.totals.technician_minutes} min`]].map(([label, value]) => <div className="result-metric" key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
          <div className="resource-headroom" aria-label="Remaining plan resources"><div><span>Projected budget remaining</span><strong>{money(cashRemaining)}</strong><small>of {money(plan.budget_paise)} limit</small><div className="resource-track"><i style={{ width: `${plan.budget_paise ? Math.min(100, plan.result.totals.cost_paise / plan.budget_paise * 100) : 0}%` }} /></div></div><div><span>Projected technician time remaining</span><strong>{timeRemaining} min</strong><small>of {plan.time_minutes} min limit</small><div className="resource-track"><i style={{ width: `${plan.time_minutes ? Math.min(100, plan.result.totals.technician_minutes / plan.time_minutes * 100) : 0}%` }} /></div></div></div>
          <h3>Final configurations</h3><div className="table-scroll"><table aria-label="Computed final configurations"><thead><tr><th>Target</th><th>RAM IDs</th><th>Storage ID</th><th>Retained / incoming</th></tr></thead><tbody>{plan.result.allocations.map(a => <tr key={a.target_asset_id}><td className="mono cyan">{a.target_asset_id}</td><td>{a.ram_component_ids.join(' + ')}</td><td>{a.storage_component_id}</td><td>{ids(a).map(id => `${id}: ${partById.get(id)?.location_asset_id === a.target_asset_id ? 'retained' : `from ${partById.get(id)?.location_asset_id ?? 'stock'}`}`).join('; ')}</td></tr>)}</tbody></table>{!plan.result.allocations.length && <p className="muted p-5">No eligible complete configuration fits these limits. This is a valid zero-recovery result if the solver reports feasibility.</p>}</div>
          <p className="caption">Every physical ID appears at most once, including retained parts. Donors count only with a valid final configuration.</p>
          <details><summary>Solver proof and baseline comparison</summary><p className="caption">Proven objectives: {JSON.stringify(plan.result.solver.objectives_proven)}</p>{baseline ? <p className="caption">Greedy baseline: {baseline.usable_final} usable · {money(baseline.cost_paise)} · {baseline.technician_minutes} min · {baseline.transfers} transfers</p> : <pre className="json-detail">{JSON.stringify(plan.result.baseline, null, 2)}</pre>}<p className="caption">{plan.result.solver.termination_reason}</p></details>
          <details><summary>Operation ledger ({plan.result.operations.length})</summary><div className="table-scroll"><table><thead><tr><th>Operation</th><th>Asset / part</th><th>Paise</th><th>Minutes</th></tr></thead><tbody>{plan.result.operations.map((op, i) => <tr key={i}><td>{human(op.operation)}</td><td>{op.asset_id}<small>{op.component_id}</small></td><td>{op.cost_paise}</td><td>{op.technician_minutes}</td></tr>)}</tbody></table></div></details>
          <details><summary>Input and version pin</summary><p className="hash">{plan.input_hash}</p><p className="caption">Scenario {plan.scenario_id} · execution context {plan.context_id}</p></details>
        </Panel>
        {parent && <Panel className="p-5 stack allocation-comparison" aria-label="Before and after comparison"><div className="step-heading"><div><span className="eyebrow">BEFORE / AFTER FAILURE</span><h2>Allocation changes</h2></div><Badge tone="cyan">{changedCount} changed · {allocationChanges.length - changedCount} unchanged</Badge></div><p className="caption">Original {parent.id.slice(0, 12)} preserved · revised {plan.id.slice(0, 12)}</p><div className="comparison-grid"><div><h3>Before</h3><p>{parent.result.totals.usable_final} usable · {money(parent.result.totals.cost_paise)} · {parent.result.totals.technician_minutes} min</p></div><div><h3>After</h3><p>{plan.result.totals.usable_final} usable · {money(plan.result.totals.cost_paise)} · {plan.result.totals.technician_minutes} min</p></div></div><div className="allocation-deltas" aria-label="Actual plan changes"><span><strong>{signed(plan.result.totals.usable_final - parent.result.totals.usable_final)}</strong> usable computers</span><span><strong>{plan.result.totals.cost_paise === parent.result.totals.cost_paise ? money(0) : `${plan.result.totals.cost_paise > parent.result.totals.cost_paise ? '+' : '−'}${money(Math.abs(plan.result.totals.cost_paise - parent.result.totals.cost_paise))}`}</strong> cash change</span><span><strong>{signed(plan.result.totals.technician_minutes - parent.result.totals.technician_minutes, ' min')}</strong> effort change</span></div><p className="caption">{changedCount ? 'Changed allocations are shown first. Highlighted IDs differ between these actual results.' : 'No final component assignments changed; review the actual resource and scenario differences.'}</p><ul className="allocation-diff">{allocationChanges.filter(change => showAllChanges || change.changed).map(({ target, before, after, changed }) => <li key={target} className={changed ? 'allocation-changed' : ''}><strong>{target}<Badge tone={changed ? 'warning' : 'neutral'}>{changed ? 'Changed' : 'Unchanged'}</Badge></strong><span>Before: {before ? ids(before).map(id => <code className={!after || !ids(after).includes(id) ? 'changed-component removed-component' : ''} key={id}>{id}</code>) : 'not allocated'}</span><span>After: {after ? ids(after).map(id => <code className={!before || !ids(before).includes(id) ? 'changed-component added-component' : ''} key={id}>{id}</code>) : 'not allocated'}</span></li>)}</ul>{allocationChanges.length > changedCount && <Button variant="secondary" onClick={() => setShowAllChanges(!showAllChanges)}>{showAllChanges ? 'Show changed allocations only' : `Show all ${allocationChanges.length} allocations`}</Button>}</Panel>}
        <Panel className="p-5 stack" aria-label="Plan approval" id="recovery-approval"><span className="eyebrow">HUMAN REVIEW</span><h2>Approval of the exact plan</h2><p className="caption">Review compatibility, synthetic assumptions and resources. Approval reserves this plan's parts for simulation in context “{plan.context_id}”. Local actor: local-demo-operator (not authenticated).</p><Badge tone={plan.status === 'approved' ? 'success' : 'warning'}>{plan.status}</Badge>
          <div className="actions"><Button variant="secondary" disabled={!canApprove || !!busy} onClick={() => { setReview(!review); setReviewCheck(false) }}>Review approval</Button><Button variant="secondary" disabled={!canApprove || !!busy} onClick={() => void run('Recording rejection…', async () => { await post(`/plans/${plan.id}/decision`, { decision: 'reject', input_hash: plan.input_hash }); await refresh(plan.id); setReview(false) })}>Reject plan</Button><Button disabled={plan.status !== 'approved' || !!stale || !!busy || !plan.result.operations.length} onClick={() => void run('Creating traceable work orders…', async () => { await post(`/plans/${plan.id}/work-orders`, {}); await refresh(plan.id) })}>Create simulation work orders</Button></div>
          {review && <div className="approval-review stack"><h3>Confirm exact simulation revision</h3><p className="hash">Plan {plan.id}<br />Input {plan.input_hash}</p><p>{money(plan.result.totals.cost_paise)} · {plan.result.totals.technician_minutes} min · {plan.result.totals.usable_final} final computers</p><label className="check-row"><input type="checkbox" checked={reviewCheck} onChange={e => setReviewCheck(e.target.checked)} />I reviewed this exact revision and authorize simulated work only.</label><Button disabled={!reviewCheck || !canApprove || !!busy} onClick={() => void run('Approving and reserving the exact revision…', async () => { await post(`/plans/${plan.id}/decision`, { decision: 'approve', input_hash: plan.input_hash }); await refresh(plan.id); setReview(false); setReviewCheck(false) })}>Approve exact simulation plan</Button></div>}
          {!canApprove && plan.status !== 'approved' && <p className="caption">Approval requires a current, independently validated, unrejected revision.</p>}
        </Panel>
        <Panel className="p-5 stack" id="recovery-export"><span className="eyebrow">REPORTS AND AUDIT</span><h2>Export this recovery record</h2><p className="caption">JSON includes pinned inputs, assumptions, original/revised allocations, human decisions, work progress and verification evidence. Environmental estimates are unavailable.</p><Button variant="secondary" disabled={!!busy} onClick={() => void run('Preparing audit report…', exportReport)}>Export audit report</Button></Panel>
      </> : <EmptyState title={simulation ? 'Calculate a plan before simulating failure' : 'No plan calculated'}><p>Import the synthetic fleet, inspect evidence and calculate a complete fleet allocation. Recovery totals remain “Not calculated” until the backend returns a solver result.</p></EmptyState>}</div>
    </div>
  </div>
}

function OrderView({ order, disabled, completedSteps = [], focusedStep, allOrders, onRevealDependency, onStep, onVerify }: { order: WorkOrder; disabled: boolean; completedSteps?: string[]; focusedStep?: string; allOrders: WorkOrder[]; onRevealDependency: (task: QueueTask) => void; onStep: (step: WorkStep, body: { evidence_ref: string; checks: string[] }) => Promise<void>; onVerify: (body: { outcome: string; evidence_ref: string; checks: string[] }) => Promise<void> }) {
  const [checks, setChecks] = useState<Record<string, string[]>>({})
  const [evidence, setEvidence] = useState<Record<string, string>>({})
  const [outcome, setOutcome] = useState('pass')
  const complete = new Set([...completedSteps, ...order.steps.filter(isDone).map(s => s.id)])
  const verify = order.steps.find(s => s.operation === 'verify_target')
  const completeCount = order.steps.filter(isDone).length
  const dependencies = new Map(allOrders.flatMap(other => other.steps.map(step => [step.id, { order: other, step }] as const)))
  const stepForm = (step: WorkStep) => {
    const recorded = step as RecordedStep
    const saved = isDone(step) || !!recorded.evidence_ref
    const values = saved ? recorded.checks ?? [] : checks[step.id] ?? []
    const evidenceValue = saved ? recorded.evidence_ref ?? '' : evidence[step.id] ?? ''
    return <><div className="step-checklist">{step.required_checks.map(check => <label className="check-row" key={check}><input type="checkbox" aria-label={`${order.target_asset_id} ${step.operation} ${check}`} checked={values.includes(check)} onChange={e => setChecks(old => ({ ...old, [step.id]: e.target.checked ? [...old[step.id] ?? [], check] : (old[step.id] ?? []).filter(c => c !== check) }))} disabled={disabled || saved} />{human(check)}</label>)}</div><label>Simulation evidence reference<input aria-label={`${order.target_asset_id} ${step.operation} evidence`} placeholder="e.g. synthetic:rehearsal-check-01" value={evidenceValue} onChange={e => setEvidence(old => ({ ...old, [step.id]: e.target.value }))} disabled={disabled || saved} /></label>{saved && <div className="saved-step-evidence"><Icon name="check" size={14} /><span>Saved simulation record{recorded.actor ? ` · ${recorded.actor}` : ''}{recorded.completed_at || recorded.recorded_at ? ` · ${new Date((recorded.completed_at ?? recorded.recorded_at)!).toLocaleString()}` : ''}</span></div>}</>
  }
  return <details className="work-order" data-testid="work-order" id={`work-order-${order.id}`}><summary><span>{order.target_asset_id} · {order.status} · {order.steps.length} steps</span><span className="work-order-progress">{completeCount}/{order.steps.length} complete</span></summary><p className="hash">{order.id}</p>{order.steps.filter(s => s.operation !== 'verify_target').map(step => <div className={`order-step stack ${focusedStep === step.id ? 'focused-work-step' : ''}`} key={step.id} id={`work-step-${step.id}`} data-testid="work-step" data-step-id={step.id} tabIndex={-1}><div className="step-heading"><h3>{human(step.operation)} {step.component_id}</h3><Badge tone={complete.has(step.id) ? 'success' : step.depends_on.every(id => complete.has(id)) ? 'cyan' : 'neutral'}>{complete.has(step.id) ? step.status : step.depends_on.every(id => complete.has(id)) ? 'Ready' : 'Blocked by prerequisite'}</Badge></div>{step.asset_id && <p className="caption">Location: {step.asset_id}</p>}{stepForm(step)}{!!step.depends_on.length && <p className="caption">Prerequisites: {step.depends_on.map(id => { const task = dependencies.get(id); return <span className="named-dependency" key={id}>{task ? <button className="text-link" onClick={() => onRevealDependency(task)}>{task.order.target_asset_id} · {human(task.step.operation)}{task.step.component_id ? ` ${task.step.component_id}` : ''} · {complete.has(id) ? 'done' : 'pending'}</button> : <span>Unknown dependency · refresh plan</span>}</span> })}</p>}<Button variant="secondary" disabled={disabled || complete.has(step.id) || !step.depends_on.every(id => complete.has(id)) || !(evidence[step.id] ?? '').trim() || step.required_checks.some(check => !(checks[step.id] ?? []).includes(check))} onClick={() => void onStep(step, { evidence_ref: evidence[step.id].trim(), checks: checks[step.id] ?? [] })}>Record {human(step.operation)}</Button></div>)}
    {verify && <div className={`order-step stack ${focusedStep === verify.id ? 'focused-work-step' : ''}`} id={`work-step-${verify.id}`} data-testid="work-step" data-step-id={verify.id} tabIndex={-1}><h3>Simulated verification</h3>{stepForm(verify)}<label>Verification outcome<select aria-label={`${order.target_asset_id} verification outcome`} value={order.verification?.outcome ?? outcome} disabled={disabled || !!order.verification} onChange={e => setOutcome(e.target.value)}><option value="pass">Pass — simulated only</option><option value="fail">Fail</option><option value="inconclusive">Inconclusive</option></select></label><Button disabled={disabled || !!order.verification || !verify.depends_on.every(id => complete.has(id)) || !order.steps.filter(s => s.operation !== 'verify_target').every(s => complete.has(s.id)) || !(evidence[verify.id] ?? '').trim() || (outcome === 'pass' && verify.required_checks.some(check => !(checks[verify.id] ?? []).includes(check)))} onClick={() => void onVerify({ outcome, evidence_ref: evidence[verify.id].trim(), checks: checks[verify.id] ?? [] })}>Record simulated verification</Button></div>}
    {order.verification && <div className="verification-result" role="status"><strong>Simulated verification: {order.verification.outcome}</strong><p className="caption">{order.verification.evidence_ref}</p><p className="caption">Does not count as a physically verified repair.</p></div>}
  </details>
}
