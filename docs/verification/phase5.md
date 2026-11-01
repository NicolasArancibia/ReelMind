# Fase 5 — Búsqueda local y consultas con citas

Fecha: 2026-11-01, America/Santiago. Implementación y cierre técnico comprobados; pendiente revisión de uso del usuario. Móvil y Supabase aplazados. [ADR 0011](../decisions/0011-busqueda-chat-local.md).

## Preparación y datos

- pgvector 0.8.7 compilado desde tag oficial con Visual Studio Build Tools ya instalado. La copia a PostgreSQL 18 necesitó PowerShell administrativo del usuario. `CREATE EXTENSION` confirmado en ReelMind; no habilitado en otras bases.
- BGE-M3 `bge-m3:567m`, 1024 dimensiones comprobadas por inferencia. Reutilizado `qwen3:4b-instruct-2507-q4_K_M`; sin comparativas ni cambio del audio. Digests/configuración en `models/search.json`, fuera de OneDrive/Git.
- `0006_retrieval` aplicada después de `before-migration-20261101-042305-133.dump`, fuera del repositorio. `alembic check`: sin operaciones nuevas. Datos de las dos fuentes existentes conservados.

## Comprobaciones dirigidas

Seis pruebas de `backend/tests/test_retrieval.py`, aprobadas en 3,53 s con Python 3.13 y PostgreSQL en esquemas aislados. Cubren:

- Fragmentos como subcadenas exactas, offsets y hashes; validación de cantidad/dimensión/valores finitos y normalización de vectores.
- Indexación incremental sin duplicados; recuperación por perfil y coseno; rechazo de citas inventadas y selección vacía válida.
- FK de origen a su misma fuente y rollback ante fallo; exclusión de versiones antiguas y fuentes en papelera.
- Historial con cita versionada exacta y marcas de versión anterior; lectura posterior desde base.
- Cancelación sin confirmar índice parcial; exclusión con motor y otra consulta; recuperación de tareas interrumpidas sin reintento.
- Exclusión de fichas experimentales de pipeline v1, observaciones inciertas y OCR marcado no fiable.

Compilación TypeScript/Vite aprobada tras el ajuste final del refresco del panel. No se repitió la suite general ni se ejecutó análisis audiovisual nuevo.

## Recorrido real en escritorio

1. Abrir app actualizada: cero de ocho fragmentos indexados; motor detenido. Abrir no inicia proveedor ni inferencia.
2. Pulsar **Actualizar índice**: ocho fragmentos disponibles, siete observaciones claras del reel y un segmento de la muestra pública. Sin reprocesar vídeos.
3. Preguntar «¿Qué tarea muestra el vídeo con Figma y Notion?». Recupera y selecciona el pasaje inglés sobre redactar texto de lanzamiento y resumir resultados de campaña. Cita del reel real, ficha v2, segundo 37. **Ver ficha de la fuente** abre su ficha correcta; texto contrastado con la evidencia v5.
4. Nueva conversación: «¿Cuánta harina lleva la receta de pan del vídeo?». Respuesta visible: «No hay evidencia suficiente para responder con citas». No inventa receta.
5. Reinicio final: evidencias/transcripciones de ambas fuentes idénticas por SHA-256; dos conversaciones y sus citas idénticas; ocho fragmentos, cero pendientes de índice. Motor detenido, ninguna tarea de recuperación activa y puerto del proveedor 11435 sin escucha. Informe externo: `verification-phase5/persistence.json` bajo la raíz de datos.

[Captura de escritorio después del reinicio](phase5-desktop.png): cita conservada y botón para abrir la ficha de su fuente.

## Límites

Verificación inicial sobre dos fuentes y dos preguntas reales; no demuestra relevancia general. Coseno mínimo 0,5 provisional, hasta seis candidatos y cuatro citas. Respuesta extractiva: conserva el idioma de la evidencia y sus posibles errores; no verifica afirmaciones del vídeo ni traduce. Contexto acotado a la pregunta anterior, sin memoria general ni herramientas externas. Índice inicial atómico hasta 2000 fragmentos de 1200 caracteres; bibliotecas mayores requieren ampliar a lotes antes de procesarlas. Sin HNSW, pruebas móviles o nuevos modelos.
