# 0016 — Conocimiento personal y operación guiada

Fecha: 2026-11-01. Estado: implementada; aceptación final del usuario pendiente.

## Motivo y alcance

El usuario autorizó implementar el plan 8–14 completo. Se conserva la prioridad de escritorio y la arquitectura existente. Reunir vídeos, guardar ideas y conversar/relacionarlas forman un mismo recorrido. No se incorporan infraestructura remota, servicios pagados ni modelos nuevos.

## Decisiones

- Las notas son revisiones inmutables, con autoría humana, favorito/archivo y rango temporal opcional. Una cita conserva el fragmento exacto y su origen; las FK compuestas impiden vincular evidencia de otra fuente. Reprocesar no modifica estos registros. Papelera oculta, sin purgar.
- `0009_personal_library` añade notas, favoritos/resumen, archivo de proyectos/conversaciones y alcance del chat. `0010_idea_connections` permite extremos de relación ligados a una revisión concreta de un apunte. Se mantienen las revisiones de relaciones y de análisis anteriores.
- Los apuntes activos más recientes se indexan junto con audio y observaciones claras. Se guardan lotes de 128 fragmentos: una interrupción conserva lotes completos; solo una nueva orden manual procesa lo pendiente. Se retira el límite inicial de 2000 fragmentos; esto no acredita rendimiento a gran escala.
- Chat conserva tres preguntas previas para resolver referencias, con filtrado por proyecto y/o fuentes. La pertenencia actual al proyecto determina recuperación. Una conversación fija su proyecto; para cambiarlo se crea otra. Saludos/ayuda son respuestas locales explícitas sin inferencia.
- El modelo de texto local existente puede explicar en español. Cada afirmación exige una cita exacta de candidatos cerrados; números nuevos se rechazan y una segunda verificación comprueba respaldo/pregunta. Fallos de validación vuelven al modo extractivo. Son controles automáticos, no una garantía de verdad; la evidencia original sigue disponible.
- Captura secuencial de lotes, deduplicación existente, errores por elemento y cancelación. Un enlace conserva metadatos; no se añade un descargador ni se accede a cuentas. Adjuntar copia local sigue siendo la alternativa operativa.
- Las acciones de clasificación/asociación/cola por selección son transacciones atómicas. Renombrar taxonomía conserva IDs y actualiza las versiones de fuentes; una reserva transaccional ordena estas operaciones para evitar conflictos de etiquetas.
- Entrega mediante lanzadores CMD mejorados y una ventana Tkinter de mantenimiento, incluida en Python 3.13. Es un proceso separado: puede detener API/frontend y volver a iniciarlos. No se exponen endpoints web que ejecuten comandos.
- La ventana permite elegir destino de copia, verificar restauración aislada, migrarla, activarla conservando configuración anterior y volver a ella. `runtime.json` guarda opcionalmente DatabaseName/DataRoot; credenciales siguen cifradas y no cambian. Cada cambio conserva el archivo previo fuera del repositorio. La activación vuelve a comprobar la API restaurada.
- Limpieza solo de temporales conocidos bajo work/staging, con selección revisada, tamaño/fecha revalidados, rechazo de enlaces/rutas ajenas y confirmación. No hay purga de originales ni limpieza automática. Copias fuera del disco y retención requieren elección del usuario antes de automatizarlas.

## Consecuencias

Se puede buscar, exportar y recuperar el conocimiento propio sin alterar el material original. Las copias completas incluyen notas y relaciones; JSON/Markdown son exportaciones legibles, no sustituyen SQL+medios. Los modelos no se incluyen en los respaldos: una raíz restaurada necesita preparación explícita antes de ejecutar inferencia. No hay EXE autónomo ni instalación automática de PostgreSQL/Node/modelos. [Verificación y límites](../verification/product1.md).
