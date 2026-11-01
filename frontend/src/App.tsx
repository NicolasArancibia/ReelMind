import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowDownLeft, ArrowUpRight, Bookmark, Check, ChevronLeft, ChevronRight, CirclePause, CirclePlay, FolderOpen, HardDrive, Layers3, Library, Link2, LoaderCircle, Pencil, Plus, RefreshCw, RotateCcw, ShieldCheck, Sparkles, Trash2 } from 'lucide-react'
import { ApiError, request } from './api'
import type { Health, Source, SourcePage, Organization } from './api'
import SourceDialog from './SourceDialog'
import ImportVideo from './ImportVideo'
import AudioPanel, { engineNames, jobNames } from './AudioPanel'
import SearchPanel from './SearchPanel'
import BatchCapture from './BatchCapture'
import NotesBrowser from './NotesBrowser'
import LibraryBatchToolbar from './LibraryBatchToolbar'
import SettingsPanel, { activityName } from './SettingsPanel'
import type { SystemStatus } from './SettingsPanel'
import ProjectsPanel from './ProjectsPanel'
import type { Selection, SourceAction } from './SourceDialog'

const platformNames: Record<string, string> = {
  instagram: 'Instagram', youtube: 'YouTube', tiktok: 'TikTok', other: 'Web', local: 'Archivo',
}

function domain(url: string | null) {
  try { return new URL(url || '').hostname.replace(/^www\./, '') } catch { return 'Vídeo local' }
}

function SourceRow({ source, disabled, onAction, selected, onToggle }: { source: Source; disabled: boolean; selected:boolean;onToggle:()=>void; onAction: (source: Source, action: SourceAction) => void }) {
  const [thumbnailError,setThumbnailError]=useState(false)
  return <article className="source-row">
    {!source.deleted_at&&<input type="checkbox" checked={selected} disabled={disabled} onChange={onToggle} aria-label={`Seleccionar ${source.title||source.assets[0]?.original_name||source.original_url}`} />}
    <a className="source-link" href={source.original_url || (source.assets[0] && !source.deleted_at ? `/api/assets/${source.assets[0].id}/content` : undefined)} target="_blank" rel="noopener noreferrer" aria-label={`Abrir ${source.title || domain(source.original_url)} en otra pestaña`}>
    <span className={`source-icon platform-${source.platform}`}>{source.assets[0] && !source.deleted_at && !thumbnailError ? <video className="source-thumbnail" src={`/api/assets/${source.assets[0].id}/content#t=0.1`} preload="metadata" muted aria-hidden="true" onError={()=>setThumbnailError(true)} /> : <CirclePlay size={21} strokeWidth={1.6} />}</span>
    <span className="source-info">
      <strong>{source.title || source.assets[0]?.original_name || domain(source.original_url)}</strong>
      <span>{platformNames[source.platform] || 'Web'}<i>·</i>{new Date(source.created_at).toLocaleDateString('es-CL', { day: 'numeric', month: 'short' })}</span>
    </span>
    <ArrowUpRight size={17} className="source-arrow" />
    </a>
    <div className="source-labels">{[...source.categories, ...source.tags].map(label => <span key={label.id}>{label.name}</span>)}<small>{source.summary && <span>{source.summary}</span>}{jobNames[source.job?.status || 'cancelled']}{source.assets.length ? ` · ${source.assets.length} archivo(s)` : ''}</small></div>
    <div className="row-actions" title={source.job?.error_message || undefined}>{!source.deleted_at && <><button className="secondary-button" disabled={disabled} onClick={() => onAction(source, 'files')}>Archivos</button><button className="secondary-button" disabled={disabled} onClick={() => onAction(source, 'transcripts')}>Ficha y audio</button><button className="secondary-button" disabled={disabled} onClick={() => onAction(source, 'organize')}>Organizar</button><button className="secondary-button" disabled={disabled} onClick={() => onAction(source, 'queue')}>{source.job?.status === 'pending' ? 'Quitar de cola' : 'Encolar'}</button></>}{source.deleted_at ? <button className="secondary-button" disabled={disabled} onClick={() => onAction(source, 'restore')}><RotateCcw size={15} /> Restaurar</button> : <><button className="icon-button" disabled={disabled} onClick={() => onAction(source, 'edit')} aria-label={`Editar título: ${source.title || source.original_url}`} title="Editar título"><Pencil size={16} /></button><button className="icon-button trash-button" disabled={disabled} onClick={() => onAction(source, 'trash')} aria-label={`Mover a la papelera: ${source.title || source.original_url}`} title="Mover a la papelera"><Trash2 size={16} /></button></>}</div>
  </article>
}

export default function App() {
  const [page, setPage] = useState<SourcePage>({ items: [], total: 0, active_total: 0, trash_total: 0, queue_total: 0, offset: 0, limit: 20 })
  const [screen, setScreen] = useState(() => location.hash.startsWith('#chat') ? 'chat' : location.hash === '#projects' ? 'projects' : location.hash === '#notes' ? 'notes' : location.hash === '#settings' ? 'settings' : 'library')
  useEffect(() => { const navigate = () => setScreen(location.hash.startsWith('#chat') ? 'chat' : location.hash === '#projects' ? 'projects' : location.hash === '#notes' ? 'notes' : location.hash === '#settings' ? 'settings' : 'library'); window.addEventListener('hashchange', navigate); return () => window.removeEventListener('hashchange', navigate) }, [])
  useEffect(() => { window.scrollTo(0, 0) }, [screen])
  const [systemStatus,setSystemStatus]=useState<SystemStatus|null>(null)
  useEffect(()=>{let cancelled=false;async function update(){try{const next=await request<SystemStatus>('/system/status');if(!cancelled)setSystemStatus(next)}catch{/* Main health and Settings expose connection errors. */}} void update();const timer=setInterval(()=>{if(!document.hidden)void update()},5000);return()=>{cancelled=true;clearInterval(timer)}},[])
  const [selectedIds,setSelectedIds]=useState<string[]>([])
  function toggleSource(id:string){if(!selectedIds.includes(id)&&selectedIds.length>=200){setSourceError('Selecciona hasta 200 fuentes por lote.');return}setSelectedIds(previous=>previous.includes(id)?previous.filter(value=>value!==id):[...previous,id])}
  const [contentRevision, setContentRevision] = useState(0)
  const [sourceError, setSourceError] = useState('')
  async function openSource(id: string, timeMs?: number) { setSourceError(''); try { const source = await request<Source>(`/sources/${id}`); setSelection({ source, action: 'transcripts', timeMs }) } catch(e) { setSourceError(e instanceof Error ? e.message : 'No se pudo abrir la fuente.') } }
  const [view, setView] = useState<'library' | 'trash' | 'queue'>('library')
  const [organization, setOrganization] = useState<Organization>({ tags: [], categories: [] })
  const [filters, setFilters] = useState({ q: '', platform: '', source_type: '', tag: '', category: '', favorite: '' })
  const [search, setSearch] = useState('')
  const [uploading, setUploading] = useState(false)
  const [offset, setOffset] = useState(0)
  const [selection, setSelection] = useState<Selection | null>(null)
  const [duplicate, setDuplicate] = useState<Source | null>(null)
  const [health, setHealth] = useState<Health | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const urlInput = useRef<HTMLInputElement>(null)
  const refreshSequence = useRef(0)

  const refresh = useCallback(async (nextView = view, nextOffset = offset) => {
    const sequence = ++refreshSequence.current
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams(Object.entries(filters).filter(([, value]) => value))
      const [nextHealth, nextPage, nextOrganization] = await Promise.all([
        request<Health>('/health'), request<SourcePage>(`/sources?view=${nextView}&offset=${nextOffset}&limit=20&${params}`), request<Organization>('/organization'),
      ])
      if (sequence !== refreshSequence.current) return
      setHealth(nextHealth)
      setOrganization(nextOrganization)
      setPage(nextPage)
      setOffset(nextPage.offset)
    } catch (e) {
      if (sequence !== refreshSequence.current) return
      setHealth(null)
      setError(e instanceof Error ? e.message : 'No pudimos cargar tu biblioteca.')
    } finally {
      if (sequence === refreshSequence.current) setLoading(false)
    }
  }, [view, offset, filters])

  useEffect(() => { void refresh(); return () => { refreshSequence.current += 1 } }, [refresh])

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    setSaving(true)
    setError('')
    setNotice('')
    setDuplicate(null)
    try {
      await request<Source>('/sources', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim(), title: title.trim() || null }),
      })
      if (view !== 'library' || offset !== 0) { setView('library'); setOffset(0) }
      else await refresh()
      setUrl('')
      setTitle('')
      setNotice('Enlace guardado en tu computador. Se procesará solo cuando inicies el motor.')
      urlInput.current?.focus()
    } catch (e) {
      if (e instanceof ApiError && (e.status === 0 || e.status >= 500)) setHealth(null)
      if (e instanceof ApiError && e.existingSource?.deleted_at) setDuplicate(e.existingSource)
      setError(e instanceof Error ? e.message : 'No pudimos guardar el enlace.')
    } finally { setSaving(false) }
  }

  const connected = health?.database === 'connected'
  const busy = loading || saving || uploading || selection !== null

  function changeView(nextView: 'library' | 'trash' | 'queue') {
    setView(nextView)
    setSelectedIds([])
    setOffset(0)
    setNotice('')
    setError('')
    setDuplicate(null)
  }

  return <div className="app-shell">
    <a className="skip-link" href="#main">Ir al contenido</a>
    <aside className="sidebar">
      <a className="brand" href="#main" aria-label="ReelMind, inicio"><span className="brand-mark"><Layers3 size={23} strokeWidth={2} /></span><span>Reel<span className="font-normal">Mind</span></span></a>
      <div className="workspace"><span className="workspace-avatar"><Bookmark size={15} /></span><div><strong>Mi espacio</strong><span>Biblioteca personal</span></div><span className="workspace-dot" /></div>
      <p className="nav-label">TU BIBLIOTECA</p>
      <nav aria-label="Navegación principal"><a className={`nav-item ${screen === 'library' ? 'active' : ''}`} aria-current={screen === 'library' ? 'page' : undefined} href="#library"><Library size={18} /> Biblioteca <span className="nav-count">{connected ? page.active_total : '—'}</span></a><a className={`nav-item ${screen === 'chat' ? 'active' : ''}`} aria-current={screen === 'chat' ? 'page' : undefined} href="#chat"><Sparkles size={17} /> Chat</a><a className={`nav-item ${screen === 'projects' ? 'active' : ''}`} aria-current={screen === 'projects' ? 'page' : undefined} href="#projects"><FolderOpen size={17} /> Proyectos</a><a className={`nav-item ${screen === 'notes' ? 'active' : ''}`} href="#notes" aria-current={screen === 'notes' ? 'page' : undefined}><Bookmark size={17}/> Mis ideas</a><a className={`nav-item ${screen === 'settings' ? 'active' : ''}`} href="#settings"><HardDrive size={17}/> Ajustes</a></nav>
      <div className="upcoming"><p className="nav-label">CONECTA TUS IDEAS</p><a href="#projects"><Layers3 size={17} /> Ver conexiones en Proyectos</a><p>Relaciona fuentes y apuntes<br />con su evidencia.</p></div>
      <div className="sidebar-footer"><HardDrive size={17} /><div><strong>En tu computador</strong><span>Tú tienes el control.</span></div></div>
    </aside>

    <div className="main-shell">
      <header className="topbar"><span>Mi espacio <ChevronRight size={14} /> <strong>{screen === 'chat' ? 'Chat' : screen === 'projects' ? 'Proyectos' : screen === 'notes' ? 'Mis ideas' : screen === 'settings' ? 'Ajustes' : 'Biblioteca'}</strong></span>{systemStatus?.heavy_busy&&<a className="activity-chip" href="#settings">{activityName(systemStatus)} · Ver actividad</a>}<span className={`connection ${connected ? 'online' : ''}`}><span />{loading ? 'Conectando…' : connected ? 'Conexión local activa' : 'Sin conexión local'}</span></header>
      <main tabIndex={-1} id="main" className={`main-content ${screen === 'chat' ? 'chat-page' : ''}`}>
        {sourceError && <p className="error-banner" role="alert">{sourceError}<button onClick={() => setSourceError('')}>Cerrar</button></p>}
        <div hidden={screen !== 'library'}>
        <section className="welcome">
          <div><p className="eyebrow"><span /> MENOS ENLACES PERDIDOS. MÁS IDEAS A MANO.</p><h1>Un lugar para lo que<br /><span>quieres volver a ver.</span></h1><p className="welcome-copy">Reúne los vídeos que te inspiran.<br className="mobile-break" /> Tu próxima idea empieza con un enlace.</p></div>
          <div className="welcome-graphic" aria-hidden="true"><div className="graphic-orbit" /><div className="graphic-card back"><span /><span /><span /></div><div className="graphic-card front"><div className="graphic-play"><CirclePlay size={35} strokeWidth={1.2} /></div><div className="graphic-lines"><span /><span /></div><span className="graphic-bookmark"><Bookmark size={15} /></span></div><span className="graphic-spark">✦</span></div>
        </section>

        <section className="overview" aria-label="Resumen de tu espacio">
          <div className="overview-item"><span className="metric-icon"><Bookmark size={19} /></span><div><span className="metric-label">Fuentes en biblioteca</span><strong>{loading ? '—' : connected ? String(page.active_total).padStart(2, '0') : '—'}</strong></div></div>
          <div className="overview-item"><span className="metric-icon"><CirclePause size={19} /></span><div><span className="metric-label">Análisis de vídeos</span><strong className="metric-text">{engineNames[health?.processing.state || 'stopped']}<span className="status-dot" /></strong></div></div>
          <div className="overview-item"><span className="metric-icon"><ShieldCheck size={19} /></span><div><span className="metric-label">Tu información</span><strong className="metric-text">Solo en este equipo</strong></div></div>
        </section>

        <div className="content-grid">
          <section className="capture-panel" aria-labelledby="capture-heading">
            <div className="panel-heading"><span className="section-icon"><Plus size={19} /></span><div><h2 id="capture-heading">Guarda una nueva idea</h2><p>Pega un enlace y déjalo a mano para después.</p></div><span className="step-number">01</span></div>
            <form onSubmit={save}>
              <label htmlFor="video-url">Enlace del vídeo</label>
              <div className="input-with-icon"><Link2 size={17} /><input ref={urlInput} id="video-url" name="url" type="url" required maxLength={4096} placeholder="https://www.instagram.com/reel/…" value={url} onChange={event => setUrl(event.target.value)} disabled={saving} autoComplete="off" /></div>
              <label htmlFor="video-title">Un nombre para recordarlo <span>Opcional</span></label>
              <input id="video-title" name="title" type="text" maxLength={240} placeholder="Por ejemplo: una idea para mi próximo proyecto" value={title} onChange={event => setTitle(event.target.value)} disabled={saving} autoComplete="off" />
              <div className="form-footer"><span><ShieldCheck size={14} /> Guardado local</span><button className="primary-button" type="submit" disabled={busy || !connected}>{saving ? <LoaderCircle className="animate-spin" size={17} /> : <Plus size={17} />}{saving ? 'Guardando…' : 'Guardar enlace'}</button></div>
            </form>
            <ImportVideo disabled={busy || !connected} onBusy={setUploading} onDuplicate={setDuplicate} onSaved={() => { setNotice('Vídeo importado. Se procesará solo en un próximo inicio manual.'); void refresh() }} />
          </section>

          <AudioPanel onChange={() => { setContentRevision(value => value + 1); void refresh() }} />
        </div>

        {notice && <p className="notice" role="status"><Check size={16} />{notice}</p>}
        {duplicate?.deleted_at && !error && <p className="notice"><button className="secondary-button" disabled={busy} onClick={() => setSelection({ source: duplicate, action: 'restore' })}>Restaurar vídeo de la papelera</button></p>}
        {error && <div className="error-banner" role="alert"><span>{error}</span>{duplicate?.deleted_at && <button onClick={() => setSelection({ source: duplicate, action: 'restore' })} disabled={busy}><RotateCcw size={15} /> Restaurar enlace</button>}{!connected && <button onClick={() => void refresh()} disabled={busy}><RefreshCw size={15} /> Reintentar conexión</button>}</div>}

        <BatchCapture onSaved={() => { setContentRevision(value => value + 1); void refresh() }} onBusy={setUploading}/>
        <section className="library-section" aria-labelledby="library-heading">
          <div className="library-heading"><div><h2 id="library-heading">{view === 'trash' ? 'Papelera' : view === 'queue' ? 'Pendientes de análisis' : 'Tu biblioteca'}</h2><p>{view === 'trash' ? 'Tus fuentes y archivos se conservan hasta que decidas restaurarlos.' : view === 'queue' ? 'Orden de llegada. Inicia el motor para transcribir esta cola.' : 'Enlaces y vídeos, de la más reciente a la primera.'}</p></div><button className="icon-button" aria-label="Actualizar biblioteca" title="Actualizar biblioteca" onClick={() => { setNotice(''); setDuplicate(null); void refresh() }} disabled={busy}><RefreshCw size={17} className={loading ? 'animate-spin' : ''} /></button></div>
          <div className="library-tabs" role="group" aria-label="Vista de enlaces"><button aria-pressed={view === 'library'} disabled={busy} onClick={() => changeView('library')}><Library size={16} /> Biblioteca <span>{connected ? page.active_total : '—'}</span></button><button aria-pressed={view === 'trash'} disabled={busy} onClick={() => changeView('trash')}><Trash2 size={16} /> Papelera <span>{connected ? page.trash_total : '—'}</span></button><button aria-pressed={view === 'queue'} disabled={busy} onClick={() => changeView('queue')}><CirclePause size={16} /> Pendientes <span>{connected ? page.queue_total : '—'}</span></button></div>
          <form className="library-filters" onSubmit={event => { event.preventDefault(); setOffset(0); setFilters({ ...filters, q: search }) }}>
            <div className="search-field"><label htmlFor="search-library">Buscar en la biblioteca</label><input id="search-library" value={search} onChange={event => setSearch(event.target.value)} maxLength={240} placeholder="Título, enlace, archivo o etiqueta" /><button className="secondary-button" disabled={busy}>Buscar</button></div>
            <label>Favoritos<select value={filters.favorite} onChange={event => { setOffset(0); setFilters({ ...filters, favorite: event.target.value }) }}><option value="">Todos</option><option value="true">Solo favoritos</option></select></label><label>Plataforma<select value={filters.platform} disabled={busy} onChange={event => { setOffset(0); setFilters({ ...filters, platform: event.target.value }) }}><option value="">Todas</option>{Object.entries(platformNames).map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select></label>
            <label>Tipo<select value={filters.source_type} disabled={busy} onChange={event => { setOffset(0); setFilters({ ...filters, source_type: event.target.value }) }}><option value="">Todos</option><option value="url">Enlaces</option><option value="file">Archivos</option></select></label>
            <label>Categoría<select value={filters.category} disabled={busy} onChange={event => { setOffset(0); setFilters({ ...filters, category: event.target.value }) }}><option value="">Todas</option>{organization.categories.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
            <label>Etiqueta<select value={filters.tag} disabled={busy} onChange={event => { setOffset(0); setFilters({ ...filters, tag: event.target.value }) }}><option value="">Todas</option>{organization.tags.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
            <button type="button" className="secondary-button" disabled={busy} onClick={() => { setSearch(''); setOffset(0); setFilters({ q: '', platform: '', source_type: '', tag: '', category: '', favorite: '' }) }}>Limpiar filtros</button>
          </form>
          {view!=='trash'&&<div className="retrieval-actions"><button className="secondary-button" disabled={busy||!page.items.length} onClick={()=>{const merged=Array.from(new Set([...selectedIds,...page.items.map(s=>s.id)]));if(merged.length>200)setSourceError('Selecciona hasta 200 fuentes por lote.');else setSelectedIds(merged)}}>Seleccionar esta página</button></div>}
          {!!selectedIds.length&&<LibraryBatchToolbar ids={selectedIds} onClear={()=>setSelectedIds([])} onBusy={setSaving} onDone={message=>{setNotice(message);setContentRevision(value=>value+1);void refresh()}}/>}
          {loading ? <div className="empty-state"><LoaderCircle className="animate-spin" size={26} /><p>Cargando tu biblioteca…</p></div> : !connected ? <div className="empty-state"><h3>Tu biblioteca está esperando.</h3><p>Vuelve a conectar para consultar y gestionar tus enlaces.</p></div> : page.items.length ? <><div className="source-list">{page.items.map(source => <SourceRow source={source} key={source.id} selected={selectedIds.includes(source.id)} onToggle={()=>toggleSource(source.id)} disabled={busy} onAction={(source, action) => { setNotice(''); setSelection({ source, action }) }} />)}</div><div className="pagination" aria-label="Páginas de enlaces"><span>{page.offset + 1}–{page.offset + page.items.length} de {page.total}</span><div><button className="secondary-button" disabled={busy || page.offset === 0} onClick={() => setOffset(Math.max(0, page.offset - page.limit))}><ChevronLeft size={16} /> Anterior</button><button className="secondary-button" disabled={busy || page.offset + page.items.length >= page.total} onClick={() => setOffset(page.offset + page.limit)}>Siguiente <ChevronRight size={16} /></button></div></div></> : <div className="empty-state"><span className="empty-icon">{view === 'trash' ? <Trash2 size={25} /> : <Bookmark size={25} strokeWidth={1.4} />}</span><h3>{view === 'trash' ? 'La papelera está vacía.' : 'No hay fuentes en esta vista.'}</h3><p>{view === 'trash' ? 'Los enlaces que retires de la biblioteca aparecerán aquí.' : 'Prueba a limpiar los filtros o añade una fuente a tu biblioteca.'}</p>{view === 'library' && <button className="text-button" onClick={() => urlInput.current?.focus()}><ArrowDownLeft size={15} /> Guardar mi primer enlace</button>}</div>}
        </section>
        </div>
        <div hidden={screen !== 'chat'}><SearchPanel visible={screen === 'chat'} contentRevision={contentRevision} onSource={(id,timeMs) => void openSource(id,timeMs)} /></div>
        {screen === 'projects' && <ProjectsPanel onSource={(id,timeMs) => void openSource(id,timeMs)} />}
        {screen === 'notes' && <NotesBrowser onSource={(id,timeMs) => void openSource(id,timeMs)} onChanged={contentRevision}/>}
        {screen === 'settings'&&<SettingsPanel status={systemStatus} onRefresh={()=>{setContentRevision(value=>value+1);void refresh();void request<SystemStatus>('/system/status').then(setSystemStatus).catch(e=>setSourceError(e.message))}}/>}
        <footer className="page-footer"><span>REELMIND <i>/</i> HECHO PARA VOLVER A LAS BUENAS IDEAS</span><span>Local por naturaleza.</span></footer>
      </main>
    </div>
    {selection && <SourceDialog key={`${selection.source.id}-${selection.action}`} selection={selection} onChanged={() => setContentRevision(value => value + 1)} onClose={() => setSelection(null)} onSaved={message => { if (duplicate) { setUrl(''); setTitle('') }; setSelection(null); setDuplicate(null); setNotice(message); setContentRevision(value => value + 1); void refresh() }} />}
  </div>
}
