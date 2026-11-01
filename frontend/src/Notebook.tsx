import { useEffect, useRef, useState } from 'react'
import { request } from './api'
import type { Source } from './api'
interface Note { id:string;version:number;source_id:string;content:string;quote_chunk_id:string|null;quote_text:string|null;start_ms:number|null;end_ms:number|null;favorite:boolean;archived:boolean }
interface Page {items:Note[];total:number}
const timestamp=(ms:number)=>`${Math.floor(ms/60000)}:${String(Math.floor(ms/1000)%60).padStart(2,'0')}`
export default function Notebook({source,onChanged,initialTime}:{source:Source;onChanged:()=>void;initialTime?:number}) {
  const [rows,setRows]=useState<Note[]>([]),[total,setTotal]=useState(0),[offset,setOffset]=useState(0),[archived,setArchived]=useState(false)
  const [content,setContent]=useState(''),[editing,setEditing]=useState<Note|null>(null),[start,setStart]=useState(''),[end,setEnd]=useState('')
  const [error,setError]=useState(''),[busy,setBusy]=useState(false),[history,setHistory]=useState<Note[]>([])
  const player=useRef<HTMLVideoElement>(null)
  useEffect(()=>{const controller=new AbortController();void request<Page>(`/notes?source_id=${source.id}&archived=${archived}&offset=${offset}&limit=20`,{signal:controller.signal}).then(p=>{setRows(p.items);setTotal(p.total)}).catch(e=>{if(!controller.signal.aborted)setError(e.message)});return()=>controller.abort()},[source.id,archived,offset])
  async function reload(){const p=await request<Page>(`/notes?source_id=${source.id}&archived=${archived}&offset=${offset}&limit=20`);setRows(p.items);setTotal(p.total);onChanged()}
  async function save(note?:Note,changes?:Partial<Note>){if(busy)return;setBusy(true);setError('');try{
    const base=note||editing
    const payload=changes?{...base,...changes,expected_version:base!.version}:{content,quote_chunk_id:base?.quote_chunk_id||null,start_ms:start===''?null:Math.round(Number(start)*1000),end_ms:end===''?null:Math.round(Number(end)*1000),favorite:base?.favorite||false,archived:base?.archived||false,expected_version:base?.version||0}
    await request(`/sources/${source.id}/notes${base?'/'+base.id:''}`,{method:base?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});await reload();setEditing(null);setContent('');setStart('');setEnd('');setHistory([])
  }catch(e){setError(e instanceof Error?e.message:'No se pudo guardar.')}finally{setBusy(false)}}
  function play(ms:number){if(player.current){player.current.currentTime=ms/1000;void player.current.play().catch(()=>setError('Pulsa reproducir para abrir el vídeo.'));player.current.scrollIntoView({block:'center'})}}
  return <section className="notebook"><h3>Vídeo y apuntes</h3>
    {source.assets.length===1?<video ref={player} controls preload="metadata" onLoadedMetadata={() => { if(player.current && initialTime !== undefined) player.current.currentTime=initialTime/1000 }} onError={() => setError('El navegador no pudo reproducir esta copia. Puedes abrir el archivo desde Archivos.')} src={`/api/assets/${source.assets[0].id}/content`} aria-label="Vídeo de la fuente" />:<p className="dialog-help">Abre una copia en Archivos. Los tiempos de apuntes requieren una fuente con una sola copia.</p>}
    <div className="retrieval-actions"><a className="secondary-button" href={`/api/sources/${source.id}/export`}>Exportar apuntes Markdown</a><a className="secondary-button" href={`/api/sources/${source.id}/export?format=json`}>Exportar JSON</a></div>
    <h4>{editing?'Editar apunte':'Guardar una idea propia'}</h4><p className="dialog-help">Tus apuntes se guardan separados del análisis automático. Editar conserva versiones.</p>
    <label>Apunte<textarea value={content} disabled={busy} onChange={e=>setContent(e.target.value)} maxLength={8000} rows={4}/></label>
    {source.assets.length===1&&<><div className="graph-fields"><label>Desde (segundos)<input type="number" min="0" step="0.1" value={start} disabled={busy} onChange={e=>setStart(e.target.value)}/></label><label>Hasta (segundos)<input type="number" min="0" step="0.1" value={end} disabled={busy} onChange={e=>setEnd(e.target.value)}/></label></div><button type="button" className="secondary-button" onClick={()=>{const value=Math.max(0,player.current?.currentTime||0);setStart(value.toFixed(1));setEnd((value+1).toFixed(1))}}>Usar momento del vídeo</button></>}
    {editing?.quote_text&&<blockquote>{editing.quote_text}</blockquote>}
    <div className="retrieval-actions"><button type="button" className="primary-button" disabled={busy||!content.trim()} onClick={()=>void save()}>Guardar apunte</button>{editing&&<button type="button" className="secondary-button" disabled={busy} onClick={()=>{setEditing(null);setContent('');setStart('');setEnd('')}}>Cancelar edición</button>}</div>
    <label>Ver apuntes<select value={String(archived)} disabled={busy} onChange={e=>{setArchived(e.target.value==='true');setOffset(0)}}><option value="false">Activos</option><option value="true">Archivados</option></select></label>
    {rows.map(n=><article className="saved-note" key={n.id}><small>Apunte personal · v{n.version}{n.favorite?' · Favorito':''}</small><p>{n.content}</p>{n.quote_text&&<><small>Cita exacta del fragmento guardado</small><blockquote>{n.quote_text}</blockquote></>}
      {n.start_ms!==null&&<button type="button" className="secondary-button" onClick={()=>play(n.start_ms!)}>Ver {timestamp(n.start_ms)}–{timestamp(n.end_ms!)}</button>}
      <div className="retrieval-actions"><button type="button" className="secondary-button" disabled={busy} onClick={()=>{setEditing(n);setContent(n.content);setStart(n.start_ms===null?'':String(n.start_ms/1000));setEnd(n.end_ms===null?'':String(n.end_ms/1000))}}>Editar apunte</button><button type="button" className="secondary-button" disabled={busy} onClick={()=>void save(n,{favorite:!n.favorite})}>{n.favorite?'Quitar favorito':'Favorito'}</button><button type="button" className="secondary-button" disabled={busy} onClick={()=>void save(n,{archived:!n.archived})}>{n.archived?'Restaurar':'Archivar'}</button><button type="button" className="secondary-button" onClick={()=>void request<Note[]>(`/sources/${source.id}/notes/${n.id}/history`).then(setHistory).catch(e=>setError(e.message))}>Ver versiones</button><button type="button" className="secondary-button" onClick={()=>void navigator.clipboard.writeText(`${n.content}\n${n.quote_text||''}\nFuente: ${source.title||source.assets[0]?.original_name||source.original_url} (${source.id}) · apunte v${n.version} · ms ${n.start_ms}–${n.end_ms}`).catch(()=>setError('No se pudo copiar. Puedes usar Exportar.'))}>Copiar</button></div>
    </article>)}
    {!rows.length&&<p className="dialog-help">No hay apuntes en esta vista.</p>}
    <div className="pagination"><span>{total} apuntes</span><button type="button" className="secondary-button" disabled={!offset} onClick={()=>setOffset(Math.max(0,offset-20))}>Anteriores</button><button type="button" className="secondary-button" disabled={offset+20>=total} onClick={()=>setOffset(offset+20)}>Siguientes</button></div>
    {!!history.length&&<details open><summary>Versiones del apunte</summary>{history.map(n=><p key={n.version}>v{n.version} · {n.archived?'Archivado':'Activo'}: {n.content}</p>)}</details>}
    {error&&<p className="dialog-error" role="alert">{error}</p>}
  </section>
}
