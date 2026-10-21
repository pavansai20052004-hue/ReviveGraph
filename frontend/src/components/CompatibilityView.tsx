import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { api, jsonMutation } from '@/api'
import type { Compatibility, Component, Computer, Configuration } from '@/types'
import { Button } from './ui/button'
import { Badge, EmptyState, ErrorNotice, HealthBadge, Loading, Panel } from './ui/primitives'
const InspectionGraph = lazy(() => import('./InspectionGraph').then(module => ({ default: module.InspectionGraph })))

export function CompatibilityView({ computers, components, target, onTargetChange }: { computers: Computer[]; components: Component[]; target: string; onTargetChange: (id: string) => void }) {
  const [result, setResult] = useState<Compatibility | null>(null)
  const [selected, setSelected] = useState('')
  const [mode, setMode] = useState('simulation')
  const [type, setType] = useState('all')
  const [decision, setDecision] = useState('all')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)
  const [ram, setRam] = useState<string[]>([])
  const [storage, setStorage] = useState('')
  const [configuration, setConfiguration] = useState<Configuration | null>(null)
  const [checking, setChecking] = useState(false)
  const selectionKey = JSON.stringify([target, mode, ram, storage])
  const latestSelection = useRef(selectionKey)
  latestSelection.current = selectionKey

  useEffect(() => {
    if (!target) return
    let active = true
    setLoading(true); setError(''); setResult(null); setConfiguration(null); setRam([]); setStorage('')
    api<Compatibility>(`/compatibility?target_asset_id=${encodeURIComponent(target)}&mode=${mode}`).then(data => {
      if (!active) return
      setResult(data); setSelected(data.items[0]?.component_id ?? '')
    }).catch(e => { if (active) setError(e.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [target, mode, reload])

  async function inspect() {
    const inputKey = selectionKey
    setChecking(true); setError('')
    try {
      const response = await api<Configuration>('/compatibility/configuration', jsonMutation({ target_asset_id: target, ram_component_ids: ram, storage_component_id: storage, mode }))
      if (latestSelection.current === inputKey) setConfiguration(response)
    }
    catch (e) { if (latestSelection.current === inputKey) setError((e as Error).message) } finally { setChecking(false) }
  }
  if (!computers.length) return <EmptyState title="Import a fleet before inspecting compatibility">The registered board rules will be checked against each imported physical part.</EmptyState>
  const edge = result?.items.find(item => item.component_id === selected)
  const filtered = result?.items.filter(item => (type === 'all' || item.type === type) && (decision === 'all' || item.hardware.decision === decision)) ?? []
  return <>
    <div className="filter-bar">
      <label>Target computer<select aria-label="Target computer" value={target} onChange={e => onTargetChange(e.target.value)}>{computers.map(c => <option key={c.asset_id}>{c.asset_id}</option>)}</select></label>
      <label>Component type<select value={type} onChange={e => setType(e.target.value)}><option value="all">All removable parts</option><option value="ram">RAM</option><option value="storage">Storage</option></select></label>
      <label>Hardware decision<select value={decision} onChange={e => setDecision(e.target.value)}><option value="all">All decisions</option><option>compatible</option><option>incompatible</option><option>unknown</option></select></label>
      <label>Eligibility mode<select aria-label="Eligibility mode" value={mode} onChange={e => setMode(e.target.value)}><option value="simulation">Simulation</option><option value="physical">Physical eligibility check</option></select></label>
    </div>
    {error && <ErrorNotice message={error}><Button variant="secondary" onClick={() => setReload(r => r + 1)}>Retry inspection</Button></ErrorNotice>}
    {loading && <Loading text="Evaluating declared hardware rules…" />}
    {result && <div className="inventory-split compatibility-split">
      <div className="stack">
        <Panel className="p-5"><span className="eyebrow">TARGET PROFILE · DETERMINISTIC RULES</span><h2>{target}</h2><p className="muted">{result.profile.id} · v{result.profile.version} · {result.profile.ram_generation ?? 'Unknown RAM'} UDIMM</p>
          <div className="inline-badges"><Badge tone="cyan">{result.rule_version}</Badge><Badge>Base: {result.target_base_health}</Badge></div>
          <p className="caption">Compatibility checks declared hardware. Health, owner and availability are checked separately. A faulty or unknown base cannot be a recovered target.</p>
          <Suspense fallback={<Loading text="Loading graph controls…" />}><InspectionGraph result={result} items={filtered} components={components} selected={selected} onSelect={setSelected} /></Suspense>
        </Panel>
        <div className="table-scroll panel table-panel" tabIndex={0} role="region" aria-label="Compatibility decision table"><table><caption className="sr-only">Deterministic compatibility decisions and separate eligibility</caption><thead><tr><th>Component ID</th><th>Hardware</th><th>Eligibility</th><th>Current location</th></tr></thead><tbody>{filtered.map(item => <tr key={item.component_id} className={selected === item.component_id ? 'selected-row' : ''}><td><button className="text-link mono" onClick={() => setSelected(item.component_id)} aria-pressed={selected === item.component_id}>{item.component_id}</button></td><td><HealthBadge value={item.hardware.decision} /></td><td><Badge tone={item.eligibility.eligible ? 'success' : 'warning'}>{item.eligibility.eligible ? 'Eligible candidate' : 'Not eligible'}</Badge></td><td>{components.find(p => p.component_id === item.component_id)?.location_asset_id ?? 'Stock'}</td></tr>)}</tbody></table>{!filtered.length && <p className="p-5 muted">No decisions match these filters. Choose “All decisions” to reset.</p>}</div>
        <p className="caption">{filtered.length} of {result.items.length} decisions · no parts allocated or reserved</p>
        <Panel className="p-5 stack" aria-label="Complete configuration inspection"><span className="eyebrow">COMPLETE CONFIGURATION INSPECTION</span><h2>Check a RAM set and storage</h2><p className="muted">Individual edges do not prove that a complete module set fits the slots or mixed-module rules.</p>
          <details><summary>Select RAM modules ({ram.length} selected)</summary><div className="checkbox-grid">{components.filter(p => p.type === 'ram').map(part => <label key={part.component_id}><input type="checkbox" checked={ram.includes(part.component_id)} onChange={e => { setRam(old => e.target.checked ? [...old, part.component_id] : old.filter(id => id !== part.component_id)); setConfiguration(null) }} />{part.component_id} · {part.ram_generation} · {part.capacity_gib ?? '?'} GiB</label>)}</div></details>
          <label>Storage device<select aria-label="Configuration storage" value={storage} onChange={e => { setStorage(e.target.value); setConfiguration(null) }}><option value="">Choose a drive</option>{components.filter(p => p.type === 'storage').map(p => <option key={p.component_id} value={p.component_id}>{p.component_id} · {p.capacity_gb ?? '?'} GB · {p.health}</option>)}</select></label>
          <div><Button variant="secondary" disabled={!storage || !ram.length || checking} onClick={inspect}>{checking ? 'Checking…' : 'Inspect configuration'}</Button></div>
          {configuration && <div aria-live="polite"><Badge tone={configuration.eligible_configuration ? 'success' : 'warning'}>{configuration.eligible_configuration ? 'Eligible simulation configuration' : 'Configuration blocked'}</Badge><ul className="reason-list">{[...configuration.ram.reasons, ...configuration.storage.reasons, ...configuration.target_eligibility_reasons, ...configuration.part_eligibility.flatMap(p => p.reasons.map(r => ({ ...r, message: `${p.component_id}: ${r.message}` })))].map((r, i) => <li key={i}><code>{r.code}</code><span>{r.message}</span></li>)}</ul><p className="caption">Base: {configuration.target_base_health}. {configuration.note}</p></div>}
        </Panel>
      </div>
      <Panel className="detail-panel" aria-label="Selected compatibility decision">
        <span className="eyebrow">SELECTED DECISION</span>
        {edge ? <><h2 className="mono">{edge.component_id}</h2><p className="muted">→ {target}</p><HealthBadge value={edge.hardware.decision} /><ul className="reason-list">{edge.hardware.reasons.map(r => <li key={r.code}><code>{r.code}</code><span>{r.message}</span></li>)}</ul><hr /><h3>Allocation eligibility</h3><Badge tone={edge.eligibility.eligible ? 'success' : 'warning'}>{edge.eligibility.eligible ? 'Eligible candidate' : 'Not eligible'}</Badge><ul className="reason-list">{edge.eligibility.reasons.map(r => <li key={r.code}><code>{r.code}</code><span>{r.message}</span></li>)}</ul><p className="caption">{edge.eligibility.note}</p><dl><dt>Health</dt><dd>{edge.eligibility.health}</dd><dt>Availability</dt><dd>{edge.eligibility.availability}</dd><dt>Part evidence</dt><dd>{edge.evidence_ref}</dd><dt>Profile evidence</dt><dd>{edge.profile_evidence_ref}</dd><dt>Registration hash</dt><dd className="hash">{result.registration_hash}</dd></dl></> : <p className="muted">Choose a component decision.</p>}
      </Panel>
    </div>}
  </>
}
