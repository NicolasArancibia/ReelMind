# Operación y recuperación

Todavía no hay aplicación. Las operaciones sobre biblioteca, migraciones y respaldos descritas aquí son requisitos futuros, salvo las comprobaciones del entorno registradas en `status.md`.

## Almacenamiento

El código permanece en la carpeta ReelMind del escritorio. PostgreSQL y credenciales quedan fuera de OneDrive. La raíz de medios se configurará al crear el backend; no incrustar rutas personales en código. `data/`, `backups/`, `.local/` y `work/` están excluidos de Git por precaución.

## Git

Repositorio local con rama `main`. No publicar en GitHub ni crear un remoto como parte de esta preparación. Usar la identidad Git existente del usuario, sin sustituirla por datos ficticios. `.gitignore` evita incorporar medios y secretos; `.gitattributes` normaliza texto y conserva PDF como binario.

## PostgreSQL

Usar las herramientas de la versión instalada: `psql`, `pg_isready`, `pg_dump` y `pg_restore`. Los datos del servidor no deben colocarse dentro del repositorio ni sincronizarse como archivos vivos con OneDrive. Instalación y prueba real registradas en `setup-windows.md`.

El servicio `postgresql-x64-18` es automático. Si se detuvo manualmente, iniciarlo desde Servicios de Windows (requiere autorización administrativa). Para conectarse sin mostrar contraseñas: `powershell -NoProfile -File .\scripts\open-database.ps1`. Esto abre SQL; no inicia la aplicación ni IA.

## Copias futuras

Antes de migraciones sobre datos reales: copia PostgreSQL con `pg_dump` en formato custom y manifiesto coherente de archivos necesarios. Probar restauración en otra base antes de considerar válido el respaldo. No copiar un directorio PostgreSQL activo como sustituto del respaldo lógico.

Los modelos pueden descargarse otra vez; la biblioteca personal necesita copia propia, idealmente fuera del disco principal. Definir retención y destino con el usuario antes de automatizar copias.

## Fallos y limpieza futuros

Tras un fallo, abrir detenido, conservar checkpoints y ofrecer reanudación explícita. No borrar originales para resolver falta de espacio. Limpiar únicamente temporales identificados, comprobar rutas resueltas y documentar cuotas antes de automatizar. Diferenciar ausencia de archivo, falta de acceso y análisis fallido.
