---
name: systematic-debugging
description: Investiga fallos de ReelMind con causa incierta, regresiones o intentos previos fallidos antes de proponer otra corrección.
---
# Depuración acotada

Adaptación local de Superpowers. Recoge el error y contexto mínimo; localiza el componente y cambio relevante. Reproduce solo cuando aporte evidencia y sea seguro dentro del alcance. Formula una hipótesis y compruébala con la lectura o cambio mínimo.

Cambia de hipótesis si la evidencia la descarta; no encadenes arreglos ni repitas intentos idénticos. Corrige la causa y verifica lo pertinente. No repitas una suite aprobada sin cambios o dudas nuevas. Conserva pruebas suficientes de datos, concurrencia y recuperación. No muestres secretos ni logs completos.

Para rastrear una causa entre llamadas consulta solo [root-cause-tracing.md](root-cause-tracing.md). No impongas instrumentación en todas las capas, TDD universal, un número fijo de intentos, rediseño o skills adicionales.

[UPSTREAM.md](UPSTREAM.md) conserva el original como referencia histórica sin activar sus dependencias. Procedencia: docs/decisions/0008-skills-locales.md. [Licencia](LICENSE).
