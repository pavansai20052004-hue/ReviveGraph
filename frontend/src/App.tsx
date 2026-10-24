import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api } from './api'
import type { Component, Computer, State } from './types'
import { Button } from './components/ui/button'
import { Badge, EmptyState, ErrorNotice, HealthBadge, Loading, Panel } from './components/ui/primitives'
import { ImportDialog } from './components/ImportDialog'
import { Evidence } from './components/Evidence'
import { AssistantPanel } from './components/AssistantPanel'
import { CompatibilityView } from './components/CompatibilityView'
import { RecoveryWorkspace } from './components/RecoveryWorkspace'
import { Dashboard } from './components/Dashboard'
import { ReportsView } from './components/ReportsView'
import { Icon, type IconName } from './components/ui/Icon'

const navigation = [
  ['dashboard', 'Dashboard'], ['inventory', 'Computer Inventory'], ['diagnostics', 'AI Diagnostics'],
  ['compatibility', 'Compatibility Graph'], ['optimizer', 'Recovery Optimizer'], ['simulation', 'Live Recovery Simulation'], ['reports', 'Reports'],
] as const
type Page = typeof navigation[number][0]
const labels: Record<Page, string> = Object.fromEntries(navigation) as Record<Page, string>
const navIcons: Record<Page, IconName> = { dashboard: 'dashboard', inventory: 'inventory', diagnostics: 'sparkles', compatibility: 'compatibility', optimizer: 'optimizer', simulation: 'workflow', reports: 'reports' }
const readPage = (): Page => navigation.some(([id]) => id === location.hash.slice(1)) ? location.hash.slice(1) as Page : 'dashboard'

export default function App() {
  const [page, setPage] = useState<Page>(readPage)
  const [mobileNav, setMobileNav] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const [globalSearch, setGlobalSearch] = useState('')
  const [helpOpen, setHelpOpen] = useState(false)
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

  const refresh = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true)
    setError('')
    try {
      const [current, assets, parts] = await Promise.all([api<State>('/state'), api<{ items: Computer[] }>('/computers'), api<{ items: Component[] }>('/components')])
      setState(current); setComputers(assets.items); setComponents(parts.items)
      setSelectedAsset(old => assets.items.some(c => c.asset_id === old) ? old : assets.items[0]?.asset_id ?? '')
      setSelectedPart(old => parts.items.some(p => p.component_id === old) ? old : parts.items[0]?.component_id ?? '')
    } catch (e) { setError((e as Error).message) } finally { if (!quiet) setLoading(false) }
  }, [])
  useEffect(() => { void refresh() }, [refresh])
  useEffect(() => {
    const handler = () => { setPage(readPage()); setMobileNav(false) }
    window.addEventListener('hashchange', handler)
    return () => window.removeEventListener('hashchange', handler)
  }, [])
  function navigate(next: string, subjectId?: string) {
    if (!navigation.some(([id]) => id === next)) return
    if (subjectId) {
      if (components.some(p => p.component_id === subjectId)) { setSelectedPart(subjectId); setTab('components') }
      else { setSelectedAsset(subjectId); setTab('computers') }
      setSearch(''); setFilter('all')
    }
    location.hash = next; setPage(next as Page); setMobileNav(false)
  }
  function searchInventory(event: FormEvent) {
    event.preventDefault()
    const query = globalSearch.trim()
    if (!query) return
    setTab(components.some(p => p.component_id.toLowerCase().includes(query.toLowerCase())) ? 'components' : 'computers')
    setSearch(query); setFilter('all'); navigate('inventory')
  }
  function selectTab(next: string) { setTab(next); setFilter('all'); setSearch('') }
  const asset = computers.find(c => c.asset_id === selectedAsset)
  const part = components.find(c => c.component_id === selectedPart)
  const matchedComputers = computers.filter(c => `${c.asset_id} ${c.board_profile_id} ${c.owner_id}`.toLowerCase().includes(search.toLowerCase()) && (filter === 'all' || c.usability.classification === filter))
  const matchedParts = components.filter(c => `${c.component_id} ${c.location_asset_id ?? 'stock'} ${c.owner_id}`.toLowerCase().includes(search.toLowerCase()) && (filter === 'all' || c.health === filter))
  const title = page === 'dashboard' ? 'Recovery overview' : labels[page]
  const subtitles: Record<Page, string> = {
    dashboard: 'Follow the fleet from intake to a reviewable repair plan.',
    inventory: 'Versioned inventory · each physical part retains one unique identity.',
    diagnostics: 'Inspect source assessments and explain saved recovery plans with grounded facts.',
    compatibility: 'Deterministic hardware decisions with separate evidence and allocation eligibility.',
    optimizer: 'Whole-fleet allocation with hard limits, pinned evidence and an independent output check.',
    simulation: 'Recalculate scenario overlays, review exact revisions and record simulated work.',
    reports: 'Traceable inputs, decisions and simulated verification. Export the full audit record.',
  }

  return <div className={`app-shell ${collapsed ? 'nav-collapsed' : ''}`}>
    <a className="skip-link" href="#main-content" onClick={event => { event.preventDefault(); document.getElementById('main-content')?.focus() }}>Skip to content</a>
    {mobileNav && <button aria-label="Close navigation" className="nav-overlay" onClick={() => setMobileNav(false)} />}
    <aside className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`} aria-label="Primary navigation"><div className="brand"><span className="brand-symbol"><Icon name="boxes" size={27} /></span><span className="brand-wordmark">REVIVEGRAPH</span></div><div className="brand-caption">FLEET RECOVERY STUDIO</div>
      <button className="sidebar-collapse" aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} onClick={() => setCollapsed(!collapsed)}><Icon name="collapse" size={15} /></button>
      <nav>{navigation.map(([id, label]) => <a href={`#${id}`} key={id} className={page === id ? 'nav-item active' : 'nav-item'} aria-label={label} title={collapsed ? label : undefined} aria-current={page === id ? 'page' : undefined} onClick={() => setMobileNav(false)}><Icon name={navIcons[id]} /><span>{label}</span></a>)}</nav>
      <div className="sidebar-bottom"><span className="sidebar-section-label">WORKSPACE</span><div className="fleet-switch"><Icon name="boxes" /><div><strong>{state?.fleet_id ?? 'RG-DEMO-12'}</strong><small>Synthetic desktop fleet</small></div><Icon name="chevron" size={15} /></div><div className="sidebar-status"><i className={error ? 'status-dot status-offline' : loading ? 'status-dot status-waiting' : 'status-dot'} /><div><strong>{error ? 'Connection needs attention' : loading ? 'Connecting to backend' : 'Local backend connected'}</strong><small>{state ? `Inventory revision ${state.revision}` : 'Waiting for inventory state'}</small></div></div></div>
    </aside>
    <div className="main-shell"><header className="top-bar"><Button variant="secondary" className="mobile-menu" aria-label="Open navigation" aria-expanded={mobileNav} onClick={() => setMobileNav(true)}><Icon name="menu" /><span className="sr-only">Menu</span></Button><div className="header-title"><h1>{title}</h1><p>{subtitles[page]}</p></div><form className="global-search" onSubmit={searchInventory}><Icon name="search" size={17} /><input aria-label="Search fleet inventory" placeholder="Search computers, components…" value={globalSearch} onChange={e => setGlobalSearch(e.target.value)} /><button aria-label="Search inventory" type="submit"><Icon name="arrow" size={15} /></button></form><div className="header-tools"><button className="icon-button alert-button" aria-label="View fleet alerts" onClick={() => navigate('dashboard')}><Icon name="bell" size={21} />{!!computers.some(c => c.usability.classification !== 'usable') && <i />}</button><button className="icon-button" aria-label="Workspace information" aria-expanded={helpOpen} onClick={() => setHelpOpen(!helpOpen)}><Icon name="help" size={20} /></button><div className="operator-profile"><div><strong>Demo operator</strong><span>Local simulation workspace</span></div><span className="operator-avatar">RG</span></div></div></header>
      <main id="main-content" className="content" tabIndex={-1}>
        <div className="workspace-toolbar"><div className="mode-strip"><Icon name="shield" size={14} /><strong>Synthetic demo — illustrative data</strong><span>Simulation only · no physical repairs</span></div><div className="toolbar-actions"><span className="revision-chip"><Icon name="activity" size={13} />Revision {state?.revision ?? '—'}</span><Button variant="secondary" onClick={() => setImportOpen(true)}><Icon name="download" size={15} />Import CSV</Button></div></div>
        {helpOpen && <Panel className="workspace-help"><Icon name="shield" /><div><h2>About this workspace</h2><p>Authored synthetic inputs. Plans use deterministic compatibility and allocation rules. Verification is simulated; the app does not run physical diagnostics. Agent37 explanations require an explicitly configured connection; local evidence is always labelled separately. The demo operator label is not authentication.</p></div><button className="icon-button" aria-label="Close workspace information" onClick={() => setHelpOpen(false)}><Icon name="close" /></button></Panel>}
        {error && <ErrorNotice message={error}><p className="caption">Any visible inventory may be stale until refresh succeeds.</p><Button variant="secondary" onClick={() => void refresh()}>Retry backend connection</Button></ErrorNotice>}
        {loading && <Loading />}
        {!loading && state && <>
          {page === 'dashboard' && <Dashboard state={state} computers={computers} components={components} onNavigate={navigate} onImport={() => setImportOpen(true)} />}
          {page === 'inventory' && <>
            <div className="filter-bar"><div className="tabs" role="tablist" aria-label="Inventory type"><button role="tab" aria-selected={tab === 'computers'} onClick={() => selectTab('computers')}>Computers · {state.counts.computers}</button><button role="tab" aria-selected={tab === 'components'} onClick={() => selectTab('components')}>Components · {state.counts.components}</button></div><label className="search-label"><span className="sr-only">Search asset or part ID</span><input aria-label="Search asset or part ID" placeholder="Search asset or part ID…" value={search} onChange={e => setSearch(e.target.value)} /></label><label><span className="sr-only">Filter status</span><select aria-label="Filter status" value={filter} onChange={e => setFilter(e.target.value)}><option value="all">{tab === 'computers' ? 'Usability' : 'Health'}: all</option>{(tab === 'computers' ? ['usable', 'unusable', 'unknown'] : ['healthy', 'faulty', 'unknown']).map(status => <option key={status}>{status}</option>)}</select></label><Button variant="ghost" onClick={() => void refresh()}>Refresh</Button></div>
            {!computers.length ? <EmptyState title="Your fleet starts here"><p>Register synthetic-v1, preview both CSVs and commit a valid batch to populate inventory.</p><Button className="mt-4" onClick={() => setImportOpen(true)}>Start CSV import</Button></EmptyState> : <div className="inventory-split">
              <div><div className="table-scroll panel table-panel"><table><caption className="sr-only">{tab === 'computers' ? 'Computers inventory' : 'Physical component inventory'}</caption>{tab === 'computers' ? <><thead><tr><th>Asset ID</th><th>Base</th><th>Board profile</th><th>RAM</th><th>Storage</th><th>Usability</th></tr></thead><tbody>{matchedComputers.map(c => <tr key={c.asset_id} className={selectedAsset === c.asset_id ? 'selected-row' : ''}><td><button className="text-link mono" aria-pressed={selectedAsset === c.asset_id} onClick={() => setSelectedAsset(c.asset_id)}>{c.asset_id}</button></td><td><HealthBadge value={c.base_health} /></td><td>{c.profile.ram_generation} / SATA<small>{c.board_profile_id.replace('RG-BOARD-', '')} · v{c.profile.version}</small></td><td>{c.installed_components.filter(p => p.type === 'ram').reduce((sum, p) => sum + (p.capacity_gib ?? 0), 0)} GiB</td><td>{c.installed_components.find(p => p.type === 'storage')?.capacity_gb ?? '—'} GB</td><td><HealthBadge value={c.usability.classification} /></td></tr>)}</tbody></> : <><thead><tr><th>Component ID</th><th>Specification</th><th>Health</th><th>Current location</th></tr></thead><tbody>{matchedParts.map(p => <tr key={p.component_id} className={selectedPart === p.component_id ? 'selected-row' : ''}><td><button className="text-link mono" aria-pressed={selectedPart === p.component_id} onClick={() => setSelectedPart(p.component_id)}>{p.component_id}</button></td><td>{p.type === 'ram' ? `${p.ram_generation ?? '?'} · ${p.capacity_gib ?? '?'} GiB` : `${p.interface ?? '?'} · ${p.capacity_gb ?? '?'} GB`}<small>{p.form_factor ?? 'Unknown form'}</small></td><td><HealthBadge value={p.health} /></td><td>{p.location_asset_id ?? 'Stock'}</td></tr>)}</tbody></>}</table>{!(tab === 'computers' ? matchedComputers : matchedParts).length && <p className="muted p-5">No records match. Clear the search or choose all statuses.</p>}</div><p className="caption table-note">{tab === 'computers' ? matchedComputers.length : matchedParts.length} matching records · one ID represents one physical part · data from SQLite</p></div>
              {tab === 'computers' && asset ? <Panel className="detail-panel" aria-label="Selected asset details"><span className="eyebrow">SELECTED ASSET</span><h2 className="mono">{asset.asset_id}</h2><Badge tone="cyan">Synthetic inventory</Badge><hr /><dl><dt>Owner</dt><dd>{asset.owner_id}</dd><dt>Base assembly</dt><dd><HealthBadge value={asset.base_health} /></dd><dt>Motherboard profile</dt><dd>{asset.board_profile_id} · v{asset.profile.version}</dd><dt>RAM support</dt><dd>{asset.profile.ram_generation} · {asset.profile.ram_voltage_mv ?? '?'} mV · {asset.profile.ram_slots ?? '?'} slots</dd><dt>Installed physical parts</dt><dd className="installed-list">{asset.installed_components.map(p => <button key={p.component_id} className="text-link" onClick={() => { setSelectedPart(p.component_id); selectTab('components') }}>{p.component_id} · {p.health}</button>)}</dd></dl><hr /><h3>Initial usability: {asset.usability.classification}</h3><ul className="reason-list">{asset.usability.blockers.map((b, i) => <li key={i}><code>{b.code}</code><span>{b.message}</span></li>)}</ul><Evidence assessment={asset.assessment} /><Button variant="secondary" onClick={() => navigate('compatibility')}>Inspect compatibility</Button><details><summary>Version pin</summary><p className="hash">{asset.registration_hash}</p></details></Panel> : part && <Panel className="detail-panel" aria-label="Selected component details"><span className="eyebrow">SELECTED COMPONENT</span><h2 className="mono">{part.component_id}</h2><HealthBadge value={part.health} /><dl><dt>Owner</dt><dd>{part.owner_id}</dd><dt>Current location</dt><dd>{part.location_asset_id ?? 'Stock'}</dd><dt>Immutable import origin</dt><dd>{part.origin_asset_id ?? 'Stock'}</dd><dt>Specification</dt><dd>{part.type === 'ram' ? `${part.ram_generation} · ${part.capacity_gib ?? '?'} GiB · ${part.speed_mt_s ?? '?'} MT/s · ${part.voltage_mv ?? '?'} mV` : `${part.capacity_gb ?? '?'} GB · ${part.interface}`}</dd><dt>Form</dt><dd>{part.form_factor ?? 'Unknown'}</dd><dt>Reservation</dt><dd>{part.reserved ? 'Physical reservation active' : 'Physical inventory; simulation reservations appear in the selected plan'}</dd></dl><Evidence assessment={part.assessment} /><p className="caption">A healthy assertion alone does not establish hardware compatibility or physical eligibility.</p><Button variant="secondary" onClick={() => navigate('compatibility')}>Inspect against a target</Button></Panel>}
            </div>}
          </>}
          {page === 'compatibility' && <CompatibilityView computers={computers} components={components} target={selectedAsset} onTargetChange={setSelectedAsset} />}
          {(page === 'optimizer' || page === 'simulation') && <RecoveryWorkspace key={page} simulation={page === 'simulation'} components={components} inventoryRevision={state.revision} onChanged={() => refresh(true)} />}
          {page === 'diagnostics' && <div className="dashboard-grid"><Panel className="p-5 stack"><span className="eyebrow">IMPORTED ASSESSMENT EVIDENCE</span><h2>Manual evidence inspection</h2><label>Computer evidence<select aria-label="Diagnostic asset" value={selectedAsset} onChange={e => setSelectedAsset(e.target.value)}>{computers.map(c => <option key={c.asset_id}>{c.asset_id}</option>)}</select></label>{asset ? <><p>Base assertion: <HealthBadge value={asset.base_health} /></p><Evidence assessment={asset.assessment} /><h3>Unresolved blockers</h3><ul className="reason-list">{asset.usability.blockers.map((b, i) => <li key={i}><code>{b.code}</code><span>{b.message}</span></li>)}</ul><Button variant="secondary" onClick={() => navigate('compatibility')}>Inspect deterministic compatibility</Button></> : <p className="muted">Import inventory to inspect supplied evidence.</p>}</Panel><AssistantPanel assetId={selectedAsset} /></div>}
        </>}
        {page === 'reports' && state && !loading && <ReportsView onNavigate={navigate} />}
        <footer className="page-footer">ReviveGraph · disclosed recovery application · {state?.rule_version ?? 'Connecting to local backend'}<span>Planning does not move physical parts.</span></footer>
      </main>
    </div>
    <ImportDialog open={importOpen} onOpenChange={setImportOpen} onImported={async () => { await refresh(); navigate('inventory') }} />
  </div>
}
