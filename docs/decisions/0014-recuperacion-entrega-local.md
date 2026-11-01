# 0014 — Respaldo coherente y entrega local de escritorio

2026-11-01. Fase 7 autorizada junto con preflight y continuación sin pausa. Se conserva React/Vite, FastAPI y PostgreSQL local; entrega mediante los lanzadores Windows existentes. No añade instalador nativo, empaquetado EXE, infraestructura remota ni servicios de pago.

## Copia y recuperación

`scripts/library-backup.ps1` ejecuta mantenimiento explícito con Python 3.13. Requiere detener ReelMind y reserva el bloqueo pesado común. `pg_export_snapshot` mantiene la misma instantánea para `pg_dump` y el inventario de tablas/medios. Copia todos los media_files, incluida papelera, con rutas SHA-256 estrictas, tamaño y hash; publica manifest.json solo al completar. Modelos, credenciales, temporales e instalaciones no se incluyen. Copia fuera de proyecto/OneDrive; no hay retención, borrado ni programación automáticos.

El formato custom y la instantánea explícita siguen las opciones oficiales de [pg_dump 18](https://www.postgresql.org/docs/18/app-pgdump.html). La restauración selectiva y transaccional usa las opciones de [pg_restore 18](https://www.postgresql.org/docs/18/app-pgrestore.html). Solo se ensayaron copias de esta base local conocida; una copia SQL de terceros contiene instrucciones de esquema y no se trata como medio importado seguro.

RestoreVerify valida hashes, cantidad y rutas antes de crear destino. Crea exclusivamente una base con nombre generado `reelmind_restore_<uuid>` y una raíz nueva bajo recovery. No acepta nombre de base de destino ni sobrescribe una existente. Admin se usa solo para crear la base y habilitar pgvector; pg_restore usa el rol de aplicación y excluye extensión/comentario ya preparados. Compara todas las tablas y todos los medios, y escribe verification.json. Las revisiones/gráficos/chats/embeddings son datos de la copia; los modelos se prepararían explícitamente después.

Un ensayo fallido se conserva, sin limpieza destructiva automática. La copia es de datos, no un programa a ejecutar ni un archivo para compartir públicamente. No está cifrada por este procedimiento. La restauración de ensayo no cambia qué base abre la aplicación habitual. Recuperación operativa: apuntar explícitamente PGDATABASE y REELMIND_DATA_ROOT a la copia verificada en una sesión local; conservar originales hasta revisar el resultado. No migrar una copia antigua sin respaldo ni cambiar credenciales para ensayarla.

## Instalación y operación

Dependencias Python en venv externo; frontend en runtime/dependencies/frontend/node_modules con Junction desde el repositorio. npm ci se ejecuta en el destino real: la prueba confirmó que ejecutarlo sobre la Junction la sustituye. setup.ps1 conserva el runtime y utiliza esta ubicación externa. Se conservó la carpeta anterior de dependencias; no se borraron datos para corregirlo.

verify-install.ps1 reproduce Python 3.13, requirements.lock, npm ci y compilación de una copia acotada del frontend en un fixture externo sin secretos/modelos. Resume retoma solo un directorio install-UUID bajo verification-phase7. Se corrigieron comillas de Python para Windows PowerShell mediante stdin. Esto prueba dependencias/build en este Windows con prerrequisitos existentes; no una instalación desde cero del sistema operativo ni de PostgreSQL.

Comprobaciones de cierre: restauración exacta de 22 tablas y dos vídeos; lecturas reales de API restaurada; bloqueo de origen/Host ajenos; rol de aplicación sin superusuario/CREATEDB/CREATEROLE; PostgreSQL/API/frontend solo loopback; motor y proveedor detenidos al entregar. [Evidencias y límites](../verification/phase7.md).
