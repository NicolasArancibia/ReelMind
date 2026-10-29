# ADR 0003: plan vivo y seguimiento del trabajo

Fecha: 2026-10-29. Estado: adoptado.

## Motivo

El usuario solicita un documento distinto del PDF para mantener las fases y los cambios ordenados cada vez que se trabaja. El PDF fue la base y se conserva como referencia histórica.

## Decisión

- Ampliar `docs/roadmap.md` como plan vigente editable, sin crear otro listado de fases que pueda divergir.
- Mantener `docs/status.md` como resumen del estado real y sus evidencias.
- Añadir `docs/bitacora.md` como registro cronológico de cada trabajo, incluso parcial o bloqueado.
- Registrar cambios de alcance o arquitectura en `docs/decisions/` y reflejarlos en el plan. Las instrucciones actuales del usuario prevalecen.
- Incluir este procedimiento en AGENTS y enlaces accesibles desde README.

## Impacto

No cambia la arquitectura ni se inicia Fase 1. Las fases futuras son planificación revisable, no funciones implementadas. Las tareas de Fase 1 detallan el alcance existente; sus decisiones de implementación se resolverán cuando corresponda. El PDF original queda intacto.
