import json
from app.config import get_settings
from app.db import get_engine
from app.processing import ManualEngine
from app.local_ai import local_provider, TEXT_MODEL
from app.embeddings import MODEL,DIMENSIONS,LocalEmbedder,profile_id

def main():
    database=get_engine(); reservation=ManualEngine(database).acquire()
    if reservation is None: raise RuntimeError('Hay otra tarea pesada activa.')
    try:
        root=get_settings().data_root
        with local_provider(root) as provider:
            installed={r['name']:r for r in provider.inventory()}
            for name in (MODEL,TEXT_MODEL):
                if name not in installed:
                    print('Preparando '+name,flush=True); provider.pull(name)
            installed={r['name']:r for r in provider.inventory()}
            LocalEmbedder(provider).embed(['La biblioteca personal conserva vídeos y sus evidencias.'])
            value={'embedding':installed[MODEL],'text':installed[TEXT_MODEL], 'dimensions':DIMENSIONS,
                'profile_id':profile_id(installed[MODEL]['digest']),'ollama_version':provider.version()}
        (root/'models'/'search.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Embeddings preparados y dimensión comprobada; biblioteca sin indexar.')
    finally: ManualEngine.release(reservation); database.dispose()

if __name__=='__main__': main()
