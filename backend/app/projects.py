from uuid import UUID,uuid4
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_session
from app.models import Project,ProjectSource,Source,RelationRevision

router=APIRouter(prefix='/api/projects')
class ProjectInput(BaseModel):
    name:str=Field(min_length=1,max_length=120)

def project(session,project_id):
    row=session.get(Project,project_id,with_for_update=True)
    if row is None: raise HTTPException(404,'Proyecto no encontrado.')
    return row

@router.get('')
def listing(session:Session=Depends(get_session)):
    return [{'id':p.id,'name':p.name} for p in session.scalars(select(Project).order_by(Project.created_at,Project.id))]

@router.post('',status_code=201)
def create(payload:ProjectInput,session:Session=Depends(get_session)):
    if not payload.name.strip(): raise HTTPException(422,'Escribe un nombre para el proyecto.')
    row=Project(name=payload.name.strip());session.add(row);session.commit();session.refresh(row)
    return {'id':row.id,'name':row.name}

@router.get('/{project_id}/sources')
def members(project_id:UUID,session:Session=Depends(get_session)):
    project(session,project_id)
    return [{'id':s.id,'title':s.title or (s.assets[0].original_name if s.assets else s.original_url)}
        for s in session.scalars(select(Source).join(ProjectSource).where(ProjectSource.project_id==project_id,Source.deleted_at.is_(None)).order_by(Source.created_at))]

@router.put('/{project_id}/sources/{source_id}')
def attach(project_id:UUID,source_id:UUID,session:Session=Depends(get_session)):
    project(session,project_id)
    source=session.get(Source,source_id,with_for_update=True)
    if source is None or source.deleted_at is not None: raise HTTPException(404,'Fuente no disponible.')
    if session.get(ProjectSource,(project_id,source_id)) is None: session.add(ProjectSource(project_id=project_id,source_id=source_id))
    session.commit(); return {'status':'associated'}

@router.delete('/{project_id}/sources/{source_id}')
def detach(project_id:UUID,source_id:UUID,session:Session=Depends(get_session)):
    project(session,project_id)
    row=session.get(ProjectSource,(project_id,source_id))
    if row: session.delete(row)
    session.commit(); return {'status':'detached'}  # The source and its analyses are preserved.

class RelationInput(BaseModel):
    from_source_id:UUID
    to_source_id:UUID
    label:str=Field(min_length=1,max_length=120)
    evidence:str=Field(min_length=1,max_length=2000)
    review_status:Literal['proposed','accepted','rejected']='proposed'
    expected_version:int=Field(default=0,ge=0)

def relation_read(row):
    return {key:getattr(row,key) for key in ('id','version','from_source_id','to_source_id','label','evidence','review_status','created_at')}

@router.get('/{project_id}/graph')
def graph(project_id:UUID,session:Session=Depends(get_session)):
    nodes=members(project_id,session)
    visible={n['id'] for n in nodes}
    rows=session.scalars(select(RelationRevision).where(RelationRevision.project_id==project_id).order_by(RelationRevision.id,RelationRevision.version)).all()
    latest={r.id:r for r in rows}
    return {'nodes':nodes,'relations':[{**relation_read(row),'history':[relation_read(r) for r in rows if r.id==row.id]}
        for row in latest.values() if row.from_source_id in visible and row.to_source_id in visible]}

def save_relation(session,project_id,payload,relation_id=None):
    project(session,project_id)  # Serialize revisions and membership changes in this project.
    if payload.from_source_id==payload.to_source_id or not payload.label.strip() or not payload.evidence.strip():
        raise HTTPException(422,'Selecciona dos fuentes distintas y escribe relación y evidencia.')
    for source_id in sorted([payload.from_source_id,payload.to_source_id],key=str):
        source=session.get(Source,source_id,with_for_update=True)
        if source is None or source.deleted_at is not None or session.get(ProjectSource,(project_id,source_id)) is None:
            raise HTTPException(409,'Ambas fuentes deben estar disponibles en este proyecto.')
    latest=session.scalar(select(RelationRevision).where(RelationRevision.id==relation_id,RelationRevision.project_id==project_id)
        .order_by(RelationRevision.version.desc()).limit(1)) if relation_id else None
    if relation_id and latest is None: raise HTTPException(404,'Relación no encontrada.')
    if payload.expected_version!=(latest.version if latest else 0): raise HTTPException(409,'La relación cambió. Actualiza el grafo antes de corregirla.')
    row=RelationRevision(id=relation_id or uuid4(),version=payload.expected_version+1,project_id=project_id,
        from_source_id=payload.from_source_id,to_source_id=payload.to_source_id,label=payload.label.strip(),
        evidence=payload.evidence.strip(),review_status=payload.review_status)
    session.add(row);session.commit();session.refresh(row);return relation_read(row)

@router.post('/{project_id}/relations',status_code=201)
def create_relation(project_id:UUID,payload:RelationInput,session:Session=Depends(get_session)):
    return save_relation(session,project_id,payload)

@router.put('/{project_id}/relations/{relation_id}')
def revise_relation(project_id:UUID,relation_id:UUID,payload:RelationInput,session:Session=Depends(get_session)):
    return save_relation(session,project_id,payload,relation_id)
