# ADR 0004: primera entrega de Fase 1 — gestión de enlaces

Fecha: 2026-10-29. Estado: implementado y verificado.

## Alcance autorizado

El usuario indicó «Empieza la Fase 1». Se comienza por el bloque 1.1 del plan vivo: edición de títulos, eliminación recuperable y navegación por toda la biblioteca. Fase 1 continúa en curso; archivos, organización y cola no se incluyen en este bloque.

## Decisiones

- Editar solo el título, opcional y de hasta 240 caracteres. Conservar URL original, identidad, procedencia y fecha de creación. No sustituir el vídeo asociado mediante una edición de título.
- Usar `deleted_at` como papelera, ya presente en la migración inicial. Eliminar desde la interfaz oculta el enlace de la biblioteca, pero conserva la fila. Restaurar recupera la misma identidad y sus datos. No hay purga ni borrado de archivos.
- Mantener la unicidad de URL normalizada también en papelera. Un alta duplicada ofrece restaurar la fuente original, sin sobrescribir su título con el del formulario.
- Paginar por bloques de 20 en UI; API admite 1–100 y desplazamiento no negativo. Orden por fecha y UUID para desempatar; papelera ordenada por fecha de eliminación. Si desaparece la última página, ajustar a la última existente.
- Contadores y filas de una respuesta se consultan en una transacción de solo lectura con snapshot consistente. Las páginas sucesivas son consultas independientes: si otra ventana agrega o retira enlaces, la lista puede desplazarse; Actualizar vuelve a consultar el estado real.
- Serializar cambios por fila con `FOR UPDATE` y exigir `expected_updated_at`. Una edición o eliminación basada en una versión anterior devuelve 409, sin sobrescribir el cambio reciente. Actualizar la fecha usando el reloj de la base después de adquirir el bloqueo.
- Repetir eliminación sobre una fila ya en papelera o restauración sobre una activa es idempotente. Una transición nueva sí verifica la versión. El motor permanece detenido.
- No crear una migración vacía: este bloque usa columnas existentes, y `alembic check` confirma que no cambia el esquema. Las tablas de archivos, clasificación y cola tendrán revisiones nuevas en sus bloques.

## Verificación y operación

Consultar [evidencias de 1.1](../verification/phase1-1.md). Se mantiene Python 3.13 y las dependencias fijadas. No se instaló infraestructura ni modelos.

Durante la primera prueba, la restricción de red impidió conectar con PostgreSQL y el traceback detallado mostró una credencial local de aplicación. Se reemplazó esa credencial, se actualizó su copia cifrada y se reinició la aplicación. Pytest ahora usa traceback corto para evitar imprimir el contexto local de librerías en errores de conexión. No se documentan valores secretos ni se versionan las herramientas temporales de recuperación.
