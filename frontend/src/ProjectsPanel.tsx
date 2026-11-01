import { lazy, Suspense, useEffect, useState } from 'react'
import { request } from './api'
import type { SourcePage } from './api'
const ProjectGraph=lazy(()=>import('./ProjectGraph'))
interface Project { id:string; name:string }
interface Member { id:string; title:string }
export default function ProjectsPanel({ onSource }:{onSource:(id:string)=>void}) {
  const [projects,setProjects]=useState<Project[]>([]), [selected,setSelected]=useState(''), [name,setName]=useState('')
  const [members,setMembers]=useState<Member[]>([]), [sources,setSources]=useState<SourcePage | null>(null), [sourceId,setSourceId]=useState('')
  const [error,setError]=useState(''), [busy,setBusy]=useState(false)
  useEffect(()=> { const controller=new AbortController(); void Promise.all([request<Project[]>('/projects',{signal:controller.signal}),request<SourcePage>('/sources?limit=100',{signal:controller.signal})]).then(([p,s])=>{setProjects(p);setSources(s)}).catch(e=>{if(!controller.signal.aborted)setError(e.message)});return()=>controller.abort() },[])
  useEffect(()=> { setMembers([]); if(!selected)return;const controller=new AbortController();void request<Member[]>(`/projects/${selected}/sources`,{signal:controller.signal}).then(setMembers).catch(e=>{if(!controller.signal.aborted)setError(e.message)});return()=>controller.abort() },[selected])
  async function change(source:string,method:string) {setBusy(true);setError('');try{await request(`/projects/${selected}/sources/${source}`,{method});setMembers(await request<Member[]>(`/projects/${selected}/sources`));setSourceId('')}catch(e){setError(e instanceof Error?e.message:'No se pudo guardar.')}finally{setBusy(false)}}
  return <section className="projects-panel"><h1>Proyectos</h1><p className="dialog-help">Reúne fuentes para trabajar una idea. Tus vídeos y análisis conservan su origen.</p>
    <form className="retrieval-actions" onSubmit={event=>{event.preventDefault();setBusy(true);void request<Project>('/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})}).then(p=>{setProjects(previous=>[...previous,p]);setSelected(p.id);setName('')}).catch(e=>setError(e.message)).finally(()=>setBusy(false))}}><label>Nombre del proyecto<input value={name} onChange={e=>setName(e.target.value)} required maxLength={120}/></label><button className="primary-button" disabled={busy||!name.trim()}>Crear proyecto</button></form>
    <label>Proyecto<select value={selected} disabled={busy} onChange={e=>setSelected(e.target.value)}><option value="">Selecciona un proyecto</option>{projects.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
    {selected&&<><form className="retrieval-actions" onSubmit={e=>{e.preventDefault();void change(sourceId,'PUT')}}><label>Añadir fuente<select value={sourceId} onChange={e=>setSourceId(e.target.value)}><option value="">Selecciona una fuente</option>{sources?.items.filter(s=>!members.some(m=>m.id===s.id)).map(s=><option key={s.id} value={s.id}>{s.title||s.assets[0]?.original_name||s.original_url}</option>)}</select></label><button className="secondary-button" disabled={busy||!sourceId}>Asociar fuente</button></form>{!!sources&&sources.total>100&&<p className="dialog-help">Se muestran las primeras 100 fuentes. La selección paginada sigue pendiente.</p>}
    {members.length?members.map(m=><article className="source-row" key={m.id}><strong className="project-source-title">{m.title}</strong><button className="secondary-button" onClick={()=>onSource(m.id)}>Ver ficha</button><button className="secondary-button" disabled={busy} onClick={()=>void change(m.id,'DELETE')}>Quitar del proyecto</button></article>):<p className="dialog-help">Todavía no hay fuentes asociadas.</p>}</>}
    {selected&&<Suspense fallback={<p className="dialog-help">Cargando grafo…</p>}><ProjectGraph key={selected+members.map(m=>m.id).join('')} projectId={selected} onSource={onSource} /></Suspense>}
    {error&&<p className="dialog-error" role="alert">{error}</p>}
  </section>
}
