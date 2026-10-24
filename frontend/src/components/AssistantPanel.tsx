import { useEffect, useRef, useState } from 'react'
import { api, jsonMutation } from '../api'
import type { Plan } from '../types'
import { Button } from './ui/button'
import { Badge, ErrorNotice, Loading, Panel } from './ui/primitives'

type Fact = { id: string; text: string; data: unknown }
type Answer = { label: string; provider: string; asset_id?: string | null; recorded_at: string; actor: string; input_hash: string; output_hash: string; facts: Fact[]; plan_status_at_response: string; provider_evidence: { response_id?: string; usage?: unknown } }

export function AssistantPanel({ assetId }: { assetId: string }) {
  const [plans, setPlans] = useState<Plan[]>([])
  const [selected, setSelected] = useState('')
  const [question, setQuestion] = useState('Review selected components, blockers and recorded failure changes.')
  const [answer, setAnswer] = useState<Answer | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('Loading saved plans…')
  const keys = useRef(new Map<string, string>())
  const currentView = useRef('')
  currentView.current = selected + ':' + assetId
  useEffect(() => {
    let active = true
    api<{ items: Plan[] }>('/plans').then(p => {
      if (!active) return
      setPlans(p.items)
      const saved = sessionStorage.getItem('revivegraph-plan')
      setSelected(p.items.find(x => x.id === saved)?.id ?? p.items[0]?.id ?? '')
    }).catch(e => active && setError((e as Error).message)).finally(() => active && setBusy(''))
    return () => { active = false }
  }, [])
  useEffect(() => {
    setAnswer(null)
    if (!selected) return
    let active = true
    // History comes from the actual persisted audit, never a synthetic conversation.
    api<{ audit_events: { action: string; entity_id: string; data: Answer }[] }>(`/plans/${selected}/report`).then(r => {
      if (active) setAnswer(r.audit_events.filter(e => e.action === 'assistant_explanation' && e.entity_id === selected && e.data.asset_id === (assetId || null)).at(-1)?.data ?? null)
    }).catch(e => active && setError((e as Error).message))
    return () => { active = false }
  }, [selected, assetId])
  async function ask() {
    setError(''); setBusy('Reading validated plan evidence...')
    const body = { question, provider: 'facts', ...(assetId ? { asset_id: assetId } : {}) }
    const view = selected + ':' + assetId
    const fingerprint = selected + JSON.stringify(body)
    let key = keys.current.get(fingerprint)
    if (!key) { key = crypto.randomUUID(); keys.current.set(fingerprint, key) }
    try {
      const result = await api<Answer>(`/plans/${selected}/assistant`, { ...jsonMutation(body, key), signal: AbortSignal.timeout(30000) })
      if (currentView.current === view) setAnswer(result)
    } catch (e) { if (currentView.current === view) setError((e as Error).message) } finally { setBusy('') }
  }
  const plan = plans.find(p => p.id === selected)
  return <Panel className="p-5 stack assistant-panel" aria-label="Grounded recovery assistant">
    <span className="eyebrow">PLAN EVIDENCE — SEPARATE FROM ASSESSMENTS</span>
    <h2>Explain the actual recovery plan</h2>
    <p className="muted">Review independently checked allocations, blockers and recorded failure changes from a saved plan. This summary is deterministic and makes no AI request. Physical repairs: 0.</p>
    <Badge>Local evidence only - no external AI provider</Badge>
    {error && <ErrorNotice message={error} />}
    {busy && <Loading text={busy} />}
    {plans.length ? <>
      <label>Assistant plan<select aria-label="Assistant plan" value={selected} disabled={!!busy} onChange={e => setSelected(e.target.value)}>{plans.map(p => <option key={p.id} value={p.id}>{p.id.slice(0, 13)} · {p.status} · {p.context_id}</option>)}</select></label>
      {plan && <p className="caption">Pinned input <span className="hash">{plan.input_hash}</span> · status {plan.status}. {assetId && `Inspecting ${assetId}.`} Stale plans are historical evidence and cannot authorize work.</p>}
      <label>Review note<textarea aria-label="Review note" maxLength={1500} rows={3} value={question} onChange={e => setQuestion(e.target.value)} /></label>
      <div className="button-row"><Button variant="secondary" disabled={!!busy || !question.trim()} onClick={() => ask()}>Read local evidence</Button></div>
      <p className="caption">The review note is stored with a fixed plan/asset summary. It does not trigger natural-language interpretation, a provider request or account charges.</p>
    </> : !busy && <p className="muted">Import inventory and calculate a recovery plan first. Then return here to inspect its saved facts.</p>}
    {answer && <div className="stack" role="region" aria-label="Saved assistant answer">
      <h3>{answer.provider === 'facts' ? answer.label : 'Historical explanation - external provider removed'}</h3><p className="caption">Recorded {new Date(answer.recorded_at).toLocaleString()} · {answer.actor} · status at response {answer.plan_status_at_response}</p>
      {answer.facts.map(f => <div key={f.id} className="stack"><p>{f.text}</p><details><summary>Source fact: {f.id}</summary><pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify(f.data, null, 2)}</pre></details></div>)}
      <details><summary>Response evidence</summary><p className="hash">Input {answer.input_hash}<br />Output {answer.output_hash}</p><pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify(answer.provider_evidence, null, 2)}</pre></details>
    </div>}
    <p className="caption">Synthetic assessment authoring is available in Inventory before approval. AI and physical diagnosis remain deferred. This evidence summary cannot approve a plan, change health or record work.</p>
  </Panel>
}
