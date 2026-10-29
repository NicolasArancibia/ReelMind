# Preparación de Windows

Fecha de diagnóstico: 2026-10-28. Este archivo se actualiza con resultados reales; no sustituye `docs/status.md`.

## Herramientas seleccionadas

| Herramienta | Base / estado |
| --- | --- |
| Git | 2.52.0.windows.1 existente |
| Node.js | 24.13.0 existente, rama 24 LTS |
| npm | 11.6.2 existente; usar npm.cmd en PowerShell |
| Python | 3.13.15 instalado mediante WinGet para ReelMind; Python 3.14.2 conservado |
| PostgreSQL | 18.6, instalado y verificado; pgAdmin incluido |
| VS Code | 1.140.0 existente |
| Codex | Chat abierto en la carpeta del proyecto |

## Comprobar sin modificar

Desde la raíz del repositorio:

```powershell
powershell -NoProfile -File .\scripts\check-environment.ps1
```

El diagnóstico muestra versiones, disponibilidad del servidor y estado de Git; no lee contraseñas ni acredita por sí solo que la futura aplicación funcione.

## Python

Se utiliza una instalación por usuario de Python 3.13 junto a la 3.14 existente. No se sustituyó el `python` general ni se cambió PATH. Seleccionar siempre el intérprete del proyecto explícitamente:

```powershell
py -3.13 --version
py -3.13 -m pip --version
```

El entorno aislado de backend ya existe bajo el almacenamiento local de ReelMind. Dependencias fijadas en `backend/requirements.lock`, instalables con `scripts/setup.ps1`. Windows puede redirigir AppData hacia la caché local de Codex: `.local/runtime.json` registra la ruta física resuelta de Python y credenciales para que los accesos funcionen fuera del chat. Ese archivo solo contiene rutas y no se versiona. La IA puede requerir un entorno separado; se resolverá con pruebas en su fase.

## PostgreSQL

PostgreSQL 18.6 está instalado en `C:\Program Files\PostgreSQL\18`, con datos en su subcarpeta `data`, fuera de OneDrive. El servicio `postgresql-x64-18` arranca automáticamente con Windows. Esto inicia solamente la base de datos: no existe todavía un motor de análisis que pueda arrancar.

- Servidor: `localhost`, puerto `5432`; escucha comprobada únicamente en `127.0.0.1` y `::1`.
- Base: `reelmind`, con tabla `sources` y control de versión `alembic_version` tras completar Fase 0.
- Usuario de desarrollo: `reelmind_app`, propietario de esta base, sin superusuario ni permiso para crear otras bases o roles. Se utilizará también para migraciones locales durante el desarrollo; separar permisos de migración y operación al endurecer una distribución futura.
- Administración: `postgres`, reservado para tareas del servidor.
- Credenciales: archivos `postgres-app.xml` y `postgres-admin.xml` bajo `%LOCALAPPDATA%\ReelMind\secrets`, cifrados por Windows para el usuario y protegidos con permisos locales. No están en Git ni en OneDrive. El archivo temporal de instalación con contraseña fue eliminado.

Para comprobar conexión desde una terminal normal abierta en ReelMind:

```powershell
powershell -NoProfile -File .\scripts\open-database.ps1 -Check
```

Para abrir una consola SQL interactiva, omitir `-Check`; salir con `\q`. `-Admin` selecciona el acceso administrativo y debe reservarse para tareas que lo requieran. No hace falta copiar ni mostrar contraseñas. Los scripts usan rutas completas, por lo que `psql` no necesita estar en PATH.

Las credenciales cifradas están ligadas al usuario de Windows y al equipo; no sirven como copia portable. Si se reinstala Windows o se pierde ese perfil, hará falta recuperar/restablecer credenciales y restaurar la base desde un respaldo. No subir estos archivos para compartir el proyecto.

## Evidencia de preparación

En 0A se verificó conexión con `reelmind_app` y `postgres` y persistencia en una base temporal. En 0B se aplicó `0001_sources` tras respaldo y se repitió persistencia sobre un enlace guardado desde la interfaz; el enlace de prueba fue retirado. Ver `docs/verification/phase0.md`.

WinGet instaló Python 3.13.15 correctamente. La descarga de PostgreSQL desde WinGet falló con HTTP 403; se descargó el mismo instalador de EDB directamente, comprobando firma válida de EnterpriseDB y SHA-256 coincidente con el manifiesto. Versión del paquete: `18.6-5`. Hash: `227E2BC08091B4C2B8338C7D61B11D057F895711480B006F90BFCFCD2410A58A`.

## Repetir la preparación en otro equipo

1. Instalar/verificar Git, Node 24 LTS, Python 3.13 y editor desde sus distribuidores oficiales. Conservar instalaciones existentes compatibles.
2. Instalar PostgreSQL 18 con Server, Command Line Tools y pgAdmin. Elegir una carpeta de datos local fuera del repositorio/OneDrive y una contraseña administrativa propia.
3. Configurar escucha solo en localhost. Crear una base vacía `reelmind` y un rol propietario `reelmind_app` sin superusuario, CREATEDB ni CREATEROLE, con una contraseña distinta de la administrativa.
4. Crear credenciales locales cifradas para ese usuario de Windows, o adaptar la conexión al almacén local elegido. No copiar los XML de otro equipo ni poner contraseñas en el repositorio.
5. Ejecutar las comprobaciones de conexión/persistencia y registrar versiones efectivas. Después crear el entorno aislado y dependencias de la aplicación durante 0B.

Si Codex muestra Python o VS Code como ausentes aunque estén instalados, comprobar desde la terminal del usuario: el entorno restringido puede tener un perfil diferente. No reinstalar ni cambiar PATH automáticamente por ese resultado.

## Referencias de instalación

- [Python para Windows](https://docs.python.org/3.13/using/windows.html): opciones de instalación por usuario y coexistencia de versiones.
- [PostgreSQL para Windows](https://www.postgresql.org/download/windows/): instalador EDB.
- [Opciones del instalador EDB](https://www.enterprisedb.com/docs/supported-open-source/postgresql/installing/command_line_parameters/): componentes y parámetros.
- [pgvector para Windows](https://github.com/pgvector/pgvector#windows): ruta de compilación nativa pendiente de probar.

El instalador y el manifiesto del gestor de paquetes deben verificarse al reproducir la preparación; las versiones disponibles pueden cambiar. No introducir Docker o WSL por defecto.
