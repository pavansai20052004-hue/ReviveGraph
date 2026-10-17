import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import type { Component, Computer, State } from './types'
import { Button } from './components/ui/button'
import { Badge, EmptyState, ErrorNotice, HealthBadge, Loading, Panel } from './components/ui/primitives'
import { ImportDialog } from './components/ImportDialog'
import { Evidence } from './components/Evidence'
import { CompatibilityView } from './components/CompatibilityView'

const navigation = [
  ['dashboard', 'Dashboard'], ['inventory', 'Computer Inventory'], ['diagnostics', 'AI Diagnostics'],
  ['compatibility', 'Compatibility Graph'], ['optimizer', 'Recovery Optimizer'], ['simulation', 'Live Recovery Simulation'],
] as const
type Page = typeof navigation[number][0]
const labels: Record<Page, string> = Object.fromEntries(navigation) as Record<Page, string>
const readPage = (): Page => navigation.some(([id]) => id === location.hash.slice(1)) ? location.hash.slice(1) as Page : 'dashboard'

export default function App() {
  const [page, setPage] = useState<Page>(readPage)
  const [mobileNav, setMobileNav] = useState(false)
  const [state, setState] = useState<State | null>(null)
  const [computers, setComputers] = useState<Computer[]>([])
  const [components, setComponents] = useState<Component[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [importOpen, setImportOpen] = useState(false)
  const [tab, setTab] = useState('computers')
  const [selectedAsset, setSelectedAsset] = useState('')
  const [selectedPart, setSelectedPart] = useState('')
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')

  const refresh = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const [current, assets, parts] = await Promise.all([api<State>('/state'), api<{ items: Computer[] }>('/computers'), api<{ items: Component[] }>('/components')])
      setState(current); setComputers(assets.items); setComponents(parts.items)
      setSelectedAsset(old => assets.items.some(c => c.asset_id === old) ? old : assets.items[0]?.asset_id ?? '')
      setSelectedPart(old => parts.items.some(p => p.component_id === old) ? old : parts.items[0]?.component_id ?? '')
    } catch (e) { setError((e as Error).message) } finally { setLoading(false) }
  }, [])
  useEffect(() => { void refresh() }, [refresh])
  useEffect(() => {
    const handler = () => { setPage(readPage()); setMobileNav(false) }
    window.addEventListener('hashchange', handler)
    return () => window.removeEventListener('hashchange', handler)
  }, [])
  function navigate(next: Page) { location.hash = next; setPage(next); setMobileNav(false) }
  function selectTab(next: string) { setTab(next); setFilter('all'); setSearch('') }
  const asset = computers.find(c => c.asset_id === selectedAsset)
  const part = components.find(c => c.component_id === selectedPart)
  const matchedComputers = computers.filter(c => `${c.asset_id} ${c.board_profile_id} ${c.owner_id}`.toLowerCase().includes(search.toLowerCase()) && (filter === 'all' || c.usability.classification === filter))
  const matchedParts = components.filter(c => `${c.component_id} ${c.location_asset_id ?? 'stock'} ${c.owner_id}`.toLowerCase().includes(search.toLowerCase()) && (filter === 'all' || c.health === filter))
  const title = page === 'dashboard' ? 'Recovery overview' : labels[page]
  const subtitles: Record<Page, string> = {
    dashboard: 'Follow the fleet from intake to a reviewable repair plan.',
    inventory: 'Versioned inventory · each physical part retains one unique identity.',
    diagnostics: 'Evidence inspection is available in Inventory. AI interpretation is a later enhancement.',
    compatibility: 'Deterministic hardware decisions with separate evidence and allocation eligibility.',
    optimizer: 'Fleet recovery, costs and resource constraints will be integrated onsite.',
    simulation: 'Failure replanning and the approval-to-verification flow are planned onsite work.',
  }

  return <div className="app-shell">
    <a className="skip-link" href="#main-content" onClick={event => { event.preventDefault(); document.getElementById('main-content')?.focus() }}>Skip to content</a>
    {mobileNav && <button aria-label="Close navigation" className="nav-overlay" onClick={() => setMobileNav(false)} />}
    <aside className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`} aria-label="Primary navigation"><div className="brand">REVIVEGRAPH</div><div className="brand-caption">FLEET RECOVERY STUDIO</div>
      <nav>{navigation.map(([id, label]) => <a href={`#${id}`} key={id} className={page === id ? 'nav-item active' : 'nav-item'} aria-current={page === id ? 'page' : undefined} onClick={() => setMobileNav(false)}>{label}</a>)}</nav>
      <div className="operator"><span>DEMO OPERATOR</span><p>Solo participant · local workspace</p><small>local-demo-operator<br />No production authentication</small></div>
    </aside>
    <div className="main-shell"><header className="top-bar"><Button variant="secondary" className="mobile-menu" aria-label="Open navigation" aria-expanded={mobileNav} onClick={() => setMobileNav(true)}>Menu</Button><span>Fleet / {state?.fleet_id ?? 'RG-DEMO-12'}</span><span className="caption">Revision {state?.revision ?? '—'} <span aria-hidden="true"> • </span> Synthetic inventory</span></header>
      <main id="main-content" className="content" tabIndex={-1}>
        <div className="mode-strip"><strong>Synthetic demo — illustrative data</strong><span>Authored inputs. No measured recovery results or physical repairs.</span></div>
        <div className="page-heading"><div><h1>{title}</h1><p className="muted">{subtitles[page]}</p></div><Button onClick={() => setImportOpen(true)}>Import CSV</Button></div>
        {error && <ErrorNotice message={error}><p className="caption">Any visible inventory may be stale until refresh succeeds.</p><Button variant="secondary" onClick={() => void refresh()}>Retry backend connection</Button></ErrorNotice>}
        {loading && <Loading />}
        {!loading && state && <>
          {page === 'dashboard' && <>
            <div className="metric-strip">{[['Fleet assets', state.counts.computers], ['Components', state.counts.components], ['Known unusable', state.counts.unusable], ['Evidence uncertain', state.counts.unknown], ['Planned recovery', state.optimization.status]].map(([label, value]) => <Panel className="metric" key={label}><span>{label}</span><strong className={typeof value === 'string' ? 'metric-text' : ''}>{value}</strong></Panel>)}</div>
            <div className="dashboard-grid"><Panel className="p-5 stack"><span className="eyebrow">RECOVERY WORKFLOW</span><h2>What needs attention next</h2><p className="muted">Current inventory revision {state.revision} · planning and execution are not implemented yet.</p><hr />
              {[
                ['01', 'Import fleet', state.counts.computers ? `${state.counts.computers} computers and ${state.counts.components} components persisted` : 'Register the fixture and review both CSV files', state.counts.computers ? 'Imported' : 'Ready to begin'],
                ['02', 'Inspect evidence', `${state.counts.unknown} computers have unresolved evidence or profile fields`, 'Review inventory'],
                ['03', 'Inspect compatibility', 'Known hardware rules, health and ownership shown separately', 'Available'],
                ['04', 'Calculate recovery plan', 'Production optimizer is reserved for onsite integration', 'Not calculated'],
                ['05', 'Approve and verify', 'Approval, work orders and verification integration are planned onsite', 'Not implemented yet'],
              ].map(([number, label, description, status]) => <div className="workflow-row" key={number}><span className="stage-number">{number}</span><div><strong>{label}</strong><p className="caption">{description}</p></div><span className="caption cyan">{status}</span></div>)}
              <div className="actions"><Button variant="secondary" onClick={() => navigate('inventory')}>Open inventory</Button><Button variant="secondary" disabled={!computers.length} onClick={() => navigate('compatibility')}>Inspect compatibility</Button></div>
            </Panel><Panel className="p-5 stack"><span className="eyebrow">REVIEW QUEUE</span><h2>Evidence before allocation</h2><p className="muted">Unknown inputs stay out of eligible configurations.</p><hr />{computers.filter(c => c.usability.classification === 'unknown').slice(0, 4).map(c => <div className="queue-item" key={c.asset_id}><button className="text-link mono" onClick={() => { setSelectedAsset(c.asset_id); navigate('inventory') }}>{c.asset_id}</button><p className="caption">{c.usability.blockers.map(b => b.message).join(' ')}</p><Badge tone="warning">Unknown</Badge></div>)}{!computers.length && <p className="muted">No inventory imported. The first reviewed batch will populate this queue.</p>}<hr /><strong>Impact estimates unavailable</strong><p className="caption">No sourced mass or CO₂e factors have been supplied. Repair verification is not implemented yet.</p></Panel></div>
          </>}
          {page === 'inventory' && <>
            <div className="filter-bar"><div className="tabs" role="tablist" aria-label="Inventory type"><button role="tab" aria-selected={tab === 'computers'} onClick={() => selectTab('computers')}>Computers · {state.counts.computers}</button><button role="tab" aria-selected={tab === 'components'} onClick={() => selectTab('components')}>Components · {state.counts.components}</button></div><label className="search-label"><span className="sr-only">Search asset or part ID</span><input aria-label="Search asset or part ID" placeholder="Search asset or part ID…" value={search} onChange={e => setSearch(e.target.value)} /></label><label><span className="sr-only">Filter status</span><select aria-label="Filter status" value={filter} onChange={e => setFilter(e.target.value)}><option value="all">{tab === 'computers' ? 'Usability' : 'Health'}: all</option>{(tab === 'computers' ? ['usable', 'unusable', 'unknown'] : ['healthy', 'faulty', 'unknown']).map(status => <option key={status}>{status}</option>)}</select></label><Button variant="ghost" onClick={() => void refresh()}>Refresh</Button></div>
            {!computers.length ? <EmptyState title="Your fleet starts here"><p>Register synthetic-v1, preview both CSVs and commit a valid batch to populate inventory.</p><Button className="mt-4" onClick={() => setImportOpen(true)}>Start CSV import</Button></EmptyState> : <div className="inventory-split">
              <div><div className="table-scroll panel table-panel"><table><caption className="sr-only">{tab === 'computers' ? 'Computers inventory' : 'Physical component inventory'}</caption>{tab === 'computers' ? <><thead><tr><th>Asset ID</th><th>Base</th><th>Board profile</th><th>RAM</th><th>Storage</th><th>Usability</th></tr></thead><tbody>{matchedComputers.map(c => <tr key={c.asset_id} className={selectedAsset === c.asset_id ? 'selected-row' : ''}><td><button className="text-link mono" aria-pressed={selectedAsset === c.asset_id} onClick={() => setSelectedAsset(c.asset_id)}>{c.asset_id}</button></td><td><HealthBadge value={c.base_health} /></td><td>{c.profile.ram_generation} / SATA<small>{c.board_profile_id.replace('RG-BOARD-', '')} · v{c.profile.version}</small></td><td>{c.installed_components.filter(p => p.type === 'ram').reduce((sum, p) => sum + (p.capacity_gib ?? 0), 0)} GiB</td><td>{c.installed_components.find(p => p.type === 'storage')?.capacity_gb ?? '—'} GB</td><td><HealthBadge value={c.usability.classification} /></td></tr>)}</tbody></> : <><thead><tr><th>Component ID</th><th>Specification</th><th>Health</th><th>Current location</th></tr></thead><tbody>{matchedParts.map(p => <tr key={p.component_id} className={selectedPart === p.component_id ? 'selected-row' : ''}><td><button className="text-link mono" aria-pressed={selectedPart === p.component_id} onClick={() => setSelectedPart(p.component_id)}>{p.component_id}</button></td><td>{p.type === 'ram' ? `${p.ram_generation ?? '?'} · ${p.capacity_gib ?? '?'} GiB` : `${p.interface ?? '?'} · ${p.capacity_gb ?? '?'} GB`}<small>{p.form_factor ?? 'Unknown form'}</small></td><td><HealthBadge value={p.health} /></td><td>{p.location_asset_id ?? 'Stock'}</td></tr>)}</tbody></>}</table>{!(tab === 'computers' ? matchedComputers : matchedParts).length && <p className="muted p-5">No records match. Clear the search or choose all statuses.</p>}</div><p className="caption table-note">{tab === 'computers' ? matchedComputers.length : matchedParts.length} matching records · one ID represents one physical part · data from SQLite</p></div>
              {tab === 'computers' && asset ? <Panel className="detail-panel" aria-label="Selected asset details"><span className="eyebrow">SELECTED ASSET</span><h2 className="mono">{asset.asset_id}</h2><Badge tone="cyan">Synthetic inventory</Badge><hr /><dl><dt>Owner</dt><dd>{asset.owner_id}</dd><dt>Base assembly</dt><dd><HealthBadge value={asset.base_health} /></dd><dt>Motherboard profile</dt><dd>{asset.board_profile_id} · v{asset.profile.version}</dd><dt>RAM support</dt><dd>{asset.profile.ram_generation} · {asset.profile.ram_voltage_mv ?? '?'} mV · {asset.profile.ram_slots ?? '?'} slots</dd><dt>Installed physical parts</dt><dd className="installed-list">{asset.installed_components.map(p => <button key={p.component_id} className="text-link" onClick={() => { setSelectedPart(p.component_id); selectTab('components') }}>{p.component_id} · {p.health}</button>)}</dd></dl><hr /><h3>Initial usability: {asset.usability.classification}</h3><ul className="reason-list">{asset.usability.blockers.map((b, i) => <li key={i}><code>{b.code}</code><span>{b.message}</span></li>)}</ul><Evidence assessment={asset.assessment} /><Button variant="secondary" onClick={() => navigate('compatibility')}>Inspect compatibility</Button><details><summary>Version pin</summary><p className="hash">{asset.registration_hash}</p></details></Panel> : part && <Panel className="detail-panel" aria-label="Selected component details"><span className="eyebrow">SELECTED COMPONENT</span><h2 className="mono">{part.component_id}</h2><HealthBadge value={part.health} /><dl><dt>Owner</dt><dd>{part.owner_id}</dd><dt>Current location</dt><dd>{part.location_asset_id ?? 'Stock'}</dd><dt>Immutable import origin</dt><dd>{part.origin_asset_id ?? 'Stock'}</dd><dt>Specification</dt><dd>{part.type === 'ram' ? `${part.ram_generation} · ${part.capacity_gib ?? '?'} GiB · ${part.speed_mt_s ?? '?'} MT/s · ${part.voltage_mv ?? '?'} mV` : `${part.capacity_gb ?? '?'} GB · ${part.interface}`}</dd><dt>Form</dt><dd>{part.form_factor ?? 'Unknown'}</dd><dt>Reservation</dt><dd>No reservations implemented</dd></dl><Evidence assessment={part.assessment} /><p className="caption">A healthy assertion alone does not establish hardware compatibility or physical eligibility.</p><Button variant="secondary" onClick={() => navigate('compatibility')}>Inspect against a target</Button></Panel>}
            </div>}
          </>}
          {page === 'compatibility' && <CompatibilityView computers={computers} components={components} target={selectedAsset} onTargetChange={setSelectedAsset} />}
          {(['diagnostics', 'optimizer', 'simulation'] as Page[]).includes(page) && <EmptyState title="Not implemented yet"><p>{subtitles[page]}</p>{page === 'optimizer' && <p className="not-calculated">Recovery count · cash total · technician effort<br /><strong>Not calculated</strong></p>}<p className="mt-3">The handwritten fixture allocations remain preparation evidence. This foundation does not calculate a repair plan.</p><Button className="mt-4" variant="secondary" onClick={() => navigate('inventory')}>Inspect imported evidence</Button></EmptyState>}
        </>}
        <footer className="page-footer">ReviveGraph · disclosed application foundation · {state?.rule_version ?? 'Connecting to local backend'}<span>Planning does not move physical parts.</span></footer>
      </main>
    </div>
    <ImportDialog open={importOpen} onOpenChange={setImportOpen} onImported={async () => { await refresh(); navigate('inventory') }} />
  </div>
}
