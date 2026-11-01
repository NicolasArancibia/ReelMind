# Operación y recuperación

La biblioteca de Fase 1 funciona con archivos, clasificación y cola detenida. Inicio, detención, migración con respaldo, importación y recuperación por reintento están comprobados. La copia/restauración aislada de base y medios quedó verificada en Fase 7; ver el procedimiento vigente al final. Fase 2 incorpora audio manual, verificado por API y recorrido visual de interfaz en escritorio/tamaño móvil.

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

## Copias previas a migraciones

`scripts/backend.ps1 -Action Migrate` ejecuta `pg_dump` en formato custom antes de aplicar Alembic y se detiene si la copia falla. Las copias quedan en `backups` dentro del directorio local de runtime, junto al directorio `secrets` pero no dentro de él; fuera del repositorio/OneDrive. El comando imprime solo la ruta del archivo. No hay limpieza automática de respaldos.

Un respaldo SQL por sí solo no incluye vídeos. Para copia integral usar library-backup.ps1, descrito al final y verificado en otra base. No copiar un directorio PostgreSQL activo como sustituto del respaldo lógico.

Los modelos pueden descargarse otra vez; la biblioteca personal necesita copia propia, idealmente fuera del disco principal. Definir retención y destino con el usuario antes de automatizar copias.

## Recuperación de importaciones de Fase 1

- **Falta de espacio o permisos:** la API informa el fallo y conserva el original. Corregir espacio/permisos y volver a importar; no vaciar carpetas de medios para resolverlo.
- **Respuesta perdida o desconexión:** actualizar la biblioteca antes de repetir. Si la importación quedó confirmada, aparece una sola fuente. Repetir el mismo contenido se reconoce por hash.
- **Copia ausente o de tamaño incorrecto:** abrirla informa el problema. Volver a importar el mismo archivo repone la copia. Puede aparecer el mensaje de duplicado porque se conservó la fuente original; actualizar y abrirla de nuevo.
- **Cambio en otra ventana:** cerrar el diálogo y actualizar antes de editar, organizar, cambiar la cola o adjuntar.
- **Cierre forzado mientras se copia:** puede quedar un `.part` en `staging` o una copia publicada sin fila de base. No se borran automáticamente al iniciar. Reintentar reutiliza la copia publicada. Cualquier limpieza futura debe detener importaciones, comprobar las referencias de PostgreSQL y validar que cada destino está dentro de la raíz; no ejecutar borrados recursivos indiscriminados.
- **Motor:** abrir, reiniciar, importar, encolar y restaurar nunca activan análisis. En Fase 2 hay motor explícito; estas acciones tampoco se incorporan a un lote ya iniciado.

Una copia importada se valida por tamaño al leer, no por un nuevo hash completo en cada reproducción. Para sospechas de corrupción con tamaño idéntico, reimportar desde el original o verificar SHA-256 manualmente. La inspección de códecs y procesamiento audiovisual se incorporará en Fase 2.

## Recuperación del motor de audio

Tras un fallo, abrir detenido, conservar checkpoints y ofrecer reanudación explícita. No borrar originales para resolver falta de espacio. Limpiar únicamente temporales identificados, comprobar rutas resueltas y documentar cuotas antes de automatizar. Diferenciar ausencia de archivo, falta de acceso y análisis fallido.


El motor siempre abre detenido. Los intentos interrumpidos quedan detenidos, sin reintento automático. **Encolar + Iniciar** crea otro intento; las transcripciones completas anteriores se conservan. Pausar finaliza el vídeo actual; Detener cancela y descarta el resultado incompleto. Un fallo por vídeo permite continuar con los siguientes del lote, sin reintentar el fallido.

Preparar el modelo solo con la aplicación detenida: `scripts/prepare-audio.ps1`. Se guarda en `models/small` bajo la raíz de datos, con manifiesto de revisión/hash. La aplicación no descarga al iniciar. El script reutiliza/verifica la versión presente; no la actualiza automáticamente. Configuración: `REELMIND_WHISPER_MODEL=small`, CPU int8/4 hilos; `REELMIND_AUDIO_TIMEOUT_SECONDS=7200`. Faltan comparaciones GPU y otros modelos.

Temporales: `work/<attempt_uuid>/audio.wav` y `result.json`. Se eliminan únicamente los del intento propio al terminar normalmente o cancelar. Un cierre forzado puede dejarlos. Para mantenimiento manual: detener la aplicación, confirmar que el UUID corresponde a un intento no activo, resolver dentro de la raíz, y retirar solo esos archivos conocidos. No borrar media, modelos ni carpetas ajenas, ni hacer limpieza recursiva por antigüedad.

Si una fuente queda `unavailable`, adjuntar su copia local y reencolar. Si tiene varias copias, importar como fuente local la que se desea transcribir. Si queda `failed`, comprobar archivo/modelo, espacio y tiempo límite; reimportar el original puede reparar una copia ausente/corrupta. No borrar el historial para resolver errores.

El ensayo dejó informes y muestras públicas en `verification-phase2` bajo la raíz de datos; no son biblioteca personal ni están en Git. El respaldo SQL no contiene estos archivos, medios ni modelos. Esquema actual: `0004_audio_integrity`. [Verificación de Fase 2](verification/phase2.md).

## Visión y síntesis — Fase 3 en evaluación

Esquema actual tras el inicio de Fase 3: `0005_audiovisual`, con respaldo SQL previo. Preparación explícita: `scripts/prepare-av.ps1`, usando Python 3.13 del runtime y Ollama ya instalado. Descarga Qwen3-VL 4B y Qwen3 4B a `models/ollama` bajo la raíz de datos; genera `models/audiovisual.json` con versión y digests. Repetir reutiliza los instalados; no actualiza sus etiquetas por iniciativa propia. No mover ni versionar esos archivos.

ReelMind crea un servidor propio en 127.0.0.1:11435 para preparación o análisis; si el puerto está ocupado, falla sin apropiarse del proceso existente. No cambia el servidor habitual de Ollama en 11434 ni sus modelos. El trabajador audiovisual queda bajo el Job Object de la API; detener/caer cancela sus descendientes antes de soltar la reserva pesada. No iniciar otra preparación mientras se analiza.

En la interfaz, marcar **Incluir visión y síntesis** antes de Iniciar/Reanudar. Abrir **Ficha y audio** para consultar versiones, evidencias y límites. Si falla la etapa visual/textual, el intento no confirma transcripción ni ficha nuevas; conserva versiones previas. Corregir modelo/archivo/contexto/recursos y reencolar explícitamente. No hay reintentos automáticos.

Se conservan hasta ocho muestras visuales temporales y hasta 12 segmentos para síntesis. Un vídeo sin pista de audio puede tener ficha visual; eso no significa que se haya recuperado voz. Verificación inicial y revisión humana completadas; [límites vigentes](verification/phase3.md).

## Recuperación semántica local — Fase 5

En este equipo ya está preparada: pgvector 0.8.7 en PostgreSQL 18, extensión en ReelMind, esquema `0006_retrieval`, BGE-M3 y texto Instruct existentes. No repetir instalación ni descargas para abrir la aplicación. [Verificación](verification/phase5.md).

Preparación explícita en otra instalación compatible, desde la raíz del proyecto:

1. `powershell -NoProfile -File .\scripts\prepare-vector.ps1`: obtiene tag oficial y compila con Build Tools C++ x64 ya disponible. No instala compiladores. Para copiar archivos a Program Files, ejecutar el mismo script con `-Install` en PowerShell como administrador. Rechaza sobrescribir archivos distintos.
2. Abrir `scripts/open-database.ps1 -Admin`, ejecutar `\connect reelmind` y `CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;`. No habilitar en otras bases ni cambiar permisos globales. Salir con `\q`.
3. `powershell -NoProfile -File .\scripts\backend.ps1 -Action Migrate`: respaldo SQL externo obligatorio antes de migrar. No reescribir revisiones aplicadas.
4. `powershell -NoProfile -File .\scripts\backend.ps1 -Action PrepareSearch`: prepara BGE-M3 y reutiliza texto Instruct en el almacén propio; comprueba 1024 dimensiones y escribe `models/search.json`. Conserva reserva pesada mientras prepara, no indexa biblioteca.

Uso vigente: analizar vídeos con el motor manual existente; abrir **Chat**, desplegar **Biblioteca disponible** y pulsar **Actualizar índice**. Escribir un mensaje y enviar con Enter o el botón de envío; Mayús+Enter añade una línea. Si llega un análisis nuevo, actualizar índice explícitamente. Repetir indexación no duplica lo ya confirmado. **Detener** conserva el índice anterior. Abrir/reiniciar solo consulta estado e historial, sin iniciar análisis, indexación ni inferencia. No iniciar preparación mientras hay trabajo pesado.

El historial conserva citas exactas y su idioma original. Fuente en papelera queda fuera de recuperación y citas; versiones anteriores del chat se marcan. Modelos/digests y espacio vectorial no se mezclan; cambiar modelo requiere preparar e indexar su perfil. Límite inicial de 2000 fragmentos; no hay indexación automática por lotes ni limpieza de historial. Datos, modelos e informes permanecen bajo la raíz externa. No hay servicios externos, móvil o Supabase.

## Vistas e inicio de proyectos, 2026-11-01

Esquema actual `0007_projects`, aplicado con respaldo previo. Biblioteca, Chat y Proyectos tienen vistas propias por hash. Abrir historial no inicia inferencia. Proyectos permite crear y asociar/quitar fuentes; no ejecuta análisis. Grafo y vínculos con evidencia pendientes.

## Grafo inicial, 2026-11-01

Esquema actual `0008_graph`. En Proyectos, asociar dos fuentes; completar Desde/Hacia, relación y evidencia/motivo. Guardar como propuesta, aceptada o rechazada. Corregir relación crea versión nueva y conserva historial. Las rechazadas no aparecen como líneas, pero permanecen en la lista. Quitar fuente o enviarla a papelera oculta relaciones; restaurar/reasociar las recupera. Abrir fichas para contrastar notas manuales. Reinicio conserva datos, sin activar motor. [Verificación](verification/phase6.md).

## Procedimiento vigente de respaldo y restauración — Fase 7

Desde la raíz del proyecto, con el usuario Windows dueño de las credenciales locales:

```powershell
powershell -NoProfile -File .\scripts\stop.ps1
powershell -NoProfile -File .\scripts\library-backup.ps1 -Action Backup
```

El resultado imprime la carpeta de copia en el runtime externo, bajo backups/library-fecha-UUID. Contiene database.dump, manifest.json y data/media. El manifiesto se escribe únicamente tras completar la copia y cotejar tamaños/hashes; si falla, conservar el intento para diagnosticar y no usarlo como copia válida. Incluye todos los medios registrados, también papelera. Modelos, secretos, código y temporales no están incluidos. La copia contiene datos personales y no está cifrada por este procedimiento; mantenerla en un destino privado. No hay retención ni eliminación automática.

Para ensayar recuperación, sustituir la ruta por la carpeta exacta impresa:

```powershell
powershell -NoProfile -File .\scripts\library-backup.ps1 -Action RestoreVerify -Bundle "RUTA_DE_LA_COPIA"
```

Valida dump, medios e inventario; crea exclusivamente base reelmind_restore_UUID y carpeta recovery/UUID/data nuevas. Nunca restaura sobre reelmind ni elimina un destino existente. Requiere la credencial administrativa cifrada ya disponible para crear la base y habilitar pgvector; los objetos de aplicación se restauran con el rol limitado. verification.json junto a la raíz restaurada confirma nombre de base, carpeta y resultado. Copias de esquema distinto de 0008_graph fallan explícitamente en esta versión del procedimiento, sin migración implícita.

La aplicación habitual sigue usando su biblioteca principal. Para una recuperación operativa, revisar primero verification.json; detener ReelMind y, en una sesión PowerShell local, fijar PGDATABASE al nombre reelmind_restore_UUID verificado y REELMIND_DATA_ROOT a la carpeta data verificada antes de invocar scripts/start.ps1. Mantener esa sesión/configuración explícita: volver a iniciar sin esas variables abre el runtime habitual. No borrar originales ni declarar sustituida la biblioteca hasta revisar el resultado. El esquema/restauración permiten leer biblioteca, análisis, chat histórico y proyectos; inferencia exige preparar los modelos explícitamente en la raíz seleccionada y revisar los scripts de preparación, que pueden usar el runtime guardado. No se copian credenciales entre máquinas; en un Windows nuevo se prepara PostgreSQL/roles/runtime con el procedimiento inicial.

Para volver al uso habitual después del ensayo:

```powershell
powershell -NoProfile -File .\scripts\start.ps1
```

No se activa inferencia al abrir. Si quedaron variables de recuperación en la sesión, retirarlas antes de iniciar la biblioteca principal. La restauración comprobada conserva el motor detenido; no reintenta trabajos interrumpidos.

## Instalación reproducida y dependencias externas

Con ReelMind detenido, scripts/setup.ps1 conserva el Python 3.13 del runtime y usa los locks. Rechaza reinstalar si existe su registro de procesos: ejecutar Detener ReelMind también cuando el registro sea de un cierre anterior. Las dependencias frontend residen en runtime/dependencies/frontend/node_modules; el repositorio tiene una Junction. **No ejecutar npm ci desde frontend sobre ese enlace:** npm lo sustituye. Usar setup.ps1, que instala npm en el destino real externo y compila desde el proyecto. No borrar la carpeta original para reparar un enlace; comprobar ambos destinos.

`powershell -NoProfile -File .\scripts\verify-install.ps1` crea un entorno de verificación externo nuevo, reproduce requirements.lock con Python 3.13, comprueba importaciones/pip check, copia solo fuentes/configuración frontend y ejecuta npm ci/build. No usa secretos, datos ni modelos. `-Resume RUTA_DEL_FIXTURE` retoma únicamente un install-UUID propio para continuar después de un fallo; conserva lo ya instalado. verification.json registra hashes de locks y resultado. Los fixtures se conservan; no hay limpieza automática.

Entrega actual: lanzadores Iniciar/Detener ReelMind.cmd y navegador local. Se verificó en este Windows con PostgreSQL 18/pgvector/Node/runtime existentes; no es instalador EXE ni ensayo de Windows nuevo. Ver [Fase 7](verification/phase7.md) para evidencias y pendientes.

## Uso guiado actual — 2026-11-01

Abre **Mantenimiento ReelMind.cmd** desde la carpeta del proyecto. La ventana dispone de Abrir/Detener app, Crear copia (elige carpeta privada, preferiblemente otro disco), Verificar restauración, Elegir copia verificada, Migrar copia, Usar copia y Volver a configuración anterior. Mantenimiento solicita detener consultas/motor, espera y cierra servicios propios; después vuelve a abrirlos. No cierres la ventana durante una operación. Si una operación falla, el resultado queda visible y puedes usar Abrir app.

**Restaurar:** elige una carpeta de respaldo propia con manifest.json y database.dump. Se crean una base reelmind_restore_UUID y una raíz recovery/UUID/data nuevas, y se comparan huellas de tablas/checksums. Verificar no cambia el almacén activo. Selecciona verification.json; si su esquema es anterior, pulsa Migrar copia verificada. La migración trabaja sobre esa copia, con respaldo y lectura por API. **Usar copia verificada** vuelve a comprobar la API y pide confirmación antes de cambiar configuración; conserva el original. **Volver a configuración anterior** permite elegir una entrada de configuration-history y conserva también la configuración que reemplaza.

Los scripts admiten DatabaseName/DataRoot opcionales en .local/runtime.json. La ventana escribe solo esas claves y guarda el archivo completo anterior fuera de OneDrive, junto al runtime. Las credenciales DPAPI y dependencias se mantienen en el runtime original. El respaldo excluye modelos: preparar modelos actúa únicamente tras pulsación explícita, puede descargar pesos si faltan y reserva la tarea pesada. No prepares modelos como parte de una simple revisión de datos restaurados.

**Revisar temporales** enumera hasta 1000 archivos conocidos en work/staging. Selecciona lo que revisaste y confirma; si cambió tamaño/fecha o una ruta no es válida, se rechaza la operación antes de eliminar. No incluye medios, modelos, bases, respaldos ni archivos de usuario. No hay purga ni retención automática. Elegir otro disco y una política de copias sigue siendo decisión del usuario.

En **Ajustes** se ve el almacén activo, tamaño de medios registrados, disco libre, preparación y tarea/etapa actual. La lista de respaldos solo enumera manifiestos; usa Verificar restauración para comprobar contenido. JSON/Markdown son exportaciones legibles; para recuperar todo usa SQL+medios. [Comprobación de esta entrega](verification/product1.md).
