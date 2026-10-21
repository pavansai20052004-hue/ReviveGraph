import { lazy, Suspense, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api } from '../api'
import type { Component, Computer, Plan, State } from '../types'
import './dashboard.css'

const DashboardCharts = lazy(() => import('./DashboardCharts'))
const cash = (paise: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(paise / 100)
const words = (text: string) => text.replaceAll('_', ' ')
type AuditEvent = { id: number; action: string; entity_id: string; actor: string; occurred_at: string; data: Record<string, unknown> }
type Navigate = (page: string, assetId?: string) => void
type IconName = 'computer' | 'component' | 'alert' | 'plan' | 'check' | 'arrow' | 'clock' | 'extract' | 'install' | 'activity' | 'file' | 'lock'

function Glyph({ name, className = '' }: { name: IconName; className?: string }) {
  const paths: Record<IconName, ReactNode> = {
    computer: <><rect x="3" y="4" width="18" height="12" rx="2" /><path d="M8 21h8M12 16v5" /></>,
    component: <><path d="m12 3 8 5v8l-8 5-8-5V8zM4 8l8 5 8-5M12 13v8" /></>,
    alert: <><path d="m12 3 10 18H2zM12 9v5M12 17h.01" /></>,
    plan: <><path d="M4 19V5M4 19h17M8 15l4-5 4 2 5-7" /><path d="M17 5h4v4" /></>,
    check: <><circle cx="12" cy="12" r="9" /><path d="m8 12 3 3 5-6" /></>,
    arrow: <path d="M4 12h16m-5-5 5 5-5 5" />,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    extract: <><path d="M5 4h14v16H5zM8 12h8m-4-4-4 4 4 4" /></>,
    install: <><path d="M5 4h14v16H5zM8 12h8m-4-4 4 4-4 4" /></>,
    activity: <path d="M2 12h5l3-8 4 16 3-8h5" />,
    file: <><path d="M5 3h9l5 5v13H5zM14 3v6h5M8 13h8M8 17h6" /></>,
    lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3" /></>,
  }
  return <svg className={`overview-glyph ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

function CardTitle({ title, action, onClick }: { title: string; action?: string; onClick?: () => void }) {
  return <div className="overview-card-title"><h2>{title}</h2>{action && <button className="overview-subtle-link" onClick={onClick}>{action}<Glyph name="arrow" /></button>}</div>
}

function FleetMap({ computers, onNavigate }: { computers: Computer[]; onNavigate: Navigate }) {
  return <div className="overview-fleet-visual"><div className="overview-board-lines" aria-hidden="true"><span /><span /><span /><span /></div><div className="overview-machine-grid">{computers.map(computer => <button className={`overview-machine overview-machine-${computer.usability.classification}`} key={computer.asset_id} onClick={() => onNavigate('inventory', computer.asset_id)} aria-label={`Inspect ${computer.asset_id}: ${computer.usability.classification}`}>
    <span className="overview-machine-display"><span /><i /></span><span className="overview-machine-stand" /><span className="overview-machine-label">{computer.asset_id.replace('RG-', '')}</span><span className="overview-machine-state" aria-hidden="true" />
  </button>)}</div></div>
}

export function Dashboard({ state, computers, components, onNavigate, onImport }: { state: State; computers: Computer[]; components: Component[]; onNavigate: Navigate; onImport: () => void }) {
  const [plans, setPlans] = useState<Plan[]>([])
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [planError, setPlanError] = useState('')
  const [auditError, setAuditError] = useState('')
  const [reload, setReload] = useState(0)
  useEffect(() => {
    let active = true
    setLoading(true); setPlanError(''); setAuditError('')
    const query = `fleet_id=${encodeURIComponent(state.fleet_id)}`
    Promise.allSettled([api<{ items: Plan[] }>(`/plans?${query}`), api<{ items: AuditEvent[] }>(`/audit-events?${query}&limit=8`)]).then(([planResponse, auditResponse]) => {
      if (!active) return
      if (planResponse.status === 'fulfilled') setPlans(planResponse.value.items)
      else { setPlans([]); setPlanError(planResponse.reason instanceof Error ? planResponse.reason.message : 'Recovery plans could not be loaded.') }
      if (auditResponse.status === 'fulfilled') setEvents(auditResponse.value.items)
      else { setEvents([]); setAuditError(auditResponse.reason instanceof Error ? auditResponse.reason.message : 'Audit events could not be loaded.') }
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [state, reload])

  const latest = plans[0]
  const parent = plans.find(plan => plan.id === latest?.parent_plan_id)
  const missing = computers.filter(c => c.usability.blockers.some(b => /MISSING/.test(b.code)))
  const faulty = components.filter(p => p.health === 'faulty')
  const unknown = components.filter(p => p.health === 'unknown')
  const planned = state.optimization.newly_recovered
  const stale = latest && ['stale', 'paused'].includes(latest.status)
  const alerts = useMemo(() => [
    ...computers.filter(c => c.usability.blockers.some(b => /MISSING/.test(b.code))).map(c => ({ id: c.asset_id, title: 'Required component missing', detail: c.usability.blockers.find(b => /MISSING/.test(b.code))!.message, tone: 'red', badge: 'Missing', page: 'inventory' })),
    ...components.filter(p => p.health === 'faulty').map(p => ({ id: p.component_id, title: 'Faulty component assertion', detail: `${p.location_asset_id ?? 'Institution stock'} · ${p.type === 'ram' ? 'RAM module' : 'SATA storage'}`, tone: 'red', badge: 'Faulty', page: 'inventory' })),
    ...computers.filter(c => c.usability.classification === 'unknown').map(c => ({ id: c.asset_id, title: 'Evidence needs review', detail: c.usability.blockers[0]?.message ?? 'Decisive evidence is unknown.', tone: 'amber', badge: 'Unknown', page: 'diagnostics' })),
    ...components.filter(p => p.health === 'unknown').map(p => ({ id: p.component_id, title: 'Component health unknown', detail: `${p.location_asset_id ?? 'Institution stock'} · assessment evidence is unresolved`, tone: 'amber', badge: 'Unknown', page: 'inventory' })),
  ], [computers, components])
  const shownAlerts = ['Missing', 'Faulty', 'Unknown'].flatMap(badge => {
    const alert = alerts.find(item => item.badge === badge)
    return alert ? [alert] : []
  })
  for (const alert of alerts) {
    if (shownAlerts.length >= 3) break
    if (!shownAlerts.includes(alert)) shownAlerts.push(alert)
  }
  const allSteps = latest?.work_orders.flatMap(order => order.steps) ?? []
  const stepTotals = (prefix: string) => {
    const steps = allSteps.filter(step => step.operation.startsWith(prefix))
    return { total: steps.length, done: steps.filter(step => step.status === 'done').length }
  }
  const extraction = stepTotals('remove_'), installation = stepTotals('install_'), verification = stepTotals('verify_')
  const passes = latest?.work_orders.filter(order => order.verification?.outcome === 'pass').length ?? 0
  const unfinishedOrders = latest?.work_orders.filter(order => order.status !== 'verified_pass').length ?? 0
  const openCurrentPlan = (page: string) => {
    if (latest) sessionStorage.setItem('revivegraph-plan', latest.id)
    onNavigate(page)
  }
  const nextAction: { title: string; description: string; label: string; icon: IconName; tone: string; action: () => void; secondary?: { label: string; action: () => void } } =
    !computers.length ? {
      title: 'Import your 12-computer synthetic fleet', description: 'Preview the bundled computers and components, review errors, then commit one complete batch. No physical computers are needed for this demonstration.',
      label: 'Start synthetic import', icon: 'computer', tone: 'blue', action: onImport,
      secondary: { label: 'What happens next', action: () => document.getElementById('recovery-journey')?.scrollIntoView({ behavior: 'smooth', block: 'center' }) },
    } : loading ? {
      title: 'Reading your current recovery state', description: 'Checking persisted plans and work progress before recommending the next action.',
      label: 'Loading next action…', icon: 'clock', tone: 'blue', action: () => {},
    } : planError ? {
      title: 'Reconnect to your recovery plans', description: 'Inventory is available, but the latest plan could not be read. Refresh before continuing so an older revision is not mistaken for the current one.',
      label: 'Retry plan connection', icon: 'alert', tone: 'amber', action: () => setReload(value => value + 1),
    } : !latest ? {
      title: 'Calculate your first recovery plan', description: `${state.counts.computers} computers and ${state.counts.components} components are imported. Inspect the supplied evidence, then calculate a whole-fleet allocation within your resource limits.`,
      label: 'Open recovery optimizer', icon: 'plan', tone: 'blue', action: () => onNavigate('optimizer'),
      secondary: { label: 'Inspect evidence first', action: () => onNavigate('diagnostics') },
    } : latest.status === 'paused' ? {
      title: 'Review paused work before starting again', description: 'A failure occurred after work began. Completed progress is preserved; automatic reconciliation is not implemented. Use a new rehearsal context for an independent run.',
      label: 'Open rehearsal controls', icon: 'alert', tone: 'amber', action: () => openCurrentPlan('optimizer'),
      secondary: { label: 'Review preserved work', action: () => openCurrentPlan('simulation') },
    } : latest.status === 'stale' ? {
      title: 'This plan needs a current replacement', description: 'The latest plan is stale and cannot authorize new work. Review the changed inputs and calculate a current revision or independent rehearsal.',
      label: 'Open recovery optimizer', icon: 'alert', tone: 'amber', action: () => openCurrentPlan('optimizer'),
      secondary: { label: 'Inspect stale revision', action: () => openCurrentPlan('simulation') },
    } : latest.status === 'rejected' ? {
      title: 'Revise the rejected recovery proposal', description: 'Rejection is preserved and created no reservations. Review the resource limits and calculate a new proposal before approving work.',
      label: 'Revise in optimizer', icon: 'plan', tone: 'amber', action: () => openCurrentPlan('optimizer'),
    } : latest.status === 'approved' && latest.work_orders.length > 0 && !unfinishedOrders ? {
      title: 'Export the recovery evidence', description: `${passes} of ${latest.work_orders.length} work orders have recorded simulated passes. Export the plan, decisions and evidence; physical repair counts remain separate.`,
      label: 'Open recovery reports', icon: 'file', tone: 'green', action: () => openCurrentPlan('reports'),
      ...(unfinishedOrders ? { secondary: { label: `Continue ${unfinishedOrders} unfinished orders`, action: () => openCurrentPlan('simulation') } } : {}),
    } : latest.status === 'approved' && latest.work_orders.length ? {
      title: 'Continue the simulated recovery work', description: `${allSteps.filter(step => step.status === 'done').length} of ${allSteps.length} work steps are recorded. Follow prerequisite-ready extraction and installation steps, then enter verification evidence.`,
      label: 'Continue simulated work', icon: 'install', tone: 'green', action: () => openCurrentPlan('simulation'),
      ...(passes ? { secondary: { label: 'Export progress so far', action: () => openCurrentPlan('reports') } } : {}),
    } : latest.status === 'approved' ? {
      title: 'Create work orders for the approved plan', description: 'The exact plan is approved and its parts are reserved in this rehearsal. Open the simulation workspace to create dependency-ordered work orders.',
      label: 'Open approved workflow', icon: 'extract', tone: 'green', action: () => openCurrentPlan('simulation'),
    } : latest.parent_plan_id ? {
      title: 'Review the revised plan before approval', description: 'The donor failure has a computed replacement plan. Inspect the changed allocations and resource totals, then approve or reject this exact revision.',
      label: 'Review revised plan', icon: 'lock', tone: 'purple', action: () => openCurrentPlan('simulation'),
      secondary: { label: 'Inspect allocation details', action: () => openCurrentPlan('optimizer') },
    } : {
      title: 'Review the computed recovery plan', description: `${latest.result.totals.usable_final} complete final configurations fit the current plan. Compare allocations and resources before approving the exact revision. A donor-failure test is an optional demonstration branch.`,
      label: 'Review recovery plan', icon: 'plan', tone: 'purple', action: () => openCurrentPlan('simulation'),
      secondary: { label: 'Test an optional donor failure', action: () => openCurrentPlan('simulation') },
    }
  const journey = [
    { title: 'Import', detail: computers.length ? `${computers.length} computers imported` : 'Preview and commit CSVs', status: computers.length ? 'complete' : 'current', action: computers.length ? () => onNavigate('inventory') : onImport },
    { title: 'Inspect', detail: computers.length ? 'Evidence available · not verified' : 'Awaiting inventory', status: computers.length ? 'available' : 'pending', action: () => onNavigate('diagnostics') },
    { title: 'Plan', detail: latest ? stale ? 'Current revision needed' : `${latest.result.totals.usable_final} final configurations` : 'Not calculated', status: latest && !stale ? 'complete' : computers.length ? 'current' : 'pending', action: () => openCurrentPlan('optimizer') },
    { title: 'Approve', detail: latest?.status === 'approved' ? 'Exact revision approved' : latest?.status === 'rejected' ? 'Rejected · revise proposal' : 'Human decision required', status: latest?.status === 'approved' && !stale ? 'complete' : latest && !stale ? 'current' : 'pending', action: () => openCurrentPlan('simulation') },
    { title: 'Verify', detail: latest?.work_orders.length ? `${passes} / ${latest.work_orders.length} simulated passes` : 'Checks and evidence required', status: latest?.work_orders.length && passes === latest.work_orders.length && !stale ? 'complete' : latest?.work_orders.length && !stale ? 'current' : 'pending', action: () => openCurrentPlan('simulation') },
  ]
  const metrics: { label: string; value: string | number; detail: string; tone: string; icon: IconName; onClick: () => void }[] = [
    { label: 'Computers in fleet', value: state.counts.computers, detail: `${state.counts.components} uniquely identified components`, tone: 'blue', icon: 'computer', onClick: () => onNavigate('inventory') },
    { label: 'Fleet needs attention', value: state.counts.unusable + state.counts.unknown, detail: `${state.counts.unusable} unusable · ${state.counts.unknown} uncertain`, tone: 'red', icon: 'alert', onClick: () => onNavigate('inventory') },
    { label: 'Planned recovery', value: planned ?? 'Not calculated', detail: stale ? `Latest plan ${latest.status} · review required` : latest ? `${latest.result.solver.status} · synthetic scenario` : 'Calculate a constrained allocation', tone: 'purple', icon: 'plan', onClick: () => onNavigate('optimizer') },
    { label: 'Assumed repair cash', value: state.optimization.cost_paise == null ? 'Not calculated' : cash(state.optimization.cost_paise), detail: state.optimization.technician_minutes == null ? 'No computed resource totals yet' : `${state.optimization.technician_minutes} technician minutes · ${stale ? 'stale plan' : 'latest plan'}`, tone: 'green', icon: 'clock', onClick: () => onNavigate('optimizer') },
    { label: 'Simulated passes', value: state.recovery?.simulated_passes ?? 0, detail: `${state.recovery?.physical_passes ?? 0} physically verified repairs`, tone: 'amber', icon: 'check', onClick: () => onNavigate('simulation') },
  ]

  return <div className="overview-dashboard">
    <section className={`overview-command overview-command-${nextAction.tone}`} aria-label="Recovery next action">
      <div className="overview-command-main"><span className={`overview-command-icon overview-${nextAction.tone}`}><Glyph name={nextAction.icon} /></span><div><span className="overview-command-kicker">YOUR NEXT STEP</span><h2>{nextAction.title}</h2><p>{nextAction.description}</p></div><div className="overview-command-actions"><button className="overview-command-primary" disabled={!!computers.length && loading} onClick={nextAction.action}>{nextAction.label}<Glyph name="arrow" /></button>{nextAction.secondary && <button className="overview-command-secondary" onClick={nextAction.secondary.action}>{nextAction.secondary.label}</button>}</div></div>
      <div id="recovery-journey" className="overview-journey" aria-label="Recovery journey">{journey.map((step, index) => <button key={step.title} className={`overview-journey-step overview-journey-${step.status}`} aria-label={`${step.title}: ${step.detail}`} title={step.detail} disabled={step.status === 'pending'} onClick={step.action}><span className="overview-journey-number">{step.status === 'complete' ? <Glyph name="check" /> : String(index + 1).padStart(2, '0')}</span><span><strong>{step.title}</strong><small>{step.detail}</small><em className="overview-journey-mobile-state">{step.status === 'complete' ? 'Done' : step.status === 'current' ? 'Next' : step.status === 'available' ? 'Available' : 'Later'}</em></span>{index < journey.length - 1 && <Glyph name="arrow" className="overview-journey-arrow" />}</button>)}</div>
    </section>
    <div className="overview-metrics">{metrics.map(metric => <button className="overview-metric" key={metric.label} onClick={metric.onClick}><span className="overview-metric-label">{metric.label}</span><strong className={typeof metric.value === 'string' && metric.value === 'Not calculated' ? 'overview-metric-pending' : ''}>{metric.value}</strong><span className="overview-metric-detail">{metric.detail}</span><span className={`overview-icon-box overview-${metric.tone}`}><Glyph name={metric.icon} /></span></button>)}</div>
    <div className="overview-layout"><div className="overview-main-column">
      <div className="overview-top-grid">
        <section className="overview-card overview-health" aria-label="Fleet health and usability"><CardTitle title="Fleet health overview" />
          {computers.length ? <><FleetMap computers={computers} onNavigate={onNavigate} /><div className="overview-health-legend"><span><i className="overview-dot overview-green" />{state.counts.usable} usable</span><span><i className="overview-dot overview-red" />{state.counts.unusable} unusable</span><span><i className="overview-dot overview-amber" />{state.counts.unknown} uncertain</span></div></> : <div className="overview-card-empty"><Glyph name="computer" /><strong>Your fleet starts here</strong><p>Import both CSV files to inspect computers and their components.</p><button className="overview-text-link" onClick={onImport}>Start CSV import <Glyph name="arrow" /></button></div>}
          <button className="overview-card-footer overview-text-link" onClick={() => onNavigate('inventory')}>View computers and components <Glyph name="arrow" /></button>
        </section>
        <section className="overview-card overview-alert-summary" aria-label="Fleet alert summary"><CardTitle title="Alert summary" /><div className="overview-summary-rows">
          {[
            { label: 'Missing parts', value: missing.length, unit: 'computers', tone: 'red' },
            { label: 'Faulty parts', value: faulty.length, unit: 'components', tone: 'red' },
            { label: 'Unknown health', value: unknown.length, unit: 'components', tone: 'amber' },
            { label: 'Uncertain usability', value: state.counts.unknown, unit: 'computers', tone: 'blue' },
          ].map(item => <button className="overview-summary-row" key={item.label} onClick={() => onNavigate(item.label === 'Uncertain usability' ? 'diagnostics' : 'inventory')}><span className={`overview-small-icon overview-${item.tone}`}><Glyph name="alert" /></span><span>{item.label}<small>{item.unit}</small></span><strong className={`overview-text-${item.tone}`}>{item.value}</strong></button>)}
          </div><div className="overview-summary-total"><span>Healthy components</span><strong>{state.counts.healthy_components}</strong></div><p className="overview-note">Categories can overlap. These are assertions, not health scores.</p>
        </section>
        <section className="overview-card overview-alerts" aria-label="Fleet alerts"><CardTitle title="Fleet alerts" />
          {shownAlerts.length ? <div className="overview-alert-list">{shownAlerts.map(alert => <button className="overview-alert-row" key={`${alert.id}:${alert.badge}`} onClick={() => onNavigate(alert.page, alert.id)}><span className={`overview-text-${alert.tone}`}><Glyph name="alert" /></span><span><span className="overview-alert-heading"><span className={`overview-status-label overview-${alert.tone}`}>{alert.badge}</span><strong>{alert.title}</strong></span><small className="overview-alert-id">{alert.id}</small><span className="overview-alert-detail">{alert.detail}</span></span></button>)}</div> : <p className="overview-inset-empty">{computers.length ? 'No missing, faulty or unknown records in this snapshot.' : 'Alerts will appear after a fleet is imported.'}</p>}
          <button className="overview-card-footer overview-text-link" onClick={() => onNavigate('inventory')}>Review source evidence <Glyph name="arrow" /></button>
        </section>
      </div>
      <div className="overview-bottom-grid">
        <section className="overview-card overview-comparison" aria-label="Actual recovery plan comparisons"><CardTitle title="Recovery plan comparison" action="Open optimizer" onClick={() => onNavigate('optimizer')} />
          {loading ? <div className="overview-chart-empty" role="status">Loading computed plan comparisons…</div> : planError ? <div className="overview-chart-empty" role="alert"><p>{planError}</p><button className="overview-text-link" onClick={() => setReload(value => value + 1)}>Retry plan data <Glyph name="arrow" /></button></div> : latest ? <Suspense fallback={<div className="overview-chart-empty" role="status">Loading comparison chart…</div>}><DashboardCharts plan={latest} parent={parent} /></Suspense> : <div className="overview-chart-empty"><Glyph name="plan" /><strong>No recovery plan calculated</strong><p>A chart will compare real solver and greedy results for the same inputs.</p><button className="overview-text-link" onClick={() => onNavigate('optimizer')}>Calculate first plan <Glyph name="arrow" /></button></div>}
          <div className={`overview-comparison-note ${stale ? 'overview-comparison-stale' : ''}`}><Glyph name={stale ? 'alert' : 'lock'} /><span>{stale ? 'Latest plan is stale or paused. Review a current revision before execution.' : 'Pinned inputs · hard resource limits · independently validated allocations'}</span></div>
        </section>
        <section className="overview-card overview-workflow" aria-label="Recovery workflow status"><CardTitle title="Recovery workflow" action="Open work orders" onClick={() => onNavigate('simulation')} />
          <p className="overview-note overview-workflow-context">{latest ? `Context ${latest.context_id} · ${latest.status} · simulation only` : 'Calculate and approve a plan to begin a tracked rehearsal.'}</p>
          <div className="overview-workflow-graph">
            <div className={`overview-workflow-node overview-workflow-approval ${latest?.status === 'approved' ? 'overview-node-done' : ''}`}><span className="overview-small-icon overview-purple"><Glyph name="lock" /></span><div><strong>Human approval</strong><small>{latest ? words(latest.status) : 'No plan yet'}</small><span>Exact plan revision</span></div></div>
            <span className="overview-workflow-connector overview-connector-first" aria-hidden="true" />
            <div className={`overview-workflow-node overview-workflow-extraction ${extraction.total > 0 && extraction.done === extraction.total ? 'overview-node-done' : ''}`}><span className="overview-small-icon overview-red"><Glyph name="extract" /></span><div><strong>Extraction &amp; removal</strong><small>{extraction.total ? `${extraction.done} / ${extraction.total} completed` : 'Waiting for work orders'}</small><span>Donor and displaced parts</span></div></div>
            <span className="overview-workflow-connector overview-connector-second" aria-hidden="true" />
            <div className={`overview-workflow-node overview-workflow-installation ${installation.total > 0 && installation.done === installation.total ? 'overview-node-done' : ''}`}><span className="overview-small-icon overview-blue"><Glyph name="install" /></span><div><strong>Installation</strong><small>{installation.total ? `${installation.done} / ${installation.total} completed` : 'Prerequisites required'}</small><span>One location per part</span></div></div>
            <span className="overview-workflow-connector overview-connector-third" aria-hidden="true" />
            <div className={`overview-workflow-node overview-workflow-verification ${verification.total > 0 && verification.done === verification.total ? 'overview-node-done' : ''}`}><span className="overview-small-icon overview-green"><Glyph name="check" /></span><div><strong>Verification</strong><small>{verification.total ? `${verification.done} / ${verification.total} simulated passes` : 'Checks and evidence required'}</small><span>Never a physical repair</span></div></div>
          </div><button className="overview-card-footer overview-text-link" onClick={() => onNavigate(latest ? 'simulation' : 'optimizer')}>{latest ? 'Review approval and execution' : 'Begin with a computed plan'} <Glyph name="arrow" /></button>
        </section>
      </div>
    </div>
    <aside className="overview-right-rail" aria-label="Recovery insights and activity">
      <section className="overview-card overview-insights"><CardTitle title="Recovery insights" action="View plan" onClick={() => onNavigate('optimizer')} />
        <div className="overview-insight"><span className="overview-small-icon overview-purple"><Glyph name="plan" /></span><div><strong>{latest ? `${latest.result.totals.usable_final} complete final configurations` : 'Fleet-wide planning'}</strong><p>{latest ? `${cash(latest.result.totals.cost_paise)} and ${latest.result.totals.technician_minutes} technician minutes from the latest ${latest.status} plan.` : 'Calculate a plan to compare real allocations, costs and technician effort.'}</p>{latest && <span className="overview-status-label overview-purple">{latest.result.solver.status}</span>}</div></div>
        <div className="overview-insight"><span className="overview-small-icon overview-green"><Glyph name="component" /></span><div><strong>{latest?.result.baseline?.totals ? 'Same-input greedy comparison' : 'Eligibility before allocation'}</strong><p>{latest?.result.baseline?.totals ? `Solver ${latest.result.totals.usable_final} usable · greedy ${latest.result.baseline.totals.usable_final} usable. Both use the same resource limits.` : 'Unknown or faulty parts remain excluded. Hardware compatibility and evidence are checked separately.'}</p><button className="overview-mini-button" onClick={() => onNavigate(latest ? 'optimizer' : 'compatibility')}>{latest ? 'Compare results' : 'Inspect compatibility'}</button></div></div>
        <div className="overview-insight"><span className="overview-small-icon overview-blue"><Glyph name="check" /></span><div><strong>Simulation and physical evidence</strong><p>{state.recovery?.simulated_passes ?? 0} recorded simulation passes. {state.recovery?.physical_passes ?? 0} physically verified repairs. AI diagnosis is not configured.</p><button className="overview-mini-button" onClick={() => onNavigate('diagnostics')}>Review evidence</button></div></div>
      </section>
      <section className="overview-card overview-activity" aria-label="Real system activity"><CardTitle title="System activity" action="View all" onClick={() => onNavigate('reports')} />
        {loading ? <p className="overview-inset-empty" role="status">Loading audit history…</p> : auditError ? <div className="overview-inset-empty" role="alert"><p>{auditError}</p><button className="overview-text-link" onClick={() => setReload(value => value + 1)}>Retry activity</button></div> : events.length ? <div className="overview-activity-list">{events.slice(0, 4).map(event => <div className="overview-activity-row" key={event.id}><span className={`overview-small-icon ${event.action.includes('failure') ? 'overview-red' : event.action.includes('verified') || event.action.includes('verification') ? 'overview-green' : 'overview-blue'}`}><Glyph name={event.action.includes('import') ? 'component' : event.action.includes('verification') ? 'check' : 'activity'} /></span><div><strong>{words(event.action)}</strong><small title={`${event.actor} · ${event.entity_id}`}>{event.actor} · {event.entity_id.length > 14 ? event.entity_id.slice(0, 14) + '…' : event.entity_id}</small></div><time dateTime={event.occurred_at}>{new Date(event.occurred_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time></div>)}</div> : <p className="overview-inset-empty">No audit events yet. Import and workflow actions will appear here.</p>}
        <p className="overview-note overview-audit-note">Persisted event times · no generated activity history</p>
      </section>
    </aside></div>
  </div>
}
