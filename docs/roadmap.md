# Plan de fases de ReelMind — documento vivo

Actualizado: 2026-10-29, America/Santiago.

Este es el **plan vigente y editable**. Se actualiza a medida que trabajamos y tomamos decisiones. El [PDF v1.3](referencias/ReelMind_Plan_Maestro_v1.3.pdf) se conserva como base histórica. Las instrucciones actuales del usuario prevalecen; los cambios de alcance o arquitectura se registran en `docs/decisions/` y se reflejan aquí.

**Situación actual: Fase 0 completada; Fase 1 en curso, bloque 1.1 completado y verificado.** Siguiente bloque: 1.2, archivos de vídeo. Las fases 2-7 conservan la distribución propuesta a partir del PDF y podrán ajustarse con pruebas. Una función planificada no está implementada por aparecer aquí.

## Vista general

Fase 1 en curso; fases 2-7 pendientes. Estados de trabajo: pendiente, en curso, bloqueado (con motivo), completado y verificado, o aplazado (con decisión).

| Fase | Entrega | Condición de cierre |
| --- | --- | --- |
| 0A, completada | Diagnóstico, herramientas, Git, documentación y diseño de datos | Herramientas verificadas, referencia preservada y secretos excluidos |
| 0B, completada | React/Vite/Tailwind, FastAPI, SQLAlchemy, Alembic y primera migración | UI/API conectadas; un registro guardado desde UI sobrevive al reinicio de API/PostgreSQL; motor detenido |
| 1, en curso | Biblioteca funcional; 1.1 completado | Enlaces y archivos, duplicados, etiquetas/categorías, filtros, edición y cola visible sin IA |
| 2 | Audio y motor secuencial | FFmpeg y faster-whisper; iniciar/pausar/detener; recuperación de fallos y exclusión real |
| 3 | Comprensión audiovisual | Visión y síntesis locales con evidencias; evaluación en vídeos reales y límites explícitos |
| 4 | Bandeja Supabase | Captura móvil pegando enlaces, RLS y sincronización idempotente; fallo entre commit y acuse sin duplicar |
| 5 | Búsqueda semántica y chat | pgvector, recuperación en español, citas válidas, separación de espacios vectoriales y coordinación de GPU |
| 6 | Proyectos y grafo | Asociaciones, Cytoscape.js, evidencias y corrección de vínculos sin perder fuentes |
| 7 | API, estabilidad y entrega | Permisos, instalación reproducible, respaldo/restauración y flujo completo verificados |

El primer MVP local se alcanza al cerrar la Fase 3. React Flow, compartir desde el teléfono, importación automática de guardados y nuevos tipos de contenido quedan para después de la versión inicial.

## Acuerdos vigentes

- React + Vite + Tailwind, FastAPI, SQLAlchemy/Alembic y PostgreSQL local como fuente de verdad.
- Enlaces y archivos de vídeo como entradas; captura inicial pegando enlaces manualmente.
- Biblioteca y análisis locales. Supabase futuro solo para enlaces pendientes y metadatos mínimos; modalidad gratuita, aceptando posibles pausas.
- Análisis completo como objetivo predeterminado cuando exista el motor. Ejecución manual: abrir, reiniciar o sincronizar no activa análisis.
- Una tarea pesada a la vez, incluido el uso pesado del chat; exclusión garantizada en backend/trabajador.
- Modelos intercambiables, elegidos mediante pruebas en este equipo; sin descargas anticipadas.
- Conservar procedencia y evidencias; no inventar contenido no recuperado. Mantener los límites de [AGENTS](../AGENTS.md).

## Fase 0 — Entorno y arranque mínimo

**Completada y verificada el 2026-10-28.**

- [x] Herramientas, Git local, documentación, referencia preservada y secretos excluidos.
- [x] Interfaz, API, PostgreSQL y primera migración conectados.
- [x] Guardado desde interfaz y persistencia tras reiniciar API/PostgreSQL.
- [x] Inicio/detención, mensajes de error y motor detenido.

Evidencias: [verificación de Fase 0](verification/phase0.md), 19 pruebas aprobadas y [decisión de arranque](decisions/0002-arranque-minimo.md). No equivale a un reinicio completo de Windows ni a un ensayo de restauración.

## Fase 1 — Biblioteca funcional

**En curso.** Orden de trabajo, ajustable durante la implementación:

- [x] **1.1 Gestión de enlaces:** editar títulos, papelera/restauración y recorrer toda la biblioteca; validación, duplicados y protección contra cambios simultáneos. [Evidencias](verification/phase1-1.md).
- [ ] **1.2 Archivos de vídeo:** importar y almacenar localmente, asociar con su fuente y detectar duplicados.
- [ ] **1.3 Organización:** categorías, etiquetas, búsqueda por texto y filtros.
- [ ] **1.4 Pendientes:** cola visible y persistente para el análisis futuro, sin ejecutar IA.
- [ ] **1.5 Cierre:** verificar el recorrido completo, persistencia, integridad y recuperación de fallos; documentar evidencias.

**Para cerrar:** gestionar enlaces y archivos desde la interfaz; conservar cambios y asociaciones tras reiniciar. Eliminación con comportamiento claro, sin borrar archivos ajenos ni perder datos por fallos parciales. Añadir nuevas migraciones sin modificar `0001_sources`.

**Decisión adoptada para 1.1:** [papelera recuperable, edición y paginación](decisions/0004-gestion-de-enlaces.md), sin purga ni cambio de URL original. **Pendiente para los próximos bloques:** raíz de datos configurable, formatos/tamaños admitidos, política de copia y eliminación de archivos, reglas adicionales de duplicados por plataforma y organización de etiquetas/categorías. Resolver antes de implementar cada comportamiento. No depende de descargar automáticamente vídeos de Instagram.

## Fase 2 — Audio y motor secuencial

**Planificada; detalles sujetos a pruebas.**

- [ ] Extracción de audio con FFmpeg y evaluación de transcripción con faster-whisper.
- [ ] Iniciar, pausar y detener, con estados persistentes y recuperación de fallos.
- [ ] Exclusión de tareas pesadas garantizada en backend/trabajador.

**Para cerrar:** transcripción real verificada, control manual y recuperación sin trabajos duplicados; arranque siempre detenido. Fijar modelo y rendimiento con pruebas locales.

## Fase 3 — Comprensión audiovisual local

**Planificada; modelos no definitivos.**

- [ ] Evaluar visión y síntesis con vídeos reales en este equipo.
- [ ] Integrar adaptadores y análisis completo con procedencia, versiones y evidencias.
- [ ] Mostrar límites y contenido no recuperado explícitamente.

**Para cerrar:** análisis audiovisual local revisado por el usuario, sin afirmaciones inventadas ni activación automática. Aquí se alcanza el primer MVP local.

## Fase 4 — Bandeja remota Supabase

**Planificada.**

- [ ] Captura móvil pegando enlaces y metadatos mínimos.
- [ ] Permisos RLS y sincronización idempotente hacia PostgreSQL local.
- [ ] Recuperación ante pausas del servicio y fallos de conexión.

**Para cerrar:** probar permisos y fallo entre guardado local y acuse remoto sin duplicar ni perder pendientes. Sincronizar no inicia análisis.

## Fase 5 — Búsqueda semántica y chat

**Planificada.**

- [ ] Instalar y verificar pgvector cuando corresponda.
- [ ] Evaluar embeddings y recuperación en español, separando espacios por modelo/versión.
- [ ] Chat con citas verificables y coordinación de GPU con el motor.

**Para cerrar:** recuperar fuentes reales y responder con citas válidas; respetar la exclusión de tareas pesadas y reconocer falta de evidencia.

## Fase 6 — Proyectos y grafo

**Planificada.**

- [ ] Asociar fuentes con proyectos y representar relaciones con Cytoscape.js.
- [ ] Consultar evidencias y corregir vínculos conservando las fuentes.

**Para cerrar:** asociaciones y correcciones persistentes, trazables y sin pérdida de información de origen.

## Fase 7 — API, estabilidad y entrega

**Planificada.**

- [ ] Revisar contratos de API, permisos y operación local.
- [ ] Verificar instalación reproducible y recorrido completo.
- [ ] Ensayar respaldo y restauración de biblioteca y medios.

**Para cerrar:** instalación y recuperación demostradas, fallos importantes resueltos y límites documentados. Los respaldos previos a migraciones y cuidados de integridad se aplican desde las fases anteriores.

## Aplazado y decisiones abiertas

- Compartir directamente desde el teléfono, React Flow, importación automática de guardados y nuevos tipos de contenido: después de la versión inicial, sin fecha comprometida.
- Recuperación de vídeos de Instagram: evaluar accesos permitidos y alternativas cuando corresponda. El pegado manual de enlaces ya es parte del plan.
- Modelos definitivos, límites y rendimiento: dependen de pruebas locales, no solo de benchmarks públicos.

## Cómo actualizarlo en cada trabajo

1. **Al comenzar:** leer [README](../README.md), este plan y [estado](status.md); identificar fase y tarea concreta.
2. **Si cambia una decisión:** actualizar el alcance aquí y añadir una nota en `docs/decisions/` con fecha, motivo, cambio e impacto. No reescribir el PDF ni borrar el historial.
3. **Al terminar:** marcar solo lo verificado, actualizar [estado](status.md) y añadir una entrada a la [bitácora](bitacora.md) con cambios, pruebas, pendientes y siguiente paso. Registrar también trabajo parcial o bloqueado.
4. **Al cerrar una fase:** enlazar las evidencias y revisar su condición de cierre.

Este plan describe hacia dónde vamos; el estado resume qué funciona hoy; la bitácora conserva lo que hicimos; las decisiones explican por qué cambió el plan. Git conserva el historial de archivos.

## Revisión de cada fase

Registrar pruebas como aprobadas, fallidas o pendientes. La revisión humana comprueba fidelidad de los análisis y comodidad de uso. No cerrar con fallos de pérdida de datos, análisis automático sin orden o flujo central roto. Los umbrales de rendimiento se fijarán con pruebas, no con promesas previas.
