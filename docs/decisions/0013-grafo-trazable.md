# 0013 — Grafo inicial de fuentes y revisiones de relaciones

2026-11-01. Implementado en la continuación autorizada de Fase 6, reutilizando proyectos locales y preservando la biblioteca.

Los nodos iniciales son fuentes existentes identificadas por UUID. No se duplican en knowledge_nodes ni se fusionan entidades por nombre. Las relaciones dirigidas son manuales entre dos fuentes distintas del mismo proyecto. Requieren etiqueta, nota de evidencia/motivo y estado propuesta/aceptada/rechazada. La nota es procedencia humana declarada; no una afirmación verificada automáticamente ni cita de análisis fabricada. Se puede abrir la ficha de ambas fuentes para contrastarla.

`0008_graph` añade relation_revisions: PK(id, version), proyecto y extremos con FK RESTRICT, etiqueta, evidencia, estado y fecha. Correcciones insertan nuevas filas; ninguna ruta sobrescribe una revisión. El bloqueo del proyecto serializa cambios y expected_version rechaza una corrección obsoleta con 409. Sin autorrelaciones. El grafo muestra última revisión; rechazos conservados en lista/historial. Fuentes retiradas del proyecto o en papelera ocultan sus relaciones, conservando historial para restaurarlas.

Cytoscape 3.34.4 fijado en el frontend, importado de forma diferida al abrir un proyecto. Sin servicio ni inferencia adicionales. Grafo con lista equivalente para consultar/corregir sin depender del lienzo. Historial muestra fechas America/Santiago. No se persisten posiciones de nodos; reconstruir el dibujo no cambia los datos.

Alcance inicial: asociaciones, grafo de fuentes, notas manuales y correcciones trazables. Entidades extraídas, vínculos automáticos, citas estructuradas a fragmentos y chat restringido por proyecto quedan como ampliaciones posteriores. Selector inicial limitado a 100 fuentes; ampliación paginada pendiente antes de bibliotecas mayores. No habilita móvil/Supabase. [Verificación](../verification/phase6.md).
