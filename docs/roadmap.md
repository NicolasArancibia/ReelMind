# Plan de fases de ReelMind — documento vivo

Actualizado: 2026-11-01, America/Santiago.

Este es el **plan vigente y editable**. Se actualiza a medida que trabajamos y tomamos decisiones. El [PDF v1.3](referencias/ReelMind_Plan_Maestro_v1.3.pdf) se conserva como base histórica. Las instrucciones actuales del usuario prevalecen; los cambios de alcance o arquitectura se registran en `docs/decisions/` y se reflejan aquí.

**Fases 0–3 y 5 aceptadas; Fase 6 verificada técnicamente en su alcance inicial manual.** Fase 7 verificada en su alcance inicial local; Fase 4 sigue aplazada. [Decisión de alcance](decisions/0010-prioridad-escritorio.md).

## Vista general

Fases 0–3 completadas; Fase 4 aplazada; fases 5–7 pendientes. Se conserva la numeración para mantener referencias históricas. Estados: pendiente, en curso, bloqueado (con motivo), completado y verificado, o aplazado (con decisión).

| Fase | Entrega | Condición de cierre |
| --- | --- | --- |
| 0A, completada | Diagnóstico, herramientas, Git, documentación y diseño de datos | Herramientas verificadas, referencia preservada y secretos excluidos |
| 0B, completada | React/Vite/Tailwind, FastAPI, SQLAlchemy, Alembic y primera migración | UI/API conectadas; un registro guardado desde UI sobrevive al reinicio de API/PostgreSQL; motor detenido |
| 1, completada | Biblioteca funcional; 1.1–1.5 verificados | Enlaces y archivos, duplicados, etiquetas/categorías, filtros, edición y cola visible sin IA |
| 2, completada | Audio y motor secuencial | FFmpeg y faster-whisper; controles/transcripciones verificados visualmente; recuperación de fallos y exclusión real |
| 3, completada | Comprensión audiovisual inicial | Ficha extractiva, evidencias, persistencia, interfaz y revisión humana aceptadas; límites explícitos |
| 4, aplazada | Bandeja móvil Supabase | Fuera del escritorio actual; reconsiderar solo por petición del usuario después de terminar escritorio |
| 5 | Búsqueda semántica y chat | pgvector, recuperación en español, citas válidas, separación de espacios vectoriales y coordinación de GPU |
| 6 | Proyectos y grafo | Asociaciones, Cytoscape.js, evidencias y corrección de vínculos sin perder fuentes |
| 7 | API, estabilidad y entrega | Permisos, instalación reproducible, respaldo/restauración y flujo completo verificados |

El primer MVP local se alcanza al cerrar la Fase 3. React Flow, compartir desde el teléfono, importación automática de guardados y nuevos tipos de contenido quedan para después de la versión inicial.

## Acuerdos vigentes

- React + Vite + Tailwind, FastAPI, SQLAlchemy/Alembic y PostgreSQL local como fuente de verdad.
- Enlaces y archivos de vídeo como entradas; captura inicial pegando enlaces manualmente.
- Biblioteca y análisis locales. Móvil/Supabase aplazados; no son requisito de búsqueda ni chat locales. Si se retoman, solo enlaces pendientes y metadatos mínimos.
- Análisis completo como objetivo predeterminado cuando exista el motor. Ejecución manual: abrir, reiniciar o sincronizar no activa análisis.
- Una tarea pesada a la vez, incluido el uso pesado del chat; exclusión garantizada en backend/trabajador.
- Modelos intercambiables, elegidos mediante pruebas en este equipo; sin descargas anticipadas.
- Conservar procedencia y evidencias; no inventar contenido no recuperado. Mantener los límites de [AGENTS](../AGENTS.md).

## Trabajo transversal — Instrucciones de Codex (2026-10-31)

Continuación autorizada: guardar skills dentro de `.agents/skills/` y crear `reelmind-preflight`. Resultado: recomendaciones breves de modelo, esfuerzo y skills antes de ejecutar una tarea. Cierre: validar formato, referencias y límites de las skills, sin trabajo de producto.

- [x] Instalada selección local de Superpowers, Impeccable y React, con originales, procedencia y entradas adaptadas; [ADR 0008](decisions/0008-skills-locales.md).
- [x] Creado preflight; cinco entradas válidas, enlaces de entradas existentes y diff/espacios comprobados; uso y seguimiento actualizados. Reconocimiento del selector pendiente de uso en turno posterior.

Alcance exclusivamente documental; [ADR 0007](decisions/0007-flujo-codex.md). Resultado observable: reglas proporcionadas a la tarea en AGENTS, inventario acotado y política de modelo sin cambiar su configuración efectiva. Las fases conservan su estado.

- [x] Ajustar instrucciones y registrar inventario/candidatos sin instalar herramientas.
- [x] Coherencia, rutas y diff/espacios comprobados; cambios previos preservados y seguimiento actualizado. Sin ejecutar aplicación, base, motor ni revisión visual.

## Fase 0 — Entorno y arranque mínimo

**Completada y verificada el 2026-10-28.**

- [x] Herramientas, Git local, documentación, referencia preservada y secretos excluidos.
- [x] Interfaz, API, PostgreSQL y primera migración conectados.
- [x] Guardado desde interfaz y persistencia tras reiniciar API/PostgreSQL.
- [x] Inicio/detención, mensajes de error y motor detenido.

Evidencias: [verificación de Fase 0](verification/phase0.md), 19 pruebas aprobadas y [decisión de arranque](decisions/0002-arranque-minimo.md). No equivale a un reinicio completo de Windows ni a un ensayo de restauración.

## Fase 1 — Biblioteca funcional

**Completada y verificada el 2026-10-29.** [Evidencias de cierre](verification/phase1.md): 57 pruebas, flujo de interfaz y persistencia tras reiniciar frontend/API.

- [x] **1.1 Gestión de enlaces:** editar títulos, papelera/restauración y recorrer toda la biblioteca; validación, duplicados y protección contra cambios simultáneos. [Evidencias](verification/phase1-1.md).
- [x] **1.2 Archivos de vídeo:** importar y almacenar localmente, asociar con su fuente y detectar duplicados.
- [x] **1.3 Organización:** categorías, etiquetas, búsqueda por texto y filtros.
- [x] **1.4 Pendientes:** cola visible y persistente para el análisis futuro, sin ejecutar IA.
- [x] **1.5 Cierre:** verificar el recorrido completo, persistencia, integridad y recuperación de fallos; documentar evidencias.

**Para cerrar:** gestionar enlaces y archivos desde la interfaz; conservar cambios y asociaciones tras reiniciar. Eliminación con comportamiento claro, sin borrar archivos ajenos ni perder datos por fallos parciales. Añadir nuevas migraciones sin modificar `0001_sources`.

**Decisión adoptada para 1.1:** [papelera recuperable, edición y paginación](decisions/0004-gestion-de-enlaces.md), sin purga ni cambio de URL original. **Decisiones de cierre:** [ADR 0005](decisions/0005-cierre-biblioteca.md): raíz configurable fuera de OneDrive, copias por SHA-256 con múltiples procedencias, límite inicial de 2 GiB, papelera sin purga, categorías planas, etiquetas reutilizables y cola FIFO detenida. Las jerarquías de categorías y edición global del catálogo quedan aplazadas. Se mantiene normalización conservadora de URL; no se incorporan reglas de equivalencia por plataforma sin verificarlas. No depende de descargar automáticamente vídeos de Instagram.

## Fase 2 — Audio y motor secuencial

**Completada y verificada el 2026-10-31.** [Evidencias](verification/phase2.md): 69 pruebas y ensayo real previos; cierre visual con navegador integrado, controles manuales y transcripciones en escritorio/móvil. El bloqueo anterior del controlador Windows queda registrado en las evidencias.

- [x] FFmpeg y evaluación real de faster-whisper small CPU int8.
- [x] Iniciar/Pausar/Detener, persistencia y recuperación probados por API; controles de interfaz implementados y compilados.
- [x] Exclusión global PostgreSQL, procesos cancelables Windows y prueba desde otro proceso.
- [x] Versiones, segmentos, hashes, modelo/configuración y garantía SQL de pertenencia del activo.
- [x] Recorrido visual de controles/transcripciones en escritorio y viewport móvil 390 × 844.

Retoma autorizada completada (2026-10-31): acceso y arranque detenido, controles con muestra pública existente y consulta de segmentos en escritorio/móvil. Evidencias guardadas y estado final detenido; sin repetir la suite aprobada ni iniciar Fase 3.

**Cierre verificado:** recorrido visual, transcripción real, control manual, recuperación sin duplicados y arranque detenido. Modelo inicial small CPU int8: seis muestras chilenas, 33,109 s de audio en 30,441 s; pico RSS muestreado 632,2 MiB. Calidad limitada al ensayo, sin evaluación GPU ni colección amplia de reels. Pausa al terminar el vídeo; detener conserva historial confirmado y exige reencolado manual del actual para reintentar.

## Fase 3 — Comprensión audiovisual local

**Completada y revisión humana aceptada el 2026-11-01. Modelos no definitivos.** Alcance inicial verificado; no equivale a calidad general en toda clase de vídeos.

Alcance: visión y síntesis locales sobre copias administradas; conservar audio, historial, procedencia y reserva pesada única. Sin Supabase, embeddings ni chat. Resultado observable: ficha con observaciones visuales temporales, síntesis enlazada a evidencias y límites de cobertura.

1. Verificar recursos y evaluar Qwen3-VL 4B y Qwen3 4B del plan con Ollama ya instalado, en servidor propio de ReelMind y almacenamiento fuera de OneDrive; no alterar configuración de otros proyectos.
2. Integrar adaptadores cancelables, muestreo temporal limitado, validación de evidencias y migración nueva para versiones de análisis; reutilizar motor manual y su exclusión PostgreSQL.
3. Mostrar ficha y límites; comprobar fallos, persistencia, exclusión/cancelación y recorrido visual. Cierre sujeto a revisión humana de fidelidad en vídeos reales; las muestras controladas no sustituyen esa revisión.

Entrega parcial del 2026-11-01: integración y variantes Instruct preparadas; cancelación/cierre forzado conservan historial y terminan los procesos visuales. Primera ficha real detectó una cita discordante; corregida mediante síntesis extractiva y probada de forma dirigida. Segundo procesamiento iniciado; UI final muestra Procesado, motor detenido y cero pendientes. Consulta API final bloqueada por fallo de revisión automática debido al límite de uso. Pendiente: validar esa ficha, persistencia tras reinicio, recorrido visual y fidelidad humana. [Detalle](verification/phase3.md). No se declara la fase completa.

- [x] Evaluación técnica inicial de visión/síntesis con reel real en este equipo; calidad general no establecida.
- [x] Adaptadores y ficha con procedencia, versiones y evidencias; referencias extractivas y persistencia tras reinicio comprobadas.
- [x] Límites y contenido no recuperado visibles en escritorio y tamaño móvil.
- [x] Revisión humana aceptada mediante «perfecto sigue con la siguiente fase», tras mostrar la versión 2 y completar persistencia/interfaz.

Continuación del 2026-11-01: consulta de versión 2 y sus cuatro citas aprobada; un reinicio conservó exactamente el historial de las dos fuentes. Recorrido visual de ficha y cita navegable en escritorio/móvil completado; ajuste mínimo de nombres largos compilado y revisado sin suite completa ni nuevo análisis. Bloqueo anterior resuelto. Motor detenido; ficha abierta para revisión del usuario. Preferencia de pruebas dirigidas registrada en AGENTS.

**Cierre:** ficha audiovisual local extractiva revisada por el usuario y ejecución exclusivamente manual. Primer MVP local alcanzado, con muestreo parcial y límites de calidad documentados.

## Fase 4 — Bandeja remota Supabase

**Aplazada por decisión del usuario, 2026-11-01.** [ADR 0010](decisions/0010-prioridad-escritorio.md). Captura móvil, RLS, recibos y sincronización quedan fuera del alcance actual. No hay sustituto nuevo que construir en escritorio: la entrada local ya existe. Reconsiderar únicamente si se solicita después de completar escritorio; no es dependencia de Fase 5.

- [ ] Captura móvil pegando enlaces y metadatos mínimos.
- [ ] Permisos RLS y sincronización idempotente hacia PostgreSQL local.
- [ ] Recuperación ante pausas del servicio y fallos de conexión.

**Para cerrar:** probar permisos y fallo entre guardado local y acuse remoto sin duplicar ni perder pendientes. Sincronizar no inicia análisis.

## Fase 5 — Búsqueda semántica y chat

**Implementada y verificada técnicamente, 2026-11-01; revisión de uso pendiente.** PostgreSQL, fuentes, transcripciones y fichas locales, sin depender de Fase 4. [Decisión](decisions/0011-busqueda-chat-local.md) y [evidencias](verification/phase5.md). No se inicia Fase 6 en este encargo.

Plan ejecutado: soporte vectorial y perfil multilingüe; migración y fragmentos con procedencia/versiones, indexación manual e invalidación; búsqueda y consultas extractivas con citas y reserva pesada compartida. Resultado observado: pregunta en español recupera el pasaje inglés del reel sobre Figma/Notion, v2, 0:37. Cierre técnico mediante comprobaciones dirigidas de relevancia, citas, integridad, persistencia y exclusión; seis pruebas aprobadas y compilación. Sin repetir la suite general.

- [x] pgvector 0.8.7 instalado y consulta vectorial real comprobada.
- [x] BGE-M3 1024 dimensiones; recuperación inicial español/inglés y separación por digest/perfil comprobadas.
- [x] Consultas extractivas con citas, historial persistente y reserva pesada compartida.

**Cierre técnico comprobado:** cita real válida y acceso a ficha, exclusión/cancelación/recuperación, falta de evidencia explícita y reinicio sin inferencia. Pendiente revisión de uso del usuario; no evaluación general de calidad. El umbral y los modelos siguen provisionales.

## Fase 6 — Proyectos y grafo

**Cierre técnico del alcance inicial manual, 2026-11-01.** Proyectos, asociaciones, grafo Cytoscape y revisiones de relaciones comprobados. [ADR 0013](decisions/0013-grafo-trazable.md), [verificación](verification/phase6.md). Migración `0008_graph`, seis pruebas dirigidas y persistencia real tras reinicio.

Plan breve: 1) separar Chat en vista propia con historial y mensajes conservando citas; 2) proyectos y asociaciones explícitas, sin borrar fuentes; 3) grafo Cytoscape con evidencias y correcciones persistentes. Comprobar navegación e historial en escritorio, integridad y persistencia por bloque; no repetir suites ajenas al cambio.

- [x] Asociar fuentes con proyectos y representar relaciones con Cytoscape.js.
- [x] Consultar fichas/notas de evidencia manual y corregir vínculos por revisiones sin borrar fuentes.

**Cierre comprobado:** asociaciones y correcciones persistentes, trazables y sin pérdida de fuentes. Grafo inicial de fuentes y notas manuales; entidades automáticas y chat por proyecto quedan fuera de este cierre. Fase 7 verificada a continuación en alcance local.

## Fase 7 — API, estabilidad y entrega

**Verificada en el alcance inicial local, 2026-11-01.** [ADR 0014](decisions/0014-recuperacion-entrega-local.md), [evidencias y límites](verification/phase7.md).

Plan ejecutado: revisar acceso/operación; reproducir dependencias y compilación en entorno externo limpio; respaldar base y medios con snapshot/hashes; restaurar a base/raíz nuevas y comprobar lecturas reales de API. No sustituir la biblioteca actual ni añadir infraestructura. Cierre con pruebas dirigidas de integridad y recuperación, sin repetir suite general.

- [x] Revisar contratos de API, permisos y operación local.
- [x] Reproducir dependencias/build con prerrequisitos Windows existentes y verificar recorrido local de lectura tras restauración.
- [x] Ensayar respaldo y restauración exacta de biblioteca y medios en destinos nuevos.

**Cierre comprobado:** dependencias/build reproducidos y recuperación local aislada demostrada; fallos de comillas y npm/Junction corregidos. Entrega mediante lanzadores CMD, no EXE. Instalación de sistema desde cero, copia fuera del disco, retención automática y escala quedan fuera del cierre.

## Plan de cierre del producto 1.0

**Implementación autorizada el 2026-11-01 por «implementa todo lo que falta»; en curso.** [ADR 0015](decisions/0015-cierre-producto-personal.md). Prioridad confirmada por el usuario: las tres funciones juntas — reunir reels, comprender/guardar lo importante y organizar/conectar/consultar. Este bloque amplía el cierre inicial técnico de las fases 0–7; no borra ni contradice sus evidencias ni supone que el producto ya esté terminado.

### Resultado que debe cumplir la versión final

Desde el escritorio, incorporar varios reels, reconocer su tema, analizar manualmente los disponibles, guardar citas e ideas propias con su origen, organizarlas por temas/proyectos, conectar fuentes e ideas y recuperarlas mediante búsqueda o conversación. Poder volver al momento original, exportar lo importante y recuperar la biblioteca sin depender de comandos cotidianos. Abrir o importar nunca inicia inferencia por sí solo. No prometer acceso a todos los enlaces de Instagram ni certeza de la IA.

### Inventario y brechas observadas

| Área | Existe y se conserva | Falta para el uso completo |
| --- | --- | --- |
| Entrada | Enlaces, archivo local, asociación de copias, deduplicación por URL exacta/hash, cola manual | Entrada por lotes, metadatos/títulos legibles, avisos de duplicados equivalentes; flujo claro para enlace inaccesible y recuperación permitida cuando sea viable |
| Comprensión | Transcripción, observaciones temporales, ficha y versiones; cobertura parcial explícita | Título/resumen/temas útiles y revisables; calidad en reels variados, no solo el caso inicial; progreso por etapa y fallos accionables |
| Contenido importante | Evidencias automáticas e historial de análisis | Apuntes personales, destacados/citas guardadas, favoritos y correcciones humanas separadas del original; copiar/exportar |
| Reproducción | Abrir archivo en otra pestaña y consultar tiempos en texto | Reproductor en ficha; abrir una cita directamente en su segundo; ir y volver sin perder conversación/proyecto |
| Organización | Etiquetas/categorías manuales, proyectos y asociación de fuentes | Gestión de proyectos/etiquetas, archivo/renombrado, selección y acciones por lote; paginación de todas las fuentes; criterios consistentes para sugerencias |
| Recuperación y Chat | Índice local, búsqueda backend, historial y citas exactas, control de falta de evidencia | Búsqueda de contenido visible en interfaz y notas; respuestas útiles en español con citas, contexto de varios turnos y selección de fuentes/proyecto; gestionar conversaciones |
| Conexiones | Grafo de fuentes, vínculos manuales, notas de evidencia, estados y revisiones | Conectar también ideas/destacados/temas y explorarlos; sugerencias revisables posteriores, sin asumir relaciones verdaderas por similitud |
| Operación de escritorio | Lanzadores CMD, loopback, parada/cancelación, respaldo/restauración aislada exacta y dependencias reproducidas | Ajustes/diagnóstico/almacenamiento accesibles; copia/restauración guiada, estado global de trabajo y entrega de escritorio definida |

### Evidencia de esta revisión

- Recorridos de lectura en la app abierta: historial de Chat con dos turnos, apertura de ficha desde cita, evidencia audiovisual v5, búsqueda de biblioteca por nombre y proyecto con grafo/revisión v2. Sin importar/borrar datos ni iniciar modelos. La búsqueda por «female» devolvió una fuente; filtros restaurados al terminar.
- **Fallo reproducido:** Chat → Ver ficha de la fuente → referencia [v5] → Cerrar cuadro termina en Biblioteca. El hash de evidencia se interpreta como una ruta de Biblioteca en App.tsx. Debe conservar vista de origen y contexto; también comprobar desde Proyectos. No se corrigió dentro de la auditoría.
- **Limitación confirmada:** preguntar «¿Y en qué momento aparece?» muestra otra vez la cita extensa; la aplicación no redacta una respuesta específica, aunque el tiempo 0:37 está visible. El selector actual devuelve IDs y el frontend presenta texto fijo/citas. No llamarlo todavía un asistente conversacional completo.
- **Detectado en código, pendiente de reproducción controlada:** SearchPanel conserva montaje al ocultarse y solo carga estado inicialmente o al completar sus tareas; revisar frescura del índice al volver tras nuevos análisis. Los errores al abrir fuentes desde Chat/Proyectos se envían al banner de Biblioteca, que puede estar oculto. Deben mostrarse en la vista activa.
- Límites explícitos en código: selector de proyectos carga primeras 100 fuentes; historial lista últimas 50 conversaciones sin paginación; contexto de recuperación usa solo la pregunta anterior; índice inicial hasta 2000 fragmentos, coseno mínimo 0,5 provisional. No se probaron bibliotecas grandes y no se asume que estas limitaciones estén resueltas.
- Sin módulos de apuntes/destacados ni gestión de conversaciones en las rutas/componentes revisados. Proyecto permite crear/asociar/quitar, pero no renombrar/archivar. La interfaz aún muestra «Conexiones» como futuro aunque el grafo vive dentro de Proyectos; aclarar navegación.
- Último estado leído: esquema 0008_graph, motor detenido, ninguna consulta activa, índice 8/8. Se reutilizan evidencias de integridad/recuperación existentes; no se repitió una suite general, una restauración ni un análisis. Revisión visual de escritorio, sin certificación WCAG ni ensayo de rendimiento/compatibilidad.

### Estado de implementación — 2026-11-01

Bloques **8–13 implementados** en el alcance funcional descrito abajo; ver [comprobaciones y límites](verification/product1.md) y [ADR 0016](decisions/0016-conocimiento-personal-y-operacion.md). Punto Git local conservado; esquema actual 0010. Apuntes, reproducción por cita, lotes, filtros, chat con respuestas/citas, gestión de historial/proyectos/taxonomía, conexiones de ideas y operación guiada integrados. Entrega elegida: lanzadores CMD más ventana Tkinter, sin nuevas dependencias de empaquetado. Enlaces sin descarga: se informa la limitación y se ofrece copia local. No hay clasificación/conexiones automáticas; propuestas y relaciones se revisan.

**14 en aceptación:** pruebas dirigidas, compilación, navegación real y recuperación exacta ejecutadas; el usuario aún debe completar el recorrido con su colección habitual y valorar respuestas/resúmenes/comparaciones. No se marca 1.0 aceptada. No se ensayó una biblioteca grande ni otra máquina. Destino de respaldo fuera del disco y retención automática quedan sujetos a elección del usuario; no hay automatización configurada. El plan original de bloques se conserva como criterio de aceptación, sin volver a diseñarlo.

### Aceptación dirigida en curso — 2026-11-01

Alcance: comprobar resumen de una fuente personal, conservación del alcance al recargar y exportación/citas; reutilizar las pruebas de integridad/recuperación aprobadas. Corregir únicamente fallos reproducidos y contrastar el resumen con evidencias. El usuario añadirá más reels en VideoPrueba para continuar con comparación y variedad de audio/temas. Los enlaces sin archivo se conservan como enlaces y no permiten análisis de contenido.

Hallazgos corregidos: resumen general de una fuente seleccionada recibía cero fragmentos por el umbral semántico; recargar historial perdía el filtro de fuente. Se añade muestreo temporal acotado solo para peticiones generales de resumen/temas con una fuente seleccionada, aviso de cobertura y recuperación del último alcance/modo. Cuatro pruebas dirigidas aprobadas; una se repitió tras extender saludo/exportación. No se repite la suite histórica. Comprobación real: alcance/fuente/modo conservados al recargar, copia/exportación con cobertura; el resumen recuperó ocho evidencias pero la explicación volvió a citas por validación. Recuperación corregida; calidad explicativa y comparación siguen pendientes de colección representativa y revisión del usuario. No se acepta 1.0 todavía.

### Orden de ejecución y cierre por bloque

**8 — Base estable y punto de recuperación del código. Primero, alcance acotado.**

- Revisar cambios de Git y guardar un punto local del código, separando cambios previos y excluyendo medios/secretos; nada de publicación automática.
- Corregir navegación entre vistas y referencias internas; volver desde cita/ficha a su conversación o proyecto. Recuperar conversación/proyecto seleccionado al recargar cuando corresponda.
- Mostrar errores en la vista activa y refrescar estados relevantes al entrar; indicador común de tarea pesada y acción de detención comprensible. Revisar foco/teclado en estos recorridos.
- **Cierre:** recorrido Chat/Proyecto → evidencia → ficha → regreso conserva el lugar; estados/errores visibles; ningún inicio automático. Una regresión dirigida por fallo, no repetir todo el motor.

**9 — Incorporar y reconocer una colección de reels.**

- Captura por lotes de archivos/enlaces con resultados por elemento, cancelación y control de duplicados; conservar vínculo original y nunca descartar elementos fallidos silenciosamente.
- Presentación legible: título editable, miniatura local cuando exista copia, tema/resumen corto y estado claro (solo enlace, archivo disponible, analizado, pendiente de índice, necesita intervención).
- Separar metadatos recuperados, sugerencias automáticas y datos confirmados. Si se añaden sugerencias de título/temas/categorías, ofrecer revisión y conservar procedencia.
- Evaluar acceso permitido a enlaces públicos; si falla o no está disponible, mostrar motivo y ofrecer adjuntar copia. Sin asumir descarga de guardados privados, acceso a cuentas o elusión de restricciones.
- **Cierre:** incorporar una tanda pequeña variada; reconocer qué es cada elemento y qué falta; reintentar fallidos sin duplicar ni perder originales. Analizar solo tras inicio manual.

**10 — Guardar lo importante y volver al original. Núcleo de conocimiento personal.**

- Ficha unificada con reproductor, transcripción, observaciones, notas y versiones. Tiempo/cita abre exactamente su punto dentro de la ficha.
- Guardar un destacado/cita, rango temporal y comentario propio; editar/archivar/restaurar notas con origen y autoría humana. Distinguir cita literal, interpretación y observación automática; no sobrescribir transcripción/evidencia original.
- Marcar favoritos o pendiente de revisar; copiar y exportar apuntes/citas con fuente y tiempos en formatos legibles y portables.
- Incluir estos datos en respaldo/restauración y definir su conservación al reprocesar o archivar la fuente. Migraciones nuevas, nunca modificar revisiones aplicadas.
- **Cierre:** guardar una idea, reiniciar, buscarla, reproducir su momento, exportarla y restaurarla conservando cita/versión y comentario. Una nueva versión de análisis no elimina el apunte.

**11 — Encontrar y conversar con la biblioteca de forma útil.**

- Búsqueda de contenido y apuntes accesible directamente, combinable con temas/proyectos/estado; conservar búsqueda por título/archivo/etiquetas. Resultados explicables con citas y apertura al momento correcto.
- Elegir biblioteca completa, proyecto o fuentes concretas. Contexto acotado de varios turnos y fuente de cada respuesta; contexto que no mezcle temas ni fuentes retiradas.
- Respuestas en español que contesten, expliquen, resuman o comparen según la pregunta. Mantener cita original y validar correspondencia; declarar evidencia insuficiente. Conservar modo extractivo como opción/fallback. Resolver saludos/ayuda sin fingir recuperación de evidencia.
- Renombrar/buscar/archivar/restaurar conversaciones, copiar/exportar respuestas con citas y paginar historial. Recuperar sesión tras recarga; no crear conversación al abrir.
- Indexación manual por lotes reanudables para superar el límite inicial, progreso real, actualización coherente de notas/versiones y perfiles separados. No convertir una puntuación en certeza factual.
- **Cierre:** un conjunto pequeño y variado acordado de reels/preguntas cubre seguimiento, resumen, comparación, falta de evidencia y cambios de fuente; respuestas/citas validadas contra originales, sin mezclar proyectos. Sin comparativas de modelos ni descargas nuevas por rutina.

**12 — Organización y conexiones aprovechables.**

- Renombrar/archivar/restaurar proyectos y gestionar etiquetas/categorías evitando duplicados; paginar y buscar fuentes para asociar más allá de las primeras 100.
- Acciones por selección para clasificar, asociar y preparar pendientes, sin activar motor. Mostrar recuentos y alcance antes de aplicar; operación coherente y recuperable.
- Conectar fuentes y apuntes/ideas mediante temas y relaciones con evidencia; vistas/listas claras y enlaces a originales. Mantener historial de correcciones y alternativa al lienzo.
- Sugerencias de categorías/conexiones solo como propuestas revisables; extracción/fusión automática de entidades más compleja es una mejora posterior si el uso real la justifica.
- **Cierre:** una colección repartida por temas/proyectos puede reorganizarse y recorrerse desde idea → relación → cita → vídeo, sin enlaces huérfanos ni pérdida de historial. Cambios de alcance de proyecto se reflejan en búsqueda/Chat.

**13 — Operación cotidiana como aplicación de escritorio.**

- Ajustes con ubicación/tamaño del almacén, disponibilidad de modelos y diagnóstico comprensible; progreso por etapa y causa recuperable de fallos. No porcentajes o tiempos estimados inventados.
- Copia y recuperación guiadas desde una experiencia de escritorio: orquestar parada/arranque seguros y verificar destino antes de activarlo. Mantener restauración aislada, no sobrescribir datos por defecto. Definir destino fuera del disco y retención con el usuario antes de automatizar nada.
- Limpieza revisable de temporales/ensayos y almacenamiento; purga definitiva opcional con confirmación explícita y comprobación de referencias, nunca requisito para usar papelera.
- Elegir y registrar cómo distribuir la app (lanzadores mejorados o ventana/instalador). Preservar arquitectura y datos; nuevas dependencias de empaquetado se evalúan en ese bloque. No asumir que tener un EXE significa que modelos/PostgreSQL se instalan solos.
- **Cierre:** usuario puede abrir, usar, detener, diagnosticar, respaldar y ensayar recuperar sin editar archivos o comandos cotidianos; dependencias/datos fuera de OneDrive. Instalación probada en el destino de escritorio acordado, con límites explícitos.

**14 — Aceptación de versión 1.0.**

- Recorrido completo con una colección pequeña representativa del usuario: incorporar → reconocer → analizar → destacar → organizar → conectar → buscar/conversar → exportar → recuperar. Revisar idioma, incertidumbre y ejemplos sin información suficiente.
- Comprobar teclado/foco, estados vacíos/desconexión/cancelación, ventanas de escritorio habituales y cierres inesperados en los puntos cambiados. Verificar integridad, concurrencia y recuperación que las nuevas funciones afecten; ampliar pruebas solo por riesgos concretos.
- Separar datos de prueba de colección personal, revisión final de secretos/versionado y documentación de uso. No borrar ensayos ni originales sin revisar sus rutas y referencias.
- **Cierre 1.0:** el usuario completa ese recorrido, recupera datos/citas exactos y no quedan fallos que impidan el uso principal. Lista explícita de límites y mejoras posteriores. No fijar fecha hasta descomponer y aceptar cada bloque.

### Límites del nuevo plan

Móvil/Supabase/sincronización siguen fuera. No multiusuario, servicios pagados, agentes ejecutando acciones externas, automatización de análisis al abrir, nuevas modalidades o selección de modelos por consumo. Un instalador no sustituye las mejoras funcionales centrales. El usuario autorizó después implementar el plan completo. Marcar cada cierre solo tras comprobarlo; no confundir código escrito con aceptación final.

## Aplazado y decisiones abiertas

- Fase 4 completa (móvil/Supabase/sincronización): fuera del producto de escritorio actual; se reconsidera solo por petición del usuario tras terminar escritorio. La entrega local de Fase 7 usa lanzadores CMD; un instalador EXE o contenedor nativo requerirá un alcance posterior explícito.
- Compartir directamente desde el teléfono, React Flow, importación automática de guardados y nuevos tipos de contenido: después de la versión inicial, sin fecha comprometida.
- Recuperación de vídeos de Instagram: evaluar accesos permitidos y alternativas cuando corresponda. El pegado manual de enlaces ya es parte del plan.
- Modelos definitivos, límites y rendimiento: dependen de pruebas locales, no solo de benchmarks públicos.

## Revisión previa a continuar — 2026-11-01

Operación local comprobada por consultas de lectura: health ok, esquema 0008_graph, motor detenido, sin consulta activa; audio/visión/búsqueda preparados e índice 8/8. Dependencias frontend enlazadas fuera de OneDrive y build presente. Se mantienen las evidencias aprobadas; no se repitieron análisis ni suites.

Antes de ampliar producto: revisar y guardar un punto del código en Git (90 entradas pendientes, 61 sin seguimiento al inspeccionar; no se incluyeron automáticamente cambios previos). Datos ya tienen respaldo/restauración aislada, pero esa copia no reemplaza el versionado del código. No hay una fase de producto nueva autorizada por esta revisión. Instalador nativo, chat generativo libre, escala y copia fuera del disco siguen pendientes de alcance.

## Cómo actualizarlo en cada trabajo

1. **Al comenzar:** leer una vez por encargo [AGENTS](../AGENTS.md), [README](../README.md), la parte vigente de este plan y [estado](status.md); identificar fase y tarea concreta. Cambios pequeños: ejecución directa. Varios pasos: plan corto aquí, con alcance, resultado observable y comprobación de cierre; documentación adicional solo según la tarea.
2. **Si cambia una decisión:** actualizar el alcance aquí y añadir una nota en `docs/decisions/` con fecha, motivo, cambio e impacto. No reescribir el PDF ni borrar el historial.
3. **Al terminar:** marcar solo lo verificado, actualizar [estado](status.md) y añadir una entrada a la [bitácora](bitacora.md) solo con cambios, comprobaciones, pendientes y siguiente paso nuevos y útiles. Registrar también trabajo parcial o bloqueado, sin reproducir la conversación ni reemplazar el historial.
4. **Al cerrar una fase:** enlazar las evidencias y revisar su condición de cierre.

Este plan describe hacia dónde vamos; el estado resume qué funciona hoy; la bitácora conserva lo que hicimos; las decisiones explican por qué cambió el plan. Git conserva el historial de archivos.

## Revisión de cada fase

Registrar pruebas como aprobadas, fallidas o pendientes. La revisión humana comprueba fidelidad de los análisis y comodidad de uso. No cerrar con fallos de pérdida de datos, análisis automático sin orden o flujo central roto. Los umbrales de rendimiento se fijarán con pruebas, no con promesas previas.

## Descarga manual desde enlaces — 2026-11-01

Autorizada por el usuario tras preflight. Alcance: reels públicos de Instagram, descargados únicamente al pulsar Iniciar en la cola existente; descarga → copia validada por hash → análisis secuencial existente. Sin cuentas, cookies de navegador, servicios pagados ni descarga al guardar/abrir. Implementar adaptador cancelable con límites, publicación idempotente y errores recuperables por elemento; mostrar etapa y conservar originales. Comprobar deduplicación, detención/exclusión, reintento y un enlace real. Cierre: copia real asociada al enlace y paso por el motor, o límite externo documentado sin declarar recuperación exitosa. Índice de Chat conserva su actualización manual.

Descarga implementada y comprobada en su alcance inicial: 17 casos dirigidos, compilación y un reel real descargado/asociado/transcrito; resto de cola conservado. Ver [ADR 0017](decisions/0017-descarga-manual-de-reels.md) y [evidencias/límites](verification/downloads.md). La necesidad anterior de descargar manualmente todos los casos queda sustituida para reels públicos recuperables; archivos adjuntos siguen siendo alternativa. Aceptación amplia y calidad de resúmenes/comparaciones siguen pendientes.
