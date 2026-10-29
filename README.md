# ReelMind

Biblioteca personal de vídeos, local en Windows. **Fase 0 completada:** interfaz React/Vite/Tailwind, API FastAPI, PostgreSQL y primera migración funcionando juntos. [Estado y comprobaciones](docs/status.md).

## Abrir y cerrar

1. Haz doble clic en **[Iniciar ReelMind.cmd](Iniciar%20ReelMind.cmd)**. Se inicia la aplicación y se abre el navegador.
2. Abre [ReelMind](http://127.0.0.1:5180) si el navegador no se abrió automáticamente.
3. Pega un enlace, añade un nombre opcional y pulsa **Guardar enlace**. Queda guardado en PostgreSQL; no se descarga ni se analiza el vídeo.
4. Para cerrar la aplicación, usa **[Detener ReelMind.cmd](Detener%20ReelMind.cmd)**. Cerrar solo la pestaña no detiene los procesos. PostgreSQL continúa como servicio local.

La biblioteca empieza vacía: el enlace usado para las pruebas ya se retiró. El motor permanece detenido y todavía no tiene controles de ejecución.

## Qué funciona en esta entrega

- Conexión real con PostgreSQL, comprobación de la revisión de esquema y estado del motor.
- Guardado de enlaces HTTP/HTTPS, título opcional, plataforma orientativa y fecha.
- Consulta de los últimos 20 enlaces y contador total. No se descarga contenido externo.
- Detección de URL normalizada repetida; validación de entradas y mensajes de conexión/errores.
- Inicio y detención de los procesos propios; no se altera otra aplicación que use otros puertos.
- Persistencia comprobada después de reiniciar la API y PostgreSQL.

La biblioteca completa, archivos de vídeo, edición, eliminación, etiquetas, búsqueda y cola pertenecen a Fase 1 o posteriores. La IA y Supabase no están integrados en esta entrega.

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

`setup.ps1` instala las dependencias fijadas y compila la interfaz. `Migrate` crea un respaldo local antes de aplicar Alembic. `start.ps1` sirve la compilación local en 5180 y la API en 8000. No inicia un trabajador de IA.

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

Los scripts inyectan la credencial PostgreSQL cifrada del usuario al proceso Python; no al navegador. `.env.example` documenta variables, pero no se carga automáticamente. `.local/runtime.json` contiene solo rutas locales para resolver instalaciones redirigidas por Windows; no contraseñas. `.local/api-error.log` y `.local/frontend-error.log` permiten revisar fallos de inicio. Todos estos archivos locales están excluidos de Git.

Los servicios escuchan solo en `127.0.0.1`; PostgreSQL en loopback. Los datos vivos y secretos están fuera de OneDrive. No hay repositorio remoto ni publicación.

## Documentación

| Documento | Contenido |
| --- | --- |
| [Plan original v1.3](docs/referencias/ReelMind_Plan_Maestro_v1.3.pdf) | Referencia original sin modificar |
| [AGENTS](AGENTS.md) | Reglas para asistentes y continuidad |
| [Arquitectura](docs/architecture.md) | Componentes, límites y contratos |
| [Base de datos](docs/database.md) | Esquema aplicado y diseño futuro |
| [Hoja de ruta](docs/roadmap.md) | Fases y condiciones de cierre |
| [Decisión inicial](docs/decisions/0001-base-del-proyecto.md) | Base de la preparación |
| [Arranque mínimo](docs/decisions/0002-arranque-minimo.md) | Alcance y decisiones de Fase 0 |
| [Modelos](docs/models.md) | Candidatos y evaluación futura |
| [Seguridad](docs/security.md) | Secretos y límites |
| [Operación](docs/operations.md) | Inicio, respaldos y recuperación |
| [Entorno Windows](docs/setup-windows.md) | Herramientas y preparación |
| [Verificación Fase 0](docs/verification/phase0.md) | Evidencia y limitaciones de las pruebas |
| [Estado](docs/status.md) | Resultado actual y siguiente paso |

Antes de retomar otra sesión, leer AGENTS, README y estado. No confundir los módulos previstos en el plan con funciones ya implementadas.
