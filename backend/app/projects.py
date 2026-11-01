from uuid import UUID,uuid4
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.db import get_session
from app.models import Project,ProjectSource,Source,RelationRevision,NoteRevision

router=APIRouter(prefix='/api/projects')
class ProjectInput(BaseModel):
    name:str=Field(min_length=1,max_length=120)

def project(session,project_id):
    row=session.get(Project,project_id,with_for_update=True)
    if row is None: raise HTTPException(404,'Proyecto no encontrado.')
    return row

@router.get('')
def listing(archived:bool=False,session:Session=Depends(get_session)):
    condition=Project.archived_at.is_not(None) if archived else Project.archived_at.is_(None)
    return [{'id':p.id,'name':p.name,'archived':p.archived_at is not None} for p in session.scalars(select(Project).where(condition).order_by(Project.created_at,Project.id))]

@router.post('',status_code=201)
def create(payload:ProjectInput,session:Session=Depends(get_session)):
    if not payload.name.strip(): raise HTTPException(422,'Escribe un nombre para el proyecto.')
    row=Project(name=payload.name.strip());session.add(row);session.commit();session.refresh(row)
    return {'id':row.id,'name':row.name,'archived':False}

class ProjectChange(BaseModel):
    name:str=Field(min_length=1,max_length=120)
    archived:bool=False
    expected_name:str
    expected_archived:bool=False

@router.put('/{project_id}')
def change_project(project_id:UUID,payload:ProjectChange,session:Session=Depends(get_session)):
    row=project(session,project_id)
    if row.name!=payload.expected_name or (row.archived_at is not None)!=payload.expected_archived:raise HTTPException(409,'El proyecto cambió. Actualiza antes de editar.')
    if not payload.name.strip():raise HTTPException(422,'Escribe un nombre.')
    row.name=payload.name.strip();row.archived_at=func.clock_timestamp() if payload.archived else None
    session.commit();return {'id':row.id,'name':row.name,'archived':row.archived_at is not None}

@router.get('/{project_id}/sources')
def members(project_id:UUID,session:Session=Depends(get_session)):
    project(session,project_id)
    return [{'id':s.id,'title':s.title or (s.assets[0].original_name if s.assets else s.original_url)}
        for s in session.scalars(select(Source).join(ProjectSource).where(ProjectSource.project_id==project_id,Source.deleted_at.is_(None)).order_by(Source.created_at))]

@router.put('/{project_id}/sources/{source_id}')
def attach(project_id:UUID,source_id:UUID,session:Session=Depends(get_session)):
    if project(session,project_id).archived_at is not None:raise HTTPException(409,'Restaura el proyecto antes de modificar sus fuentes.')
    source=session.get(Source,source_id,with_for_update=True)
    if source is None or source.deleted_at is not None: raise HTTPException(404,'Fuente no disponible.')
    if session.get(ProjectSource,(project_id,source_id)) is None: session.add(ProjectSource(project_id=project_id,source_id=source_id))
    session.commit(); return {'status':'associated'}

@router.delete('/{project_id}/sources/{source_id}')
def detach(project_id:UUID,source_id:UUID,session:Session=Depends(get_session)):
    if project(session,project_id).archived_at is not None:raise HTTPException(409,'Restaura el proyecto antes de modificar sus fuentes.')
    row=session.get(ProjectSource,(project_id,source_id))
    if row: session.delete(row)
    session.commit(); return {'status':'detached'}  # The source and its analyses are preserved.

class RelationInput(BaseModel):
    from_source_id:UUID
    from_note_id:UUID|None=None
    from_note_version:int|None=Field(default=None,ge=1)
    to_note_id:UUID|None=None
    to_note_version:int|None=Field(default=None,ge=1)
    to_source_id:UUID
    label:str=Field(min_length=1,max_length=120)
    evidence:str=Field(min_length=1,max_length=2000)
    review_status:Literal['proposed','accepted','rejected']='proposed'
    expected_version:int=Field(default=0,ge=0)

def relation_read(row):
    return {key:getattr(row,key) for key in ('id','version','from_source_id','to_source_id','label','evidence','review_status','created_at','from_note_id','from_note_version','to_note_id','to_note_version')}

@router.get('/{project_id}/graph')
def graph(project_id:UUID,session:Session=Depends(get_session)):
    from app.notebook import latest_notes
    nodes=[{**node,'kind':'source','source_id':node['id']} for node in members(project_id,session)]
    visible={n['id'] for n in nodes}
    note_rows=session.scalars(latest_notes().where(NoteRevision.source_id.in_(visible),NoteRevision.archived.is_(False))).all()
    active_notes={r.id:r for r in note_rows}
    def note_node(row):return {'id':f'note:{row.id}:v{row.version}','title':row.content[:70]+f' · v{row.version}', 'kind':'note','source_id':row.source_id,'note_id':row.id,'note_version':row.version,'start_ms':row.start_ms}
    nodes.extend(note_node(r) for r in note_rows)
    node_ids={str(n['id']) for n in nodes}
    rows=session.scalars(select(RelationRevision).where(RelationRevision.project_id==project_id).order_by(RelationRevision.id,RelationRevision.version)).all()
    latest={r.id:r for r in rows};relations=[]
    for row in latest.values():
        if row.from_source_id not in visible or row.to_source_id not in visible:continue
        endpoints={};available=True
        for side in ('from','to'):
            note_id=getattr(row,side+'_note_id');version=getattr(row,side+'_note_version')
            endpoint=str(getattr(row,side+'_source_id'))
            if note_id:
                if note_id not in active_notes:available=False;break
                pinned=session.get(NoteRevision,(note_id,version))
                if pinned is None:available=False;break
                endpoint=f'note:{note_id}:v{version}'
                if endpoint not in node_ids:nodes.append(note_node(pinned));node_ids.add(endpoint)
            endpoints[side+'_node_id']=endpoint
        if available:relations.append({**relation_read(row),**endpoints,'history':[relation_read(r) for r in rows if r.id==row.id]})
    return {'nodes':nodes,'relations':relations}

def save_relation(session,project_id,payload,relation_id=None):
    if project(session,project_id).archived_at is not None:raise HTTPException(409,'Restaura el proyecto antes de modificar relaciones.')
    if (payload.from_source_id==payload.to_source_id and payload.from_note_id==payload.to_note_id) or not payload.label.strip() or not payload.evidence.strip():
        raise HTTPException(422,'Selecciona dos fuentes distintas y escribe relación y evidencia.')
    for source_id in sorted([payload.from_source_id,payload.to_source_id],key=str):
        source=session.get(Source,source_id,with_for_update=True)
        if source is None or source.deleted_at is not None or session.get(ProjectSource,(project_id,source_id)) is None:
            raise HTTPException(409,'Ambas fuentes deben estar disponibles en este proyecto.')
    for side in ('from','to'):
        note_id=getattr(payload,side+'_note_id');version=getattr(payload,side+'_note_version')
        if (note_id is None)!=(version is None):raise HTTPException(422,'La referencia de apunte está incompleta.')
        if note_id:
            note=session.get(NoteRevision,(note_id,version))
            current=session.scalar(select(NoteRevision).where(NoteRevision.id==note_id).order_by(NoteRevision.version.desc()).limit(1))
            if note is None or note.source_id!=getattr(payload,side+'_source_id') or current.archived:raise HTTPException(422,'Apunte no disponible o ajeno a la fuente.')
    latest=session.scalar(select(RelationRevision).where(RelationRevision.id==relation_id,RelationRevision.project_id==project_id)
        .order_by(RelationRevision.version.desc()).limit(1)) if relation_id else None
    if relation_id and latest is None: raise HTTPException(404,'Relación no encontrada.')
    if payload.expected_version!=(latest.version if latest else 0): raise HTTPException(409,'La relación cambió. Actualiza el grafo antes de corregirla.')
    row=RelationRevision(id=relation_id or uuid4(),version=payload.expected_version+1,project_id=project_id,
        from_source_id=payload.from_source_id,to_source_id=payload.to_source_id,label=payload.label.strip(),
        evidence=payload.evidence.strip(),review_status=payload.review_status,from_note_id=payload.from_note_id,from_note_version=payload.from_note_version,to_note_id=payload.to_note_id,to_note_version=payload.to_note_version)
    session.add(row);session.commit();session.refresh(row);return relation_read(row)

@router.post('/{project_id}/relations',status_code=201)
def create_relation(project_id:UUID,payload:RelationInput,session:Session=Depends(get_session)):
    return save_relation(session,project_id,payload)

@router.put('/{project_id}/relations/{relation_id}')
def revise_relation(project_id:UUID,relation_id:UUID,payload:RelationInput,session:Session=Depends(get_session)):
    return save_relation(session,project_id,payload,relation_id)
