# Hoja de ruta

Referencia: plan v1.3, páginas 8-11. La distribución de fases 2-7 es la consolidación propuesta en el PDF. Los hitos no acreditan funciones implementadas.

| Fase | Entrega | Condición de cierre |
| --- | --- | --- |
| 0A, preparación actual | Diagnóstico, herramientas, Git, documentación y diseño de datos | Herramientas verificadas, referencia preservada, secretos excluidos y siguiente paso claro |
| 0B, pendiente de iniciar | React/Vite/Tailwind, FastAPI, SQLAlchemy, Alembic y primera migración | UI y API arrancan; API consulta PostgreSQL; un registro sobrevive al reinicio; motor detenido |
| 1 | Biblioteca funcional | Enlaces y archivos, duplicados, etiquetas/categorías, filtros, edición y cola visible sin IA |
| 2 | Audio y motor secuencial | FFmpeg y faster-whisper; iniciar/pausar/detener; recuperación de fallos y exclusión real |
| 3 | Comprensión audiovisual | Visión y síntesis locales con evidencias; evaluación en vídeos reales y límites explícitos |
| 4 | Bandeja Supabase | Captura móvil pegando enlaces, RLS y sincronización idempotente; fallo entre commit y acuse sin duplicar |
| 5 | Búsqueda semántica y chat | pgvector, recuperación en español, citas válidas, separación de espacios vectoriales y coordinación de GPU |
| 6 | Proyectos y grafo | Asociaciones, Cytoscape.js, evidencias y corrección de vínculos sin perder fuentes |
| 7 | API, estabilidad y entrega | Permisos, instalación reproducible, respaldo/restauración y flujo completo verificados |

El primer MVP local se alcanza al cerrar la Fase 3. React Flow, compartir desde el teléfono, importación automática de guardados y nuevos tipos de contenido quedan para después de la versión inicial.

## Revisión de cada fase

Registrar pruebas como aprobadas, fallidas o pendientes. La revisión humana comprueba fidelidad de los análisis y comodidad de uso. No cerrar con fallos de pérdida de datos, análisis automático sin orden o flujo central roto. Los umbrales de rendimiento se fijarán con pruebas, no con promesas previas.
