import { useCallback, useEffect, useRef, useState } from 'react'
import { Send, Plus, MessageSquare, RefreshCw, Square } from 'lucide-react'
import { request } from './api'
import { useSessionValue } from './persisted'

interface Hit {
  chunk_id: string; source_id: string; title: string; content: string; historical: boolean
  origin: { kind: string; version: number }; time_ms: number | null; start_ms: number | null; end_ms: number | null
}
interface Task {
  id: string; action: string; query: string; session_id: string | null; status: string
  help?:string; claims?: {text:string;quote:string;chunk_id:string}[]; fallback?:boolean; scope?: {project_id?:string|null};
  error_message: string | null; hits: Hit[]; selected: Hit[]; added: number | null; total: number | null
}
interface IndexStatus { ready: boolean; total: number; missing: number; current: Task | null }
interface Conversation { id: string; title: string; project_id:string|null; archived:boolean }
const active = (task: Task | null) => !!task && ['running', 'stop_requested'].includes(task.status)
const timestamp = (ms: number) => `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}`

function Citation({ hit, onSource }: { hit: Hit; onSource: (id: string, timeMs?:number) => void }) {
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  async function saveQuote() { if(saving || saved)return; setSaving(true); try { await request(`/sources/${hit.source_id}/notes`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:'Destacado guardado',quote_chunk_id:hit.chunk_id,start_ms:hit.start_ms??hit.time_ms,end_ms:hit.end_ms??(hit.time_ms===null?null:hit.time_ms+1)})}); setSaved(true) } catch(e) { setError(e instanceof Error ? e.message : 'No se pudo guardar.') } finally {setSaving(false)} }
  return <article className="retrieval-citation">
    <div><strong>{hit.title}</strong><span>{hit.origin.kind === 'audio' ? 'Transcripción' : hit.origin.kind === 'note' ? 'Apunte personal' : 'Observación visual'} · v{hit.origin.version}
      {hit.time_ms !== null ? ` · ${timestamp(hit.time_ms)}` : hit.start_ms !== null ? ` · ${timestamp(hit.start_ms)}–${timestamp(hit.end_ms!)}` : ''}
      {hit.historical && ' · Versión anterior'}</span></div>
    <blockquote>{hit.content}</blockquote>
    <button className="secondary-button" onClick={() => onSource(hit.source_id,hit.time_ms??hit.start_ms??undefined)}>Ver ficha de la fuente</button> <button className="secondary-button" disabled={saving || saved} onClick={() => void saveQuote()}>{saved ? 'Destacado guardado' : 'Guardar destacado'}</button>{error && <p role="alert" className="dialog-error">{error}</p>}
  </article>
}

export default function SearchPanel({ onSource, visible, contentRevision }: { onSource: (id: string, timeMs?:number) => void; visible: boolean; contentRevision: number }) {
  const [index, setIndex] = useState<IndexStatus | null>(null)
  const [task, setTask] = useState<Task | null>(null)
  const [sessions, setSessions] = useState<Conversation[]>([])
  const [sessionId, setSessionId] = useSessionValue('reelmind.chat')
  const [projects, setProjects] = useState<{id:string;name:string}[]>([])
  const [projectId,setProjectId]=useState('')
  const [mode,setMode]=useState('grounded')
  const [historyQuery,setHistoryQuery]=useState('')
  const [showArchived,setShowArchived]=useState(false)
  const [rename,setRename]=useState('')
  const [historyOffset,setHistoryOffset]=useState(0)
  const [sources,setSources]=useState<{id:string;label:string}[]>([])
  const [sourceFilter,setSourceFilter]=useState('')
  const [sourceQuery,setSourceQuery]=useState(''),[sourceOffset,setSourceOffset]=useState(0),[sourceTotal,setSourceTotal]=useState(0)
  const [help,setHelp]=useState(false)
  const [turns, setTurns] = useState<Task[]>([])
  const [query, setQuery] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const historySequence = useRef(0)
  const messages = useRef<HTMLDivElement>(null)
  useEffect(() => { if (messages.current) messages.current.scrollTop = messages.current.scrollHeight }, [turns, task?.id, task?.status])
  const running = active(task)
  const localHelp=['hola','buenas','ayuda','qué puedes hacer','que puedes hacer'].includes(query.toLowerCase().replace(/^[ ¿?¡!.,]+|[ ¿?¡!.,]+$/g,''))
  const busy = sending || running
  const selectedSession=sessions.find(s=>s.id===sessionId)
  useEffect(()=>{const c=new AbortController();void request<{id:string;name:string}[]>('/projects',{signal:c.signal}).then(setProjects).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[visible,contentRevision])
  useEffect(()=>{if(!visible)return;const c=new AbortController();void request<{items:{id:string;title:string|null;assets:{original_name:string}[];original_url:string|null}[];total:number}>(`/sources?limit=20&offset=${sourceOffset}&q=${encodeURIComponent(sourceQuery)}${projectId?'&project_id='+projectId:''}`,{signal:c.signal}).then(p=>{setSourceTotal(p.total);setSources(p.items.map(s=>({id:s.id,label:s.title||s.assets[0]?.original_name||s.original_url||'Fuente'})))}).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[visible,projectId,contentRevision,sourceQuery,sourceOffset])
  useEffect(()=>{if(!sessionId)return;const c=new AbortController();void request<Task[]>(`/retrieval/sessions/${sessionId}`,{signal:c.signal}).then(rows=>{setTurns(rows);setProjectId(rows[0]?.scope?.project_id||'')}).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[sessionId])
  async function changeConversation(archive:boolean){if(!selectedSession)return;try{await request(`/retrieval/sessions/${sessionId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:rename.trim()||selectedSession.title,archived:archive,expected_title:selectedSession.title,expected_archived:selectedSession.archived})});setRename('');setSessionId('');setTurns([]);await refresh()}catch(e){setError(e instanceof Error?e.message:'No se pudo guardar.')}}

  const refresh = useCallback(async (signal?: AbortSignal) => {
    const [status, history] = await Promise.all([
      request<IndexStatus>('/retrieval/status', { signal }), (async()=>{const rows:Conversation[]=[];for(let offset=0;offset<=historyOffset;offset+=100){rows.push(...await request<Conversation[]>(`/retrieval/sessions?archived=${showArchived}&q=${encodeURIComponent(historyQuery)}&offset=${offset}&limit=${Math.min(100,historyOffset+20-offset)}`,{signal}))}return rows})(),
    ])
    if (signal?.aborted) return
    setIndex(status); setSessions(history)
    if (status.current) setTask(status.current)
  }, [showArchived, historyQuery, historyOffset])

  useEffect(() => {
    if (!visible) return
    const controller = new AbortController()
    void refresh(controller.signal).catch(e => { if (!controller.signal.aborted) setError(e.message) })
    return () => controller.abort()
  }, [refresh, visible, contentRevision])

  useEffect(() => {
    if (!task || !active(task)) return
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout>
    const poll = async () => {
      try {
        const next = await request<Task>(`/retrieval/tasks/${task.id}`, { signal: controller.signal })
        if (controller.signal.aborted) return
        if (!active(next)) {
          if (next.session_id) {
            setSessionId(next.session_id)
            setTurns(await request<Task[]>(`/retrieval/sessions/${next.session_id}`, { signal: controller.signal }))
          }
          await refresh(controller.signal)
          if (!controller.signal.aborted) setTask(next)
        } else { setTask(next); timer = setTimeout(() => void poll(), 1200) }
      } catch (e) {
        if (!controller.signal.aborted) { setError(e instanceof Error ? e.message : 'No se pudo consultar el estado.'); timer = setTimeout(() => void poll(), 3000) }
      }
    }
    timer = setTimeout(() => void poll(), 500)
    return () => { controller.abort(); clearTimeout(timer) }
  }, [task?.id, running, refresh])

  async function start(action: 'index' | 'search' | 'chat') {
    setSending(true); setError('')
    try {
      const next = await request<{ id: string }>('/retrieval/tasks', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, query, session_id: action === 'chat' && sessionId ? sessionId : null, project_id: projectId || null, source_ids: sourceFilter ? [sourceFilter] : [], answer_mode: mode }),
      })
      const started = await request<Task>(`/retrieval/tasks/${next.id}`)
      setTask(started)
      if (action === 'chat') { setSessionId(started.session_id || ''); setQuery(''); setTurns(previous => [...previous, started]) }
      if (!active(started)) {
        if (started.session_id) { setSessionId(started.session_id); setTurns(await request<Task[]>(`/retrieval/sessions/${started.session_id}`)) }
        await refresh()
      }
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo iniciar la consulta.') }
    finally { setSending(false) }
  }

  async function loadHistory(id: string) {
    ++historySequence.current
    if(!id){setShowArchived(false);setHistoryQuery('');setHistoryOffset(0)}
    setSessionId(id); setTurns([]); setTask(null); setError(''); setQuery(''); setSourceFilter(''); setProjectId(sessions.find(s=>s.id===id)?.project_id||'')

  }

  return <section className="chat-workspace" aria-label="Chat con tu biblioteca">
    <aside className="chat-history" aria-label="Conversaciones">
      <button className="secondary-button" disabled={busy} onClick={() => void loadHistory('')}><Plus size={16} /> Nuevo chat</button>
      <p className="nav-label">CONVERSACIONES</p><label className="chat-history-search">Buscar conversaciones<input value={historyQuery} maxLength={240} onChange={e=>{setHistoryQuery(e.target.value);setHistoryOffset(0)}} /></label><label className="dialog-help"><input type="checkbox" checked={showArchived} onChange={e=>{setShowArchived(e.target.checked);setHistoryOffset(0)}}/> Archivadas</label>
      {sessions.map(s => <button className={`chat-history-item ${sessionId === s.id ? 'selected' : ''}`} key={s.id} disabled={busy} aria-pressed={sessionId === s.id} onClick={() => void loadHistory(s.id)}><MessageSquare size={15} /><span>{s.title}</span></button>)}
      <button className="secondary-button" disabled={busy||sessions.length<historyOffset+20} onClick={()=>setHistoryOffset(value=>value+20)}>Más conversaciones</button>
      {selectedSession && <details><summary>Gestionar conversación</summary><input value={rename} maxLength={120} placeholder={selectedSession.title} onChange={e=>setRename(e.target.value)}/><button className="secondary-button" disabled={busy||!rename.trim()} onClick={()=>void changeConversation(showArchived)}>Renombrar</button><button className="secondary-button" disabled={busy} onClick={()=>void changeConversation(!showArchived)}>{showArchived?'Restaurar chat':'Archivar chat'}</button><a className="secondary-button" href={`/api/retrieval/sessions/${sessionId}/export`}>Exportar chat</a></details>}
      {!sessions.length && <p className="dialog-help">Tus conversaciones aparecerán aquí.</p>}
      <details className="chat-index"><summary>Biblioteca disponible</summary><p className="dialog-help">{!index ? 'Cargando…' : !index.ready ? 'Falta preparar los modelos locales.' : `${index.total - index.missing} de ${index.total} fragmentos indexados.`}</p><button className="secondary-button" disabled={busy || !index?.ready} onClick={() => void start('index')}><RefreshCw size={14} /> Actualizar índice</button></details>
    </aside>
    <div className="chat-conversation">
      <header className="chat-header"><div><h1>Chat con tu biblioteca</h1><p>Conecta ideas y vuelve a las fuentes.</p></div><span>Local</span></header>
      <div className="chat-scope"><label>Consultar<select disabled={busy||!!sessionId} value={projectId} onChange={e=>{setProjectId(e.target.value);setSourceFilter('');setSourceOffset(0);setSourceQuery('')}}><option value="">Toda la biblioteca</option>{projects.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label><label>Buscar fuente<input value={sourceQuery} maxLength={240} disabled={busy} onChange={e=>{setSourceQuery(e.target.value);setSourceOffset(0)}}/><select aria-label="Fuente" value={sourceFilter} disabled={busy} onChange={e=>setSourceFilter(e.target.value)}><option value="">Todas las del alcance</option>{sourceFilter&&!sources.some(s=>s.id===sourceFilter)&&<option value={sourceFilter}>Fuente seleccionada</option>}{sources.map(s=><option key={s.id} value={s.id}>{s.label}</option>)}</select><span><button className="text-button" disabled={busy||!sourceOffset} onClick={()=>setSourceOffset(v=>Math.max(0,v-20))}>Fuentes anteriores</button><button className="text-button" disabled={busy||sourceOffset+20>=sourceTotal} onClick={()=>setSourceOffset(v=>v+20)}>Más fuentes</button></span></label><label>Respuesta<select value={mode} disabled={busy} onChange={e=>setMode(e.target.value)}><option value="grounded">Explicar con citas</option><option value="extractive">Solo citas originales</option></select></label><button className="text-button" onClick={()=>setHelp(value=>!value)}>Ayuda</button></div>
      {help&&<p className="dialog-help chat-help">Puedes pedir resúmenes, comparaciones o momentos de tus fuentes. Guarda destacados en Mis ideas. Para cambiar de proyecto abre un nuevo chat. Las respuestas automáticas pueden contener errores; contrasta siempre las citas.</p>}
      <div className="chat-messages" ref={messages} role="log" aria-label="Mensajes de la conversación" aria-live="polite">
        {!turns.length && !busy && <div className="chat-empty"><MessageSquare size={28} /><h2>¿Qué tienes en mente?</h2><p>Podemos explorar tus vídeos, comparar ideas o retomar una conversación. Las respuestas se apoyan en lo que ya analizaste.</p><button className="secondary-button" onClick={() => { setQuery('¿Qué ideas aparecen en mis vídeos?'); document.getElementById('library-question')?.focus() }}>Explorar mi biblioteca</button></div>}
        {turns.map(turn => <div className="chat-exchange" key={turn.id}>
          <div className="chat-user"><span>Tú</span><p>{turn.query}</p></div>
          <div className="chat-assistant"><span>ReelMind</span>{turn.status === 'completed' ? <>
            <p>{turn.help || (turn.selected.length ? turn.claims?.length ? 'Respuesta basada en tus fuentes:' : 'Citas originales relacionadas con tu pregunta:' : 'No encuentro evidencia suficiente en tus vídeos para responder a esto. Puedes reformularlo o añadir y analizar una fuente relacionada.')}</p>
            {turn.claims?.map((claim,i)=><p className="grounded-claim" key={i}>{claim.text} <small>[{turn.selected.findIndex(h=>h.chunk_id===claim.chunk_id)+1}]</small></p>)}
            {turn.fallback&&<p className="dialog-help">La explicación no pasó la validación. Se conservan solo citas originales.</p>}
            {turn.selected.map(h => <details className="chat-source" key={h.chunk_id} open><summary>Fuente · {h.origin.kind === 'audio' ? 'Audio' : h.origin.kind==='note'?'Apunte':'Visual'} · {timestamp(h.time_ms ?? h.start_ms ?? 0)}</summary><Citation hit={h} onSource={onSource} /></details>)}
            <button className="secondary-button" onClick={()=>void navigator.clipboard.writeText([turn.help||'',...(turn.claims||[]).map(c=>c.text),...turn.selected.map(h=>`${h.content}\nFuente: ${h.title} (${h.source_id}) · ${h.origin.kind} v${h.origin.version} · ${timestamp(h.time_ms??h.start_ms??0)}`)].filter(Boolean).join('\n\n')||'Sin evidencia suficiente.').catch(()=>setError('No se pudo copiar. Puedes exportar el chat desde Gestionar conversación.'))}>Copiar respuesta con citas</button>
          </> : <p role="status">{turn.error_message || (task?.status === 'stop_requested' ? 'Deteniendo…' : 'Revisando tu biblioteca…')}</p>}</div>
        </div>)}
        {task?.action === 'search' && task.status==='completed' && <section><h3>Fragmentos encontrados</h3>{task.hits.length?task.hits.map(h=><Citation key={h.chunk_id} hit={h} onSource={onSource}/>):<p>No hay evidencia suficiente para esta búsqueda.</p>}</section>}
        {task?.action === 'index' && <p role="status" className="dialog-help">{active(task) ? 'Actualizando el índice…' : task.status === 'completed' ? `Índice actualizado: ${task.total} fragmentos disponibles.` : task.error_message}</p>}
      </div>
      <div className="chat-composer">
        {error && <p className="dialog-error" role="alert">{error}<button className="secondary-button" onClick={() => void refresh().then(() => setError('')).catch(e => setError(e.message))}>Reintentar</button></p>}
        {!!index?.missing && <p className="dialog-help">Hay evidencias nuevas. Actualiza el índice en «Biblioteca disponible» para conversar.</p>}
        <form onSubmit={event => { event.preventDefault(); if (!busy && query.trim() && (localHelp || index?.ready && !index.missing)) void start('chat') }}>
          <label className="sr-only" htmlFor="library-question">Mensaje para ReelMind</label>
          <textarea id="library-question" value={query} onChange={event => setQuery(event.target.value)} maxLength={800} rows={2} placeholder="Escribe un mensaje…" disabled={busy} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); event.currentTarget.form?.requestSubmit() } }} />
          {running ? <button type="button" className="secondary-button" disabled={task?.status === 'stop_requested'} onClick={() => { void request<Task>(`/retrieval/tasks/${task!.id}/stop`, { method: 'POST' }).then(next => { setTask(next); setTurns(previous => previous.map(t => t.id === next.id ? next : t)) }).catch(e => setError(e.message)) }}><Square size={15} /> Detener</button> : <><button type="button" className="secondary-button" disabled={busy||!query.trim()||!index?.ready||!!index.missing} onClick={()=>void start('search')}>Buscar contenido</button><button className="primary-button" aria-label="Enviar mensaje" disabled={busy || !query.trim() || (!localHelp && (!index?.ready || !!index?.missing)) || !!selectedSession?.archived}><Send size={17} /></button></>}
        </form>
        <p>Enter para enviar · Mayús + Enter para otra línea. Respuestas automáticas con citas originales. Pueden contener errores.</p>
      </div>
    </div>
  </section>
}
