import { useCallback, useEffect, useRef, useState } from 'react'
import { Send, Plus, MessageSquare, RefreshCw, Square } from 'lucide-react'
import { request } from './api'

interface Hit {
  chunk_id: string; source_id: string; title: string; content: string; historical: boolean
  origin: { kind: string; version: number }; time_ms: number | null; start_ms: number | null; end_ms: number | null
}
interface Task {
  id: string; action: string; query: string; session_id: string | null; status: string
  error_message: string | null; hits: Hit[]; selected: Hit[]; added: number | null; total: number | null
}
interface IndexStatus { ready: boolean; total: number; missing: number; current: Task | null }
interface Conversation { id: string; title: string }
const active = (task: Task | null) => !!task && ['running', 'stop_requested'].includes(task.status)
const timestamp = (ms: number) => `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}`

function Citation({ hit, onSource }: { hit: Hit; onSource: (id: string) => void }) {
  return <article className="retrieval-citation">
    <div><strong>{hit.title}</strong><span>{hit.origin.kind === 'audio' ? 'Transcripción' : 'Observación visual'} · v{hit.origin.version}
      {hit.time_ms !== null ? ` · ${timestamp(hit.time_ms)}` : hit.start_ms !== null ? ` · ${timestamp(hit.start_ms)}–${timestamp(hit.end_ms!)}` : ''}
      {hit.historical && ' · Versión anterior'}</span></div>
    <blockquote>{hit.content}</blockquote>
    <button className="secondary-button" onClick={() => onSource(hit.source_id)}>Ver ficha de la fuente</button>
  </article>
}

export default function SearchPanel({ onSource }: { onSource: (id: string) => void }) {
  const [index, setIndex] = useState<IndexStatus | null>(null)
  const [task, setTask] = useState<Task | null>(null)
  const [sessions, setSessions] = useState<Conversation[]>([])
  const [sessionId, setSessionId] = useState('')
  const [turns, setTurns] = useState<Task[]>([])
  const [query, setQuery] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const historySequence = useRef(0)
  const messages = useRef<HTMLDivElement>(null)
  useEffect(() => { if (messages.current) messages.current.scrollTop = messages.current.scrollHeight }, [turns, task?.id, task?.status])
  const running = active(task)
  const busy = sending || running

  const refresh = useCallback(async (signal?: AbortSignal) => {
    const [status, history] = await Promise.all([
      request<IndexStatus>('/retrieval/status', { signal }), request<Conversation[]>('/retrieval/sessions', { signal }),
    ])
    if (signal?.aborted) return
    setIndex(status); setSessions(history)
    if (status.current) setTask(status.current)
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    void refresh(controller.signal).catch(e => { if (!controller.signal.aborted) setError(e.message) })
    return () => controller.abort()
  }, [refresh])

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
        body: JSON.stringify({ action, query, session_id: action === 'chat' && sessionId ? sessionId : null }),
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
    const sequence = ++historySequence.current
    setSessionId(id); setTurns([]); setTask(null); setError(''); setQuery('')
    if (!id) return
    try {
      const history = await request<Task[]>(`/retrieval/sessions/${id}`)
      if (sequence === historySequence.current) setTurns(history)
    } catch (e) { if (sequence === historySequence.current) setError(e instanceof Error ? e.message : 'No se pudo abrir la conversación.') }
  }

  return <section className="chat-workspace" aria-label="Chat con tu biblioteca">
    <aside className="chat-history" aria-label="Conversaciones">
      <button className="secondary-button" disabled={busy} onClick={() => void loadHistory('')}><Plus size={16} /> Nuevo chat</button>
      <p className="nav-label">CONVERSACIONES</p>
      {sessions.map(s => <button className={`chat-history-item ${sessionId === s.id ? 'selected' : ''}`} key={s.id} disabled={busy} aria-pressed={sessionId === s.id} onClick={() => void loadHistory(s.id)}><MessageSquare size={15} /><span>{s.title}</span></button>)}
      {!sessions.length && <p className="dialog-help">Tus conversaciones aparecerán aquí.</p>}
      <details className="chat-index"><summary>Biblioteca disponible</summary><p className="dialog-help">{!index ? 'Cargando…' : !index.ready ? 'Falta preparar los modelos locales.' : `${index.total - index.missing} de ${index.total} fragmentos indexados.`}</p><button className="secondary-button" disabled={busy || !index?.ready} onClick={() => void start('index')}><RefreshCw size={14} /> Actualizar índice</button></details>
    </aside>
    <div className="chat-conversation">
      <header className="chat-header"><div><h1>Chat con tu biblioteca</h1><p>Conecta ideas y vuelve a las fuentes.</p></div><span>Local</span></header>
      <div className="chat-messages" ref={messages} role="log" aria-label="Mensajes de la conversación" aria-live="polite">
        {!turns.length && !busy && <div className="chat-empty"><MessageSquare size={28} /><h2>¿Qué tienes en mente?</h2><p>Podemos explorar tus vídeos, comparar ideas o retomar una conversación. Las respuestas se apoyan en lo que ya analizaste.</p><button className="secondary-button" onClick={() => { setQuery('¿Qué ideas aparecen en mis vídeos?'); document.getElementById('library-question')?.focus() }}>Explorar mi biblioteca</button></div>}
        {turns.map(turn => <div className="chat-exchange" key={turn.id}>
          <div className="chat-user"><span>Tú</span><p>{turn.query}</p></div>
          <div className="chat-assistant"><span>ReelMind</span>{turn.status === 'completed' ? <>
            <p>{turn.selected.length ? 'Esto es lo que encuentro en tus vídeos sobre lo que preguntas:' : 'No encuentro evidencia suficiente en tus vídeos para responder a esto. Puedes reformularlo o añadir y analizar una fuente relacionada.'}</p>
            {turn.selected.map(h => <details className="chat-source" key={h.chunk_id} open><summary>Fuente · {h.origin.kind === 'audio' ? 'Audio' : 'Visual'} · {timestamp(h.time_ms ?? h.start_ms ?? 0)}</summary><Citation hit={h} onSource={onSource} /></details>)}
          </> : <p role="status">{turn.error_message || (task?.status === 'stop_requested' ? 'Deteniendo…' : 'Revisando tu biblioteca…')}</p>}</div>
        </div>)}
        {task?.action === 'index' && <p role="status" className="dialog-help">{active(task) ? 'Actualizando el índice…' : task.status === 'completed' ? `Índice actualizado: ${task.total} fragmentos disponibles.` : task.error_message}</p>}
      </div>
      <div className="chat-composer">
        {error && <p className="dialog-error" role="alert">{error}<button className="secondary-button" onClick={() => void refresh().then(() => setError('')).catch(e => setError(e.message))}>Reintentar</button></p>}
        {!!index?.missing && <p className="dialog-help">Hay evidencias nuevas. Actualiza el índice en «Biblioteca disponible» para conversar.</p>}
        <form onSubmit={event => { event.preventDefault(); if (!busy && query.trim() && index?.ready && !index.missing) void start('chat') }}>
          <label className="sr-only" htmlFor="library-question">Mensaje para ReelMind</label>
          <textarea id="library-question" value={query} onChange={event => setQuery(event.target.value)} maxLength={800} rows={2} placeholder="Escribe un mensaje…" disabled={busy} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); event.currentTarget.form?.requestSubmit() } }} />
          {running ? <button type="button" className="secondary-button" disabled={task?.status === 'stop_requested'} onClick={() => { void request<Task>(`/retrieval/tasks/${task!.id}/stop`, { method: 'POST' }).then(next => { setTask(next); setTurns(previous => previous.map(t => t.id === next.id ? next : t)) }).catch(e => setError(e.message)) }}><Square size={15} /> Detener</button> : <button className="primary-button" aria-label="Enviar mensaje" disabled={busy || !query.trim() || !index?.ready || !!index.missing}><Send size={17} /></button>}
        </form>
        <p>Enter para enviar · Mayús + Enter para otra línea. Citas automáticas en su idioma original; pueden contener errores.</p>
      </div>
    </div>
  </section>
}
