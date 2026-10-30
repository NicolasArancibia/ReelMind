# Diseño de datos y migraciones

**Estado: `0001_sources` y `0002_library` aplicadas. Fase 1 implementada; las secciones de audio, análisis, sincronización, búsqueda semántica y proyectos siguen siendo diseño futuro.** Referencia: plan v1.3, páginas 12-14 y 17. SQLAlchemy y Alembic materializarán las entidades restantes en sus fases. No modificar la revisión ya aplicada: usar nuevas migraciones.

La revisión inicial incluye las columnas de sources, checks de plataforma/tipo/estado/URL obligatoria, índice único parcial de canonical_url e índices de plataforma y estado/fecha. El título admite 240 caracteres. La API guarda enlaces HTTP/HTTPS sin credenciales, conserva la URL original y usa una normalización conservadora para duplicados. No descarga medios de enlaces. Desde `0002_library`, el alta crea un pendiente en la misma transacción.

## Convenciones SQL

- Identidades `uuid PRIMARY KEY DEFAULT gen_random_uuid()`; campos obligatorios `NOT NULL`; fechas `timestamptz NOT NULL DEFAULT now()`.
- Texto libre `text`; tamaños e intervalos `bigint`; contadores `integer`; datos variables `jsonb`. No convertir todo el modelo en JSONB.
- Nombres de restricciones e índices explícitos para migraciones reproducibles. Fechas internas UTC; presentación según zona del usuario.
- `updated_at` se actualiza explícitamente en cada mutación de 1.1 con `clock_timestamp()` después del bloqueo por fila; `DEFAULT now()` solo inicializa. La API exige la versión anterior para evitar cambios perdidos entre ventanas.
- Borrado lógico con `deleted_at timestamptz NULL` en fuentes. La purga de archivos será una operación separada; no aplicar cascadas globales a información citada.
- Los estados siguientes son un diseño propuesto a fijar en migraciones con `CHECK`; calidad y estado operativo no se confunden.

## Esquema aplicado en Fase 1

La [decisión 0005](decisions/0005-cierre-biblioteca.md) concreta el diseño del núcleo:

| Tabla | Columnas y restricciones aplicadas |
| --- | --- |
| `media_files` | UUID PK, checksum SHA-256 único, local_path relativo único, mime_type, size_bytes > 0 |
| `media_assets` | UUID PK, source_id y file_id FK RESTRICT indexadas, original_name hasta 240 caracteres, created_at; UNIQUE(source_id, file_id) |
| `tags`, `categories` | UUID PK, name hasta 60 caracteres no vacío, normalized_name único; categorías planas |
| `source_tags`, `source_categories` | PK compuesta, FK RESTRICT e índice inverso por etiqueta/categoría |
| `processing_jobs` | UUID PK, source_id FK RESTRICT único, status `pending` o `cancelled`, created_at; índice (status, created_at) |

Una copia física puede pertenecer a varias fuentes. La API impide duplicar una fuente local por contenido mediante bloqueo transaccional por hash; las asociaciones preservan procedencias. El backfill crea pendientes para fuentes anteriores, incluidas las de papelera, que se ocultan de la cola visible.

La cola de Fase 1 no tiene estados de ejecución. La jerarquía, duración/fotogramas, tipos de derivados y campos de trabajador descritos a continuación son **ampliaciones futuras**, no columnas ya aplicadas. Necesitarán nuevas revisiones; no modificar migraciones publicadas. Los nombres `0002`–`0006` del cuadro histórico al final son hitos del plan, no revisiones ejecutables actuales.

## Núcleo: base aplicada y ampliaciones previstas

### sources

| Columna | Tipo / regla |
| --- | --- |
| id | uuid PK |
| platform | text NOT NULL; `instagram`, `youtube`, `tiktok`, `local`, `other` |
| source_type | text NOT NULL; `url` o `file` |
| original_url | text NULL; requerido y no vacío para `url` |
| canonical_url | text NULL; normalizar únicamente cuando sea fiable |
| title / author | text NULL; no inventar metadatos ausentes |
| status | text NOT NULL DEFAULT `pending`; `pending`, `ready`, `needs_input`, `failed` |
| created_at / updated_at | timestamptz NOT NULL DEFAULT now() |
| deleted_at | timestamptz NULL |

Índice único parcial `uq_sources_canonical_url ON sources(canonical_url) WHERE canonical_url IS NOT NULL`. La normalización conserva identidad del vídeo, no elimina arbitrariamente parámetros. Conservar original_url. La unicidad también alcanza fuentes borradas lógicamente: una nueva importación ofrece restaurarlas en vez de duplicarlas. Indexar `(status, created_at)` y `platform` según consultas.

### media_assets — diseño ampliado futuro

`id uuid PK`, `source_id uuid NOT NULL REFERENCES sources(id) ON DELETE RESTRICT`, `asset_type text NOT NULL` (`original`, `audio`, `frame`, `other`), `local_path text NOT NULL`, `mime_type text NOT NULL`, `size_bytes bigint NOT NULL CHECK (size_bytes >= 0)`, `checksum text NULL`, `duration_ms bigint NULL CHECK (duration_ms >= 0)`, `frame_ms bigint NULL CHECK (frame_ms >= 0)`, `created_at timestamptz NOT NULL DEFAULT now()`.

Ruta relativa a la raíz de almacenamiento, validada en backend; `UNIQUE(local_path)` para un activo físico registrado una sola vez. Índices en `source_id` y `checksum`. Hash SHA-256 en contenido disponible: no imponer unicidad global al hash sin diseñar antes cómo conservar múltiples procedencias. La base no puede demostrar por sí sola que el archivo existe ni que una ruta resuelta permanezca dentro de la raíz.

### tags y categories — diseño ampliado futuro

- `tags`: `id uuid PK`, `name text NOT NULL`, `normalized_name text NOT NULL UNIQUE`, `CHECK (btrim(name) <> '')`.
- `categories`: mismos campos, `description text NULL`, `parent_id uuid NULL REFERENCES categories(id) ON DELETE RESTRICT`, `CHECK (parent_id IS NULL OR parent_id <> id)`.
- Normalización de nombres definida en backend (espacios/casefold) y almacenada explícitamente. Conservar acentos por defecto; no fusionar significados solo por similitud.
- Impedir ciclos largos de categorías mediante una comprobación recursiva dentro de una transacción que serialice cambios de jerarquía; el `CHECK` anterior solo impide autorreferencia directa. Cubrir cambios concurrentes antes de aceptar la migración.
- `source_tags(source_id uuid FK RESTRICT, tag_id uuid FK RESTRICT, PRIMARY KEY(source_id, tag_id))` y `source_categories(source_id uuid FK RESTRICT, category_id uuid FK RESTRICT, PRIMARY KEY(source_id, category_id))`. Añadir índice por la segunda FK para búsqueda inversa. Eliminar la asociación no elimina la fuente.

### processing_jobs — diseño ampliado para el motor futuro

`id uuid PK`, `source_id uuid NOT NULL REFERENCES sources(id) ON DELETE RESTRICT`, `job_type text NOT NULL` (`full_analysis`, `transcription`, `vision`, `indexing`), `status text NOT NULL DEFAULT 'pending'`, `attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0)`, `checkpoint jsonb NOT NULL DEFAULT '{}'::jsonb`, `error_message text NULL`, `created_at timestamptz NOT NULL DEFAULT now()`, `started_at`, `finished_at`, `heartbeat_at` (`timestamptz NULL`), `worker_id text NULL`.

Estados permitidos: `pending`, `running`, `pause_requested`, `paused`, `stop_requested`, `stopped`, `completed`, `failed`. `checkpoint` debe ser un objeto JSON mediante `CHECK (jsonb_typeof(checkpoint) = 'object')`. Un `finished_at` definido requiere `started_at` y no puede ser anterior. Índices `(status, created_at)` y `source_id`.

Propuesta: índice único parcial por `(source_id, job_type)` para estados activos/pendientes que impida encolar duplicados involuntarios. Reprocesar un trabajo finalizado crea uno nuevo, preservando historial. Fase 1 adopta FIFO; prioridades y estados adicionales se evaluarán con el motor en Fase 2.

Concurrencia global: una reserva de recursos compartida con chat más reclamación transaccional de trabajos. `FOR UPDATE SKIP LOCKED` evita reclamar la misma fila, pero por sí solo no limita a un único vídeo global. Definir bloqueo del trabajador, latidos y recuperación explícita en Fase 2. No adoptar un segundo servicio de colas por defecto.

## Audio, fase 2

| Tabla | Columnas y restricciones |
| --- | --- |
| provider_configs | id uuid PK; provider, model_name, task_type text NOT NULL; settings jsonb NOT NULL DEFAULT '{}'; created_at. Sin secretos. Perfil inmutable una vez utilizado: cambiar parámetros crea otro perfil. |
| transcripts | id uuid PK; source_id uuid FK RESTRICT; model_id uuid FK provider_configs RESTRICT; language text NULL; version integer NOT NULL CHECK > 0; created_at. UNIQUE(source_id, version), UNIQUE(id, source_id). |
| transcript_segments | id uuid PK; transcript_id uuid FK RESTRICT; ordinal integer NOT NULL CHECK >= 0; start_ms, end_ms bigint NOT NULL; text text NOT NULL. CHECK(0 <= start_ms AND start_ms < end_ms); UNIQUE(transcript_id, ordinal). |

Índice de segmentos `(transcript_id, start_ms)`. Un vídeo sin voz conserva el resultado de la etapa sin inventar segmentos. No borrar transcripciones citadas por análisis posteriores.

## Análisis y recursos, fase 3

| Tabla | Columnas y restricciones |
| --- | --- |
| analyses | id uuid PK; source_id uuid FK RESTRICT; model_id uuid FK RESTRICT; version integer NOT NULL CHECK > 0; summary text NULL; structured_data jsonb NOT NULL; schema_version integer NOT NULL CHECK > 0; quality_status text NOT NULL (`complete`, `partial`, `unavailable`); created_at. UNIQUE(source_id, version), UNIQUE(id, source_id). |
| resources | id uuid PK; resource_type, name text NOT NULL; canonical_url, description text NULL; índice único parcial en canonical_url cuando exista. |
| source_resources | source_id uuid FK RESTRICT; resource_id uuid FK RESTRICT; analysis_id uuid NOT NULL; evidence jsonb NOT NULL; PK(source_id, resource_id, analysis_id); FK(analysis_id, source_id) REFERENCES analyses(id, source_id) ON DELETE RESTRICT. |

La FK compuesta evita atribuir a una fuente un análisis de otra. Repetir la misma regla en tablas futuras que dupliquen source_id y analysis_id. Validar la estructura versionada de evidencia en backend; conservar tipo de evidencia, activo/segmento, intervalo, observación literal e interpretación separada. Añadir referencias SQL a segmentos/activos cuando deban garantizar integridad, en vez de depender solo de IDs dentro de JSON.

## Sincronización, fase 4

- Remota `pending_links`: id uuid PK estable por envío; user_id uuid NOT NULL; original_url text NOT NULL; canonical_url text NULL; status text NOT NULL (`pending`, `imported`, `error`); created_at; imported_at timestamptz NULL; last_error text NULL. RLS por propietario en SELECT/INSERT/UPDATE/DELETE. Definir FK del usuario en la migración Supabase.
- Local `sync_receipts`: remote_id uuid PK; source_id uuid NOT NULL FK RESTRICT; imported_at timestamptz NOT NULL DEFAULT now(). Para el alcance de un único proyecto remoto, remote_id basta; si se incorporan varios proyectos, agregar el identificador remoto a la clave antes de usarlos.
- Guardar fuente y recibo en una transacción; confirmar recepción remota solo después del commit. Repetir envío/acuse es idempotente. No transmitir vídeos, análisis ni embeddings.

## Recuperación y chat, fase 5

| Tabla | Columnas y reglas |
| --- | --- |
| content_chunks | id uuid PK; source_id uuid FK RESTRICT; analysis_id y transcript_id uuid NULL; ordinal integer NOT NULL CHECK >= 0; text text NOT NULL; start_ms/end_ms bigint NULL. Referencias compuestas a su misma fuente cuando corresponda. Pares de tiempos ambos nulos o `0 <= start_ms < end_ms`. Definir unicidad por versión de origen y ordinal, sin depender de NULL como igual. |
| embeddings | id uuid PK; chunk_id uuid FK RESTRICT; model_id uuid FK RESTRICT; embedding vector(D) NOT NULL. UNIQUE(chunk_id, model_id). Dimensión y perfil fijados antes de migrar. |
| chat_sessions | id uuid PK; title text NOT NULL; created_at. project_id se añade cuando exista projects en Fase 6. |
| chat_messages | id uuid PK; session_id uuid FK RESTRICT; role text CHECK en `user`, `assistant`, `system`; content text NOT NULL; citations jsonb NOT NULL DEFAULT '[]'; model_id uuid NULL FK RESTRICT; created_at. |

Comenzar con búsqueda vectorial exacta. Separar dimensiones/perfiles en espacios compatibles y diseñar reindexación al cambiar modelo. HNSW solo tras mediciones. Las citas deben resolver fuente, versión y fragmento; definir relaciones normalizadas si la persistencia de referencias requiere validación por FK.

## Proyectos y grafo, fase 6

- `projects(id uuid PK, name text NOT NULL, description text NULL, created_at timestamptz NOT NULL DEFAULT now())`.
- `project_sources(project_id uuid FK RESTRICT, source_id uuid FK RESTRICT, PRIMARY KEY(project_id, source_id))`; índice inverso por source_id.
- Añadir `chat_sessions.project_id uuid NULL REFERENCES projects(id) ON DELETE RESTRICT`.
- `knowledge_nodes(id uuid PK, node_type text NOT NULL, name text NOT NULL, metadata jsonb NOT NULL DEFAULT '{}')`. Consolidación trazable; no fusionar solo por nombre.
- `knowledge_edges(id uuid PK, from_node_id uuid FK RESTRICT, to_node_id uuid FK RESTRICT, relation_type text NOT NULL, confidence numeric NULL CHECK (confidence >= 0 AND confidence <= 1), analysis_id uuid NULL FK RESTRICT, evidence jsonb NOT NULL, review_status text NOT NULL)`. Los vínculos manuales también conservan su procedencia; distinguir propuesto, aceptado y rechazado. Definir política de autorrelaciones según tipo antes de migrar.

## Historial Alembic propuesto

| Orden | Alcance |
| --- | --- |
| 0001_sources (aplicada) | Fuentes, restricciones e índices; Fase 0 |
| 0002_library (aplicada) | Copias físicas, activos, categorías/etiquetas, asociaciones y cola detenida; Fase 1 |
| 0002 | Perfiles, transcripciones y segmentos; fase 2 |
| 0003 | Análisis, recursos y evidencias; fase 3 |
| 0004 local + migración Supabase independiente | Recibos y bandeja remota; fase 4 |
| 0005 | Fragmentos, embeddings y chat; fase 5 |
| 0006 | Proyectos, project_id del chat y grafo; fase 6 |
| Posteriores | Integraciones que realmente necesiten datos; fase 7 |

Los nombres del PDF eran hitos orientativos. Esta secuencia coloca sincronización antes de búsqueda semántica y evita crear una FK a projects antes de que exista la tabla. Las revisiones Alembic reales se generarán al implementar.

## Aceptación de cada migración

Aplicar en base vacía y en una copia con datos; comprobar duplicados, FK, intervalos, estados, conservación de versiones y rollback de transacciones. Probar restauración antes de cambios destructivos. No prometer un downgrade sin verificarlo. La primera migración no habilita procesamiento automático ni descarga modelos.
