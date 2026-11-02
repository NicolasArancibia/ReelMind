# ReelMind

Biblioteca personal de vídeos, local en Windows: reunir reels, analizar su contenido, guardar ideas, organizarlas, conectarlas y conversar con citas. El [plan de producto 1.0](docs/roadmap.md#plan-de-cierre-del-producto-10) está implementado en su alcance funcional de escritorio; queda la aceptación final con tu colección. [Estado y comprobaciones](docs/status.md). Móvil y Supabase están aplazados.

**Chat local con fuentes.** Abre **Chat**, actualiza manualmente el índice en **Biblioteca disponible** después de analizar vídeos o editar apuntes, y escribe tu mensaje. Enter envía y Mayús+Enter añade línea. Puedes consultar toda la biblioteca, un proyecto o una fuente. **Explicar con citas** responde en español con el modelo local; **Solo citas originales** conserva los pasajes literales. La explicación vuelve a citas si no pasa la validación. Revisa siempre el original: las respuestas pueden contener errores. [Comprobaciones actuales y límites](docs/verification/product1.md).

Para pedir un resumen general, selecciona una **Fuente** en Chat. Se usa una muestra temporal acotada y se indica su cobertura; el texto puede apoyarse solo en parte de ella. La conversación recupera su última fuente y modo al recargar. La calidad de resumen/comparación continúa en aceptación con una colección más amplia.

## Recorrido cotidiano

- **Biblioteca:** incorpora varios archivos/enlaces desde **Incorporar varios reels**. Cada elemento muestra su resultado; guardados/duplicados salen del lote y los pendientes pueden corregirse y reintentarse. Guardar no descarga enlaces ni inicia análisis. Adjunta una copia local cuando solo tengas un enlace.
- **Organizar:** cambia título, resumen revisado, favorito, categorías y etiquetas. Una propuesta desde observaciones existentes requiere revisión. Selecciona varias fuentes para clasificar, asociar a un proyecto o preparar pendientes en una sola operación; el motor sigue detenido.
- **Ficha y audio:** reproduce la copia local y guarda apuntes, rangos y favoritos. **Guardar destacado** desde Chat conserva la cita exacta junto a tu comentario. Editar añade una versión; archivar/restaurar conserva el historial. Los tiempos abren el momento original cuando hay una única copia reproducible.
- **Mis ideas:** busca en apuntes y citas, filtra por proyecto/etiqueta/favorito/archivo y vuelve a la ficha. Exporta Markdown o JSON desde la ficha.
- **Chat:** busca contenido o conversa con contexto acotado. Renombra, busca, archiva/restaura y exporta conversaciones; copia respuestas con citas. Una conversación conserva su proyecto y se recupera al recargar. Para cambiar de proyecto, abre un chat nuevo.
- **Proyectos:** agrupa fuentes, renombra/archiva/restaura proyectos y conecta fuentes o revisiones concretas de apuntes. Las relaciones tienen motivo/evidencia, estado e historial. Puedes recorrer el grafo o su lista equivalente.
- **Ajustes:** consulta actividad, almacenamiento y preparación local; detén la tarea actual, renombra etiquetas/categorías o exporta una copia legible de la biblioteca.
- **Mantenimiento ReelMind.cmd:** crea una copia completa, verifica una restauración aislada, migra/activa una copia y vuelve a la configuración anterior, sin editar comandos. Cada cambio conserva el original. Las copias no incluyen modelos ni se cifran automáticamente; elige otro disco para protegerte de un fallo físico. No hay limpieza automática: los temporales se revisan y confirman por selección.

## Abrir y cerrar

1. Haz doble clic en **[Iniciar ReelMind.cmd](Iniciar%20ReelMind.cmd)**. Se inicia la aplicación y se abre el navegador.
2. Abre [ReelMind](http://127.0.0.1:5180) si el navegador no se abrió automáticamente.
3. Pega un enlace, añade un nombre opcional y pulsa **Guardar enlace**. Queda guardado en PostgreSQL; no se descarga ni se analiza el vídeo.
4. Para cerrar la aplicación, usa **[Detener ReelMind.cmd](Detener%20ReelMind.cmd)**. Cerrar solo la pestaña no detiene los procesos. PostgreSQL continúa como servicio local.

Los registros temporales de la verificación inicial se retiraron; la revisión visual posterior conserva una muestra pública `female-0.mp4` en la biblioteca. El motor arranca siempre detenido. Controles y transcripciones comprobados en escritorio y tamaño móvil; [evidencias y límites de la verificación](docs/verification/phase2.md).

## Gestionar tu biblioteca

- Pulsa el **lápiz** de un enlace para editar su título. Puedes dejarlo vacío; la URL original se conserva.
- Pulsa la **papelera** y confirma para retirarlo de la biblioteca. Sus datos se conservan.
- Abre **Papelera** y pulsa **Restaurar** para recuperarlo. Si pegas un enlace ya presente en papelera, se ofrece restaurar el original sin duplicarlo.
- Usa **Anterior/Siguiente** para recorrer páginas de 20 enlaces. Los contadores separan biblioteca y papelera.
- Si otra ventana cambió el mismo enlace, cierra el cuadro y pulsa **Actualizar biblioteca** antes de intentarlo nuevamente.

## Qué funciona en esta entrega

- Conexión real con PostgreSQL, comprobación de la revisión de esquema y estado del motor.
- Guardado de enlaces HTTP/HTTPS, título opcional, plataforma orientativa y fecha.
- Consulta paginada de toda la biblioteca y papelera; contadores de ambas. No se descarga contenido externo.
- Edición de títulos, eliminación recuperable y restauración con protección contra cambios simultáneos.
- Detección de URL normalizada repetida; validación de entradas y mensajes de conexión/errores.
- Inicio y detención de los procesos propios; no se altera otra aplicación que use otros puertos.
- Persistencia comprobada después de reiniciar la API y PostgreSQL.

- **Importar vídeo:** selecciona un archivo MP4, MOV, M4V, WebM, MKV o AVI y pulsa Importar vídeo. Se guarda una copia local; tu original permanece intacto. Hasta 2 GiB por defecto. El mismo contenido no crea otra fuente local.
- **Archivos:** adjunta un vídeo a un enlace existente o abre sus copias guardadas. Varias fuentes pueden compartir una copia sin perder su procedencia. La reproducción depende del navegador; no hay conversión de formatos.
- **Organizar:** escribe categorías y etiquetas separadas por comas. Puedes reutilizar nombres o vaciar un campo para retirar asociaciones. Hasta 10 categorías y 20 etiquetas de 60 caracteres por fuente.
- **Buscar y filtrar:** busca por título, enlace, nombre de archivo, categoría o etiqueta; combina plataforma, tipo, categoría y etiqueta. Limpiar filtros vuelve a mostrar toda la vista.
- **Pendientes:** consulta el orden de transcripción. Quitar de cola conserva la fuente; Encolar la añade al final. Enviar a papelera oculta su pendiente y restaurar recupera su estado anterior.

La papelera conserva los archivos y no tiene purga. Si falta una copia local, vuelve a importar el mismo archivo para recuperarla. Las etiquetas/categorías son planas y sus nombres sin uso se conservan para reutilizarlos.

## Transcribir audio

1. Importa un vídeo o adjunta una copia local a su enlace. Un enlace solo no proporciona audio; no hay descarga automática.
2. Añade la fuente a **Pendientes** y pulsa **Iniciar**. Se toma únicamente la cola existente en ese momento. Importar o restaurar después espera otro inicio.
3. **Pausar** termina el vídeo actual y espera; **Reanudar** requiere pulsación. **Detener** cancela el actual sin guardar segmentos incompletos; para reintentarlo pulsa Encolar e Iniciar.
4. Abre **Ficha y audio** para consultar versiones, tiempos, idioma y modelo. «Sin voz detectada» no garantiza ausencia de habla. Los resultados automáticos pueden tener errores.

Se conserva el historial al reprocesar. Con varias copias adjuntas, importa el archivo elegido como fuente local independiente. Se procesa la primera pista de audio. [Pruebas y cierre visual de Fase 2](docs/verification/phase2.md).

**Incluir visión y síntesis** está seleccionada de forma predeterminada y añade una ficha con evidencias temporales y referencias; desmárcala para procesar solo audio. El motor siempre espera a **Iniciar**. Requiere preparar los modelos explícitamente con `powershell -NoProfile -File .\scripts\prepare-av.ps1`; usa Ollama ya instalado y almacenamiento propio fuera de OneDrive. Mientras no termine la preparación, Iniciar queda deshabilitado en ese modo. Supabase está aplazado; Chat local ya está disponible en su vista propia.

La ficha revisa hasta ocho fotogramas y usa hasta 12 segmentos de audio para sintetizar: puede omitir escenas, acciones o texto. Contrasta sus afirmaciones con las evidencias y el vídeo original. La revisión inicial fue aceptada; los modelos siguen siendo provisionales y no hay evaluación general de calidad. [Estado actual](docs/status.md).

## Arquitectura conservada

React + Vite + Tailwind, Python + FastAPI, SQLAlchemy/Alembic y PostgreSQL local. Biblioteca y análisis locales; Supabase futuro únicamente para pendientes. Análisis audiovisual completo como objetivo, manual y secuencial. Diseño negro con acentos verde esmeralda, sin APIs de pago obligatorias.

## Desarrollo y reproducción

Herramientas: Node 24.13.0, Python 3.13.15 y PostgreSQL 18.6. Las dependencias exactas están en `frontend/package-lock.json` y `backend/requirements.lock`.

Desde una terminal normal en esta carpeta, después de completar [la preparación de PostgreSQL](docs/setup-windows.md):

```powershell
powershell -NoProfile -File .\scripts\setup.ps1
powershell -NoProfile -File .\scripts\backend.ps1 -Action Migrate
powershell -NoProfile -File .\scripts\start.ps1 -OpenBrowser
```

`setup.ps1` instala las dependencias fijadas y compila la interfaz. `Migrate` crea un respaldo local antes de aplicar Alembic. La revisión actual es `0010_idea_connections`; las migraciones previas aplicadas permanecen intactas. `start.ps1` sirve la compilación local en 5180 y la API en 8000. El motor arranca detenido; solo Iniciar lanza trabajo pesado.

Para preparar el audio por primera vez, con la aplicación detenida y conexión a Internet:

```powershell
powershell -NoProfile -File .\scripts\prepare-audio.ps1
```

Descarga small a la raíz local de datos fuera de OneDrive y registra revisión/hash. Repetir conserva/verifica el modelo. Después la transcripción funciona offline: CPU int8, cuatro hilos. No descarga modelos al abrir ni al pulsar Iniciar. FFmpeg viene con las dependencias fijadas. `REELMIND_AUDIO_TIMEOUT_SECONDS` limita cada vídeo a 7200 s de ejecución por defecto; no es un límite de duración del archivo.

```powershell
# Pruebas aisladas en PostgreSQL y consistencia del esquema
powershell -NoProfile -File .\scripts\backend.ps1 -Action Test
powershell -NoProfile -File .\scripts\backend.ps1 -Action Check
# Cerrar los procesos iniciados por ReelMind
powershell -NoProfile -File .\scripts\stop.ps1
```

Para editar con recarga de frontend: detener el inicio normal, ejecutar `scripts/backend.ps1 -Action Run` en una terminal y `npm.cmd run dev` dentro de `frontend` en otra. Terminar ambas con Ctrl+C. Después de editar, `npm.cmd run build` actualiza la versión que abre el acceso de inicio. La API no usa recarga automática en esta fase.

La documentación de la API está en [localhost:8000/docs](http://127.0.0.1:8000/docs) mientras ReelMind está abierto.

## Configuración y registros

Los scripts inyectan la credencial PostgreSQL cifrada del usuario al proceso Python; no al navegador. `.env.example` documenta variables, pero no se carga automáticamente. `.local/runtime.json` contiene solo rutas locales para resolver instalaciones redirigidas por Windows; no contraseñas. `.local/api-error.log` y `.local/frontend-error.log` permiten revisar fallos de inicio. Todos estos archivos locales están excluidos de Git. Los scripts resuelven la raíz de medios con `REELMIND_DATA_ROOT`, el campo opcional `DataRoot` del manifiesto o el directorio `data` del runtime. Se guarda fuera de OneDrive; [configuración y recuperación](docs/operations.md).

Los servicios escuchan solo en `127.0.0.1`; PostgreSQL en loopback. Los datos vivos y secretos están fuera de OneDrive. No hay repositorio remoto ni publicación.

## Documentación

### Skills locales para Codex

Guardadas en `.agents/skills/`, solo para este proyecto. Para orientar una tarea antes de ejecutarla, escribe **`$reelmind-preflight quiero…`** o **«Preflight: quiero…»**. Recomienda modelo, razonamiento, skills y comprobación; después ajusta la selección de la app si procede y responde «continúa». No cambia el modelo automáticamente ni garantiza un coste exacto.

También disponibles: `writing-plans`, `systematic-debugging`, `impeccable` y `vercel-react-best-practices`, con entradas adaptadas al proyecto. Las referencias se leen solo cuando hacen falta. [Procedencia, límites y verificación](docs/decisions/0008-skills-locales.md). Si el selector no las muestra todavía, inicia otro chat en ReelMind; la alternativa «Preflight: …» queda indicada en AGENTS.

Consultar el **[plan de fases vigente](docs/roadmap.md)** para seguir el proyecto. Se actualiza con el trabajo y las decisiones; el PDF conserva la base original. La **[bitácora](docs/bitacora.md)** registra cada trabajo y [estado](docs/status.md) resume qué funciona y qué sigue.

| Documento | Contenido |
| --- | --- |
| [Plan original v1.3](docs/referencias/ReelMind_Plan_Maestro_v1.3.pdf) | Referencia original sin modificar |
| [AGENTS](AGENTS.md) | Reglas para asistentes y continuidad |
| [Arquitectura](docs/architecture.md) | Componentes, límites y contratos |
| [Base de datos](docs/database.md) | Esquema aplicado y diseño futuro |
| [Plan de fases vigente](docs/roadmap.md) | Documento vivo: fases, tareas, estados y condiciones de cierre |
| [Bitácora de trabajo](docs/bitacora.md) | Historial de cambios, pruebas, pendientes y siguientes pasos |
| [Plan vivo y seguimiento](docs/decisions/0003-plan-vivo.md) | Cómo mantener el plan y el historial |
| [Decisión inicial](docs/decisions/0001-base-del-proyecto.md) | Base de la preparación |
| [Arranque mínimo](docs/decisions/0002-arranque-minimo.md) | Alcance y decisiones de Fase 0 |
| [Modelos](docs/models.md) | Candidatos y evaluación futura |
| [Seguridad](docs/security.md) | Secretos y límites |
| [Operación](docs/operations.md) | Inicio, respaldos y recuperación |
| [Entorno Windows](docs/setup-windows.md) | Herramientas y preparación |
| [Verificación Fase 0](docs/verification/phase0.md) | Evidencia y limitaciones de las pruebas |
| [Gestión de enlaces, decisión](docs/decisions/0004-gestion-de-enlaces.md) | Papelera, paginación y concurrencia |
| [Verificación Fase 1.1](docs/verification/phase1-1.md) | 34 pruebas, recorrido de interfaz y persistencia |
| [Biblioteca completa, decisión](docs/decisions/0005-cierre-biblioteca.md) | Copias, clasificación, cola y límites de Fase 1 |
| [Verificación de Fase 1](docs/verification/phase1.md) | 57 pruebas, interfaz, fallos parciales y reinicio |
| [Audio y motor manual](docs/decisions/0006-audio-motor-manual.md) | Semántica, procedencia y selección inicial de modelo |
| [Verificación Fase 2](docs/verification/phase2.md) | 69 pruebas, audio real, recuperación y cierre visual |
| [Estado](docs/status.md) | Resultado actual y siguiente paso |

Antes de retomar otra sesión, leer AGENTS, README, plan de fases y estado. Al cerrar cada trabajo, actualizar el seguimiento según AGENTS. No confundir los módulos previstos en el plan con funciones ya implementadas.

**Proyectos:** crea un proyecto y asocia fuentes desde su vista propia. Quitar una asociación conserva vídeo y análisis. Grafo manual disponible: relaciona dos fuentes con una nota de evidencia, consulta sus fichas y corrige conservando versiones. Las notas son manuales y no están verificadas automáticamente. [Verificación y límites](docs/verification/phase6.md).

## Respaldo y recuperación

Detén ReelMind y ejecuta `scripts/library-backup.ps1 -Action Backup` desde PowerShell. Guarda base y vídeos juntos, con manifiesto y hashes, fuera de OneDrive. Para comprobar una copia: `scripts/library-backup.ps1 -Action RestoreVerify -Bundle "RUTA_DE_LA_COPIA"`; crea una base y carpeta nuevas, sin sustituir tu biblioteca. Modelos y credenciales se preparan aparte. [Procedimiento vigente](docs/operations.md), [verificación de Fase 7](docs/verification/phase7.md).

Las dependencias quedan en el runtime externo; para reinstalarlas usa `scripts/setup.ps1`. La entrega actual utiliza los lanzadores Windows y navegador local; no incluye instalador EXE. Dependencias/build y recuperación aislada comprobados con los prerrequisitos ya instalados.
