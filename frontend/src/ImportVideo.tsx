import { useRef, useState } from 'react'
import { ApiError, request } from './api'
import type { Source } from './api'

export default function ImportVideo({ source, disabled, onSaved, onDuplicate, onBusy }: {
  source?: Source; disabled?: boolean; onSaved: () => void; onDuplicate?: (source: Source) => void; onBusy?: (busy: boolean) => void
}) {
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const input = useRef<HTMLInputElement>(null)
  const submitting = useRef(false)
  async function upload() {
    if (!file || submitting.current) return
    submitting.current = true
    setBusy(true); onBusy?.(true); setError('')
    try {
      const params = new URLSearchParams({ filename: file.name })
      if (source) { params.set('source_id', source.id); params.set('expected_updated_at', source.updated_at) }
      await request<Source>(`/imports?${params}`, { method: 'POST', body: file, headers: { 'Content-Type': 'application/octet-stream' }, signal: AbortSignal.timeout(30 * 60 * 1000) })
      setFile(null)
      if (input.current) input.current.value = ''
      onSaved()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo importar el vídeo.')
      if (e instanceof ApiError && e.existingSource?.deleted_at) onDuplicate?.(e.existingSource)
    } finally { submitting.current = false; setBusy(false); onBusy?.(false) }
  }
  return <div className="import-video">
    <label htmlFor={source ? 'attach-video' : 'import-video'}>{source ? 'Adjuntar una copia a esta fuente' : 'O importa un vídeo de tu equipo'}</label>
    <input id={source ? 'attach-video' : 'import-video'} ref={input} type="file" accept=".mp4,.mov,.m4v,.webm,.mkv,.avi" disabled={busy || disabled} onChange={event => { setFile(event.target.files?.[0] ?? null); setError('') }} />
    <p className="dialog-help">MP4, MOV, M4V, WebM, MKV o AVI · Hasta 2 GiB por defecto. Se conserva tu original. La reproducción depende del navegador.</p>
    <button type="button" className="secondary-button" disabled={!file || busy || disabled} onClick={() => void upload()}>{busy ? 'Copiando vídeo… Mantén esta ventana abierta.' : 'Importar vídeo'}</button>
    {error && <p role="alert" className="dialog-error">{error}</p>}
  </div>
}
