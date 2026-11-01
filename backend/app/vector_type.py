import json
import math
from sqlalchemy.types import UserDefinedType
from sqlalchemy.dialects.postgresql.base import ischema_names

class Vector(UserDefinedType):
    cache_ok=True
    def __init__(self, dimensions=1024): self.dimensions=dimensions
    def get_col_spec(self, **kw): return f'public.vector({int(self.dimensions)})'
    def bind_processor(self, dialect):
        def encode(value):
            if value is None: return None
            if len(value)!=self.dimensions or any(not math.isfinite(x) for x in value): raise ValueError('Vector incompatible.')
            return json.dumps(value)
        return encode
    def result_processor(self, dialect, coltype):
        return lambda value: json.loads(value) if isinstance(value,str) else value

ischema_names.setdefault('vector',Vector)
