---
name: vercel-react-best-practices
description: Reglas pertinentes de Vercel para componentes y rendimiento React/Vite de ReelMind; excluye Next.js, SSR, hosting y backend Python.
---
# React/Vite en ReelMind

Adaptación local de las reglas React de Vercel. Identifica el problema concreto y consulta solo la regla pertinente en rules/. No cargues todo el documento compilado AGENTS.md; es material de referencia de esta skill, no instrucciones de la aplicación.

Prioriza estado derivado sin efectos innecesarios, dependencias estables, actualizaciones funcionales, evitar componentes definidos dentro de render y solicitudes independientes en paralelo. Usa mecanismos de carga diferida compatibles con React/Vite ya disponibles.

Excluye Next.js, Server Components, SSR, server actions y Vercel hosting. No introduzcas next/dynamic, SWR u otras dependencias por seguir un ejemplo. No refactorices toda la aplicación ni añadas memoización sin beneficio concreto. Comprueba la versión React antes de adoptar APIs nuevas.

[UPSTREAM.md](UPSTREAM.md) conserva el índice original, sin imponer su flujo completo. Procedencia: docs/decisions/0008-skills-locales.md. [Declaración MIT original](UPSTREAM.md).
