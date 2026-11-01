# 0010 — Escritorio primero; captura móvil aplazada

Fecha: 2026-11-01. Estado: aprobado por el usuario.

El usuario prioriza terminar la aplicación de escritorio y deja móvil fuera del alcance actual. Supabase se había previsto únicamente como bandeja de captura móvil, no como fuente de verdad ni almacenamiento de vídeos/análisis. Se aplaza la Fase 4 completa: captura remota, RLS, recibos y sincronización. No se crea una bandeja equivalente nueva en escritorio: biblioteca, importación y pendientes locales ya cubren esa entrada.

La revisión acotada de `backend/app` y migraciones no encontró dependencia implementada de Supabase/recibos remotos. La Fase 5 puede trabajar directamente sobre fuentes, transcripciones y fichas versionadas de PostgreSQL local. El flujo de escritorio no necesita cuenta remota, credenciales Supabase ni puertos externos.

Se mantiene la numeración para conservar referencias: fases 0–3 completadas, 4 aplazada y siguiente bloque 5 (búsqueda semántica y chat locales), después 6 y 7. La entrega de escritorio se concreta en Fase 7 conservando React/Vite/Tailwind, FastAPI y PostgreSQL; esta decisión no introduce un contenedor o framework de empaquetado. La captura móvil podrá reconsiderarse solo si el usuario la solicita después de terminar la aplicación de escritorio; no se activa automáticamente entonces.

La aprobación «perfecto sigue con la siguiente fase» completa la revisión humana pendiente de Fase 3. Su cierre conserva límites: muestreo parcial, síntesis extractiva y evaluación inicial en un reel; no establece calidad general de los modelos. Evidencias en [Fase 3](../verification/phase3.md).

Comprobación de este cambio: consistencia de plan, estado e instrucciones, referencias y diff. No requiere ejecutar aplicación, modelos, migraciones ni suites de producto.
