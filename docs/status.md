# Estado del proyecto

Actualizado: 2026-10-29, America/Santiago.

## Resultado actual

**Fase 0 completada; Fase 1 en curso.** El usuario autorizó comenzar Fase 1. Bloque **1.1 completado y verificado**: editar títulos, papelera/restauración y paginación. El próximo bloque es 1.2, archivos de vídeo; no se inició IA ni Supabase.

## Implementado

Seguimiento: [plan de fases vigente](roadmap.md) y [bitácora de trabajo](bitacora.md). El PDF se conserva como base histórica; los cambios se registran en el plan y en decisiones.

Último trabajo (2026-10-29): gestión de enlaces 1.1, protección frente a ediciones concurrentes, 34 pruebas aprobadas y recorrido en navegador. [Decisión 0004](decisions/0004-gestion-de-enlaces.md) y [evidencias](verification/phase1-1.md). El plan vivo y la bitácora se mantienen según [decisión 0003](decisions/0003-plan-vivo.md).

- Pantalla local para guardar enlaces, editar títulos, paginar toda la biblioteca y consultar la papelera; eliminación recuperable, restauración y contadores separados.
- API de salud, alta, listado paginado, consulta por ID, edición, eliminación lógica y restauración. Control de versiones y bloqueo de fila para evitar sobrescribir cambios de otra ventana. Nunca descarga el enlace ni inicia análisis.
- Migración `0001_sources` aplicada y sin cambios: 1.1 usa `deleted_at` y `updated_at` existentes; no necesitó otra revisión. `alembic check` sin diferencias. Resto del esquema previsto pendiente por bloques.
- Accesos `Iniciar ReelMind.cmd` y `Detener ReelMind.cmd`; procesos ocultos y cierre únicamente de los procesos creados por este proyecto.
- Interfaz `http://127.0.0.1:5180`; API `http://127.0.0.1:8000`. El puerto 5173 pertenece a otro proyecto y no se modificó.
- Credenciales PostgreSQL cifradas fuera de Git/OneDrive; rutas resueltas en `.local/runtime.json` para instalaciones redirigidas por Windows. No se creó `.env` con contraseña.
- Respaldo automático previo a migrar; instalación reproducible con dependencias fijadas.
- Git local en `main`, sin remoto. El PDF original sigue intacto en `docs/referencias/`.

## Comprobaciones

### Bloque 1.1, 2026-10-29

- **34 pruebas aprobadas** (19 existentes + 15 nuevas), con esquemas PostgreSQL aislados. Edición persistente, papelera, restauración idempotente, duplicados, páginas con fechas iguales, ajuste de última página, validaciones y concurrencia real entre dos peticiones.
- Compilación TypeScript/Vite aprobada; esquema sin diferencias. Ninguna dependencia nueva.
- Recorrido en navegador: edición, cancelación, papelera, restauración normal y desde duplicado, navegación 1–20/21 con registros temporales identificados. Persistencia comprobada tras reiniciar frontend/API; mismo ID, título editado y estado de papelera.
- Revisión de escritorio y móvil de 390 px sin desbordamiento; foco de edición y cierre con Escape comprobados. Registros de prueba retirados; aplicación iniciada con motor detenido.
- Se reemplazó una credencial local de aplicación mostrada por un traceback de la primera prueba bloqueada por el entorno restringido. Copia cifrada actualizada; salida de pytest ajustada a traceback corto. Ver decisión 0004, sin secretos.

### Evidencias previas de Fase 0

Las comprobaciones siguientes corresponden al cierre de Fase 0 del 2026-10-28; se conservan como evidencia histórica. En 1.1 se repitió la suite automatizada, pero no el reinicio del servicio PostgreSQL.

- **19 pruebas aprobadas** con esquemas temporales PostgreSQL aislados, retirados al terminar. Guardado visible en otra conexión, duplicados, validación, procedencia de plataforma, motor detenido, migración repetida, restricciones de origen/host, errores sin secretos y configuración segura.
- `npm ci` y compilación TypeScript/Vite satisfactorias. `pip check` sin dependencias rotas. `alembic check` sin diferencias entre modelos y esquema.
- Guardado y rechazo de duplicados comprobados desde la interfaz en el navegador.
- Se detuvieron frontend/API y se reinició el servicio PostgreSQL. Después de volver a iniciar, se recuperó el mismo ID, URL y título por API y en pantalla; motor detenido. El registro de prueba se retiró usando ID, URL y título exactos. La biblioteca se entregó vacía.
- Desconexión visible en UI, botón de guardar deshabilitado sin conexión y recuperación al iniciar otra vez.
- Escritorio de 1440 px y móvil de 390 px revisados, sin desbordamiento horizontal. [Evidencia](verification/phase0.md).
- Scripts PowerShell sin errores de sintaxis. Inicio repetido detecta la instancia existente. Puertos API/interfaz escuchando solo en loopback.

Aviso no bloqueante: Starlette advierte que el adaptador de pruebas `httpx` está deprecado; las 19 pruebas pasan. No afecta al servidor en ejecución. Revisar su sustitución al actualizar dependencias.

## Límites y siguiente paso

Siguiente: **1.2, importación y almacenamiento local de archivos de vídeo**. Después, categorías/etiquetas, búsqueda/filtros y cola visible. Fase 1 no está completa. Incorporar tablas mediante nuevas migraciones; no editar `0001_sources` ya aplicada. La deduplicación actual conserva parámetros/fragmentos: no equivale todavía a reconocer todas las variantes de una URL de plataforma. Papelera sin purga; la paginación no congela datos entre ventanas distintas.

pgvector: ruta nativa de Windows documentada, aún no instalado ni ensayado. FFmpeg/transcripción, modelos locales, Supabase y chat semántico esperan sus fases. La restauración completa de la biblioteca y sus futuros medios sigue pendiente; el respaldo previo y prueba de reinicio no sustituyen ese ensayo.

## Entorno verificado

Git 2.52.0; Node 24.13.0; npm 11.6.2; Python 3.13.15 (3.14 conservado); PostgreSQL 18.6; VS Code 1.140.0. React 19.3.1, Vite 8.3.5, Tailwind 4.3.3, FastAPI 0.162.0, SQLAlchemy 2.0.55 y Alembic 1.20.1. Versiones transitivas en los archivos de bloqueo.

Preparación previa: PostgreSQL solo local, usuario `reelmind_app` sin superusuario/CREATEDB/CREATEROLE, contraseñas `scram-sha-256`, pgAdmin disponible. Hardware observado: 15,6 GiB de RAM visible y RTX 3060 Laptop de 6144 MiB de VRAM; los recursos libres varían.
