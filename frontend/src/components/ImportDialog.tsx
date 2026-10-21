import * as Dialog from '@radix-ui/react-dialog'
import { useEffect, useRef, useState } from 'react'
import { api, jsonMutation, mutationHeaders } from '@/api'
import type { Batch, Registration } from '@/types'
import { Button } from './ui/button'
import { Badge, ErrorNotice, Loading, Panel } from './ui/primitives'
import { Icon } from './ui/Icon'

export function ImportDialog({ open, onOpenChange, onImported }: { open: boolean; onOpenChange: (open: boolean) => void; onImported: () => Promise<void> }) {
  const [registration, setRegistration] = useState<Registration | null>(null)
  const [computers, setComputers] = useState<File | null>(null)
  const [components, setComponents] = useState<File | null>(null)
  const [batch, setBatch] = useState<Batch | null>(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const key = useRef(crypto.randomUUID())

  useEffect(() => {
    if (!open) return
    let active = true
    api<{ items: Registration[] }>('/fixture-registrations').then(data => { if (active) setRegistration(current => current ?? data.items[0] ?? null) }).catch(e => { if (active) setError(e.message) })
    return () => { active = false }
  }, [open])

  async function action(label: string, fn: () => Promise<void>) {
    setBusy(label); setError('')
    try { await fn() } catch (e) { setError((e as Error).message) } finally { setBusy('') }
  }
  function clearPreview() { setBatch(null); key.current = crypto.randomUUID() }
  async function register() {
    await action('Registering immutable fixture…', async () => {
      setRegistration(await api<Registration>('/fixture-registrations', jsonMutation({ fixture_id: 'revivegraph-synthetic-v1' })))
    })
  }
  async function bundledFiles() {
      const responses = await Promise.all(['computers.csv', 'components.csv'].map(name => fetch(`/api/v1/bundled-fixture/${name}`, { signal: AbortSignal.timeout(15000) })))
      if (responses.some(r => !r.ok)) throw new Error('Bundled CSV files could not be loaded. Check datasets/synthetic-v1 and retry.')
      const blobs = await Promise.all(responses.map(r => r.blob()))
      return [new File([blobs[0]], 'computers.csv', { type: 'text/csv' }), new File([blobs[1]], 'components.csv', { type: 'text/csv' })] as const
  }
  async function bundled() {
    await action('Loading the disclosed CSV files…', async () => {
      const [assets, parts] = await bundledFiles()
      setComputers(assets); setComponents(parts); clearPreview()
    })
  }
  async function previewFiles(rules: Registration, assets: File, parts: File) {
    const data = new FormData()
    data.set('registration_id', rules.id); data.set('fleet_id', 'RG-DEMO-12'); data.set('mode', 'simulation')
    data.set('computers_file', assets); data.set('components_file', parts)
    return api<Batch>('/imports/preview', { method: 'POST', headers: mutationHeaders(), body: data })
  }
  async function prepareDemo() {
    await action('Preparing and validating the synthetic demo preview…', async () => {
      setBatch(null)
      const rules = registration ?? await api<Registration>('/fixture-registrations', jsonMutation({ fixture_id: 'revivegraph-synthetic-v1' }))
      setRegistration(rules)
      const [assets, parts] = await bundledFiles()
      setComputers(assets); setComponents(parts)
      setBatch(await previewFiles(rules, assets, parts)); key.current = crypto.randomUUID()
    })
  }
  async function preview() {
    if (!registration || !computers || !components) return
    await action('Validating both CSV files…', async () => {
      setBatch(await previewFiles(registration, computers, components)); key.current = crypto.randomUUID()
    })
  }
  async function commit() {
    if (!batch) return
    await action('Committing inventory atomically…', async () => {
      const committed = await api<Batch>(`/imports/${batch.batch_id}/commit`, jsonMutation({ preview_hash: batch.preview_hash, expected_revision: batch.expected_revision }, key.current))
      setBatch(committed)
      await onImported()
    })
  }

  return <Dialog.Root open={open} onOpenChange={value => { if (!busy) onOpenChange(value) }}>
    <Dialog.Portal><Dialog.Overlay className="dialog-overlay" /><Dialog.Content className="dialog-content">
      <div className="dialog-heading"><div><span className="eyebrow">BULK CSV IMPORT · SIMULATION</span><Dialog.Title>Review before inventory changes</Dialog.Title></div><Dialog.Close asChild><Button variant="ghost" aria-label="Close import dialog" disabled={!!busy}>✕</Button></Dialog.Close></div>
      <Dialog.Description className="muted">Register versioned rules, preview both files, then commit the reviewed batch. Preview writes no inventory.</Dialog.Description>
      <Panel className="demo-import-guide" aria-label="Guided synthetic demo"><span className="demo-import-symbol"><Icon name="play" size={24} /></span><div><strong>Start with the 12-computer demo</strong><p>Use the disclosed synthetic fleet and 31 component records. No broken computers are needed. This prepares a preview; you decide whether to import it.</p><Button disabled={!!busy} onClick={prepareDemo}><Icon name="clipboard" size={16} />Prepare demo preview</Button></div></Panel>
      <Panel className="import-step"><div className="step-heading"><strong>01 · Register the fixture</strong>{registration && <Badge tone="success">Registered · v{registration.version}</Badge>}</div>
        {registration ? <><p>{registration.profile_count} toy board profiles and operation assumptions are pinned.</p><details><summary>Content hashes</summary><dl>{Object.entries(registration.file_hashes).map(([name, hash]) => <div key={name}><dt>{name}</dt><dd className="hash">{hash}</dd></div>)}</dl><p className="caption">scenarios.json is preparation evidence only. No handwritten allocation is served as a solver result.</p></details></> : <><p className="muted">Use the disclosed synthetic-v1 profiles, manifest and resource assumptions.</p><Button variant="secondary" onClick={register} disabled={!!busy}>Register synthetic-v1</Button></>}
      </Panel>
      <Panel className="import-step"><div className="step-heading"><strong>02 · Select both CSV files</strong><Button variant="secondary" onClick={bundled} disabled={!registration || !!busy}>Use bundled CSV pair</Button></div>
        <div className="file-inputs"><label>Computers CSV<input aria-label="Computers CSV" type="file" accept=".csv,text/csv" disabled={!!busy} onChange={e => { setComputers(e.target.files?.[0] ?? null); clearPreview() }} /><span className="caption">{computers?.name ?? 'No file selected'}</span></label><label>Components CSV<input aria-label="Components CSV" type="file" accept=".csv,text/csv" disabled={!!busy} onChange={e => { setComponents(e.target.files?.[0] ?? null); clearPreview() }} /><span className="caption">{components?.name ?? 'No file selected'}</span></label></div>
        <p className="caption">UTF-8 · schema v1 · up to 1 MiB and 1,000 rows per file · local demo operator</p>
        <Button variant="secondary" disabled={!registration || !computers || !components || !!busy} onClick={preview}>Preview both files</Button>
      </Panel>
      {busy && <Loading text={busy} />}
      {error && <ErrorNotice message={error}><p className="caption">A failed commit keeps the same preview and retry key. Refresh the preview if the fleet revision changed.</p></ErrorNotice>}
      {batch && <Panel className="import-step" aria-live="polite"><div className="step-heading"><strong>03 · {batch.committed ? 'Batch committed' : 'Review preview'}</strong><Badge tone={batch.valid ? 'success' : 'error'}>{batch.valid ? batch.committed ? 'Imported' : 'Validation passed' : `${batch.errors.length} blocking errors`}</Badge></div>
        <p>{batch.counts.computers} computers · {batch.counts.components} physical component IDs · {batch.committed ? `revision ${batch.revision}` : `expected revision ${batch.expected_revision}`}</p>
        {!batch.valid && <div className="table-scroll"><table><thead><tr><th>File / row</th><th>Field</th><th>Correction needed</th></tr></thead><tbody>{batch.errors.map((e, i) => <tr key={i}><td>{e.file}:{e.row}</td><td><code>{e.field}</code></td><td>{e.message}<small>{e.code}</small></td></tr>)}</tbody></table></div>}
        {batch.valid && <details><summary>Inspect normalized preview records</summary><div className="preview-records">{batch.preview.computers.map(row => <p key={row.asset_id}><code>{row.asset_id}</code> · {row.base_health} base · {row.board_profile_id}</p>)}{batch.preview.components.map(row => <p key={row.component_id}><code>{row.component_id}</code> · {row.health} · {row.location_asset_id || 'Stock'}</p>)}</div></details>}
        <p className="caption">Unknown evidence remains unknown. Synthetic assertions are simulation-only; import does not record a technician approval.</p>
        {batch.committed ? <Button onClick={() => onOpenChange(false)}>View imported inventory</Button> : <Button onClick={commit} disabled={!batch.valid || !!busy}>Commit batch</Button>}
      </Panel>}
    </Dialog.Content></Dialog.Portal>
  </Dialog.Root>
}
