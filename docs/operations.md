# Operación y recuperación

La aplicación mínima ya funciona. El inicio, detención, migración con respaldo previo y consultas están comprobados. La restauración completa y la operación de medios/IA siguen pendientes de sus fases.

## Inicio y detención actuales

Usar los accesos `Iniciar ReelMind.cmd` y `Detener ReelMind.cmd` en la raíz. La interfaz abre en `http://127.0.0.1:5180`. Cerrar el navegador no detiene servicios. Los procesos se registran en `.local/processes.json`, con ID y hora de creación para no cerrar un proceso ajeno que reutilice el mismo número. No se configura inicio automático de ReelMind con Windows.

El inicio habitual usa el build de Vite. Después de cambios de frontend, compilar con `npm.cmd run build` dentro de `frontend`; para desarrollo usar las dos terminales descritas en README. Logs locales: `.local/api.log`, `.local/api-error.log`, `.local/frontend.log` y `.local/frontend-error.log`.

## Almacenamiento

El código permanece en la carpeta ReelMind del escritorio. PostgreSQL y credenciales quedan fuera de OneDrive. La raíz de medios se configurará al crear el backend; no incrustar rutas personales en código. `data/`, `backups/`, `.local/` y `work/` están excluidos de Git por precaución.

## Git

Repositorio local con rama `main`. No publicar en GitHub ni crear un remoto como parte de esta preparación. Usar la identidad Git existente del usuario, sin sustituirla por datos ficticios. `.gitignore` evita incorporar medios y secretos; `.gitattributes` normaliza texto y conserva PDF como binario.

## PostgreSQL

Usar las herramientas de la versión instalada: `psql`, `pg_isready`, `pg_dump` y `pg_restore`. Los datos del servidor no deben colocarse dentro del repositorio ni sincronizarse como archivos vivos con OneDrive. Instalación y prueba real registradas en `setup-windows.md`.

El servicio `postgresql-x64-18` es automático. Si se detuvo manualmente, iniciarlo desde Servicios de Windows (requiere autorización administrativa). Para conectarse sin mostrar contraseñas: `powershell -NoProfile -File .\scripts\open-database.ps1`. Esto abre SQL; no inicia la aplicación ni IA.

## Copias futuras

`scripts/backend.ps1 -Action Migrate` ejecuta `pg_dump` en formato custom antes de aplicar Alembic y se detiene si la copia falla. Las copias quedan en `backups` dentro del directorio local de runtime, junto al directorio `secrets` pero no dentro de él; fuera del repositorio/OneDrive. El comando imprime solo la ruta del archivo. No hay limpieza automática de respaldos.

Cuando existan medios: añadir manifiesto coherente de archivos necesarios. Probar restauración en otra base antes de considerar válido un procedimiento completo de recuperación. La restauración integral aún no ha sido ensayada. No copiar un directorio PostgreSQL activo como sustituto del respaldo lógico.

Los modelos pueden descargarse otra vez; la biblioteca personal necesita copia propia, idealmente fuera del disco principal. Definir retención y destino con el usuario antes de automatizar copias.

## Fallos y limpieza futuros

Tras un fallo, abrir detenido, conservar checkpoints y ofrecer reanudación explícita. No borrar originales para resolver falta de espacio. Limpiar únicamente temporales identificados, comprobar rutas resueltas y documentar cuotas antes de automatizar. Diferenciar ausencia de archivo, falta de acceso y análisis fallido.
