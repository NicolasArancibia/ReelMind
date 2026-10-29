import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowDownLeft, ArrowUpRight, Bookmark, Check, ChevronRight, CirclePause, CirclePlay, FolderOpen, HardDrive, Layers3, Library, Link2, LoaderCircle, Plus, RefreshCw, ShieldCheck, Sparkles } from 'lucide-react'
import { ApiError, request } from './api'
import type { Health, Source, SourcePage } from './api'

const platformNames: Record<string, string> = {
  instagram: 'Instagram', youtube: 'YouTube', tiktok: 'TikTok', other: 'Web', local: 'Archivo',
}

function domain(url: string) {
  try { return new URL(url).hostname.replace(/^www\./, '') } catch { return 'Enlace guardado' }
}

function SourceRow({ source }: { source: Source }) {
  return <a className="source-row group" href={source.original_url} target="_blank" rel="noopener noreferrer">
    <span className={`source-icon platform-${source.platform}`}><CirclePlay size={21} strokeWidth={1.6} /></span>
    <span className="source-info">
      <strong>{source.title || domain(source.original_url)}</strong>
      <span>{platformNames[source.platform] || 'Web'}<i>·</i>{new Date(source.created_at).toLocaleDateString('es-CL', { day: 'numeric', month: 'short' })}</span>
    </span>
    <span className="source-pending"><span />Guardado</span>
    <ArrowUpRight size={17} className="source-arrow" aria-label="Abrir enlace en otra pestaña" />
  </a>
}

export default function App() {
  const [page, setPage] = useState<SourcePage>({ items: [], total: 0 })
  const [health, setHealth] = useState<Health | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const urlInput = useRef<HTMLInputElement>(null)
  const refreshSequence = useRef(0)

  const refresh = useCallback(async () => {
    const sequence = ++refreshSequence.current
    setLoading(true)
    setError('')
    try {
      const [nextHealth, nextPage] = await Promise.all([
        request<Health>('/health'), request<SourcePage>('/sources'),
      ])
      if (sequence !== refreshSequence.current) return
      setHealth(nextHealth)
      setPage(nextPage)
    } catch (e) {
      if (sequence !== refreshSequence.current) return
      setHealth(null)
      setError(e instanceof Error ? e.message : 'No pudimos cargar tu biblioteca.')
    } finally {
      if (sequence === refreshSequence.current) setLoading(false)
    }
  }, [])

  useEffect(() => { void refresh(); return () => { refreshSequence.current += 1 } }, [refresh])

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const saved = await request<Source>('/sources', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim(), title: title.trim() || null }),
      })
      setPage(previous => ({ items: [saved, ...previous.items].slice(0, 20), total: previous.total + 1 }))
      setUrl('')
      setTitle('')
      setNotice('Enlace guardado en tu computador. El análisis permanece detenido.')
      urlInput.current?.focus()
    } catch (e) {
      if (e instanceof ApiError && (e.status === 0 || e.status >= 500)) setHealth(null)
      setError(e instanceof Error ? e.message : 'No pudimos guardar el enlace.')
    } finally { setSaving(false) }
  }

  const connected = health?.database === 'connected'

  return <div className="app-shell">
    <a className="skip-link" href="#main">Ir al contenido</a>
    <aside className="sidebar">
      <a className="brand" href="#main" aria-label="ReelMind, inicio"><span className="brand-mark"><Layers3 size={23} strokeWidth={2} /></span><span>Reel<span className="font-normal">Mind</span></span></a>
      <div className="workspace"><span className="workspace-avatar"><Bookmark size={15} /></span><div><strong>Mi espacio</strong><span>Biblioteca personal</span></div><span className="workspace-dot" /></div>
      <p className="nav-label">TU BIBLIOTECA</p>
      <nav aria-label="Navegación principal"><a className="nav-item active" href="#main" aria-current="page"><Library size={18} /> Inicio <span className="nav-count">{connected ? page.total : '—'}</span></a></nav>
      <div className="upcoming"><p className="nav-label">MÁS ADELANTE</p><span><FolderOpen size={17} /> Proyectos</span><span><Sparkles size={17} /> Chat con tu biblioteca</span><span><Layers3 size={17} /> Conexiones</span><p>Tu espacio irá creciendo,<br />una etapa a la vez.</p></div>
      <div className="sidebar-footer"><HardDrive size={17} /><div><strong>En tu computador</strong><span>Tú tienes el control.</span></div></div>
    </aside>

    <div className="main-shell">
      <header className="topbar"><span>Mi espacio <ChevronRight size={14} /> <strong>Inicio</strong></span><span className={`connection ${connected ? 'online' : ''}`}><span />{loading ? 'Conectando…' : connected ? 'Conexión local activa' : 'Sin conexión local'}</span></header>
      <main id="main" className="main-content">
        <section className="welcome">
          <div><p className="eyebrow"><span /> MENOS ENLACES PERDIDOS. MÁS IDEAS A MANO.</p><h1>Un lugar para lo que<br /><span>quieres volver a ver.</span></h1><p className="welcome-copy">Reúne los vídeos que te inspiran.<br className="mobile-break" /> Tu próxima idea empieza con un enlace.</p></div>
          <div className="welcome-graphic" aria-hidden="true"><div className="graphic-orbit" /><div className="graphic-card back"><span /><span /><span /></div><div className="graphic-card front"><div className="graphic-play"><CirclePlay size={35} strokeWidth={1.2} /></div><div className="graphic-lines"><span /><span /></div><span className="graphic-bookmark"><Bookmark size={15} /></span></div><span className="graphic-spark">✦</span></div>
        </section>

        <section className="overview" aria-label="Resumen de tu espacio">
          <div className="overview-item"><span className="metric-icon"><Bookmark size={19} /></span><div><span className="metric-label">Enlaces guardados</span><strong>{loading ? '—' : connected ? String(page.total).padStart(2, '0') : '—'}</strong></div></div>
          <div className="overview-item"><span className="metric-icon"><CirclePause size={19} /></span><div><span className="metric-label">Análisis de vídeos</span><strong className="metric-text">Detenido<span className="status-dot" /></strong></div></div>
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
              <div className="form-footer"><span><ShieldCheck size={14} /> Guardado local</span><button className="primary-button" type="submit" disabled={saving || !connected || loading}>{saving ? <LoaderCircle className="animate-spin" size={17} /> : <Plus size={17} />}{saving ? 'Guardando…' : 'Guardar enlace'}</button></div>
            </form>
            {notice && <p className="notice" role="status"><Check size={16} />{notice}</p>}
          </section>

          <aside className="control-panel"><div className="control-top"><span className="control-icon"><CirclePause size={22} /></span><span className="small-tag">EN PAUSA</span></div><h2>A tu ritmo.</h2><p>Guardar un enlace no inicia su análisis. Tú decidirás cuándo procesar tus vídeos.</p><div className="control-note"><span />El análisis se incorporará<br />en una próxima etapa.</div><div className="control-bottom"><HardDrive size={14} /> Tu biblioteca se queda contigo.</div></aside>
        </div>

        {error && <div className="error-banner" role="alert"><span>{error}</span>{!connected && <button onClick={() => void refresh()} disabled={loading || saving}><RefreshCw size={15} /> Reintentar conexión</button>}</div>}

        <section className="library-section" aria-labelledby="library-heading">
          <div className="library-heading"><div><h2 id="library-heading">Últimos enlaces</h2><p>Un punto de partida para tus próximas ideas.</p></div><button className="icon-button" aria-label="Actualizar biblioteca" title="Actualizar biblioteca" onClick={() => { setNotice(''); void refresh() }} disabled={loading || saving}><RefreshCw size={17} className={loading ? 'animate-spin' : ''} /></button></div>
          {loading ? <div className="empty-state"><LoaderCircle className="animate-spin" size={26} /><p>Cargando tu biblioteca…</p></div> : page.items.length ? <div className="source-list">{page.items.map(source => <SourceRow source={source} key={source.id} />)}{page.total > page.items.length && <p className="list-footnote">Mostrando los {page.items.length} enlaces más recientes de {page.total}.</p>}</div> : <div className="empty-state"><span className="empty-icon"><Bookmark size={25} strokeWidth={1.4} /><span><Plus size={11} /></span></span><h3>{connected ? 'Tu primera idea tiene un lugar aquí.' : 'Tu biblioteca está esperando.'}</h3><p>{connected ? 'Añade un enlace arriba y empieza a construir tu colección.' : 'Inicia ReelMind y vuelve a conectar para ver tus enlaces.'}</p>{connected && <button className="text-button" onClick={() => urlInput.current?.focus()}><ArrowDownLeft size={15} /> Guardar mi primer enlace</button>}</div>}
        </section>
        <footer className="page-footer"><span>REELMIND <i>/</i> HECHO PARA VOLVER A LAS BUENAS IDEAS</span><span>Local por naturaleza.</span></footer>
      </main>
    </div>
  </div>
}
