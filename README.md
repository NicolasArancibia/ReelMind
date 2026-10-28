# ReelMind

Biblioteca personal de vídeos que convertirá audio, imágenes y metadatos en conocimiento consultable desde una aplicación web local para Windows.

**Estado:** preparación anterior a la aplicación. No hay frontend, backend, modelos descargados ni migraciones ejecutadas. Ver [estado real y próximo paso](docs/status.md).

## Decisiones conservadas

- React + Vite + Tailwind para la interfaz; Python + FastAPI para la API.
- PostgreSQL local como fuente principal de conocimiento; SQLAlchemy + Alembic para datos y migraciones.
- Vídeos, análisis y biblioteca locales. Supabase Free llegará en Fase 4 exclusivamente como bandeja de enlaces pendientes.
- Entrada inicial: enlaces pegados y archivos aportados por el usuario.
- Análisis audiovisual completo por defecto, con límites explícitos cuando falte evidencia.
- Motor detenido al abrir; inicio, pausa y detención manuales; una tarea pesada a la vez, coordinada también con el chat.
- IA local futura, sin APIs pagadas obligatorias. Los modelos del plan son candidatos, no resultados validados.
- Diseño negro minimalista con acentos verde esmeralda.

## Empezar o retomar

1. Abrir esta carpeta en Codex o VS Code.
2. Leer [AGENTS.md](AGENTS.md), este documento y [docs/status.md](docs/status.md).
3. Consultar [preparación de Windows](docs/setup-windows.md) y ejecutar `powershell -NoProfile -File .\scripts\check-environment.ps1` para un diagnóstico de lectura.
4. Continuar únicamente con el siguiente paso indicado en el estado. El usuario pidió completar la preparación antes de comenzar la aplicación.

La base prevista es Node.js 24 LTS y Python 3.13. `.node-version` y `.python-version` documentan la selección; no cambian por sí solos el intérprete de Windows. Usar `py -3.13` explícitamente.

## Documentación

| Documento | Contenido |
| --- | --- |
| [Plan original v1.3](docs/referencias/ReelMind_Plan_Maestro_v1.3.pdf) | Referencia original conservada sin modificar |
| [Arquitectura](docs/architecture.md) | Componentes, límites y flujo |
| [Base de datos](docs/database.md) | Esquema propuesto, restricciones y migraciones |
| [Hoja de ruta](docs/roadmap.md) | Fases y condiciones de cierre |
| [Decisiones](docs/decisions/0001-base-del-proyecto.md) | Decisiones y alcance de esta preparación |
| [Modelos](docs/models.md) | Candidatos y protocolo de evaluación futura |
| [Seguridad](docs/security.md) | Secretos, archivos y límites de red |
| [Operación](docs/operations.md) | Datos, copias, recuperación y Git |
| [Entorno](docs/setup-windows.md) | Herramientas y pasos reproducibles |
| [Estado](docs/status.md) | Comprobaciones, pendientes y siguiente sesión |

## Arranque, migraciones y pruebas de la aplicación

Todavía pendientes. No ejecutar comandos de arranque ni `alembic upgrade` hasta crear la aplicación y sus dependencias. Se documentarán aquí comandos comprobados cuando exista una implementación.

El siguiente hito será un frontend y una API mínimos conectados a PostgreSQL, con una migración y una prueba de persistencia tras reinicio. Esto pertenece a la parte restante de la Fase 0, no a esta preparación.

## Archivos privados

`.gitignore` excluye credenciales, datos, modelos, entornos, respaldos y temporales. La carpeta del código está en OneDrive por elección del usuario; los datos vivos de PostgreSQL y las credenciales deben quedar fuera de esa sincronización. Git es historial de código, no respaldo de la biblioteca.
