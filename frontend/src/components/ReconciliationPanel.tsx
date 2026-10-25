import { useCallback, useEffect, useRef, useState } from 'react'
import { api, jsonMutation } from '../api'
import type { Plan } from '../types'
import { Button } from './ui/button'
import { Badge, ErrorNotice, Loading, Panel } from './ui/primitives'

const money = (value: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(value / 100)
type Preview = {
  source_state_hash: string; consumed: { cost_paise: number; technician_minutes: number };
  remaining_limits: { budget_paise: number; time_minutes: number };
  original_limits: { budget_paise: number; time_minutes: number };
  locations: Record<string, string | null>; failed_component_ids: string[];
  consumed_operations: { operation: string; component_id?: string; asset_id: string; evidence_ref: string }[];
  preparation_policy: string; counting_policy: string; continuation_plan_id?: string | null;
}

export function ContinuationAccounting({ plan }: { plan: Plan }) {
  const value = plan.resource_accounting
  if (!value) return null
  return <Panel className="p-5 stack" aria-label="Continuation resource accounting">
    <span className="eyebrow">REVIEWED SIMULATION CONTINUATION</span>
    <h2>Original limits still apply</h2>
    <div className="resource-headroom">
      <div><span>Previously recorded work</span><strong>{money(value.consumed.cost_paise)} · {value.consumed.technician_minutes} min</strong></div>
      <div><span>This plan’s remaining limits</span><strong>{money(value.remaining_limits.budget_paise)} · {value.remaining_limits.time_minutes} min</strong></div>
      <div><span>Recorded work + proposed work</span><strong>{money(value.cumulative_projected.cost_paise)} · {value.cumulative_projected.technician_minutes} min</strong><span>Original ceiling: {money(value.original_limits.budget_paise)} · {value.original_limits.time_minutes} min</span></div>
    </div>
    <p className="caption">Saved simulated locations carry forward; completed component movements are not replayed. Preparation and verification are conservatively charged again for interrupted targets. A new exact-plan approval is required. Recovery counts refer to this snapshot and must not be added across revisions.</p>
  </Panel>
}

export function ReconciliationPanel({ planId, onChanged }: { planId: string; onChanged: (id: string) => Promise<void> }) {
  const [preview, setPreview] = useState<Preview | null>(null)
  const [reference, setReference] = useState('synthetic:')
  const [reviewed, setReviewed] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const key = useRef<{ fingerprint: string; value: string } | null>(null)
  const load = useCallback(async () => {
    setBusy(true); setError(''); setReviewed(false)
    try { setPreview(await api<Preview>(`/plans/${planId}/reconciliation-preview`)) } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }, [planId])
  useEffect(() => { void load() }, [load])
  async function continueWork() {
    if (!preview || !reviewed || busy) return
    const body = { source_state_hash: preview.source_state_hash, reviewed: true, evidence_ref: reference }
    const fingerprint = `${planId}:${JSON.stringify(body)}`
    const storageKey = `revivegraph-reconcile:${fingerprint}`
    if (key.current?.fingerprint !== fingerprint) {
      const value = sessionStorage.getItem(storageKey) ?? crypto.randomUUID()
      key.current = { fingerprint, value }; sessionStorage.setItem(storageKey, value)
    }
    setBusy(true); setError('')
    try {
      const result = await api<Plan>(`/plans/${planId}/reconcile`, { ...jsonMutation(body, key.current.value), signal: AbortSignal.timeout(120000) })
      await onChanged(result.id)
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  return <Panel id="recovery-reconciliation" className="p-5 stack" aria-label="Paused work reconciliation">
    <span className="eyebrow">EXPLICIT REVIEW REQUIRED</span><h2>Reconcile interrupted simulated work</h2>
    <Badge tone="warning">Old work remains paused · old approval cannot resume it</Badge>
    <p>Review saved locations, completed evidence and resource usage. A continuation uses the local solver and needs fresh approval before any work can proceed.</p>
    {error && <ErrorNotice message={error} />}{busy && <Loading text="Reading or calculating continuation…" />}
    <Button variant="secondary" disabled={busy} onClick={() => void load()}>Refresh reconciliation preview</Button>
    {preview && <>
      <dl><dt>Original limits</dt><dd>{money(preview.original_limits.budget_paise)} · {preview.original_limits.time_minutes} min</dd>
        <dt>Recorded synthetic operation charges</dt><dd>{money(preview.consumed.cost_paise)} · {preview.consumed.technician_minutes} min</dd>
        <dt>Remaining hard limits</dt><dd>{money(preview.remaining_limits.budget_paise)} · {preview.remaining_limits.time_minutes} min</dd>
        <dt>Excluded failed parts</dt><dd>{preview.failed_component_ids.join(', ')}</dd></dl>
      <details><summary>Preserved operation evidence ({preview.consumed_operations.length})</summary><ul className="reason-list">{preview.consumed_operations.map((op, i) => <li key={i}><span>{op.operation.replaceAll('_', ' ')} · {op.component_id ?? op.asset_id}<small className="caption">{op.evidence_ref}</small></span></li>)}</ul></details>
      <details><summary>Saved simulated component locations</summary><div className="table-scroll"><table><thead><tr><th>Component</th><th>Simulation location</th></tr></thead><tbody>{Object.entries(preview.locations).map(([id, location]) => <tr key={id}><td className="mono">{id}</td><td>{location ?? 'Stock / extracted'}</td></tr>)}</tbody></table></div></details>
      <p className="caption">{preview.preparation_policy} {preview.counting_policy}</p>
      {preview.continuation_plan_id ? <Button onClick={() => void onChanged(preview.continuation_plan_id!)}>Open saved continuation plan</Button> : <>
        <label>Reconciliation simulation evidence reference<input aria-label="Reconciliation simulation evidence reference" value={reference} maxLength={2000} onChange={e => setReference(e.target.value)} disabled={busy} /></label>
        <label className="checkbox-line"><input type="checkbox" checked={reviewed} onChange={e => setReviewed(e.target.checked)} disabled={busy} />I reviewed the saved simulated locations, completed evidence and remaining limits.</label>
        <Button disabled={busy || !reviewed || !reference.startsWith('synthetic:') || !reference.slice(10).trim()} onClick={() => void continueWork()}>Calculate reviewed continuation</Button>
      </>}
    </>}
  </Panel>
}
