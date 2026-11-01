from typing import Literal
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select,func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from app.db import get_session
from app.models import Source,ProcessingJob,Project,ProjectSource,Tag,Category
from app.schemas import OrganizationUpdate

router=APIRouter(prefix='/api/library')
class BatchAction(BaseModel):
    source_ids:list[UUID]=Field(min_length=1,max_length=200)
    action:Literal['enqueue','dequeue','favorite','unfavorite','associate','labels']
    project_id:UUID|None=None
    tags:list[str]=Field(default_factory=list,max_length=20)
    categories:list[str]=Field(default_factory=list,max_length=10)

@router.post('/actions')
def apply_batch(payload:BatchAction,session:Session=Depends(get_session)):
    if payload.action=='labels':
        from app.organization_lock import lock_organization
        lock_organization(session)
    ids=sorted(set(payload.source_ids),key=str)
    # Same project-before-source order as relationship edits.
    if payload.action=='associate':
        project=session.get(Project,payload.project_id,with_for_update=True) if payload.project_id else None
        if project is None or project.archived_at is not None:raise HTTPException(409,'Proyecto no disponible.')
    rows=session.scalars(select(Source).where(Source.id.in_(ids)).order_by(Source.id).with_for_update()).all()
    if len(rows)!=len(ids) or any(s.deleted_at is not None for s in rows):raise HTTPException(409,'Una fuente ya no está disponible. Actualiza la selección.')
    if payload.action in {'enqueue','dequeue'} and any(s.job and s.job.status=='running' for s in rows):raise HTTPException(409,'Detén el motor antes de cambiar trabajos activos.')
    try:tags=OrganizationUpdate.clean_names(payload.tags);categories=OrganizationUpdate.clean_names(payload.categories)
    except ValueError:raise HTTPException(422,'Revisa los nombres de etiquetas y categorías.') from None
    labels={}
    if payload.action=='labels':
        for key,model,names in [('tags',Tag,tags),('categories',Category,categories)]:
            labels[key]=[]
            for name in sorted(names,key=str.casefold):
                session.execute(insert(model).values(name=name,normalized_name=name.casefold()).on_conflict_do_nothing(index_elements=['normalized_name']))
                labels[key].append(session.scalar(select(model).where(model.normalized_name==name.casefold())))
    for row in rows:
        if payload.action in {'favorite','unfavorite'}:row.favorite=payload.action=='favorite'
        elif payload.action=='associate':
            if session.get(ProjectSource,(payload.project_id,row.id)) is None:session.add(ProjectSource(project_id=payload.project_id,source_id=row.id))
        elif payload.action=='labels':
            for key,limit in [('tags',20),('categories',10)]:
                merged={i.id:i for i in [*getattr(row,key),*labels[key]]}
                if len(merged)>limit:raise HTTPException(422,'Una fuente superaría el límite de etiquetas/categorías. No se aplicó el lote.')
                setattr(row,key,list(merged.values()))
        elif payload.action=='enqueue':
            if row.job is None:row.job=ProcessingJob()
            if row.job.status!='pending':row.job.created_at=func.clock_timestamp()
            row.job.status='pending';row.job.error_message=None;row.job.run_id=None
        elif payload.action=='dequeue' and row.job and row.job.status=='pending':row.job.status='cancelled';row.job.run_id=None
        row.updated_at=func.clock_timestamp()
    session.commit();return {'updated':len(rows),'analysis_started':False}
