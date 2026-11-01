# Fase 7 — Estabilidad y recuperación local

2026-11-01, America/Santiago. Alcance inicial de entrega mediante lanzadores Windows y prerrequisitos existentes. [ADR 0014](../decisions/0014-recuperacion-entrega-local.md).

## Verificado

- Copia `library-20261101T080925Z-f820d142`, fuera de OneDrive, con snapshot PostgreSQL, database.dump, manifest.json y dos medios con hash/tamaño. Inventario y dump provienen de la misma instantánea. 22 tablas incluidas, también historial, vectores, relaciones y papelera.
- Restauración final aislada en `reelmind_restore_b2f8dcae02bc403baf380149c77e975e` y recovery/b2f8dcae02bc403baf380149c77e975e/data bajo runtime externo: 22 tablas con conteos/hashes idénticos, dos archivos idénticos y lista de medios exactamente igual a la base. Ningún modelo o secreto copiado. Informe verification.json junto al destino.
- Primera restauración `reelmind_restore_9592ab6dd2344c03b82ef68873949bbc` comprobada por TestClient contra PostgreSQL/medios restaurados: dos fuentes, sus fichas/transcripciones, dos lecturas HTTP Range de 16 bytes, dos conversaciones y un proyecto/grafo. Motor detenido, ninguna consulta activa. Escritura con Origin ajeno: 403; Host ajeno: 400. Informe api-verification.json. La comprobación final añadió validación de inventario completo y se repitió la restauración por ese cambio; no se repitió una suite general.
- Cuatro pruebas dirigidas de mantenimiento aprobadas en 0,29 s: contención/rutas estrictas; corrupción de medio con igual tamaño; corrupción SQL y duplicados; omisión de un medio del manifiesto. Sin ejecutar restauraciones sobre la base real.
- La base original, antes de reabrir la app, idéntica al inventario completo de la copia. Rol de aplicación sin superusuario, CREATEDB o CREATEROLE.
- Instalación limpia en verification-phase7/install-b6170f2f83514fb19c15c470a29c032b: Python 3.13, pip check sin conflictos, importación de FastAPI/SQLAlchemy/psycopg/PyAV/faster-whisper/httpx; npm ci y TypeScript/Vite aprobados. Locks SHA-256 en verification.json. Falló primero una comprobación por comillas de Windows PowerShell, corregida por stdin y retomada sin reinstalar Python.
- Dependencias del proyecto trasladadas a runtime/dependencies/frontend/node_modules; Junction comprobada. npm ci ejecutado en destino real y compilación aprobada. La prueba previa mostró que npm ci desde el enlace lo sustituye: setup corregido y vuelto a comprobar. Dependencias anteriores preservadas, sin borrado automático.
- Control real: Backup con API abierta rechaza antes de crear una copia; setup rechaza antes de instalar si existe su registro de procesos. Se corrigió el primer guard, que dependía de visibilidad de procesos y no se activó dentro del sandbox; la comprobación final validó el marcador de rechazo temprano, no solo un código de error.
- Entrega reabierta: health ok, esquema 0008_graph, motor stopped, ninguna consulta activa, proveedor 11435 sin escucha. Puertos 5180/8000 en 127.0.0.1; PostgreSQL 5432 en 127.0.0.1 y ::1. Sin puertos externos ni descarga de modelos.

## Límites

No instalación de Windows/PostgreSQL desde cero, reinicio del sistema, instalador EXE ni empaquetado nativo. Se usa el runtime/credenciales locales existentes y lanzadores CMD. No se activó una copia restaurada como biblioteca principal ni se sustituyeron originales. Modelos requieren preparación explícita si se pierde su almacén. No copia fuera del disco, cifrado, programación o retención automáticos; definir destino físico/retención antes de automatizar. No prueba de bibliotecas grandes ni recuperación durante un corte eléctrico real. Copias/fixtures/bases de ensayo retenidas para revisión; ninguna purga automática.
