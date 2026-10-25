import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import type { Plan } from '../types'
import { Button } from './ui/button'
import { Badge, EmptyState, ErrorNotice, Loading, Panel } from './ui/primitives'
import './reports.css'

type AuditEvent = { id: number; action: string; entity_id: string; actor: string; occurred_at: string; data: Record<string, unknown> }
type AuditPage = { items: AuditEvent[]; total: number; offset: number; limit: number }
type ReportPlan = Plan & {
  snapshot?: { registration_hash?: string; inspection_rule_version?: string; engine_version?: string; file_hashes?: Record<string, string> }
  snapshot_hash?: string; output_hash?: string; assumptions?: string[]
  decisions?: { id: string; decision: string; actor: string; occurred_at: string; input_hash: string }[]
}
type AuditReport = { report_version: string; generated_at: string; mode: string; disclaimer: string; plan: ReportPlan; history: ReportPlan[]; audit_events: AuditEvent[]; physical_verified_repairs: number }
const human = (value: string) => value.replaceAll('_', ' ')
const money = (value: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(value / 100)
const recorded = (value: string) => {
  const date = new Date(value)
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

function ReportMark({ kind = 'document' }: { kind?: 'document' | 'check' | 'activity' | 'pin' }) {
  const paths = {
    document: 'M6 3h8l4 4v14H6V3m8 0v5h5M9 12h6m-6 4h6',
    check: 'M12 3l8 4v6c0 5-8 9-8 9S4 18 4 13V7l8-4m-4 9 3 3 5-6',
    activity: 'M3 12h4l3-8 4 16 3-8h4',
    pin: 'M9 3h6v5l3 4v2h-5v7h-2v-7H6v-2l3-4V3',
  }
  return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[kind]} /></svg>
}

export function ReportsView({ onNavigate }: { onNavigate: (page: string) => void }) {
  const [plans, setPlans] = useState<ReportPlan[]>([])
  const [selected, setSelected] = useState('')
  const [report, setReport] = useState<AuditReport | null>(null)
  const [audit, setAudit] = useState<AuditPage>({ items: [], total: 0, offset: 0, limit: 20 })
  const [action, setAction] = useState('')
  const [actions, setActions] = useState<string[]>([])
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [reportLoading, setReportLoading] = useState(false)
  const [auditLoading, setAuditLoading] = useState(false)
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)

  useEffect(() => {
    let active = true
    setLoading(true); setError('')
    api<{ items: ReportPlan[] }>('/plans').then(data => {
      if (!active) return
      setPlans(data.items)
      setSelected(old => data.items.some(p => p.id === old) ? old : data.items[0]?.id ?? '')
    }).catch(e => { if (active) setError((e as Error).message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [reload])

  useEffect(() => {
    let active = true
    if (!selected) { setReport(null); return }
    setReportLoading(true); setReport(null)
    api<AuditReport>(`/plans/${encodeURIComponent(selected)}/report`).then(data => { if (active) setReport(data) })
      .catch(e => { if (active) setError((e as Error).message) }).finally(() => { if (active) setReportLoading(false) })
    return () => { active = false }
  }, [selected, reload])

  useEffect(() => {
    let active = true
    setAuditLoading(true)
    api<AuditPage>(`/audit-events?limit=20&offset=${offset}${action ? `&action=${encodeURIComponent(action)}` : ''}`).then(data => {
      if (!active) return
      setAudit(data)
      setActions(old => [...new Set([...old, ...data.items.map(item => item.action)])].sort())
    }).catch(e => { if (active) setError((e as Error).message) }).finally(() => { if (active) setAuditLoading(false) })
    return () => { active = false }
  }, [action, offset, reload])

  const download = useCallback(() => {
    if (!report) return
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }))
    const anchor = document.createElement('a')
    anchor.href = url; anchor.download = `revivegraph-${report.plan.id}-audit.json`; anchor.click()
    URL.revokeObjectURL(url)
  }, [report])
  const plan = report?.plan
  const steps = plan?.work_orders.flatMap(order => order.steps) ?? []
  const completedSteps = steps.filter(step => step.status === 'done').length
  const simulatedPasses = plan?.work_orders.filter(order => order.verification?.outcome === 'pass').length

  return <div className="reports-workspace stack">
    {error && <ErrorNotice message={error}><p className="caption">Reports are read-only. Existing plan and work records are preserved.</p><Button variant="secondary" onClick={() => setReload(value => value + 1)}>Retry report connection</Button></ErrorNotice>}
    <div className="reports-toolbar"><label>Report plan<select aria-label="Report plan" value={selected} disabled={loading || !plans.length} onChange={event => { setError(''); setSelected(event.target.value) }}><option value="" disabled>No calculated plan</option>{plans.map(p => <option key={p.id} value={p.id}>{p.id.slice(0, 13)} · {p.context_id} · {p.status}</option>)}</select></label><Button variant="secondary" onClick={() => setReload(value => value + 1)}>Refresh reports</Button><Button disabled={!report || reportLoading} onClick={download}>Export audit JSON</Button></div>
    {loading && <Loading text="Loading persisted recovery reports…" />}
    {!loading && !plans.length && <EmptyState title="Your recovery record starts with a plan"><p>Import inventory and calculate a validated recovery plan. Its version pins, assumptions, allocation and later decisions will appear here.</p><Button className="mt-4" variant="secondary" onClick={() => onNavigate('optimizer')}>Open Recovery Optimizer</Button></EmptyState>}
    {reportLoading && <Loading text="Reading the selected plan and its audit history…" />}
    {report && plan && <>
      <div className="reports-metrics">
        <Panel className="reports-metric"><span className="reports-metric-icon blue"><ReportMark /></span><span>PLAN REVISIONS</span><strong>{report.history.length}</strong><small>Linked rehearsal history</small></Panel>
        <Panel className="reports-metric"><span className="reports-metric-icon violet"><ReportMark kind="activity" /></span><span>WORK PROGRESS</span><strong>{completedSteps}<em> / {steps.length}</em></strong><small>Recorded completed steps</small></Panel>
        <Panel className="reports-metric"><span className="reports-metric-icon green"><ReportMark kind="check" /></span><span>SIMULATED PASSES</span><strong>{simulatedPasses}</strong><small>Authored checks, not physical repairs</small></Panel>
        <Panel className="reports-metric"><span className="reports-metric-icon amber"><ReportMark kind="pin" /></span><span>PHYSICAL REPAIRS</span><strong>{report.physical_verified_repairs}</strong><small>Physical execution unavailable</small></Panel>
      </div>
      <div className="reports-main-grid">
        <Panel className="reports-record"><div className="reports-section-head"><h2>Recovery record</h2><Badge tone={plan.status === 'approved' ? 'success' : plan.status === 'stale' || plan.status === 'paused' ? 'error' : 'cyan'}>{plan.status}</Badge></div><div className="reports-record-summary"><div><span>Estimated cash</span><strong>{money(plan.result.totals.cost_paise)}</strong></div><div><span>Technician effort</span><strong>{plan.result.totals.technician_minutes}<small> min</small></strong></div><div><span>Usable final</span><strong>{plan.result.totals.usable_final}</strong></div></div><p className="caption">{plan.result.solver.status} · {plan.context_id} · inventory revision {plan.inventory_revision} · {plan.mode}</p><p className="reports-disclaimer">{report.disclaimer}</p><div className="reports-pin-grid"><div><span>PLAN ID</span><code>{plan.id}</code></div><div><span>SCENARIO</span><code>{plan.scenario_id}</code></div><div className="reports-wide-pin"><span>PINNED INPUT HASH</span><code>{plan.input_hash}</code></div></div><details><summary>Source and engine versions</summary><dl><dt>Registration hash</dt><dd className="hash">{plan.snapshot?.registration_hash ?? 'Not supplied'}</dd><dt>Inspection rules</dt><dd>{plan.snapshot?.inspection_rule_version ?? 'Not supplied'}</dd><dt>Allocation engine</dt><dd>{plan.result.solver.engine_version ?? plan.snapshot?.engine_version ?? 'Not supplied'}</dd><dt>Report version</dt><dd>{report.report_version}</dd><dt>Report read at</dt><dd><time dateTime={report.generated_at}>{recorded(report.generated_at)}</time></dd></dl></details><details><summary>Recorded model assumptions</summary><ul className="reports-assumptions">{plan.assumptions?.map(value => <li key={value}>{value}</li>)}</ul></details></Panel>
        <Panel className="reports-decisions"><div className="reports-section-head"><h2>Approval & verification</h2><ReportMark kind="check" /></div>{plan.decisions?.length ? plan.decisions.map(item => <div className="reports-decision" key={item.id}><Badge tone={item.decision === 'approve' ? 'success' : 'error'}>{item.decision === 'approve' ? 'Approved' : 'Rejected'}</Badge><p>{item.actor}</p><time dateTime={item.occurred_at}>{recorded(item.occurred_at)}</time><small>Exact input hash retained in exported evidence.</small></div>) : <div className="reports-no-record"><p>No decision recorded</p><small>This plan has not been approved for simulated work.</small></div>}<div className="reports-order-results">{plan.work_orders.length ? plan.work_orders.map(order => <div key={order.id}><span className="mono">{order.target_asset_id}</span><Badge tone={order.verification?.outcome === 'pass' ? 'success' : order.status === 'paused' ? 'error' : 'neutral'}>{order.verification ? `Simulated ${order.verification.outcome}` : human(order.status)}</Badge></div>) : <p className="caption">No work orders created for this plan.</p>}</div><Button variant="secondary" onClick={() => onNavigate('simulation')}>Open simulation workflow</Button></Panel>
      </div>
      <Panel className="reports-ledger"><div className="reports-section-head"><h2>Operation ledger</h2><span className="caption">{plan.result.operations.length} estimated operations · integer resource accounting</span></div><div className="table-scroll"><table aria-label="Report operation ledger"><thead><tr><th>Operation</th><th>Computer</th><th>Component</th><th>Cash</th><th>Minutes</th></tr></thead><tbody>{plan.result.operations.map((item, index) => <tr key={`${item.operation}-${item.component_id}-${index}`}><td>{human(item.operation)}</td><td className="mono">{item.asset_id}</td><td className="mono">{item.component_id ?? '—'}</td><td>{money(item.cost_paise)}</td><td>{item.technician_minutes}</td></tr>)}</tbody></table>{!plan.result.operations.length && <p className="caption reports-table-empty">No operations are required by this allocation.</p>}</div></Panel>
    </>}
    <Panel className="reports-audit"><div className="reports-section-head"><div><h2>System activity</h2><p className="caption">Actual recorded fleet events · newest first</p></div><label><span className="sr-only">Audit event type</span><select aria-label="Audit event type" value={action} onChange={event => { setOffset(0); setAction(event.target.value) }}><option value="">All event types</option>{actions.map(value => <option key={value} value={value}>{human(value)}</option>)}</select></label></div>{auditLoading ? <Loading text="Reading recorded audit events…" /> : audit.items.length ? <div className="reports-activity-list">{audit.items.map(item => <article key={item.id}><span className={`reports-event-icon ${item.action.includes('failure') || item.action.includes('rejected') ? 'red' : item.action.includes('completed') || item.action.includes('verification') ? 'green' : 'blue'}`}><ReportMark kind="activity" /></span><div><strong>{human(item.action)}</strong><p><code>{item.entity_id}</code><span> · {item.actor}</span></p><details><summary>Event details</summary><pre className="json-detail">{JSON.stringify(item.data, null, 2)}</pre></details></div><time dateTime={item.occurred_at} title={item.occurred_at}>{recorded(item.occurred_at)}</time></article>)}</div> : <div className="reports-no-record"><p>No recorded events{action ? ' of this type' : ''}</p><small>Import a fleet or complete a recovery action to create an audit record.</small></div>}<div className="reports-pagination"><span className="caption">{audit.total ? `${offset + 1}–${Math.min(offset + audit.items.length, audit.total)} of ${audit.total}` : '0 events'}</span><div><Button variant="secondary" disabled={auditLoading || offset === 0} onClick={() => setOffset(value => Math.max(0, value - 20))}>Previous events</Button><Button variant="secondary" disabled={auditLoading || offset + audit.items.length >= audit.total} onClick={() => setOffset(value => value + 20)}>Next events</Button></div></div></Panel>
  </div>
}
