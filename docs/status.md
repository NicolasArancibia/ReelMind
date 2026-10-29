# Estado del proyecto

Actualizado: 2026-10-28, America/Santiago.

## Resultado actual

**Fase 0 completada y verificada.** El usuario autorizó continuar desde la preparación y cerrar el arranque mínimo. Hay interfaz React/Vite/Tailwind, backend FastAPI, SQLAlchemy, Alembic y PostgreSQL conectados. El próximo trabajo es Fase 1; no se inició IA ni Supabase.

## Implementado

- Pantalla local para guardar un enlace y título opcional, ver últimos registros y contador; mensajes de validación, duplicados y desconexión.
- API de salud, alta, listado y consulta por ID. Nunca descarga el enlace ni inicia análisis.
- Migración `0001_sources` aplicada: tabla `sources`, restricciones, índices y registro Alembic. Resto del esquema previsto pendiente por fases.
- Accesos `Iniciar ReelMind.cmd` y `Detener ReelMind.cmd`; procesos ocultos y cierre únicamente de los procesos creados por este proyecto.
- Interfaz `http://127.0.0.1:5180`; API `http://127.0.0.1:8000`. El puerto 5173 pertenece a otro proyecto y no se modificó.
- Credenciales PostgreSQL cifradas fuera de Git/OneDrive; rutas resueltas en `.local/runtime.json` para instalaciones redirigidas por Windows. No se creó `.env` con contraseña.
- Respaldo automático previo a migrar; instalación reproducible con dependencias fijadas.
- Git local en `main`, sin remoto. El PDF original sigue intacto en `docs/referencias/`.

## Comprobaciones

- **19 pruebas aprobadas** con esquemas temporales PostgreSQL aislados, retirados al terminar. Guardado visible en otra conexión, duplicados, validación, procedencia de plataforma, motor detenido, migración repetida, restricciones de origen/host, errores sin secretos y configuración segura.
- `npm ci` y compilación TypeScript/Vite satisfactorias. `pip check` sin dependencias rotas. `alembic check` sin diferencias entre modelos y esquema.
- Guardado y rechazo de duplicados comprobados desde la interfaz en el navegador.
- Se detuvieron frontend/API y se reinició el servicio PostgreSQL. Después de volver a iniciar, se recuperó el mismo ID, URL y título por API y en pantalla; motor detenido. El registro de prueba se retiró usando ID, URL y título exactos. La biblioteca se entregó vacía.
- Desconexión visible en UI, botón de guardar deshabilitado sin conexión y recuperación al iniciar otra vez.
- Escritorio de 1440 px y móvil de 390 px revisados, sin desbordamiento horizontal. [Evidencia](verification/phase0.md).
- Scripts PowerShell sin errores de sintaxis. Inicio repetido detecta la instancia existente. Puertos API/interfaz escuchando solo en loopback.

Aviso no bloqueante: Starlette advierte que el adaptador de pruebas `httpx` está deprecado; las 19 pruebas pasan. No afecta al servidor en ejecución. Revisar su sustitución al actualizar dependencias.

## Límites y siguiente paso

Fase 1: biblioteca funcional, archivos, edición/eliminación, categorías/etiquetas, filtros y cola visible. Incorporar tablas mediante nuevas migraciones; no editar `0001_sources` ya aplicada. La deduplicación actual conserva parámetros/fragmentos: no equivale todavía a reconocer todas las variantes de una URL de plataforma.

pgvector: ruta nativa de Windows documentada, aún no instalado ni ensayado. FFmpeg/transcripción, modelos locales, Supabase y chat semántico esperan sus fases. La restauración completa de la biblioteca y sus futuros medios sigue pendiente; el respaldo previo y prueba de reinicio no sustituyen ese ensayo.

## Entorno verificado

Git 2.52.0; Node 24.13.0; npm 11.6.2; Python 3.13.15 (3.14 conservado); PostgreSQL 18.6; VS Code 1.140.0. React 19.3.1, Vite 8.3.5, Tailwind 4.3.3, FastAPI 0.162.0, SQLAlchemy 2.0.55 y Alembic 1.20.1. Versiones transitivas en los archivos de bloqueo.

Preparación previa: PostgreSQL solo local, usuario `reelmind_app` sin superusuario/CREATEDB/CREATEROLE, contraseñas `scram-sha-256`, pgAdmin disponible. Hardware observado: 15,6 GiB de RAM visible y RTX 3060 Laptop de 6144 MiB de VRAM; los recursos libres varían.
