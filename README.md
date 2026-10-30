# ReelMind

Biblioteca personal de vídeos, local en Windows. **Fases 0 y 1 completadas y verificadas:** enlaces y archivos de vídeo, categorías/etiquetas, búsqueda/filtros, papelera y cola persistente sin IA. [Estado y comprobaciones](docs/status.md).

## Abrir y cerrar

1. Haz doble clic en **[Iniciar ReelMind.cmd](Iniciar%20ReelMind.cmd)**. Se inicia la aplicación y se abre el navegador.
2. Abre [ReelMind](http://127.0.0.1:5180) si el navegador no se abrió automáticamente.
3. Pega un enlace, añade un nombre opcional y pulsa **Guardar enlace**. Queda guardado en PostgreSQL; no se descarga ni se analiza el vídeo.
4. Para cerrar la aplicación, usa **[Detener ReelMind.cmd](Detener%20ReelMind.cmd)**. Cerrar solo la pestaña no detiene los procesos. PostgreSQL continúa como servicio local.

Los registros temporales usados para verificar la entrega se retiraron. El motor permanece detenido y todavía no tiene controles de ejecución.

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
- **Pendientes:** consulta el orden de análisis futuro. Quitar de cola conserva la fuente; Encolar la añade al final. Enviar a papelera oculta su pendiente y restaurar recupera su estado anterior.

La papelera conserva los archivos y no tiene purga. Si falta una copia local, vuelve a importar el mismo archivo para recuperarla. Las etiquetas/categorías son planas y sus nombres sin uso se conservan para reutilizarlos.

**La Fase 1 no analiza ni descarga vídeos de enlaces.** La siguiente fase es audio y motor manual (Fase 2); IA y Supabase esperan sus fases. [Pruebas y límites de esta entrega](docs/verification/phase1.md).

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

`setup.ps1` instala las dependencias fijadas y compila la interfaz. `Migrate` crea un respaldo local antes de aplicar Alembic. La revisión actual es `0002_library`; `0001_sources` permanece intacta. `start.ps1` sirve la compilación local en 5180 y la API en 8000. No inicia un trabajador de IA.

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
| [Estado](docs/status.md) | Resultado actual y siguiente paso |

Antes de retomar otra sesión, leer AGENTS, README, plan de fases y estado. Al cerrar cada trabajo, actualizar el seguimiento según AGENTS. No confundir los módulos previstos en el plan con funciones ya implementadas.
