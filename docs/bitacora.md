# Bitácora de trabajo de ReelMind

Registro cronológico, con las entradas más recientes primero. Fechas en America/Santiago. Conservar resultados anteriores y añadir correcciones explícitas si se descubre un error.

Consultar el [plan vigente](roadmap.md) y el [estado actual](status.md).

## 2026-11-01 — Auditoría de producto y plan para versión 1.0

- Objetivo confirmado: el usuario quiere las tres áreas juntas — reunir reels, saber de qué son y guardar lo importante, organizar/categorizar/conectar y conversar. No prioriza una a costa de las otras.
- Revisión real de historial/citas, ficha y ancla v5, búsqueda de Biblioteca (female), proyecto y grafo. Fallo reproducido Chat → ficha → [v5] → cerrar devuelve a Biblioteca. Filtros restaurados; sin cambios de datos ni inferencia.
- Código confirma Chat extractivo (IDs/citas y texto fijo), contexto de una pregunta anterior, últimas 50 conversaciones, selector de proyectos de 100 fuentes e índice hasta 2000 fragmentos. Identificadas ausencias de apuntes/destacados, gestión de chat/proyectos y reproducción temporal. Frescura de estado/errores en vistas ocultas identificada por código, sin ensayo destructivo para reproducirla.
- Plan único ampliado en roadmap: estabilización/versionado; captura/identificación; apuntes y ficha; búsqueda/chat; organización/conexiones; operación de escritorio y aceptación 1.0. [ADR 0015](decisions/0015-cierre-producto-personal.md). Nuevas funciones propuestas, ninguna declarada implementada.
- Verificación de este encargo: lectura de UI/código y consistencia documental; se conservan pruebas previas sin repetir suites, modelos, compilaciones ni restauraciones. Motor detenido y sin consultas activas en la lectura de estado. Siguiente bloque propuesto: 8, correcciones de recorridos y punto de código antes de ampliar.

## 2026-11-01 — Revisión antes de ampliar el producto

- Lecturas reales: health ok, 0008_graph, motor detenido, consultas inactivas, audio/visión/búsqueda preparados, índice 8/8, dos fuentes y un proyecto. Build y Junction externa presentes; sin nuevas ejecuciones pesadas ni repetición de suites.
- Documentación: operación actualizada de Consulta tus vídeos/Preguntar al flujo real de Chat; entrega local CMD distinguida de futuro instalador nativo.
- Git: 90 entradas pendientes, 61 sin seguimiento; revisión por nombre/ruta de candidatos: las dos coincidencias de carpeta data son catálogos font-index de una skill, no medios/copias de la biblioteca. Sin rutas de usuario fijas en aplicación/scripts; no equivale a auditoría exhaustiva de secretos dentro de cada archivo. No se hizo stage/commit de cambios previos. Siguiente paso recomendado: punto revisado de código antes de ampliar alcance. Copia de datos no sustituye versionado del código.

## 2026-11-01 — Fase 7: respaldo, recuperación e instalación local

- Autorización: preflight y continuación sin pausa; un agente, pruebas por riesgo. [ADR 0014](decisions/0014-recuperacion-entrega-local.md).
- library-backup.ps1: snapshot compartido entre pg_dump e inventario, medios por hash/tamaño y manifiesto completo. RestoreVerify crea base/raíz nuevas, nunca sobrescribe principal; coteja 22 tablas y dos medios. Modelos/secretos excluidos, sin limpieza automática.
- API restaurada leyó fuentes, fichas, transcripciones, rangos de medios, chats y proyecto/grafo; Origin/Host ajenos rechazados. Base original idéntica a la copia antes de reabrir; rol de aplicación no administrativo. Cuatro pruebas de rutas/corrupción/omisiones aprobadas.
- verify-install.ps1 reprodujo Python 3.13/pip check/importaciones/npm ci/build en fixture externo; corregido comando Python por stdin y retomado sin reinstalar. npm ci sustituía la Junction desde OneDrive; setup ahora instala en destino real externo y compila desde el proyecto. Dependencias anteriores conservadas.
- Controles finales: copia rechazada con API abierta; setup bloqueado antes de instalar ante registro de procesos (se corrigió el primer guard dependiente de visibilidad de procesos del sandbox). Sintaxis de cuatro scripts, Python, enlaces y diff revisados.
- Entrega local reabierta, motor detenido, consultas inactivas, PostgreSQL/API/frontend en loopback y proveedor liberado. [Detalle y límites](verification/phase7.md). No EXE, reinstalación de Windows/PostgreSQL, copia fuera del disco ni automatización de retención. Ensayos y copias se conservan.

## 2026-11-01 — Grafo manual y cierre técnico de Fase 6

- Documentación previa sincronizada, incluida la referencia de fase que había quedado desactualizada en AGENTS. [ADR 0013](decisions/0013-grafo-trazable.md) concreta nodos fuente, notas manuales y revisiones sin sustituir historial.
- Cytoscape 3.34.4 fijado y diferido; grafo/lista de relaciones, propuesta/aceptada/rechazada, acceso a fichas y corrección con expected_version. Migración aditiva `0008_graph` respaldada previamente.
- Seis pruebas dirigidas aprobadas, compilación y Alembic sin diferencias. Relación real de contraste de modalidades creada y corregida en interfaz, historial v1/v2 visible. Reinicio conservó el grafo exactamente; motor detenido y ninguna consulta activa. [Evidencias](verification/phase6.md).
- Límites: notas manuales no verificadas automáticamente, sin entidades extraídas/chat por proyecto; selector inicial 100 fuentes. Siguiente: Fase 7, estabilidad, instalación reproducible y restauración integral; móvil sigue aplazado.

## 2026-11-01 — Chat como vista propia y primer bloque de proyectos

- Solicitud: navegación independiente, flujo de chat y continuación al siguiente punto. Skills locales impeccable y React; un agente.
- Chat: historial lateral, nuevo chat, mensajes, citas desplegables y editor al pie; Enter envía, Mayús+Enter añade línea. Estado conservado al cambiar Biblioteca/Chat. Backend extractivo y contexto previo se conservan, sin prometer asistente general.
- Proyectos: creación y asociaciones manuales idempotentes; quitar asociación conserva fuente/análisis. Papelera oculta fuentes asociadas y restaurar las recupera. Migración `0007_projects` con respaldo externo previo.
- Verificación: dos pruebas PostgreSQL aisladas aprobadas; compilación y Alembic sin diferencias. Revisión de navegación e historial existente en escritorio. Sin reanalizar vídeos ni repetir suite general.
- Recorrido real: proyecto «Ideas de IA» creado y reel asociado desde la interfaz; historial previo abierto en Chat, sin contenido de Biblioteca visible. Envío con Enter limpió el editor y añadió el turno; seguimiento «¿Y en qué momento aparece?» completado con cita a 37,167 s en la misma conversación. Cierre: motor detenido, ninguna consulta activa. Capturas [Chat](verification/chat-workspace.png) y [Proyectos](verification/projects-initial.png).
- Pendiente: grafo Cytoscape, vínculos con evidencia/correcciones y alcance de chat por proyecto. Selección inicial hasta 100 fuentes. [ADR 0012](decisions/0012-chat-y-proyectos.md); fase 6 parcial.

## 2026-11-01 — Fase 5 local: índice manual y citas persistentes

- **Realizado:** pgvector 0.8.7 compilado con herramientas existentes, instalación administrativa completada por el usuario; extensión en ReelMind y `0006_retrieval` aplicada con respaldo previo. BGE-M3 multilingüe 1024 dimensiones preparado; texto Instruct 4B reutilizado. [ADR 0011](decisions/0011-busqueda-chat-local.md).
- **Producto:** fragmentos exactos con procedencia, perfiles separados, índice incremental atómico y manual; búsqueda por coseno y consultas extractivas con IDs cerrados. Historial persistente, fuente/versión/tiempo, acceso a ficha, exclusión de papelera y versiones superadas. Reserva pesada global, subprocesos protegidos, cancelación y recuperación sin reintentar al abrir.
- **Evidencia:** seis pruebas dirigidas aprobadas, compilación y Alembic sin diferencias. Ocho fragmentos reales indexados sin reanalizar medios. Pregunta en español sobre Figma/Notion seleccionó la evidencia del reel v2, 0:37; pregunta de receta reconoció falta de evidencia. Reinicio conservó análisis e historial exactos, índice ocho de ocho, motor detenido y proveedor liberado. [Detalle y límites](verification/phase5.md).
- **Pendiente:** revisión de uso del usuario; relevancia general y bibliotecas mayores sin evaluar. Respuestas iniciales como citas en idioma original, umbral 0,5 provisional. Fase 6 no iniciada; móvil/Supabase siguen aplazados. No repetir suite general aprobada sin motivo nuevo.

## 2026-11-01 — Cierre de Fase 3 y prioridad de escritorio

- **Aceptación:** «perfecto sigue con la siguiente fase» completa la revisión humana pendiente; Fase 3 cerrada con su alcance y límites iniciales, sin atribuir una evaluación general de modelos.
- **Cambio de alcance:** usuario prioriza terminar escritorio y deja móvil fuera. [ADR 0010](decisions/0010-prioridad-escritorio.md): Fase 4 completa aplazada, sin cuenta Supabase, RLS, sincronización ni bandeja de escritorio duplicada. Reconsiderar móvil solo si se solicita después de completar escritorio.
- **Dependencias revisadas:** sin referencias implementadas a Supabase/recibos remotos en backend o migraciones actuales. La biblioteca y las fichas de PostgreSQL permiten continuar con Fase 5 local; plan breve actualizado sin renumerar fases. Arquitectura conservada y entrega de escritorio dentro de Fase 7.
- **Comprobación:** coherencia, referencias y diff documental; no se ejecutaron aplicación, base, modelos o suites ni se descargaron modelos. Cambios previos de producto conservados.
- **Siguiente paso:** Fase 5 (búsqueda semántica y chat locales), todavía sin implementar; pruebas dirigidas según riesgo, sin repetir suites por rutina.

## 2026-11-01 — Ficha corregida y persistencia: verificación dirigida

- **Solicitud:** continuar el punto pendiente y reducir pruebas redundantes; preferencia registrada en AGENTS conservando controles de datos.
- **Comprobado:** consulta antes bloqueada ya ejecutada; versión 2 conserva cuatro citas exactas de sus evidencias y el historial `[2,1]`. Un único reinicio preservó IDs, versiones, segmentos, evidencias y procedencia de ambas fuentes; motor detenido.
- **Interfaz:** ficha y cita [v4] revisadas en escritorio y viewport móvil. Ajustado `overflow-wrap` por nombre largo; compilación correcta y sin desbordamiento horizontal en ambos tamaños. Capturas fuera de Git, en visualizaciones de la conversación; versión 2 abierta para el usuario.
- **Alcance de comprobación:** sin repetir suite completa, añadir pruebas para CSS ni reprocesar vídeos. Únicamente validación de citas, persistencia y presentación pendientes.
- **Resultado/siguiente paso:** verificación técnica pendiente completada; falta revisión humana de fidelidad para cerrar Fase 3. No se inició Fase 4. Estado, plan y evidencias actualizados; bloqueo anterior resuelto.

## 2026-11-01 — Fase 3: integración y evaluación en curso

- **Autorización:** continuación de Fase 3 tras preflight. Plan breve en roadmap y [ADR 0009](decisions/0009-comprension-audiovisual.md); un solo agente y sin cambiar el transcriptor.
- **Implementado:** adaptadores locales, muestreo temporal acotado, ficha versionada con síntesis y referencias, controles explícitos y persistencia atómica con procedencia SQL. Migración `0005_audiovisual` aplicada con respaldo; esquema sin diferencias y frontend compilado.
- **Pruebas:** suite previa de 80 aprobada; después, 12 pruebas dirigidas tras la corrección extractiva y compilación final aprobadas. Suite completa con los últimos cambios pendiente; no se atribuye inferencia operativa a pruebas simuladas.
- **Caso real autorizado:** reel de `VideoPrueba`, 59,433 s y sin pista de audio; copia importada con hash idéntico al original. Fallos de inferencia no publicaron resultados parciales; motor volvió a detenido. Un segundo inicio durante inferencia fue rechazado con 409.
- **Causas y correcciones:** etiquetas cortas apuntaban a Thinking; variantes Instruct explícitas preparadas y comprobadas. Primera ficha completa detectó cita discordante; pipeline 2 usa selección extractiva con cita literal, y marca OCR corrupto como no recuperado. Segunda ejecución iniciada manualmente. Se conservan versiones anteriores con aviso y diagnósticos solo locales. Sin comparativas de consumo de Codex ni instalaciones globales.
- **Recuperación comprobada:** Detener y cierre forzado durante carga visual terminaron procesos propios; reinicio detenido e historial idéntico. Motor detenido, cero pendientes y reel Procesado observados al entregar.
- **Bloqueo final y siguiente paso:** consulta API de la segunda ficha no ejecutada porque la revisión automática falló por límite de uso, sin determinar que fuera insegura. Sin eludirla mediante otro canal. Pendientes validación del resultado, persistencia posterior, recorrido visual de ficha y revisión humana. Fase 3 sigue en curso; no se inicia Fase 4.

## 2026-10-31 — Cierre visual de Fase 2

- **Realizado:** continuación autorizada tras preflight. Navegador integrado con URL local observada; importación de muestra pública existente sin activación automática, Iniciar/Pausar/Reanudar/Detener y consulta de transcripción. Sin cambios de código, modelos ni arquitectura.
- **Comprobado:** pausa al terminar el vídeo, detención del segundo intento, Versión 1 conservada sin versión parcial nueva y motor detenido al entregar. Inspección de escritorio y viewport móvil 390 × 844; capturas en [verificación de Fase 2](verification/phase2.md). No se repitieron las 69 pruebas previas.
- **Incidencia de entorno:** app inicialmente apagada; inicio restringido falló sin log de API. El mismo script con ejecución ampliada autorizada inició correctamente, sin modificar credenciales. El navegador integrado permitió completar la revisión que antes bloqueaba el controlador Windows; no se declara reparado ese controlador.
- **Resultado:** Fase 2 completada y verificada; seguimiento, README, operación y contexto de AGENTS sincronizados. Queda una muestra pública `female-0.mp4` en la biblioteca, cero pendientes y motor detenido. No se borraron datos personales.
- **Siguiente paso:** Fase 3 pendiente, sin iniciarla en este trabajo. La comprobación móvil fue responsive en escritorio; no se probó un teléfono físico.

## 2026-10-31 — Instrucciones de Codex y trabajo acotado

### Ampliación posterior — Skills locales y preflight

- **Autorizado y realizado:** guardar skills dentro de ReelMind y crear recomendador breve. Instaladas cuatro skills de fuentes oficiales con revisiones fijadas; entradas adaptadas a las reglas locales y originales conservados como UPSTREAM.md. Creada `reelmind-preflight`, con recomendación de modelo/esfuerzo y hasta dos skills usando el contexto disponible, sin ejecutar la tarea. [ADR 0008](decisions/0008-skills-locales.md) registra procedencia y el cambio respecto de la prohibición anterior de instalación.
- **Comprobado:** Python 3.13.15 del runtime existente, cinco entradas válidas mediante quick_validate, enlaces locales de sus entradas existentes y referencias selectivas de diseño presentes; `git diff --check` sin errores. README, AGENTS, estado y plan sincronizados. No se probaron las skills ejecutando tareas de producto ni comparando modelos.
- **Límites y siguiente paso:** usar `$reelmind-preflight <tarea>` o «Preflight: <tarea>» en el siguiente turno; comprobar entonces su reconocimiento por la app. Selección de modelo manual, sin promesa de consumo exacto. No se instalaron herramientas globales, activaron hooks ni ejecutaron scripts auxiliares importados. La revisión visual de Fase 2 continúa pendiente y no se inicia otra fase.

- **Alcance y resultado:** configuración documental completada en ReelMind. AGENTS incorpora lectura acotada, ejecución directa o plan breve según la tarea, depuración con evidencia, un agente por defecto, selección suficiente de modelo/esfuerzo y comprobaciones pertinentes sin repetición injustificada. Plan y estado sincronizados; historial conservado.
- **Decisión:** [ADR 0007](decisions/0007-flujo-codex.md), con inventario acotado y candidatos Superpowers, Impeccable y reglas React de Vercel sin instalar. Documentación/navegador ya disponibles en la sesión; no se añadieron herramientas ni configuración global.
- **Verificado:** coherencia, 35 referencias locales existentes, diferencias de este encargo separadas de las previas y `git diff --check` sin errores. Los 34 archivos previamente modificados/no versionados ajenos al encargo conservaron sus hashes. Solo se editaron instrucciones y seguimiento; README ya conserva el pendiente correcto.
- **Límites:** modelo/esfuerzo efectivos del chat no confirmados mediante las capacidades disponibles; política documentada, sin cambio aplicado. Sin benchmarks, compilación, ejecución de app/base/motor, descarga de modelos, transcripción ni recorrido visual.
- **Pendiente y siguiente paso:** la revisión visual de Fase 2 conserva su estado previo; retomarla en un encargo de producto. No se cierra Fase 2 ni se inicia Fase 3 con este trabajo.

## 2026-10-30 — Fase 2: audio y motor implementados; cierre visual pendiente

- **Solicitud:** «comienza y completa la fase 2 en otro chat». Autorización registrada en [ADR 0006](decisions/0006-audio-motor-manual.md).
- **Realizado:** FFmpeg, adaptador faster-whisper, modelo small CPU int8 offline, controles manuales, lotes explícitos, bloqueo PostgreSQL global, subprocesos cancelables Windows, recuperación detenida, versiones/segmentos/procedencia e historial de intentos. Migraciones 0003 y 0004 con respaldos; anteriores intactas.
- **Verificado:** 69 pruebas, compilación TypeScript/Vite, alembic check; seis muestras humanas chilenas, silencio/tono/sin pista y cancelación real. Flujo API sobre cinco registros de prueba, pausa/detención/reintento y caída forzada de API con transcripciones idénticas tras reinicio. [Evidencias](verification/phase2.md).
- **Incidencias resueltas:** PyAV 19 incompatible con faster-whisper 1.2.1; fijado PyAV 16.0.1 y repetida transcripción real. Temporales pytest bloqueados por sandbox: suite repetida con acceso autorizado. Ruta de módulo del subproceso fijada para inicio desde la raíz. Setup conserva runtime existente.
- **Limpieza:** retirados solo cinco registros identificados, cuatro copias no compartidas y temporales de sus intentos, con validación de IDs/metadatos/hash/rutas. Muestras e informes públicos conservados fuera del repositorio. Sin publicación, nuevos servicios, otros modelos ni agentes delegados.
- **Pendiente/bloqueo:** Computer Use terminó al no poder verificar la URL del navegador Windows; no se continuó automatizando UI. Falta recorrido visual de controles/transcripciones en escritorio/móvil. Fase 2 no se declara completada.
- **Siguiente paso:** terminar esa verificación visual, corregir hallazgos si los hay y cerrar Fase 2. No iniciar Fase 3. Motor detenido y seguimiento sincronizado; PDF original preservado.
- **Cierre técnico:** setup reproducido preservando el hash del runtime, pip check correcto y modelo reutilizado/verificado sin actualización. Aplicación iniciada en loopback con `0004_audio_integrity`, motor detenido; enlaces documentales comprobados. Cambios conservados en el workspace, sin publicación.

## 2026-10-29 — Cierre completo de Fase 1

- **Solicitud:** «termina la fase 1» y «termina lo que estabas haciendo y deja todo bien documentado y listo».
- **Realizado:** importación por copia y SHA-256, archivos asociados a fuentes, categorías/etiquetas, búsqueda y filtros combinados, cola persistente FIFO sin ejecución; migración `0002_library` aplicada con respaldo previo. Raíz de medios estable y configurable fuera de OneDrive.
- **Decisión:** [0005: cierre de biblioteca](decisions/0005-cierre-biblioteca.md). Categorías planas, papelera sin purga, múltiples procedencias para una copia, estados de trabajador reservados para Fase 2.
- **Verificación:** 57 pruebas aprobadas en PostgreSQL aislado, compilación TypeScript/Vite y `alembic check`; flujo real de importación, clasificación, búsqueda, filtros, cola y papelera en navegador. Reinicio de frontend/API con mismos datos, asociaciones y hash del vídeo. Revisión móvil de 390 px y puertos solo locales. [Evidencias y límites](verification/phase1.md).
- **Incidencias resueltas:** conexión de pruebas bloqueada por el entorno restringido, repetida con acceso autorizado a loopback; selección de archivo lenta en la herramienta de navegador, completada sin importaciones parciales.
- **Limpieza:** retirados exclusivamente los dos registros temporales identificados y sus asociaciones, cola y copia sintética verificada por hash. Documentación, plan, README, arquitectura, datos, operación y AGENTS sincronizados; PDF original intacto.
- **Resultado:** Fase 1 completada y verificada. Aplicación preparada e iniciada con motor detenido; sin nuevas dependencias, modelos, servicios ni publicaciones.
- **Pendientes/siguiente paso:** Fase 2, audio y motor manual. No iniciada. Restauración integral base/medios en Fase 7; no se sustituye con la prueba de reinicio.

## 2026-10-29 — Fase 1.1: gestión de enlaces

- **Solicitud:** «Empieza la Fase 1». Se comienza por el primer bloque del plan.
- **Realizado:** editar títulos, papelera recuperable, restauración desde papelera o alta duplicada, paginación y contadores; control de versión para cambios simultáneos.
- **Decisión:** [0004: gestión de enlaces](decisions/0004-gestion-de-enlaces.md). Sin nueva migración: se usan columnas existentes.
- **Verificación:** 34 pruebas aprobadas, compilación correcta, esquema sin diferencias; flujo real en navegador, paginación con 21 registros temporales y persistencia de edición/papelera tras reiniciar API. [Evidencias](verification/phase1-1.md).
- **Incidencia resuelta:** reemplazo de credencial local expuesta por un traceback de conexión y salida de pruebas ajustada; sin valores secretos en documentación.
- **Resultado:** 1.1 completado, Fase 1 en curso. Registros de prueba retirados, motor detenido.
- **Siguiente paso:** 1.2, archivos de vídeo; después organización y cola. No iniciadas IA ni Supabase.

## 2026-10-29 — Organización del plan vivo

- **Fase/tarea:** documentación transversal, antes de iniciar Fase 1.
- **Solicitud:** mantener fases y cambios en un documento editable, conservando el PDF como base.
- **Realizado:** ampliado el plan con estados, tareas y condiciones de cierre; creada esta bitácora; actualizado el procedimiento de seguimiento en AGENTS, README y estado.
- **Decisión:** [0003: plan vivo y seguimiento](decisions/0003-plan-vivo.md).
- **Verificación:** enlaces locales y consistencia documental revisados. Sin cambios de aplicación ni nuevas pruebas funcionales; las evidencias de Fase 0 mantienen su fecha original.
- **Pendiente/siguiente paso:** iniciar Fase 1 cuando el usuario indique continuar; primera tarea prevista: gestión de enlaces (1.1).

## 2026-10-28 — Cierre de Fase 0

Entrada retrospectiva incorporada el 2026-10-29 a partir del estado y las evidencias existentes.

- **Realizado:** entorno local, interfaz/API/PostgreSQL, primera migración, guardado de enlaces y accesos de inicio/detención.
- **Verificación:** 19 pruebas aprobadas; guardado y duplicados desde interfaz; persistencia tras reiniciar API y PostgreSQL. [Detalle y límites](verification/phase0.md).
- **Decisión:** [0002: arranque mínimo](decisions/0002-arranque-minimo.md).
- **Resultado:** Fase 0 completada. Commit de cierre: `cbc5a5f`.
- **Pendiente:** biblioteca completa de Fase 1; IA y Supabase en fases posteriores.

## Plantilla para la próxima entrada

Copiar al inicio del registro y completar; esta plantilla no representa trabajo realizado.

```text
## AAAA-MM-DD — Trabajo realizado
- Fase/tarea:
- Solicitud u objetivo:
- Realizado:
- Decisiones (enlaces, si corresponde):
- Verificación (aprobada, fallida o pendiente; evidencia):
- Pendientes o bloqueos:
- Siguiente paso:
```

## 2026-11-01 — Implementación del cierre funcional de escritorio

- Autorización del usuario: implementar todo el plan pendiente 8–14. Guardado punto local de código previo; sin publicación ni delegación. Se conserva la arquitectura y móvil/Supabase aplazados.
- Añadidos captura/acciones por lotes, favoritos/resumen revisado, apuntes/destacados inmutables con reproductor/exportación, Mis ideas, filtros y gestión de chat/proyectos/taxonomía. Grafo con extremos de apuntes versionados. Migraciones 0009/0010 con respaldo.
- Chat explicativo en español con citas exactas/verificación y fallback extractivo; alcance por proyecto/fuente, tres preguntas previas, archivo/renombrado/exportación e índice manual por lotes confirmados. Sin modelos nuevos ni análisis al abrir.
- Diagnóstico y ventana Tkinter de mantenimiento: copia, restauración aislada, migración/activación reversible de configuración y limpieza revisada de temporales; entrega CMD mejorada. 27 pruebas dirigidas distintas aprobadas, build y Check sin diferencias; límites en [verificación](verification/product1.md).
- Recorrido real con destacado de Figma/Notion, comentario versionado, vídeo a 37,167 s, regreso al mismo Chat e índice 9/9. Respuesta real en español y cita correcta. Copia guiada de 23 tablas/dos medios, restauración exacta en destino nuevo, activación temporal y regreso al original comprobados. Se conservan las dos fuentes, el apunte de ensayo y los respaldos.
- Siguiente paso: aceptación personal del bloque 14 con colección representativa y revisión de resumen/comparación/utilidad. No se declara versión 1.0 aceptada ni rendimiento general; copia fuera del disco/retención por elegir. [ADR 0016](decisions/0016-conocimiento-personal-y-operacion.md).
