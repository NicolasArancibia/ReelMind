# Verificación de cierre de Fase 1

Fecha: 2026-10-29, America/Santiago. Resultado: **Fase 1 completada y verificada**.

Alcance y decisiones: [ADR 0005](../decisions/0005-cierre-biblioteca.md). Las pruebas previas de gestión de enlaces permanecen en [1.1](phase1-1.md).

## Pruebas automatizadas

Comando: `powershell -NoProfile -File .\scripts\backend.ps1 -Action Test`, con Python 3.13.15. **57 pruebas aprobadas**: 34 previas y 23 de cierre. Se crean esquemas PostgreSQL aleatorios por prueba y raíces temporales independientes para medios; se retiran los esquemas al terminar.

Comprobado:

- Copia, hash, tamaño, descarga y lectura parcial HTTP Range; duplicados por contenido y lectura desde otra conexión.
- Un único archivo físico compartido por dos fuentes, sin perder URL o nombre importado; papelera y restauración conservan activos.
- Rechazo de nombres con rutas, formatos no permitidos, firmas incompatibles, archivos vacíos y exceso de tamaño tanto por cabecera como durante el flujo.
- Carga interrumpida sin fuente ni temporal residual; error de disco sin datos nuevos parciales; reintento satisfactorio.
- Error antes de commit y error después de un commit exitoso: copia preservada, reintento sin duplicar la fuente ni perder medios.
- Archivo ausente, mensaje claro y reparación por reimportación; bloqueo de lectura fuera de raíz.
- Dos importaciones simultáneas del mismo contenido producen una fuente y un archivo físico.
- Adjuntos con versión obsoleta o fuente en papelera rechazados.
- Nombres normalizados, reutilización sin duplicados, asignación y retirada, validación, búsqueda literal y filtros combinados. Dos fuentes crean simultáneamente las mismas etiquetas sin duplicarlas.
- Cola FIFO, cancelación, reencolado al final, ocultación por papelera, restauración, persistencia y motor detenido.
- Upgrade de `0001_sources` con datos existentes, backfill de cola, aplicación repetida y esquema sin diferencias. Restricciones de integridad activas.

Los fixtures automatizados de medios prueban ingestión y consistencia; no simulan un decodificador. La prueba de interfaz usó además un AVI sintético válido de 32 × 32 píxeles, 10 fotogramas, 1 segundo y 31.192 bytes, generado localmente sin FFmpeg ni modelos.

## Aplicación local y navegador

- Compilación TypeScript/Vite aprobada. Ninguna dependencia añadida.
- Respaldo `before-migration-20261029-211314-837.dump` creado por el script habitual fuera de OneDrive antes de aplicar `0002_library`.
- `backend.ps1 -Action Check`: `No new upgrade operations detected.`
- Inicio de frontend/API actualizado y salud real con `schema_revision=0002_library`, motor `stopped`, `available=false`, `autostart=false`.
- Flujo desde navegador: crear enlace, asignar categoría y dos etiquetas, adjuntar AVI a ese enlace e importar el mismo AVI como fuente independiente; ambas fuentes visibles.
- Búsqueda por etiqueta, filtro de tipo archivo, retirada de cola, papelera del archivo y restauración. La fuente restaurada recupera su pendiente; el enlace retirado de cola permanece fuera.
- Descarga del AVI asociado por API comparada con el original mediante SHA-256 antes y después del reinicio: igualdad exacta.
- Reinicio real de frontend/API: mismos IDs, marcas de tiempo, activos, categorías, etiquetas y estados de papelera y cola; motor detenido. No se reinició PostgreSQL en este cierre; el reinicio de ese servicio corresponde a la evidencia histórica de Fase 0.
- Escucha comprobada: API 8000 e interfaz 5180 en `127.0.0.1`; PostgreSQL 5432 en `127.0.0.1` y `::1`.
- Revisión visual de escritorio y móvil de 390 px: filtros, acciones y contenido sin desbordamiento horizontal. Se restauró el tamaño habitual del navegador al terminar.
- Los dos registros temporales, sus asociaciones y nombres sin uso, la cola de prueba y la copia administrada del AVI sintético se retiraron verificando IDs y hash. No se eliminaron fuentes del usuario. Las capturas documentan la prueba antes de esta limpieza.

Capturas: [biblioteca durante la prueba](phase1-library.jpg), [móvil](phase1-mobile.jpg) y [aplicación lista después de retirar los datos temporales](phase1-ready.jpg).

## Incidencias de verificación

El entorno restringido bloqueó inicialmente la conexión TCP a PostgreSQL (`Permission denied`); las pruebas se ejecutaron después con acceso autorizado a loopback. La selección de archivos del navegador se demoró y un selector coincidió con dos botones de importación; se completó usando el botón del diálogo activo. Ninguno de estos fallos dejó una importación parcial.

Se conserva el aviso de deprecación de Starlette sobre su adaptador de pruebas `httpx`; la suite pasa. No afecta al servidor.

## Límites explícitos

No se probó una carga real de 2 GiB ni una colección masiva; sí se probaron límites reducidos y recepción por bloques. La cabecera no garantiza que el vídeo sea decodificable. Reproducción según capacidades del navegador, sin transcodificación. No se incluyen descargas de enlaces, jerarquía de categorías, búsqueda semántica, purga, limpieza automática, trabajador o IA. El ensayo integral de respaldo/restauración de base y medios corresponde a Fase 7; reiniciar servicios no lo sustituye. Un cierre forzado puede dejar temporales o archivos huérfanos conservados; consultar [operación](../operations.md).
