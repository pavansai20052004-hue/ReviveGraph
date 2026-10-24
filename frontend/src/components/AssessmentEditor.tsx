import { useEffect, useState } from 'react'
import { api, jsonMutation } from '../api'
import type { Assessment } from '../types'
import { Button } from './ui/button'
import { Badge, ErrorNotice } from './ui/primitives'

type History = { current_assessment_id: string; items: (Assessment & { id: string; health: string; notes?: string })[] }

export function AssessmentEditor({ kind, subjectId, revision, onChanged }: {
  kind: 'computer' | 'component'; subjectId: string; revision: number; onChanged: () => Promise<void>
}) {
  const [history, setHistory] = useState<History | null>(null)
  const [health, setHealth] = useState('unknown')
  const [source, setSource] = useState('')
  const [reference, setReference] = useState('synthetic:')
  const [notes, setNotes] = useState('')
  const [ack, setAck] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const path = `/assessments/${kind}/${subjectId}`
  useEffect(() => {
    let current = true
    setHistory(null); setError(''); setAck(false); setSource(''); setReference('synthetic:'); setNotes('')
    api<History>(path).then(value => { if (current) { setHistory(value); setHealth(value.items.at(-1)?.health ?? 'unknown') } }).catch(e => { if (current) setError((e as Error).message) })
    return () => { current = false }
  }, [path, revision])
  async function save() {
    if (!history || !ack || busy) return
    setBusy(true); setError('')
    try {
      await api(path, jsonMutation({ health, expected_revision: revision, expected_assessment_id: history.current_assessment_id,
        source, evidence_ref: reference, notes, simulation_only: true }, crypto.randomUUID()))
      await onChanged()
    } catch (e) { setError((e as Error).message) } finally { setBusy(false) }
  }
  return <details className="evidence" aria-label="Synthetic assessment authoring">
    <summary>Assessment history and synthetic authoring</summary>
    <div className="stack">
      <Badge tone="warning">Simulation assertions only</Badge>
      <p className="caption">Author a synthetic scenario assertion before approving or recording work. Original import evidence remains in history. This cannot certify physical health or record technician review.</p>
      {error && <ErrorNotice message={error} />}
      {!history ? <p role="status">Loading assessment history…</p> : <>
        <ol className="reason-list">{history.items.map(item => <li key={item.id}><span>{item.health} · {item.source ?? 'Original imported assertion'}<small className="caption">{item.recorded_value ?? 'Date unknown'} · {item.supplied_author_label ?? 'Author not supplied'} · {item.evidence_ref ?? 'No base evidence reference'}</small></span></li>)}</ol>
        <label>Authored synthetic health<select aria-label="Authored synthetic health" value={health} onChange={e => setHealth(e.target.value)} disabled={busy}><option value="healthy">Healthy (synthetic assertion)</option><option value="faulty">Faulty (synthetic assertion)</option><option value="unknown">Unknown</option></select></label>
        <label>Authored source<input aria-label="Authored source" value={source} maxLength={200} onChange={e => setSource(e.target.value)} disabled={busy} /></label>
        <label>Synthetic evidence reference<input aria-label="Synthetic assessment evidence reference" value={reference} maxLength={2000} onChange={e => setReference(e.target.value)} disabled={busy} /></label>
        <label>Assessment notes<textarea aria-label="Assessment notes" value={notes} maxLength={2000} onChange={e => setNotes(e.target.value)} disabled={busy} /></label>
        <label className="checkbox-line"><input type="checkbox" checked={ack} onChange={e => setAck(e.target.checked)} disabled={busy} />I am authoring a synthetic assertion, not a physical assessment.</label>
        <Button variant="secondary" disabled={busy || !ack || !source.trim() || !reference.startsWith('synthetic:') || !reference.slice(10).trim()} onClick={() => void save()}>{busy ? 'Saving authored assertion…' : 'Save synthetic assessment'}</Button>
      </>}
    </div>
  </details>
}
