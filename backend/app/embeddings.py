"""Versioned embedding space; local provider only, no implicit preparation."""
import hashlib
import json
import math
from typing import Protocol

MODEL = 'bge-m3:567m'
DIMENSIONS = 1024
CHUNK_CHARS = 1200

class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...

def vectors(rows, count):
    if len(rows) != count:
        raise ValueError('Cantidad de embeddings incorrecta.')
    result=[]
    for row in rows:
        if len(row) != DIMENSIONS or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in row):
            raise ValueError('Espacio de embeddings incompatible.')
        norm=math.sqrt(sum(x*x for x in row))
        if norm < 1e-12: raise ValueError('Embedding vacío.')
        result.append([float(x/norm) for x in row])
    return result

def profile_id(digest):
    return hashlib.sha256(json.dumps({'model':MODEL,'digest':digest,'dimensions':DIMENSIONS,
        'chunk_chars':CHUNK_CHARS,'pipeline':1,'normalize':'l2'},sort_keys=True).encode()).hexdigest()

class LocalEmbedder:
    def __init__(self, provider): self.provider=provider
    def embed(self, texts):
        response=self.provider.client.post('/api/embed',json={'model':MODEL,'input':texts,
            'truncate':False,'keep_alive':'5m'})
        response.raise_for_status()
        return vectors(response.json()['embeddings'],len(texts))

def manifest(root):
    value=json.loads((root/'models'/'search.json').read_text(encoding='utf-8'))
    if value['profile_id'] != profile_id(value['embedding']['digest']):
        raise ValueError('Perfil de embeddings no válido.')
    if value['embedding']['name'] != MODEL or value['dimensions'] != DIMENSIONS:
        raise ValueError('Modelo de embeddings incompatible.')
    return value

def ready(root):
    try: manifest(root); return True
    except (OSError,ValueError,KeyError,TypeError): return False
