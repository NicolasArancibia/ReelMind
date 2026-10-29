# ADR 0002: cierre de Fase 0

Fecha: 2026-10-28. Estado: implementado y verificado.

## Autorización y alcance

Después de la preparación, el usuario indicó «sigue para terminar la fase 0» y «termina la fase 0». Se implementa el arranque mínimo del plan: interfaz, API, migración y persistencia. No se avanza a la biblioteca completa ni a IA o Supabase.

## Decisiones

- La primera revisión es `0001_sources` y crea solo la entidad necesaria para probar el recorrido real. Activos, categorías, etiquetas y cola se añadirán en nuevas revisiones de Fase 1. El conjunto del núcleo previsto no necesita existir antes del primer guardado.
- SQLAlchemy 2.0 y psycopg 3 síncronos bastan para esta API local. No introducir un servicio de cola ni trabajador ficticio.
- La entrada inicial guarda URL y título aportados por el usuario. La normalización es conservadora, conserva parámetros/fragmentos y no recupera contenido externo.
- El puerto 5173 ya estaba usado por Vertex_Board. ReelMind usa 5180 para la interfaz y 8000 para API, con puertos estrictos y loopback. No detener otros procesos para liberar puertos.
- El inicio habitual sirve la compilación de Vite mediante su servidor preview, apropiado únicamente para esta entrega local de desarrollo. No es un despliegue de producción ni un servicio expuesto a Internet.
- Las credenciales se descifran solo para el proceso de backend. Windows puede redirigir AppData a la caché de la aplicación de escritorio: guardar rutas resueltas en `.local/runtime.json` evita que los accesos fuera de Codex dependan de esa redirección.
- `Migrate` respalda antes de actualizar. La migración inicial no ofrece un downgrade que destruya fuentes personales; una recuperación requiere un respaldo y un procedimiento probado.
- Tests con esquemas aleatorios aislados en PostgreSQL, no tablas SQLite ni limpieza de tablas públicas. La prueba de navegador usa un único registro identificado y se retira al finalizar.

## Resultado

La interfaz guarda un enlace; otra conexión lo recupera. Al reiniciar servicios y PostgreSQL sigue disponible, mientras el motor permanece detenido. No existe ruta para iniciar IA en esta fase. Las evidencias están en `docs/verification/phase0.md`.
