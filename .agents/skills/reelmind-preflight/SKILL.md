---
name: reelmind-preflight
description: Recomienda brevemente modelo, razonamiento y skills antes de ejecutar una tarea de ReelMind. Usar al pedir preflight, qué modelo usar o evaluar una nueva tarea grande.
---
# Preflight breve

Evalúa la petición sin resolverla ni ejecutar el trabajo. Usa el mensaje y contexto existente. No hagas búsquedas web, benchmarks, llamadas a otros modelos, subagentes, pruebas ni inventarios. No releas documentación inicial para esta orientación sin cambios de archivos. Si falta un dato decisivo, pregunta una vez o lee como máximo dos fragmentos concretos. No cargues las skills recomendadas para seleccionarlas.

Responde en español, preferentemente en 60–100 palabras:
- **Dificultad:** pequeña, media o grande, con una razón.
- **Modelo:** conserva el actual si basta y está explícitamente identificado. Recomienda otro nombre solo si consta en las opciones disponibles o aportadas por el usuario. Sin catálogo conocido, recomienda una categoría y reconoce esa limitación; no busques nombres en Internet.
- **Razonamiento:** bajo para cambios claros/documentación; medio para varios pasos; alto para concurrencia, migraciones, recuperación o fallos ambiguos. Máximo solo con dificultad excepcional concreta. Sujeto a opciones de la app.
- **Skills:** ninguna, una o como máximo dos, elegidas del catálogo conocido por su utilidad concreta.
- **Cierre:** una comprobación pertinente del resultado.

Rutas locales: writing-plans para plan breve de varios pasos; systematic-debugging para causa incierta; impeccable para diseño/revisión visual solicitados; vercel-react-best-practices para componentes o rendimiento React. Documentación simple suele necesitar ninguna.

No afirmes cambiar modelo/esfuerzo ni conocerlos si no están informados. No prometas ahorro exacto de tokens o créditos. No cambies el modelo local de transcripción.

Termina tras recomendar: el usuario ajusta la app y responde «continúa». Si autoriza explícitamente evaluar y ejecutar sin pausa, continúa después de recomendar. No repitas dentro de una tarea acordada. No actualices el seguimiento por una consulta orientativa sin cambios ni ejecuciones.
