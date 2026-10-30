import { useEffect, useRef, useState } from 'react'
import { LoaderCircle, X } from 'lucide-react'
import { request } from './api'
import type { Source } from './api'
import ImportVideo from './ImportVideo'

export type SourceAction = 'edit' | 'trash' | 'restore' | 'organize' | 'files' | 'queue'
export interface Selection { source: Source; action: SourceAction }

export default function SourceDialog({ selection, onClose, onSaved }: {
  selection: Selection; onClose: () => void; onSaved: (message: string) => void
}) {
  const { source, action } = selection
  const dialog = useRef<HTMLDialogElement>(null)
  const [title, setTitle] = useState(source.title || '')
  const [tags, setTags] = useState(source.tags.map(item => item.name).join(', '))
  const [categories, setCategories] = useState(source.categories.map(item => item.name).join(', '))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submitting = useRef(false)
  const heading = { edit: 'Editar título', trash: 'Mover a la papelera', restore: 'Restaurar fuente', organize: 'Organizar fuente', files: 'Archivos de la fuente', queue: source.job?.status === 'pending' ? 'Retirar de pendientes' : 'Añadir a pendientes' }[action]

  useEffect(() => {
    const element = dialog.current
    element?.showModal()
    element?.querySelector('input')?.focus()
    return () => element?.close()
  }, [])

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting.current || action === 'files') return
    submitting.current = true; setBusy(true); setError('')
    try {
      const split = (value: string) => value.split(',').map(item => item.trim()).filter(Boolean)
      const suffix = action === 'organize' ? '/organization' : action === 'queue' ? '/queue' : action === 'restore' ? '/restore' : ''
      await request<Source>(`/sources/${source.id}${suffix}`, {
        method: action === 'organize' || action === 'queue' ? 'PUT' : action === 'edit' ? 'PATCH' : action === 'trash' ? 'DELETE' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expected_updated_at: source.updated_at, ...(action === 'edit' ? { title: title.trim() || null } : action === 'organize' ? { tags: split(tags), categories: split(categories) } : action === 'queue' ? { queued: source.job?.status !== 'pending' } : {}) }),
      })
      onSaved(action === 'edit' ? 'Título actualizado.' : action === 'trash' ? 'Fuente en la papelera. Datos y archivos conservados.' : action === 'restore' ? 'Fuente restaurada.' : action === 'organize' ? 'Organización guardada.' : 'Cola actualizada. El motor sigue detenido.')
    } catch (e) { setError(e instanceof Error ? e.message : 'No pudimos guardar el cambio.') }
    finally { submitting.current = false; setBusy(false) }
  }

  return <dialog ref={dialog} className="source-dialog" aria-labelledby="dialog-title" onCancel={event => { event.preventDefault(); if (!submitting.current) onClose() }}>
    <form onSubmit={submit}>
      <div className="dialog-heading"><h2 id="dialog-title">{heading}</h2><button type="button" className="icon-button" aria-label="Cerrar cuadro" onClick={onClose} disabled={busy}><X size={18} /></button></div>
      <p className="dialog-source">{source.title || source.original_url || 'Vídeo local'}</p>
      {action === 'edit' && <><label htmlFor="edit-title">Un nombre para recordarlo</label><input id="edit-title" value={title} maxLength={240} autoFocus disabled={busy} onChange={event => setTitle(event.target.value)} /><p className="dialog-help">Opcional, hasta 240 caracteres. La fuente original se conserva.</p></>}
      {action === 'organize' && <><label htmlFor="edit-categories">Categorías, separadas por comas</label><input id="edit-categories" value={categories} disabled={busy} onChange={event => setCategories(event.target.value)} /><label htmlFor="edit-tags">Etiquetas, separadas por comas</label><input id="edit-tags" value={tags} disabled={busy} onChange={event => setTags(event.target.value)} /><p className="dialog-help">Hasta 10 categorías y 20 etiquetas; 60 caracteres por nombre. Puedes crear nombres aquí, reutilizarlos o vaciar el campo para quitar las asociaciones.</p></>}
      {action === 'files' && <><div className="asset-list">{source.assets.length ? source.assets.map(asset => <a key={asset.id} href={`/api/assets/${asset.id}/content`} target="_blank" rel="noopener noreferrer">{asset.original_name} · {(asset.file.size_bytes / 1024 / 1024).toFixed(2)} MiB ↗</a>) : <p className="dialog-help">Todavía no hay un archivo asociado.</p>}</div><ImportVideo source={source} onBusy={value => { submitting.current = value; setBusy(value) }} onSaved={() => onSaved('Copia guardada y asociada a la fuente.')} /></>}
      {action === 'trash' && <p className="dialog-help">La fuente saldrá de la biblioteca y de pendientes. Sus datos, etiquetas y archivos se conservan para restaurarlos. No se borra tu original.</p>}
      {action === 'restore' && <p className="dialog-help">Recuperará sus datos y su estado previo de pendientes. Esto no inicia análisis.</p>}
      {action === 'queue' && <p className="dialog-help">{source.job?.status === 'pending' ? 'La fuente seguirá en la biblioteca, fuera de la cola.' : 'Se añadirá al final de la cola para un análisis futuro.'} El motor permanece detenido.</p>}
      {error && <p className="dialog-error" role="alert">{error}</p>}
      <div className="dialog-actions"><button type="button" className="secondary-button" disabled={busy} onClick={onClose}>{action === 'files' ? 'Cerrar' : 'Cancelar'}</button>{action !== 'files' && <button type="submit" className={action === 'trash' ? 'danger-button' : 'primary-button'} disabled={busy}>{busy && <LoaderCircle size={16} className="animate-spin" />}{busy ? 'Guardando…' : heading}</button>}</div>
    </form>
  </dialog>
}
