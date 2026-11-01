import { useEffect, useRef, useState } from 'react'
import cytoscape from 'cytoscape'
import { request } from './api'
interface Node { id:string; title:string }
interface Revision { id:string; version:number; from_source_id:string; to_source_id:string; label:string; evidence:string; review_status:string; created_at:string }
interface Relation extends Revision { history:Revision[] }
interface Graph { nodes:Node[]; relations:Relation[] }
const blank={from_source_id:'',to_source_id:'',label:'',evidence:'',review_status:'proposed',expected_version:0}
const states:Record<string,string>={proposed:'Propuesta',accepted:'Aceptada',rejected:'Rechazada'}
export default function ProjectGraph({projectId,onSource}:{projectId:string;onSource:(id:string)=>void}) {
  const [graph,setGraph]=useState<Graph>({nodes:[],relations:[]}),[form,setForm]=useState(blank),[editing,setEditing]=useState('')
  const [error,setError]=useState(''),[busy,setBusy]=useState(false)
  const container=useRef<HTMLDivElement>(null)
  useEffect(()=>{const c=new AbortController();void request<Graph>(`/projects/${projectId}/graph`,{signal:c.signal}).then(setGraph).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[projectId])
  useEffect(()=>{
    if(!container.current)return
    const cy=cytoscape({container:container.current,elements:[...graph.nodes.map(n=>({data:{id:n.id,label:n.title.length>34?n.title.slice(0,31)+'…':n.title}})),...graph.relations.filter(r=>r.review_status!=='rejected').map(r=>({data:{id:r.id,source:r.from_source_id,target:r.to_source_id,label:r.label,status:r.review_status}}))],
      layout:{name:'grid',rows:1,padding:35,nodeDimensionsIncludeLabels:true},style:[{selector:'node',style:{'background-color':'#8eddb0',label:'data(label)',color:'#c4d4c9','font-size':11,'text-wrap':'wrap','text-max-width':'130px','text-valign':'bottom','text-margin-y':10}},{selector:'edge',style:{width:2,'line-color':'#52795f','target-arrow-color':'#52795f','target-arrow-shape':'triangle','curve-style':'bezier',label:'data(label)',color:'#a7b9ad','font-size':10,'text-background-color':'#101a13','text-background-opacity':1,'text-background-padding':'4px'}},{selector:'edge[status="proposed"]',style:{'line-style':'dashed'}}]})
    cy.on('tap','edge',event=>{const r=graph.relations.find(x=>x.id===event.target.id());if(r){setEditing(r.id);setForm({...r,expected_version:r.version})}})
    return()=>cy.destroy()
  },[graph])
  async function save(){setBusy(true);setError('');try{await request(`/projects/${projectId}/relations${editing?'/'+editing:''}`,{method:editing?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(form)});setGraph(await request<Graph>(`/projects/${projectId}/graph`));setEditing('');setForm(blank)}catch(e){setError(e instanceof Error?e.message:'No se pudo guardar.')}finally{setBusy(false)}}
  return <section className="project-graph"><h2>Relaciones y evidencias</h2><p className="dialog-help">Cada nodo es una fuente. Las líneas discontinuas son propuestas; las rechazadas se conservan en el historial. Haz clic en una línea para corregirla.</p>
    <div className="graph-canvas" ref={container} role="img" aria-label={`Grafo de ${graph.nodes.length} fuentes y ${graph.relations.filter(r=>r.review_status!=='rejected').length} relaciones visibles`} />
    <form onSubmit={e=>{e.preventDefault();void save()}}><h3>{editing?'Corregir relación':'Nueva relación manual'}</h3><div className="graph-fields">
      <label>Desde<select required disabled={busy} value={form.from_source_id} onChange={e=>setForm({...form,from_source_id:e.target.value})}><option value="">Selecciona una fuente</option>{graph.nodes.map(n=><option key={n.id} value={n.id}>{n.title}</option>)}</select></label>
      <label>Hacia<select required disabled={busy} value={form.to_source_id} onChange={e=>setForm({...form,to_source_id:e.target.value})}><option value="">Selecciona otra fuente</option>{graph.nodes.filter(n=>n.id!==form.from_source_id).map(n=><option key={n.id} value={n.id}>{n.title}</option>)}</select></label>
      <label>Relación<input required disabled={busy} maxLength={120} value={form.label} onChange={e=>setForm({...form,label:e.target.value})} placeholder="Por ejemplo: complementa" /></label>
      <label>Estado<select disabled={busy} value={form.review_status} onChange={e=>setForm({...form,review_status:e.target.value})}>{Object.entries(states).map(([id,label])=><option key={id} value={id}>{label}</option>)}</select></label></div>
      <label>Evidencia o motivo<textarea required disabled={busy} maxLength={2000} value={form.evidence} onChange={e=>setForm({...form,evidence:e.target.value})} placeholder="Explica qué fragmentos o momentos de estas fuentes respaldan tu relación. Es una nota manual, no una verificación automática." /></label>
      <div className="retrieval-actions"><button className="primary-button" disabled={busy||graph.nodes.length<2}>Guardar {editing?'corrección':'relación'}</button>{editing&&<button type="button" className="secondary-button" disabled={busy} onClick={()=>{setEditing('');setForm(blank)}}>Cancelar edición</button>}<button type="button" className="secondary-button" disabled={busy} onClick={()=>void request<Graph>(`/projects/${projectId}/graph`).then(setGraph).catch(e=>setError(e.message))}>Actualizar grafo</button></div>
    </form>
    {graph.nodes.length<2&&<p className="dialog-help">Asocia al menos dos fuentes para crear una relación.</p>}
    {error&&<p className="dialog-error" role="alert">{error}</p>}
    <div className="graph-relations">{graph.relations.map(r=><article key={r.id}><h3>{r.label} · {states[r.review_status]} · v{r.version}</h3><p>{r.evidence}</p><div className="retrieval-actions"><button className="secondary-button" onClick={()=>onSource(r.from_source_id)}>Ver fuente de origen</button><button className="secondary-button" onClick={()=>onSource(r.to_source_id)}>Ver fuente de destino</button><button className="secondary-button" disabled={busy} onClick={()=>{setEditing(r.id);setForm({...r,expected_version:r.version})}}>Corregir relación</button></div><details><summary>Historial ({r.history.length})</summary>{r.history.map(h=><p key={h.version}>v{h.version} · {states[h.review_status]} · {new Date(h.created_at).toLocaleString('es-CL',{timeZone:'America/Santiago'})}<br/>{h.label}: {h.evidence}</p>)}</details></article>)}</div>
  </section>
}
