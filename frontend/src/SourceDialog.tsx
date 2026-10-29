import { useEffect, useRef, useState } from 'react'
import { LoaderCircle, X } from 'lucide-react'
import { request } from './api'
import type { Source } from './api'

export type SourceAction = 'edit' | 'trash' | 'restore'
export interface Selection { source: Source; action: SourceAction }

export default function SourceDialog({ selection, onClose, onSaved }: {
  selection: Selection; onClose: () => void; onSaved: (message: string) => void
}) {
  const { source, action } = selection
  const dialog = useRef<HTMLDialogElement>(null)
  const [title, setTitle] = useState(source.title || '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submitting = useRef(false)
  const heading = action === 'edit' ? 'Editar título' : action === 'trash' ? 'Mover a la papelera' : 'Restaurar enlace'

  useEffect(() => {
    const element = dialog.current
    element?.showModal()
    element?.querySelector('input')?.focus()
    return () => element?.close()
  }, [])

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting.current) return
    submitting.current = true
    setBusy(true)
    setError('')
    try {
      await request<Source>(`/sources/${source.id}${action === 'restore' ? '/restore' : ''}`, {
        method: action === 'edit' ? 'PATCH' : action === 'trash' ? 'DELETE' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expected_updated_at: source.updated_at, ...(action === 'edit' ? { title: title.trim() || null } : {}) }),
      })
      onSaved(action === 'edit' ? 'Título actualizado.' : action === 'trash' ? 'Enlace en la papelera. Puedes restaurarlo cuando quieras.' : 'Enlace restaurado en tu biblioteca.')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No pudimos guardar el cambio.')
    } finally { submitting.current = false; setBusy(false) }
  }

  return <dialog ref={dialog} className="source-dialog" aria-labelledby="dialog-title" onCancel={event => { event.preventDefault(); if (!submitting.current) onClose() }}>
    <form onSubmit={submit}>
      <div className="dialog-heading"><h2 id="dialog-title">{heading}</h2><button type="button" className="icon-button" aria-label="Cerrar cuadro" onClick={onClose} disabled={busy}><X size={18} /></button></div>
      <p className="dialog-source">{source.title || source.original_url}</p>
      {action === 'edit' ? <><label htmlFor="edit-title">Un nombre para recordarlo</label><input id="edit-title" value={title} maxLength={240} autoFocus disabled={busy} onChange={event => setTitle(event.target.value)} /><p className="dialog-help">Opcional, hasta 240 caracteres. El enlace original se conserva.</p></> : <p className="dialog-help">{action === 'trash' ? 'El enlace saldrá de la biblioteca. Sus datos se conservan y podrás recuperarlo desde la papelera.' : 'Volverá a tu biblioteca con sus datos originales. Esto no descarga ni analiza el vídeo.'}</p>}
      {error && <p className="dialog-error" role="alert">{error}</p>}
      <div className="dialog-actions"><button type="button" className="secondary-button" disabled={busy} onClick={onClose}>Cancelar</button><button type="submit" className={action === 'trash' ? 'danger-button' : 'primary-button'} disabled={busy}>{busy && <LoaderCircle size={16} className="animate-spin" />}{busy ? 'Guardando…' : heading}</button></div>
    </form>
  </dialog>
}
