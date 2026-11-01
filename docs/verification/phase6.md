# Fase 6 — Proyectos y grafo inicial

2026-11-01, America/Santiago. Cierre técnico del alcance inicial manual. [ADR 0013](../decisions/0013-grafo-trazable.md).

- Migraciones aditivas `0007_projects` y `0008_graph`, respaldos externos previos; último `before-migration-20261101-050052-440.dump`. Alembic sin diferencias. Ninguna migración aplicada reescrita.
- Seis pruebas dirigidas de proyectos/grafo aprobadas en 3,45 s con PostgreSQL en esquemas aislados: idempotencia y conservación de fuentes; historial de revisiones; rechazo de correcciones obsoletas; dos correcciones simultáneas con un único ganador; validación de extremos/evidencia/autorrelaciones; ocultación por papelera o retirada del proyecto y recuperación al reasociar.
- TypeScript/Vite aprobados tras ajustes finales de disposición y zona horaria. Cytoscape diferido en paquete separado; sin cargarlo en Biblioteca/Chat. No se repitió la suite general ni se analizaron vídeos.
- Recorrido real: proyecto «Ideas de IA» conserva el reel; asociada también la muestra de audio existente. Relación propuesta «Contrasta modalidades» con nota manual sobre ficha visual sin pista de audio frente a transcripción de voz. Corrección «Contrasta audio y visión», aceptada: historial visible de v1 propuesta y v2 aceptada, sin borrar evidencia ni fuentes. No representa una relación temática inferida.
- Reinicio de ReelMind: respuesta completa del grafo idéntica antes/después, dos nodos, una relación y dos revisiones. Esquema `0008_graph`, motor detenido, ninguna consulta activa. No se reinició PostgreSQL ni Windows ni se ensayó restauración integral (Fase 7).

[Captura del grafo](phase6-graph.png).

Límites: relaciones manuales con motivo declarado, sin validación automática del contenido; sin entidades extraídas ni chat por proyecto. Posiciones del dibujo no persistentes. Selector inicial de 100 fuentes. No se ha evaluado rendimiento con grafos grandes; móvil/Supabase fuera de alcance.
