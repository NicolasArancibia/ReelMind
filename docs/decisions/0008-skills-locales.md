# ADR 0008: skills locales y preflight breve

Fecha: 2026-10-31. Estado: adoptado.

## Autorización y alcance

El usuario solicita guardar las skills dentro de ReelMind y crear una orientación rápida sobre modelo, esfuerzo y skills antes de tareas grandes. Esta autorización posterior sustituye la prohibición de instalar skills de aquel encargo documental del [ADR 0007](0007-flujo-codex.md); su inventario anterior conserva su fecha. No autoriza instalación global, hooks, nuevos servicios ni trabajo de producto.

## Selección y procedencia

Destino exclusivo: `.agents/skills/`. Descargadas con el instalador disponible y revisiones fijadas:

| Entradas locales | Fuente original | Revisión |
| --- | --- | --- |
| systematic-debugging, writing-plans | [obra/superpowers](https://github.com/obra/superpowers) — skills/systematic-debugging y skills/writing-plans | `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b` |
| impeccable | [pbakaus/impeccable](https://github.com/pbakaus/impeccable) — .agents/skills/impeccable | `4f956490f0056ae1ff5ea80372cf56e83c001d3c` |
| vercel-react-best-practices | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) — skills/react-best-practices | `1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62` |

Los SKILL originales se conservan como `UPSTREAM.md`; los nuevos `SKILL.md` son adaptaciones locales breves, no copias oficiales intactas. Material auxiliar original disponible bajo demanda, sin ejecución de scripts. Superpowers e Impeccable conservan LICENSE; Vercel declara MIT en el frontmatter original. No se instala el framework completo de Superpowers, sus hooks o sus flujos de delegación.

Las adaptaciones eliminan planes paralelos, dependencias obligatorias de otras skills, subagentes, TDD universal y setup auxiliar. Impeccable conserva el estilo actual y usa referencias selectivas, sin launchers/hooks/doctor ni PRODUCT.md o DESIGN.md. React se limita a React/Vite y excluye Next.js, SSR y servicios Vercel. Ninguna skill externa se aplicó para modificar la aplicación en este encargo.

## Preflight y selección de modelo

`reelmind-preflight` es creación local. Uso: `$reelmind-preflight <tarea>`; alternativa en lenguaje natural: «Preflight: <tarea>». Responde preferentemente en 60–100 palabras con dificultad, modelo, razonamiento, cero a dos skills y una comprobación. Usa el mensaje y contexto existente; no hace búsquedas web, benchmarks, pruebas, subagentes o inventarios. Solo pregunta o consulta hasta dos fragmentos si falta un dato decisivo. El límite de respuesta es una orientación de brevedad, no un límite garantizado de tokens internos o coste.

Solo nombra modelos explícitamente conocidos en la sesión o proporcionados por el usuario; sin catálogo recomienda una categoría. No cambia selecciones de la app ni el modelo local de transcripción. Recomienda y espera «continúa», salvo instrucción explícita para evaluar y ejecutar sin pausa. No repite el preflight en una tarea ya acordada ni escribe seguimiento por una consulta sin cambios.

AGENTS añade esta orientación antes de nuevas tareas grandes y exceptúa las consultas orientativas de la lectura inicial y cierre documental. La skill conserva descubrimiento automático normal; no se convierte en un preámbulo para toda tarea pequeña.

## Cierre

Validar formato de las cinco entradas con el validador disponible, referencias locales y coherencia, más diff/espacios. La validación estructural no demuestra selección automática o reconocimiento por el selector de esta sesión: comprobar ese comportamiento al usarla en un turno posterior. Las skills quedan persistentes en este proyecto, sin instalación global. Fase 2 conserva su revisión visual pendiente.
