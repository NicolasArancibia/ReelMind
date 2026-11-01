import { useEffect, useRef, useState } from 'react'
import { request } from './api'
import type { Health } from './api'

export const engineNames: Record<string, string> = { stopped: 'Detenido', running: 'Analizando', pause_requested: 'Pausando al terminar', paused: 'En pausa', stop_requested: 'Deteniendo' }
export const jobNames: Record<string, string> = { pending: 'Pendiente', cancelled: 'Fuera de cola', running: 'Analizando', completed: 'Procesado', failed: 'Error recuperable', stopped: 'Interrumpido', unavailable: 'Necesita un archivo' }

export default function AudioPanel({ onChange }: { onChange: () => void }) {
  const [state, setState] = useState<Health['processing'] | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [audiovisual, setAudiovisual] = useState(true)
  const previous = useRef('')
  const onChangeRef = useRef(onChange)
  onChangeRef.current = onChange
  useEffect(() => {
    let cancelled = false
    let timer: ReturnType<typeof setTimeout>
    async function poll() {
      try {
        const next = await request<Health['processing']>('/processing')
        if (cancelled) return
        setState(next)
        const key = `${next.state}-${next.active_source_id}`
        if (previous.current && key !== previous.current) onChangeRef.current()
        previous.current = key
      } catch { if (!cancelled) setState(null) }
      if (!cancelled) timer = setTimeout(() => void poll(), 1500)
    }
    void poll()
    return () => { cancelled = true; clearTimeout(timer) }
  }, [])
  async function control(action: string) {
    setBusy(true); setError('')
    try { setState(await request<Health['processing']>(`/processing/${action}?mode=${audiovisual ? 'audiovisual' : 'audio'}`, { method: 'POST' })); previous.current = '__control__'; onChangeRef.current() }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudo cambiar el motor.') }
    finally { setBusy(false) }
  }
  const idle = state && ['stopped', 'paused'].includes(state.state)
  return <aside className="control-panel audio-panel">
    <div className="control-top"><span className="small-tag" role="status">{state ? engineNames[state.state] : 'Sin conexión'}</span></div>
    <h2>Vuelve a tus ideas.</h2>
    <p>Analiza las copias locales de tus pendientes. Cada inicio toma la cola actual; guardar o importar nunca activa el análisis.</p>
    <label className="dialog-help"><input type="checkbox" checked={audiovisual} disabled={busy || !idle} onChange={event => setAudiovisual(event.target.checked)} /> Incluir visión y síntesis</label>
    {audiovisual && <p className="dialog-help">Revisa fotogramas muestreados y audio. Puede omitir escenas o texto; contrasta la ficha con el original.</p>}
    <div className="audio-controls">
      <button className="primary-button" disabled={busy || !idle || !state?.available || (audiovisual && !state?.audiovisual_available)} onClick={() => void control('start')}>{state?.state === 'paused' ? 'Reanudar' : 'Iniciar'}</button>
      <button className="secondary-button" disabled={busy || state?.state !== 'running'} onClick={() => void control('pause')}>Pausar</button>
      <button className="secondary-button" disabled={busy || !state || state.state === 'stopped'} onClick={() => void control('stop')}>Detener</button>
    </div>
    <p className="dialog-help">Pausar termina el vídeo actual. Detener cancela el actual; para reintentarlo, vuelve a encolarlo. Los resultados anteriores se conservan.</p>
    {state && !state.available && <p className="dialog-error">Falta preparar el modelo local. Consulta la preparación de audio en README.</p>}
    {audiovisual && state && !state.audiovisual_available && <p className="dialog-error">Visión y síntesis aún no están preparadas. Consulta README.</p>}
    {error && <p className="dialog-error" role="alert">{error}</p>}
  </aside>
}

interface Transcript {
  id: string; version: number; outcome: string; language: string | null; duration_ms: number
  provenance: { model: string; provider_version: string; device: string; compute_type: string; source_sha256: string; original_name: string }
  segments: { start_ms: number; end_ms: number; text: string }[]
}

function timestamp(ms: number) { return `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}` }

export function Transcripts({ sourceId }: { sourceId: string }) {
  const [rows, setRows] = useState<Transcript[] | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let alive = true
    request<Transcript[]>(`/sources/${sourceId}/transcripts`).then(value => { if (alive) setRows(value) }).catch(e => { if (alive) setError(e.message) })
    return () => { alive = false }
  }, [sourceId])
  return <div className="transcripts">
    <Analyses sourceId={sourceId} />
    <p className="dialog-help">Transcripción automática: puede contener errores. «Sin voz detectada» no demuestra ausencia de habla. No incluye interpretación visual.</p>
    {error && <p role="alert">{error}</p>}
    {!rows && !error && <p>Cargando transcripciones…</p>}
    {rows?.length === 0 && <p>Aún no hay transcripción. Adjunta una copia local, añádela a pendientes e inicia el motor.</p>}
    {rows?.map((row, index) => <details key={row.id} open={index === 0}>
      <summary>Versión {row.version} · {row.outcome === 'speech' ? 'Voz transcrita' : row.outcome === 'no_audio' ? 'Sin pista de audio' : 'Sin voz detectada'}</summary>
      <p className="dialog-help">{row.provenance.original_name} · {timestamp(row.duration_ms)} · {row.language || 'Sin idioma'}<br />{row.provenance.model} · faster-whisper {row.provenance.provider_version} · {row.provenance.device} {row.provenance.compute_type}</p>
      {row.segments.map((segment, ordinal) => <p className="transcript-segment" key={ordinal}><span>{timestamp(segment.start_ms)}–{timestamp(segment.end_ms)}</span>{segment.text}</p>)}
    </details>)}
  </div>
}

interface Analysis {
  id: string; version: number
  evidence: { id: string; kind: string; time_ms?: number; start_ms?: number; end_ms?: number; description?: string; visible_text?: string; uncertain?: boolean; ocr_unusable?: boolean; text?: string }[]
  synthesis: { claims: { text: string; evidence_ids: string[] }[]; limitations: string[] }
  limitations: string[]
  coverage: { sampled_frames: number; audio_segments_used: number; audio_segments_total: number }
  provenance: { vision_model: string; text_model: string; synthesis_mode?: string }
}

function Analyses({ sourceId }: { sourceId: string }) {
  const [rows, setRows] = useState<Analysis[] | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let alive = true
    request<Analysis[]>(`/sources/${sourceId}/analyses`).then(value => { if (alive) setRows(value) }).catch(e => { if (alive) setError(e.message) })
    return () => { alive = false }
  }, [sourceId])
  return <section aria-label="Análisis audiovisual">
    {error && <p role="alert">{error}</p>}
    {rows?.length === 0 && <p className="dialog-help">Sin ficha audiovisual. Para crearla, encola la fuente y elige Incluir visión y síntesis antes de iniciar.</p>}
    {rows?.map((row, index) => <details key={row.id} open={index === 0}>
      <summary>Ficha audiovisual · Versión {row.version} · Cobertura parcial</summary>
      <p className="dialog-help">{row.coverage.sampled_frames} fotogramas · Audio: {row.coverage.audio_segments_used}/{row.coverage.audio_segments_total} segmentos · {row.provenance.vision_model} / {row.provenance.text_model}</p>
      <h3>Observaciones destacadas</h3>
      {row.provenance.synthesis_mode !== 'extractive' && <p className="dialog-error">Versión experimental anterior. Sus referencias requieren revisión.</p>}
      <p className="dialog-help">Esta ficha describe el vídeo; no verifica sus afirmaciones.</p>
      {row.synthesis.claims.length === 0 && <p>No hay evidencia suficiente para sintetizar.</p>}
      {row.synthesis.claims.map((claim, i) => <p key={i}>{claim.text} <small>{claim.evidence_ids.map(id => <a key={id} href={`#evidence-${row.id}-${id}`}> [{id}] </a>)}</small></p>)}
      <h3>Evidencias</h3>
      {row.evidence.map(item => <p className="transcript-segment" id={`evidence-${row.id}-${item.id}`} key={item.id}><span>{item.id} · {timestamp(item.time_ms ?? item.start_ms ?? 0)} · {item.kind === 'visual' ? 'Visual' : 'Audio'}</span>{item.description || item.text}{item.visible_text && <> Texto visible: {item.visible_text}</>}{item.ocr_unusable && <> · Texto visual no recuperado de forma fiable</>}{item.uncertain && <> · Observación incierta</>}</p>)}
      <h3>Límites</h3>
      {[...row.limitations, ...row.synthesis.limitations].map((limit, i) => <p className="dialog-help" key={i}>{limit}</p>)}
    </details>)}
  </section>
}
