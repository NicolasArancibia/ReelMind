# Verificación de Fase 3 — cierre inicial aceptado

Fecha: 2026-11-01, America/Santiago. [Decisión](../decisions/0009-comprension-audiovisual.md).

## Implementación y pruebas

- Adaptadores separados de visión/texto con Ollama local existente, inferencia sin descarga automática, proceso propio por intento en loopback y bajo el Job Object del trabajador.
- Muestreo máximo de ocho fotogramas, tiempos reales y hashes JPEG; resolución acotada a 768 × 1024. La síntesis recibe como máximo 12 segmentos de audio. Es cobertura parcial explícita, no análisis de todos los fotogramas ni de todo el audio.
- JSON estricto; rechazo de respuesta truncada/no JSON y de referencias inexistentes. Cada síntesis cita IDs visibles en la ficha. Eso no garantiza corrección factual.
- `0005_audiovisual` aplicada con respaldo previo `before-migration-20261101-000549-452.dump`; esquema coincide (`alembic check`). FK compuesta impide usar transcripción de otra fuente/activo; ficha y transcripción se confirman juntas.
- **Suite previa: 80 pruebas aprobadas** en 43,74 s con Python 3.13.15 y esquemas PostgreSQL aislados. Después se añadieron controles de razonamiento interno, liberación entre etapas y OCR no recuperable; tras la corrección extractiva pasaron **12 pruebas dirigidas**, excluyendo dos casos de integración ya existentes. La suite completa con los últimos cambios no se ejecutó; no se presenta como aprobada.
- La primera ejecución tuvo 71 aprobadas y dos fallos del contenedor JPEG en memoria. Se corrigió `image2` → `image2pipe`, se probaron los casos afectados y luego la suite final de 77 pasó. Otro intento unitario no llegó a ejecutar casos por permisos del temporal del sandbox; se usó un temporal dentro de `.local`, sin cambiar permisos globales.
- TypeScript/Vite compilados. Ninguna nueva dependencia Python/Node ni instalación global. Modelo de transcripción conservado.

## Preparación y caso real

Ollama 0.40.13 ya instalado, inicialmente sin modelos. Preparación explícita de `qwen3-vl:4b` y `qwen3:4b` en `models/ollama` bajo raíz local de datos fuera de OneDrive. Manifiesto `models/audiovisual.json` conserva versión, cuantización y digests. No se modificó la configuración global de Ollama. Su consulta inicial por CLI abrió su aplicación existente; las descargas/análisis de ReelMind usan otro proceso/puerto y almacén.

El usuario proporcionó un reel en `VideoPrueba`; se importó una copia administrada sin alterar el original. Archivo: 4.002.868 bytes, duración 59,433 s, una pista de vídeo y ninguna de audio. Fotogramas muestreados a 0, 7433, 14867, 22300, 29733, 37167, 44600 y 52033 ms. No se atribuye voz a este archivo. Medios y resultados detallados fuera de Git; su contenido no se copia a esta documentación.

Los ensayos iniciales fallaron sin publicar transcripción ni ficha parciales; motor detenido sin reintentos automáticos. Durante inferencia, otro inicio fue rechazado con HTTP 409. Se confirmó hash original/importación idéntico. Un fotograma aislado produjo JSON válido, pero otro agotó salida: el diagnóstico posterior mostró `done_reason=length`, 1536 tokens, 5825 caracteres de razonamiento interno y cero de contenido final pese a `think:false`. No se conserva razonamiento interno en esta documentación.

La inspección `/api/show` confirmó Thinking en las etiquetas cortas; texto declara únicamente `[true]`. Se prepararon las variantes Instruct explícitas `qwen3-vl:4b-instruct-q4_K_M` y `qwen3:4b-instruct-2507-q4_K_M`. Visión declara `[false]`, default false. Texto enumera capacidad thinking pero sin configuración; pasó una respuesta estructurada breve sin razonamiento. Preparación y ejecución usan la misma reserva PostgreSQL. No hubo comparativas de modelos ni de consumo de Codex.

## Comprobaciones reales completadas y cierre pendiente

- **Cancelación durante carga visual:** botón Detener; Ollama y llama-server propios terminaron, motor detenido y ninguna versión parcial. Instantánea de transcripciones/análisis de las dos fuentes idéntica antes/después.
- **Cierre forzado:** API cerrada con muestra pública durante carga visual; ambos procesos terminaron. Reinicio detenido, intento detenido, sin reintento automático; versiones, segmentos, evidencias y procedencia idénticos a la instantánea previa.
- **Primera ficha Instruct completa:** ocho fotogramas, `no_audio`, cero segmentos. Etapa visual/textual 110,998 s. Pico observado del árbol API 2569,7 MiB RSS; GPU total usada 5919 MiB, incluye otros consumidores y no equivale a VRAM exclusiva del modelo. Corresponde a ese ensayo inicial, no a la segunda versión ni a una comparación de modelos.
- **Fidelidad:** se detectó una referencia discordante en la paráfrasis. Pipeline 2 selecciona IDs mediante enum y cita literalmente su observación; excluye observaciones inciertas. OCR con escapes repetidos se marca no recuperado. Primera versión conservada con aviso, sin reescribir historial. Pruebas dirigidas y compilación aprobadas; segundo procesamiento iniciado manualmente.
- **Límite del cierre:** la revisión automática rechazó ejecutar la consulta API del resultado por límite de uso; fue un fallo de revisión, no una decisión de inseguridad. No se consultó la ficha por otro canal para eludirlo. Quedan sin verificar contenido de la segunda versión, persistencia posterior a reinicio y recorrido visual final de ficha en escritorio/móvil.
- **Estado de entrega leído en UI:** conexión activa, reel Procesado, motor Detenido, cero pendientes. Controles móviles revisados a 390 × 844; tamaño normal restaurado. No se confunde esa lectura con inspección de la ficha pendiente.

Diagnósticos y muestras derivados bajo raíz local de datos, fuera de OneDrive/Git. Modelo de transcripción conservado. Fases 4–7 sin iniciar.

## Condición de cierre

La comprobación técnica pendiente se completó en la continuación descrita abajo. El usuario aceptó después la revisión de fidelidad con «perfecto sigue con la siguiente fase», el 2026-11-01. Fase 3 cerrada en su alcance inicial; un único reel no evalúa vídeos largos, ruido, música, escenas rápidas ni texto muy pequeño. Fase 4 quedó aplazada por prioridad de escritorio; [ADR 0010](../decisions/0010-prioridad-escritorio.md). No se añaden nuevas pruebas a las evidencias por registrar esta aprobación.

## Continuación dirigida — 2026-11-01

- La consulta API antes bloqueada se ejecutó correctamente. Historial `[2, 1]`; versión 2 extractiva con cuatro citas. Cada cita contiene exactamente la observación de su único ID de evidencia y excluye observaciones inciertas; ocho fotogramas, cero segmentos de audio usados. No hubo nueva inferencia.
- Instantánea `verification-phase3/confirmed-extractive.json` bajo raíz local de datos. Tras un único reinicio de frontend/API, transcripciones y análisis de ambas fuentes idénticos, incluyendo IDs, versiones, segmentos, evidencias y procedencia. Motor detenido, sin fuente activa.
- Interfaz: versión 2 visible y versión 1 conservada, cobertura parcial y límites explícitos. Enlace [v4] navega al fragmento de 0:29. Inspección en escritorio y viewport 390 × 844; no es teléfono físico.
- Se detectó desbordamiento por el nombre de archivo en metadatos. Ajuste de `overflow-wrap` solo en ayudas del diálogo; compilación TypeScript/Vite correcta. Ancho de contenido/scroll iguales tras corregir: 463/463 en escritorio y 320/320 en móvil. Sin prueba automatizada nueva para CSS.
- Capturas de escritorio y móvil guardadas en el directorio de visualizaciones de esta conversación, fuera del repositorio; ficha abierta y tamaño normal restaurado al entregar.
- No se repitió la suite ni se reprocesó el reel. Preferencia de verificaciones dirigidas por riesgo registrada en AGENTS; se conserva la comprobación de persistencia por su importancia para datos.
