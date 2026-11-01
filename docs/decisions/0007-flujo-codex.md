# ADR 0007: flujo de Codex proporcionado a la tarea

Fecha: 2026-10-31. Estado: adoptado.

## Motivo y decisión

El usuario pide reducir procesos innecesarios mediante instrucciones del proyecto, sin benchmarks, instalaciones ni trabajo de producto. Se ajusta [AGENTS](../../AGENTS.md): lectura inicial acotada, ejecución directa para cambios pequeños, plan corto en el [seguimiento existente](../roadmap.md) para varios pasos, depuración guiada por evidencia, un agente por defecto y comprobaciones pertinentes. Se conserva la condición de autorización explícita para delegar y el seguimiento establecido por [ADR 0003](0003-plan-vivo.md).

Se distingue la autorización previa de Fase 2 del alcance de cada encargo. Este trabajo documental no ejecuta su revisión visual ni altera evidencias anteriores, dependencias, datos, servicios o modelos locales.

## Inventario acotado disponible

- Proyecto: `AGENTS.md` como instrucciones; no se encontraron otras instrucciones AGENTS ni archivos SKILL en las carpetas de proyecto examinadas, excluyendo dependencias, Git, temporales y datos locales. No hay carpetas de configuración `.agents`, `.codex`, `.claude` o `skills`, ni archivo `.mcp.json` en la raíz. No se detectaron instrucciones aplicables de Superpowers, Impeccable o reglas React de Vercel; no se inspeccionaron configuraciones globales.
- Herramientas locales disponibles: PowerShell, Git y `rg`, usados para la revisión documental. Los scripts existentes son `scripts/backend.ps1`, `scripts/check-environment.ps1`, `scripts/common.ps1`, `scripts/open-database.ps1`, `scripts/prepare-audio.ps1`, `scripts/setup.ps1`, `scripts/start.ps1` y `scripts/stop.ps1`; su existencia no supone una nueva ejecución o verificación funcional.
- Capacidades suministradas a esta sesión, sin instalarse en el proyecto: OpenAI Docs para documentación oficial, búsqueda web y Computer Use para navegador/escritorio. Se usó OpenAI Docs; Computer Use no se ejecutó. Su disponibilidad no resuelve el bloqueo visual registrado de Fase 2.

## Modelo y razonamiento

Política: usar el nivel suficiente y reservar el máximo para problemas que lo justifiquen, sin avisos rutinarios si la configuración es adecuada. No se identificó una capacidad disponible que informe de forma verificable el modelo y esfuerzo efectivos de este chat; no se atribuyen valores ni cambios por escribir instrucciones.

Selección manual propuesta para tareas documentales pequeñas: conservar un modelo adecuado que ofrezca la app y elegir esfuerzo bajo si está disponible; medio para tareas de varios pasos que lo necesiten. Reservar niveles superiores para problemas concretos que lo justifiquen. Es una recomendación, no una configuración aplicada, compatibilidad garantizada o promesa de ahorro. No cambia el modelo local de transcripción ni configuraciones globales.

## Candidatos no incorporados al proyecto

- **Superpowers:** considerar sus pautas de planificación y depuración solo si aportan algo a un problema futuro; evitar duplicar el plan y las reglas ya presentes.
- **Impeccable:** considerar para una tarea futura de diseño y revisión visual, sin convertirlo en requisito para editar código o documentación.
- **Reglas React de Vercel:** considerar únicamente las pertinentes a React/Vite (componentes, renderizado y carga); excluir reglas de Next.js, hosting o despliegue.
- **Documentación/navegador:** las capacidades de sesión ya existen; no se propone otra instalación. Reconsiderar solo ante una carencia concreta demostrada.

Ningún candidato fue instalado ni probado; la ausencia constatada se limita al proyecto y al catálogo de skills expuesto a esta sesión, no a todo el equipo.

## Impacto

Solo instrucciones y seguimiento dentro de ReelMind. [Estado](../status.md) y [bitácora](../bitacora.md) conservan las evidencias de producto. Fase 2 sigue pendiente de revisión visual; no se inicia otra fase ni se modifica el PDF original. El cierre de este encargo requiere coherencia documental, rutas existentes y revisión de diferencias/espacios distinguiendo los cambios previos.
