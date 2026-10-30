# ADR 0005: cierre de Fase 1 — biblioteca local

Fecha: 2026-10-29, America/Santiago. Estado: implementado y verificado.

## Autorización y alcance

El usuario indicó «termina la fase 1» y posteriormente «termina lo que estabas haciendo y deja todo bien documentado y listo». Esto amplía la entrega anterior de 1.1 a los bloques 1.2–1.5. Se conserva la arquitectura aprobada. No se inicia Fase 2, IA, Supabase ni servicios nuevos.

## Archivos y procedencia

- Importación manual por copia, como fuente local nueva o adjunta a una fuente existente. Nunca se mueve, modifica ni elimina el archivo original seleccionado.
- MP4, M4V, MOV, WebM, MKV y AVI; límite predeterminado de 2 GiB, configurable mediante `REELMIND_MAX_UPLOAD_BYTES`. Se comprueban extensión, firma inicial y tamaño mientras se recibe. Es una comprobación de contenedor, no una garantía de decodificación ni de presencia de una pista de vídeo. La inspección audiovisual corresponde a Fase 2.
- El cliente transmite el cuerpo binario; el servidor escribe por bloques y calcula SHA-256 sin cargar el archivo completo en memoria. El nombre original se conserva como metadato, nunca se usa como ruta de destino.
- `REELMIND_DATA_ROOT` debe ser absoluta. Los scripts prefieren esa variable, después `DataRoot` del manifiesto local y finalmente `data` junto a `secrets` en el runtime existente, fuera de OneDrive. Esto evita cambiar de almacén por la redirección de `LOCALAPPDATA` entre terminales. Cambiar la configuración no traslada archivos automáticamente.
- `media_files` representa una copia física única por SHA-256; `media_assets` asocia esa copia a fuentes conservando el nombre importado. Dos enlaces pueden compartir bytes sin fusionar sus procedencias. Reimportar el mismo contenido como fuente local devuelve la fuente local existente; si está en papelera se ofrece restaurarla. Una segunda asociación idéntica no duplica el activo.
- Rutas persistidas relativas `media/<prefijo>/<sha256>`, validadas dentro de la raíz resuelta antes de escribir o leer. La API pública devuelve identificadores, nombre, tamaño, MIME y hash, sin rutas locales.
- Un archivo ausente o con tamaño alterado se informa al abrirlo. Reimportar los mismos bytes repone la copia; si la fuente ya existía se devuelve 409 por duplicado después de reparar. No se verifica el hash completo en cada lectura para evitar releer vídeos grandes: alteraciones del mismo tamaño requieren reimportación o una auditoría manual.
- Papelera conserva archivos y asociaciones; no hay purga pública ni limpieza automática.

## Consistencia entre disco y PostgreSQL

1. Cada petición escribe un temporal UUID en `staging`, valida y sincroniza sus bytes.
2. Un bloqueo transaccional PostgreSQL por hash serializa la publicación de ese contenido incluso entre procesos de API.
3. Se publica la copia con renombrado en el mismo volumen antes de confirmar metadatos y asociaciones.
4. Un fallo antes de confirmar no deja una fuente nueva incompleta. Puede quedar una copia sin registro si hubo un fallo después de publicar; se reutiliza al reintentar. Nunca se elimina una copia publicada como compensación: una respuesta perdida podría ocultar un commit exitoso.
5. Se limpia solo el temporal de la petición actual. Un cierre forzado del proceso puede dejar temporales; se conservan para revisión manual, sin borrar archivos por antigüedad al arrancar.

Se probaron falta de espacio/permisos simulada, interrupción de carga, error antes del commit y pérdida de respuesta después de un commit exitoso. No equivale a un ensayo de corte eléctrico o restauración completa.

## Organización y búsqueda

- Categorías planas y etiquetas reutilizables. La jerarquía de categorías del diseño inicial queda aplazada: no hace falta para cerrar la biblioteca y evita introducir ciclos o edición de árboles sin una necesidad concreta.
- Hasta 10 categorías y 20 etiquetas por fuente, con nombres de 1–60 caracteres. Normalización Unicode NFC, espacios y `casefold`; los acentos se conservan. El primer nombre guardado proporciona su presentación. UI usa comas para separar nombres.
- Se crean y asignan desde Organizar; vaciar un campo quita asociaciones, no otras fuentes. El catálogo conserva nombres sin uso para reutilizarlos. No se incluye edición global ni eliminación del catálogo.
- Búsqueda literal por título, URL, nombre original de archivo, categorías y etiquetas, sin distinguir mayúsculas según PostgreSQL. No es búsqueda semántica ni elimina acentos. `%` y `_` se buscan como caracteres, no comodines.
- Filtros combinables por plataforma, tipo, categoría y etiqueta en biblioteca, papelera y pendientes. El total de la página corresponde al filtro; los contadores de las pestañas son globales. Páginas independientes de 20 filas.
- Se mantiene la normalización conservadora de URL de 1.1. No se eliminan parámetros ni se promete reconocer variantes equivalentes de plataformas sin verificar sus reglas.

## Cola detenida

- Una fila persistente por fuente, creada en la misma transacción del alta; la migración también cubre las fuentes previas. Solo admite `pending` y `cancelled` en esta fase.
- Orden FIFO por fecha e ID del trabajo. Quitar de cola conserva la fuente; volver a encolar la sitúa al final. La papelera oculta el pendiente sin perder su estado; restaurar lo recupera si estaba pendiente.
- Las mutaciones de clasificación, cola y adjuntos usan bloqueo de fuente y `expected_updated_at`, igual que edición/papelera.
- No existe trabajador, endpoint de ejecución ni descarga de modelos. La exclusión global de tareas pesadas, historial de intentos, checkpoints y estados de ejecución se implementarán con nuevas migraciones en Fase 2. No se afirma que una cola visible sea un motor operativo.

## Migración y verificación

`0002_library` añade siete tablas: archivos físicos, asociaciones de medios, categorías, etiquetas, sus dos relaciones y pendientes. `0001_sources` queda intacta. Upgrade probado en esquema vacío y con datos anteriores; repetición idempotente, integridad y `alembic check` aprobados. Se respalda la base real antes de migrar. No hay downgrade destructivo.

Evidencia: [cierre de Fase 1](../verification/phase1.md). No se añadieron dependencias ni se cambió el PDF original.
