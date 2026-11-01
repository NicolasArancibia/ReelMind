"""Pure evidence extraction plus live-version SQL filters. Never reads media."""
import hashlib
from uuid import UUID
from sqlalchemy import select,func,or_,Float,bindparam
from sqlalchemy.orm import aliased
from app.models import Source,Transcript,AudiovisualAnalysis,ContentChunk,ChunkEmbedding
from app.embeddings import CHUNK_CHARS
from app.vector_type import Vector

def current_rows(model):
    other=aliased(model)
    newest=select(func.max(other.version)).where(other.source_id==model.source_id).correlate(model).scalar_subquery()
    return select(model).join(Source,Source.id==model.source_id).where(Source.deleted_at.is_(None),model.version==newest)

def live_chunks():
    audio=current_rows(Transcript).with_only_columns(Transcript.id)
    visual=current_rows(AudiovisualAnalysis).with_only_columns(AudiovisualAnalysis.id)
    return select(ContentChunk).join(Source,Source.id==ContentChunk.source_id).where(Source.deleted_at.is_(None),
        or_(ContentChunk.transcript_id.in_(audio),ContentChunk.analysis_id.in_(visual)))

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
    if len(result)>2000: raise ValueError('Más de 2000 fragmentos; se requiere indexación por lotes antes de continuar.')
    return result

def ranked(session,profile,query_vector,limit=8,min_score=.5):
    distance=ChunkEmbedding.embedding.op('OPERATOR(public.<=>)',return_type=Float)(bindparam('query_vector',query_vector,type_=Vector(1024)))
    rows=session.execute(live_chunks().add_columns(distance.label('distance')).join(ChunkEmbedding,ChunkEmbedding.chunk_id==ContentChunk.id)
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
