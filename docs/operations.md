# Operación y recuperación

La biblioteca de Fase 1 funciona con archivos, clasificación y cola detenida. Inicio, detención, migración con respaldo, importación y recuperación por reintento están comprobados. La restauración integral de base y medios y la operación de IA esperan sus fases.

## Inicio y detención actuales

Usar los accesos `Iniciar ReelMind.cmd` y `Detener ReelMind.cmd` en la raíz. La interfaz abre en `http://127.0.0.1:5180`. Cerrar el navegador no detiene servicios. Los procesos se registran en `.local/processes.json`, con ID y hora de creación para no cerrar un proceso ajeno que reutilice el mismo número. No se configura inicio automático de ReelMind con Windows.

El inicio habitual usa el build de Vite. Después de cambios de frontend, compilar con `npm.cmd run build` dentro de `frontend`; para desarrollo usar las dos terminales descritas en README. Logs locales: `.local/api.log`, `.local/api-error.log`, `.local/frontend.log` y `.local/frontend-error.log`.

## Almacenamiento

El código permanece en la carpeta ReelMind del escritorio. PostgreSQL y credenciales quedan fuera de OneDrive. La raíz de medios se resuelve en este orden: variable `REELMIND_DATA_ROOT`, propiedad opcional `DataRoot` de `.local/runtime.json`, o carpeta `data` junto a `secrets` en el runtime persistido. La ruta predeterminada de esta instalación está fuera de OneDrive. Los scripts derivan la ruta del manifiesto para no cambiarla entre una terminal normal y la app con `LOCALAPPDATA` redirigido. No incrustar rutas personales en código.

Para consultar la ubicación sin leer credenciales:

```powershell
. .\scripts\common.ps1
Get-ReelMindDataRoot (Get-ReelMindRuntime)
```

Para personalizarla antes de importar, exportar una ruta absoluta fuera de OneDrive en `REELMIND_DATA_ROOT` al arrancar, o añadir `DataRoot` al manifiesto local. Si ya existen archivos, detener la aplicación y planificar su traslado/copia y verificación antes de cambiar la raíz: la configuración sola no los mueve. No borrar el almacén anterior para resolver errores.

El almacén contiene `media/<prefijo>/<sha256>` y temporales `staging/<uuid>.part`. PostgreSQL conserva rutas relativas, nombres originales y asociaciones. La papelera no libera espacio; no hay purga pública. Se admiten MP4, M4V, MOV, WebM, MKV y AVI con firma compatible, hasta 2 GiB por defecto. `REELMIND_MAX_UPLOAD_BYTES` cambia el límite del servidor; la interfaz recuerda el valor predeterminado. `data/`, `backups/`, `.local/` y `work/` están excluidos de Git por precaución.

## Git

Repositorio local con rama `main`. No publicar en GitHub ni crear un remoto como parte de esta preparación. Usar la identidad Git existente del usuario, sin sustituirla por datos ficticios. `.gitignore` evita incorporar medios y secretos; `.gitattributes` normaliza texto y conserva PDF como binario.

## PostgreSQL

Usar las herramientas de la versión instalada: `psql`, `pg_isready`, `pg_dump` y `pg_restore`. Los datos del servidor no deben colocarse dentro del repositorio ni sincronizarse como archivos vivos con OneDrive. Instalación y prueba real registradas en `setup-windows.md`.

El servicio `postgresql-x64-18` es automático. Si se detuvo manualmente, iniciarlo desde Servicios de Windows (requiere autorización administrativa). Para conectarse sin mostrar contraseñas: `powershell -NoProfile -File .\scripts\open-database.ps1`. Esto abre SQL; no inicia la aplicación ni IA.

## Copias futuras

`scripts/backend.ps1 -Action Migrate` ejecuta `pg_dump` en formato custom antes de aplicar Alembic y se detiene si la copia falla. Las copias quedan en `backups` dentro del directorio local de runtime, junto al directorio `secrets` pero no dentro de él; fuera del repositorio/OneDrive. El comando imprime solo la ruta del archivo. No hay limpieza automática de respaldos.

Ahora existen medios: un respaldo de PostgreSQL por sí solo no incluye los vídeos. El procedimiento integral deberá añadir una copia coherente del almacén y un manifiesto de los archivos necesarios. Probar restauración en otra base antes de considerar válido un procedimiento completo de recuperación. La restauración integral aún no ha sido ensayada. No copiar un directorio PostgreSQL activo como sustituto del respaldo lógico.

Los modelos pueden descargarse otra vez; la biblioteca personal necesita copia propia, idealmente fuera del disco principal. Definir retención y destino con el usuario antes de automatizar copias.

## Recuperación de importaciones de Fase 1

- **Falta de espacio o permisos:** la API informa el fallo y conserva el original. Corregir espacio/permisos y volver a importar; no vaciar carpetas de medios para resolverlo.
- **Respuesta perdida o desconexión:** actualizar la biblioteca antes de repetir. Si la importación quedó confirmada, aparece una sola fuente. Repetir el mismo contenido se reconoce por hash.
- **Copia ausente o de tamaño incorrecto:** abrirla informa el problema. Volver a importar el mismo archivo repone la copia. Puede aparecer el mensaje de duplicado porque se conservó la fuente original; actualizar y abrirla de nuevo.
- **Cambio en otra ventana:** cerrar el diálogo y actualizar antes de editar, organizar, cambiar la cola o adjuntar.
- **Cierre forzado mientras se copia:** puede quedar un `.part` en `staging` o una copia publicada sin fila de base. No se borran automáticamente al iniciar. Reintentar reutiliza la copia publicada. Cualquier limpieza futura debe detener importaciones, comprobar las referencias de PostgreSQL y validar que cada destino está dentro de la raíz; no ejecutar borrados recursivos indiscriminados.
- **Motor:** abrir, reiniciar, importar, encolar y restaurar nunca activan análisis. No existe trabajador en Fase 1.

Una copia importada se valida por tamaño al leer, no por un nuevo hash completo en cada reproducción. Para sospechas de corrupción con tamaño idéntico, reimportar desde el original o verificar SHA-256 manualmente. La inspección de códecs y procesamiento audiovisual se incorporará en Fase 2.

## Recuperación del motor futuro

Tras un fallo, abrir detenido, conservar checkpoints y ofrecer reanudación explícita. No borrar originales para resolver falta de espacio. Limpiar únicamente temporales identificados, comprobar rutas resueltas y documentar cuotas antes de automatizar. Diferenciar ausencia de archivo, falta de acceso y análisis fallido.
