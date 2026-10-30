# Estado del proyecto

Actualizado: 2026-10-29, America/Santiago.

## Resultado actual

**Fases 0 y 1 completadas y verificadas.** El usuario autorizó terminar Fase 1. La biblioteca gestiona enlaces y archivos locales, títulos, categorías/etiquetas, búsqueda/filtros, papelera y pendientes. **El motor permanece detenido y aún no existe ejecución de IA.**

La siguiente fase es **2: audio y motor manual**, todavía no iniciada. Supabase y los demás módulos esperan sus fases.

## Implementado

- Interfaz local con guardado de enlaces y copia de vídeos, archivos adjuntos a una fuente, edición de título, categorías y etiquetas reutilizables, búsqueda textual y filtros combinables.
- Biblioteca, papelera y cola paginadas de 20 en 20; contadores globales separados y total filtrado. Cola en orden de llegada, con retirada y reencolado manual.
- Duplicados de URL normalizada y contenido SHA-256; varias fuentes pueden compartir una copia física sin perder procedencia. Restauración del original cuando el duplicado está en papelera.
- Almacenamiento fuera de OneDrive y configurable; nombres de archivo tratados como metadatos y rutas relativas validadas. El original seleccionado no se modifica. La papelera conserva todas las asociaciones y copias.
- Protección por versión y bloqueo de fila para edición, papelera, organización, cola y adjuntos. Bloqueo PostgreSQL por hash para publicación concurrente de medios; recuperación de importaciones por reintento.
- Migraciones `0001_sources` y `0002_library` aplicadas. La primera no se modificó. La segunda añade archivos físicos, activos, etiquetas/categorías, relaciones y pendientes, con backfill de fuentes existentes.
- Accesos de inicio y detención; solo procesos de ReelMind. Interfaz en `http://127.0.0.1:5180`, API en `http://127.0.0.1:8000`. Puerto 5173 de otro proyecto sin cambios.
- Credenciales PostgreSQL cifradas fuera de Git/OneDrive; `.local/runtime.json` sin contraseñas. Raíz de medios resuelta desde variable de entorno o runtime persistido. Respaldo automático antes de migrar.
- Git local en `main`, sin remoto ni publicación. Sin nuevas dependencias, infraestructura ni modelos. PDF original conservado.

Decisiones: [0005, biblioteca completa](decisions/0005-cierre-biblioteca.md) y [0004, gestión de enlaces](decisions/0004-gestion-de-enlaces.md). Seguimiento: [plan vigente](roadmap.md) y [bitácora](bitacora.md).

## Comprobaciones del cierre de Fase 1

- **57 pruebas aprobadas** con Python 3.13.15 y esquemas PostgreSQL aislados: regresión de 1.1, archivos, validación, rutas, duplicados, concurrencia, fallos parciales y reintentos, clasificación, búsqueda/filtros, cola, migración con datos e integridad.
- TypeScript/Vite compila. `alembic check` sin diferencias. Respaldo previo a migrar creado y esquema real en `0002_library`.
- Recorrido de interfaz con un enlace y un AVI sintético: creación, clasificación, adjunto, importación independiente, búsqueda por etiqueta, filtro de archivos, retirada de cola, papelera y restauración.
- Reinicio de frontend/API: mismos IDs, fechas, etiquetas, categorías, activos, estados de papelera y cola. Copia descargada idéntica por SHA-256 antes y después; motor detenido. No se reinició el servicio PostgreSQL en este cierre.
- Escritorio y móvil de 390 px revisados sin desbordamiento horizontal. Puertos API/interfaz/PostgreSQL limitados a loopback. Los dos registros de prueba y su copia sintética administrada fueron retirados por ID/hash, conservando datos ajenos.
- Aplicación iniciada y lista para uso local. Las capturas documentan la prueba anterior a la limpieza.

[Evidencia detallada y límites](verification/phase1.md). Se conserva el aviso no bloqueante de Starlette por su adaptador de pruebas `httpx` deprecado; la suite pasa.

## Evidencias históricas

- [Fase 0](verification/phase0.md), 2026-10-28: 19 pruebas, herramientas e inicio local, guardado de enlace y persistencia tras reiniciar API y servicio PostgreSQL. No equivale a reiniciar Windows o restaurar un respaldo.
- [Bloque 1.1](verification/phase1-1.md), 2026-10-29: 34 pruebas, edición, papelera, restauración, paginación con 21 registros, concurrencia y recorrido de interfaz. Su incidencia de credencial quedó resuelta en esa entrega; no se publican secretos.

## Límites y siguiente paso

- Importación manual hasta 2 GiB por defecto; extensión y firma de contenedor comprobadas, sin decodificación ni transcodificación. No se ensayó un archivo real de 2 GiB. La reproducción depende del navegador.
- Categorías planas. Sin edición global/borrado de nombres del catálogo ni jerarquías. Búsqueda textual literal, no semántica; conserva acentos. Duplicados de URL conservadores, sin prometer equivalencia de todas las variantes de plataforma.
- Papelera sin purga. No hay limpieza automática; un cierre forzado puede dejar temporales o copias sin fila, conservadas para recuperación. Archivo ausente: reimportar el mismo original. [Operación y recuperación](operations.md).
- No hay descarga automática de enlaces, FFmpeg, transcripción, trabajador, modelos, Supabase ni chat. Próximo trabajo: Fase 2, con controles manuales y exclusión real de tareas pesadas.
- El respaldo de PostgreSQL no incluye medios. La restauración integral de biblioteca y archivos sigue pendiente de Fase 7; no está cubierta por las pruebas de reinicio o reintento.

## Entorno verificado

Git 2.52.0; Node 24.13.0; npm 11.6.2; Python 3.13.15 (3.14 conservado); PostgreSQL 18.6; VS Code 1.140.0. React 19.3.1, Vite 8.3.5, Tailwind 4.3.3, FastAPI 0.162.0, SQLAlchemy 2.0.55 y Alembic 1.20.1. Dependencias exactas en los archivos de bloqueo existentes.

PostgreSQL local con usuario de aplicación sin superusuario/CREATEDB/CREATEROLE y contraseñas scram-sha-256. Hardware observado previamente: 15,6 GiB de RAM visible y RTX 3060 Laptop de 6144 MiB de VRAM; recursos libres variables. pgvector no instalado ni ensayado.
