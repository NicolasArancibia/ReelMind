# Estado del proyecto

Actualizado: 2026-11-01, America/Santiago.

## Resultado actual

**Descarga manual integrada, 2026-11-01:** Iniciar intenta recuperar reels públicos de Instagram sin copia y después los analiza, uno a uno; guardar/abrir no descarga. Adaptador cancelable bajo reserva pesada; copia validada/deduplicada y conservada si se detiene el análisis. 17 casos dirigidos aprobados, build/pip check correctos. Reel real: 2.199.499 bytes asociados al enlace y transcripción v1 de 25.195 ms/ocho segmentos. Solo se procesó esa fuente; demás pendientes conservados. Sin esquema/modelos nuevos ni cookies de cuentas. [Evidencias y límites](verification/downloads.md), [ADR 0017](decisions/0017-descarga-manual-de-reels.md). Índice de Chat conserva actualización manual; aceptación 1.0 pendiente.

**Aceptación dirigida, 2026-11-01:** reproducidos y corregidos dos fallos: resumen general de una fuente recibía cero fragmentos por el umbral semántico; recargar un chat perdía la fuente/modo elegidos. Resumen acotado con muestreo de hasta ocho fragmentos vigentes, aviso de cobertura, y restauración del último alcance incluso tras saludo/cancelación. Cuatro pruebas dirigidas aprobadas y build correcto; copia y exportación reales conservan aviso/fuente. Recarga real conservó fuente y modo. El caso de resumen recuperó 8/8 fragmentos del reel, pero la explicación fue rechazada por validación y devolvió cuatro citas originales: **calidad del resumen explicativo aún no aceptada**. El usuario añadirá más vídeos; los enlaces nuevos guardados no tienen archivo local y VideoPrueba aún conserva solo el reel anterior. Motor detenido, índice sin pendientes; 1.0 continúa en aceptación. [Detalle](verification/product1.md#aceptación-dirigida-posterior).


**Implementación del plan de escritorio 8–13, 2026-11-01:** captura por lotes y selección múltiple; favoritos/resúmenes; apuntes/destacados versionados con reproductor y exportación; Mis ideas con filtros; chat local en español con citas, alcance por proyecto/fuente, gestión de historial e índice por lotes; proyectos archivables, taxonomía editable y relaciones entre apuntes/fuentes. Ajustes y ventana de mantenimiento mediante CMD/Tkinter. Migraciones 0009/0010 aplicadas, sin cambiar la arquitectura. [ADR 0016](decisions/0016-conocimiento-personal-y-operacion.md).

**Comprobación:** 27 casos dirigidos distintos aprobados, build y Alembic Check correctos; recorrido real de destacado → comentario → vídeo a 37,167 s → regreso al chat, indexación manual 9/9 y respuesta en español con cita. Copia completa de 23 tablas/dos medios restaurada con huellas exactas. Activación temporal de la copia y regreso a configuración original comprobados; ambos almacenes conservados, motor detenido. [Evidencias y límites](verification/product1.md). Bloque 14: falta aceptación del usuario con una colección representativa; no se declara 1.0 aceptada ni rendimiento/calidad general. Las dos fuentes existentes y el apunte identificado como ensayo se conservan; no se descargaron modelos nuevos.


**Revisión de producto y plan 1.0, 2026-11-01:** usuario prioriza el recorrido completo de reunir reels, comprender/guardar lo importante, organizar/conectar y conversar. Revisión real de Biblioteca/Chat/fichas/Proyectos y código: base inicial útil, pero faltan apuntes/destacados, reproducción por cita, captura por lotes, gestión completa de organización/chat, síntesis conversacional y operación guiada. Fallo reproducido: referencia de evidencia desde Chat cambia a Biblioteca al cerrar ficha. [Plan priorizado 8–14](roadmap.md#plan-de-cierre-del-producto-10), [ADR 0015](decisions/0015-cierre-producto-personal.md). Solo planificación/documentación, sin implementar funciones, ejecutar modelos o alterar registros.

**Revisión para continuar, 2026-11-01:** consultas locales de lectura confirmaron health ok, esquema 0008_graph, audio/visión/búsqueda preparados, índice 8/8, dos fuentes y un proyecto; motor detenido y ninguna consulta activa. Build y enlace externo de dependencias presentes. Se corrigieron instrucciones antiguas de Chat. No se repitieron pruebas aprobadas ni se inició inferencia. Pendiente guardar un punto revisado de código en Git: 90 entradas con cambios, 61 sin seguimiento al revisar; se preservaron todos los cambios previos.

**Fase 7 verificada en su alcance inicial local:** respaldo coherente de 22 tablas y dos vídeos; restauración exacta en destinos nuevos, lecturas reales de API y controles Origin/Host. Cuatro pruebas dirigidas aprobadas. Dependencias Python 3.13/npm y build reproducidos en entorno externo limpio; corregidos comillas de PowerShell y npm ci sobre Junction. Base original conservada, app reabierta con motor detenido y sin consultas activas. [Evidencias y límites](verification/phase7.md), [ADR 0014](decisions/0014-recuperacion-entrega-local.md). Entrega mediante lanzadores existentes; sin EXE ni instalación del sistema desde cero.

**Fase 6 verificada técnicamente en su alcance inicial manual:** grafo Cytoscape, relaciones con nota de evidencia y estados, revisiones persistentes y rechazo de correcciones obsoletas. Seis pruebas dirigidas, compilación y Alembic aprobados. Reinicio conservó exactamente dos nodos, una relación y dos revisiones; motor detenido y ninguna consulta activa. [Verificación](verification/phase6.md), [ADR 0013](decisions/0013-grafo-trazable.md). Fase 7 completó después la restauración aislada descrita arriba.

**Actualización de interfaz e inicio de Fase 6:** Biblioteca, Chat y Proyectos son vistas separadas. Chat tiene historial lateral, mensajes encadenados y editor al pie; conserva citas extractivas y contexto acotado. Proyectos permite crear y asociar/quitar fuentes sin borrarlas. `0007_projects` aplicada con respaldo; dos pruebas dirigidas aprobadas, compilación y Alembic sin diferencias. Seguimiento real «¿Y en qué momento aparece?» completado en la misma conversación con cita al segundo 37,167. Motor detenido y ninguna consulta activa al cierre. El grafo y las correcciones se completaron en la continuación descrita arriba. [ADR 0012](decisions/0012-chat-y-proyectos.md).

**Fase 5 implementada y verificada técnicamente en su alcance inicial; revisión inicial aceptada por el usuario.** Búsqueda semántica y consultas extractivas con citas, índice manual e historial local. pgvector 0.8.7, BGE-M3 1024 dimensiones y Qwen3 Instruct existente; migración `0006_retrieval` aplicada con respaldo y esquema sin diferencias. Seis pruebas dirigidas y compilación aprobadas. Pregunta real en español recuperó cita del reel, v2, 0:37; pregunta sin evidencia reconocida. Reinicio conservó exactamente evidencias, índice e historial. [Verificación y límites](verification/phase5.md), [ADR 0011](decisions/0011-busqueda-chat-local.md).

**Fases 0–3 completadas y verificadas.** Revisión humana de Fase 3 aceptada el 2026-11-01. Prioridad: completar escritorio; Fase 4 móvil/Supabase aplazada por [ADR 0010](decisions/0010-prioridad-escritorio.md). Fase 6 verificada técnicamente en su alcance manual.

**Fase 3 cerrada:** visión/síntesis extractiva locales, muestreo acotado, versiones, referencias y controles manuales. Migración `0005_audiovisual` aplicada con respaldo y esquema sin diferencias. Suite previa de 80 pruebas y 12 pruebas dirigidas tras la corrección; no se presenta una suite completa final distinta de esas evidencias. Cierre técnico con comprobaciones dirigidas y compilación por ajuste de CSS; aceptación humana registrada sin nuevas ejecuciones.

La consulta pendiente pudo ejecutarse en esta continuación: versiones 2 y 1 conservadas, cuatro citas de la versión 2 idénticas al texto de su evidencia, ninguna observación incierta seleccionada y cobertura explícita de ocho fotogramas. Un único reinicio conservó exactamente versiones, segmentos, evidencias y procedencia de las dos fuentes. Sin reprocesar el vídeo. Ficha revisada en escritorio y viewport móvil 390 × 844; corregido desbordamiento por nombre largo, enlace [v4] navega a evidencia de 0:29 y tamaño normal restaurado. El bloqueo de revisión automática de la sesión anterior queda resuelto para estas comprobaciones.

**Última entrega comprobada:** conexión local activa, motor detenido, ninguna consulta activa y proveedor local liberado. Ocho fragmentos indexados y dos conversaciones conservadas. Original y análisis previos idénticos tras reinicio. Preferencia de pruebas dirigidas conservada, sin suite general repetida. [Evidencias de Fase 3](verification/phase3.md), [decisión y límites](decisions/0009-comprension-audiovisual.md).

El cierre visual previo de Fase 2 mantiene su evidencia en [Fase 2](verification/phase2.md). Se conservan aquella muestra pública y su transcripción.

## Configuración documental de Codex — 2026-10-31

**Ampliación posterior autorizada:** cinco skills locales en `.agents/skills/`: `reelmind-preflight` (creación local) y adaptaciones de `writing-plans`, `systematic-debugging`, `impeccable` y `vercel-react-best-practices`. [ADR 0008](decisions/0008-skills-locales.md) conserva fuentes/revisiones y límites. Cinco entradas aprobadas por el validador de skills con Python 3.13.15; enlaces de las entradas comprobados y `git diff --check` correcto. Preflight recomienda brevemente modelo/esfuerzo/skills sin ejecutar, cambiar selecciones ni garantizar coste. Uso en README; reconocimiento automático/selector pendiente de uso posterior. Sin instalación global, activación de hooks o ejecución de scripts importados; aplicación y fases sin cambios.

Reglas de trabajo ajustadas en [AGENTS](../AGENTS.md): lectura acotada, planes breves en el seguimiento existente, depuración con evidencia, un agente por defecto y verificaciones proporcionales. [ADR 0007](decisions/0007-flujo-codex.md) registra el inventario disponible, candidatos sin instalar y política de modelo/esfuerzo; no se pudo confirmar su selección efectiva ni se modificó configuración global o el modelo de transcripción.

Encargo documental previo completado: coherencia y 35 referencias locales comprobadas; diferencias respecto del inicio revisadas y `git diff --check` sin errores. Los 34 archivos con cambios previos ajenos a aquel encargo conservaron sus hashes. Aquel trabajo no ejecutó aplicación, base, motor ni revisión visual. La continuación de producto del 2026-10-31 completó después la revisión visual descrita arriba, usando preflight y las skills computer-use y systematic-debugging.

## Implementado y comprobado

- Biblioteca de Fase 1 conservada: enlaces/copias por SHA-256, asociaciones, categorías/etiquetas, búsqueda/filtros, papelera, paginación y cola. Regresiones aprobadas.
- Iniciar/Reanudar toma los pendientes existentes; importaciones/restauraciones/reencolados posteriores esperan otro inicio. Pausar termina el vídeo actual. Detener cancela el proceso y deja el actual `stopped`; reintentar exige Encolar e Iniciar.
- Bloqueo de sesión PostgreSQL compartido para futuras tareas pesadas; un único propietario entre procesos. Audio en subproceso cancelable y Job Object Windows; preparación de modelo explícita, inferencia offline.
- `small`, CPU int8, 4 hilos, beam 5, VAD. Sin pista → `no_audio`; silencio/tono → `no_speech` sin segmentos inventados. Enlace sin archivo → `unavailable`, sin descarga automática.
- Versiones e intentos persistentes; segmentos temporales, activo, hashes, revisión/modelo/configuración y versiones de herramientas. Reprocesar conserva versiones anteriores. La base exige que el activo pertenezca a la fuente.
- Migraciones `0001_sources` → `0002_library` → `0003_audio` → **`0004_audio_integrity`**. Respaldos previos a las nuevas revisiones. Ninguna migración aplicada fue reescrita.
- Frontend con controles y consulta de transcripciones; TypeScript/Vite compila. Recorrido visual completado en escritorio y tamaño móvil.
- `setup.ps1` conserva runtime existente y verifica Python 3.13; `prepare-audio.ps1` verifica/conserva el modelo existente.

## Evidencias de este trabajo

- **69 pruebas aprobadas** con Python 3.13.15 en esquemas PostgreSQL aislados; incluyen exclusión desde otro proceso, versiones, pausa/detención, recuperación, fallos, procedencia y caída del supervisor. `alembic check` sin diferencias.
- Seis grabaciones humanas públicas en español chileno: 33,109 s de audio en 30,441 s totales, incluyendo carga por vídeo. Pico RSS muestreado 632,2 MiB. WER simple 2/57 = 3,51%, incluyendo una representación numérica. No equivale a evaluación general de calidad.
- Silencio, tono y ausencia de pista reconocidos sin transcripción inventada. Cancelación real del proceso a los 1,021 s desde el inicio del ensayo; solicitud al superar un segundo.
- API real a través del frontend local: importación detenida, pausa, detención, reintento explícito, cuatro resultados de audio y enlace no disponible. Cierre forzado de API durante trabajo y reinicio: motor e intento detenidos, transcripciones previas idénticas en IDs, versiones, segmentos y procedencia.
- Retirados exclusivamente cinco registros temporales verificados, cuatro copias no compartidas e intermedios por intento. Muestras e informes conservados fuera de Git/OneDrive, en `verification-phase2` bajo la raíz de datos.
- Aplicación local preparada; motor detenido. API `127.0.0.1:8000`, frontend `127.0.0.1:5180`. Sin remoto, publicación ni puertos externos.

## Límites y siguiente paso

- Fases 0–3 cerradas; Fase 4 aplazada. Fase 5 lista para revisión de uso; después siguen 6 y 7. Mantener detenida la ejecución al entregar.
- Audio CPU, visión/síntesis y búsqueda/chat locales con alcance inicial comprobado. Sin Supabase ni instalación de CUDA/cuDNN. Los resultados automáticos y el umbral de búsqueda siguen siendo provisionales.
- Primera pista de audio. Con varias copias en una fuente, crear una fuente local del archivo elegido; no se selecciona arbitrariamente. Sin diarización.
- Pausa por vídeo; no hay reanudación parcial dentro de un vídeo. Detener conserva lo confirmado y descarta el resultado incompleto. Modelos liberados entre trabajos.
- `no_speech` expresa ausencia de voz detectada, no certeza de ausencia de habla. Puede haber errores. Falta evaluar vídeos largos, música, ruido y habla superpuesta.
- Papelera sin purga. Cierre abrupto puede dejar temporales; limpieza manual por intento, sin borrar originales. Límite de ejecución de 7200 s configurable.
- Importación hasta 2 GiB por defecto; no se ensayó ese tamaño. Restauración aislada de base y medios comprobada en Fase 7. Los respaldos SQL previos a migraciones no incluyen vídeos; la copia integral sí. No se reinició Windows ni PostgreSQL en este trabajo.

## Documentación y entorno

[Plan vigente](roadmap.md), [bitácora](bitacora.md), [ADR 0006](decisions/0006-audio-motor-manual.md), [operación](operations.md), [modelos](models.md).

Histórico: [Fase 0](verification/phase0.md), [Fase 1.1](verification/phase1-1.md), [Fase 1](verification/phase1.md). Conservan fecha y alcance.

Python 3.13.15, PostgreSQL 18.6, Node 24.13.0; React/Vite/Tailwind y FastAPI/SQLAlchemy/Alembic conservados. Paquetes fijados en `backend/requirements.lock`: faster-whisper 1.2.1, CTranslate2 4.8.4, PyAV 16.0.1, imageio-ffmpeg 0.6.0 y dependencias. FFmpeg 7.1 incluido. PyAV 19 se descartó tras un fallo real de compatibilidad.
