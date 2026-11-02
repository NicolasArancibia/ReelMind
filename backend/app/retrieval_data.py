"""Pure evidence extraction plus live-version SQL filters. Never reads media."""
import hashlib
from uuid import UUID
from sqlalchemy import select,func,or_,Float,bindparam
from sqlalchemy.orm import aliased
from app.models import Source,Transcript,AudiovisualAnalysis,ContentChunk,ChunkEmbedding,NoteRevision
from app.embeddings import CHUNK_CHARS
from app.vector_type import Vector

def current_rows(model):
    other=aliased(model)
    newest=select(func.max(other.version)).where(other.source_id==model.source_id).correlate(model).scalar_subquery()
    return select(model).join(Source,Source.id==model.source_id).where(Source.deleted_at.is_(None),model.version==newest)

def live_chunks():
    audio=current_rows(Transcript).with_only_columns(Transcript.id)
    visual=current_rows(AudiovisualAnalysis).with_only_columns(AudiovisualAnalysis.id)
    from app.notebook import latest_notes
    notes=latest_notes().where(NoteRevision.archived.is_(False)).with_only_columns(NoteRevision.id,NoteRevision.version).subquery()
    from sqlalchemy import tuple_
    return select(ContentChunk).join(Source,Source.id==ContentChunk.source_id).where(Source.deleted_at.is_(None),
        or_(ContentChunk.transcript_id.in_(audio),ContentChunk.analysis_id.in_(visual),tuple_(ContentChunk.note_id,ContentChunk.note_version).in_(select(notes))))

def split_text(content):
    # Exact substrings; offsets are recorded, no generated summaries in the index.
    for start in range(0,len(content),CHUNK_CHARS):
        value=content[start:start+CHUNK_CHARS]
        if value.strip(): yield start,value

def snapshots(session):
    result=[]
    def append(source_id,record_id,kind,ordinal,content,origin,**times):
        for offset,part in split_text(content):
            result.append({'source_id':str(source_id),'analysis_id':str(record_id) if kind=='visual' else None,
                'transcript_id':str(record_id) if kind=='audio' else None,'origin_key':f'{kind}:{record_id}:{ordinal}:{offset}',
                'ordinal':ordinal,'content':part,'content_sha256':hashlib.sha256(part.encode()).hexdigest(),
                'origin':{**origin,'kind':kind,'offset':offset},'start_ms':None,'end_ms':None,'time_ms':None,**times})
    for row in session.scalars(current_rows(Transcript)).all():
        for ordinal,segment in enumerate(row.segments):
            append(row.source_id,row.id,'audio',ordinal,segment.text,{'version':row.version},start_ms=segment.start_ms,end_ms=segment.end_ms)
    for row in session.scalars(current_rows(AudiovisualAnalysis)).all():
        if row.payload.get('provenance',{}).get('pipeline_version',0)<2: continue
        for ordinal,item in enumerate(row.payload.get('evidence',[])):
            if item.get('kind')!='visual' or item.get('uncertain') or item.get('ocr_unusable'): continue
            description=item.get('description','').strip(); visible=item.get('visible_text','').strip()
            content=description + ('\nTexto visible: '+visible if visible and visible not in description else '')
            append(row.source_id,row.id,'visual',ordinal,content,{'version':row.version,'evidence_id':item['id']},time_ms=item['time_ms'])
    from app.notebook import latest_notes
    for row in session.scalars(latest_notes().where(NoteRevision.archived.is_(False))).all():
        content=row.content+('\nCita guardada: '+row.quote_text if row.quote_text else '')
        for offset,part in split_text(content):
            result.append({'source_id':str(row.source_id),'analysis_id':None,'transcript_id':None,'note_id':str(row.id),'note_version':row.version,
                'origin_key':f'note:{row.id}:{row.version}:{offset}','ordinal':offset//CHUNK_CHARS,'content':part,
                'content_sha256':hashlib.sha256(part.encode()).hexdigest(),'origin':{'kind':'note','version':row.version,'offset':offset,'author':'user'},
                'start_ms':row.start_ms,'end_ms':row.end_ms,'time_ms':None})
    return result

def scoped_chunks(project_id=None,source_ids=None):
    query=live_chunks()
    if project_id:
        from app.models import ProjectSource,Project
        query=query.where(ContentChunk.source_id.in_(select(ProjectSource.source_id).join(Project).where(ProjectSource.project_id==UUID(str(project_id)),Project.archived_at.is_(None))))
    if source_ids:query=query.where(ContentChunk.source_id.in_([UUID(str(i)) for i in source_ids]))
    return query


def overview_requested(query):
    import re,unicodedata
    plain=''.join(c for c in unicodedata.normalize('NFD',query.casefold()) if not unicodedata.combining(c)).lstrip(' ¿¡')
    return bool(re.match(r'^(resume(?:n|me)?\b|haz(?:me)? (?:un )?resumen\b|de que trata\b|que temas\b)',plain))


def sampled_overview(session,profile,source_ids,project_id=None):
    """A bounded temporal sample for an explicit single-source overview, not a similarity score."""
    order=(func.coalesce(ContentChunk.time_ms,ContentChunk.start_ms,0),ContentChunk.ordinal,ContentChunk.id)
    sample=scoped_chunks(project_id,source_ids).with_only_columns(ContentChunk.id,
        func.row_number().over(order_by=order).label('position'),func.count().over().label('total'))\
        .join(ChunkEmbedding,ChunkEmbedding.chunk_id==ContentChunk.id).where(ChunkEmbedding.profile_id==profile).subquery()
    rows=session.execute(select(sample.c.id,sample.c.total).where(or_(
        *(sample.c.position==func.floor((sample.c.total-1)*i/7)+1 for i in range(8))))
        .order_by(sample.c.position).limit(8)).all()
    return [{'chunk_id':str(row.id),'score':None} for row in rows],(rows[0].total if rows else 0)


def ranked(session,profile,query_vector,limit=8,min_score=.5,project_id=None,source_ids=None):
    distance=ChunkEmbedding.embedding.op('OPERATOR(public.<=>)',return_type=Float)(bindparam('query_vector',query_vector,type_=Vector(1024)))
    query=scoped_chunks(project_id,source_ids)
    rows=session.execute(query.add_columns(distance.label('distance')).join(ChunkEmbedding,ChunkEmbedding.chunk_id==ContentChunk.id)
        .where(ChunkEmbedding.profile_id==profile).order_by(distance,ContentChunk.id).limit(limit)).all()
    return [{'chunk_id':str(row.id),'score':round(1-float(d),6)} for row,d in rows if 1-float(d)>=min_score]

def hydrate(session,hits,historical=False):
    result=[]
    live=set(session.scalars(live_chunks().with_only_columns(ContentChunk.id)).all())
    for hit in hits:
        chunk=session.get(ContentChunk,UUID(hit['chunk_id']))
        if not chunk: continue
        source=session.get(Source,chunk.source_id)
        if source is None or source.deleted_at is not None: continue
        if not historical and chunk.id not in live: continue
        result.append({'chunk_id':str(chunk.id),'source_id':str(source.id),'title':source.title or (source.assets[0].original_name if source.assets else source.original_url),
            'content':chunk.content,'score':hit.get('score'),'origin':chunk.origin,'time_ms':chunk.time_ms,'start_ms':chunk.start_ms,'end_ms':chunk.end_ms,
            'historical':chunk.id not in live,
            'analysis_id':str(chunk.analysis_id) if chunk.analysis_id else None,'transcript_id':str(chunk.transcript_id) if chunk.transcript_id else None})
    return result
