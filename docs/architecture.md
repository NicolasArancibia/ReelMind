# Arquitectura aprobada

Referencia: plan v1.3, páginas 3-7. El diagrama describe el sistema completo previsto. Implementado hasta Fase 1.1: entrada por URL, edición de título, papelera/restauración, paginación, interfaz React/Vite/Tailwind, API FastAPI y PostgreSQL con `sources`. Archivos, clasificación, cola, trabajador, modelos y Supabase siguen pendientes.

## Contratos actuales

`GET /api/health` verifica PostgreSQL y revisión Alembic, devuelve motor detenido/no disponible. `POST /api/sources` guarda URL/título, responde 201 o 409 si existe; si está en papelera incluye `existing_source` para ofrecer restauración. `GET /api/sources?limit=20&offset=0&view=library` entrega página y contadores activos/papelera; `view=trash` consulta eliminados, límite 1–100. `GET /api/sources/{id}` recupera una fuente activa o 404.

`PATCH /api/sources/{id}` recibe título y `expected_updated_at`. `DELETE /api/sources/{id}` recibe un cuerpo JSON con `expected_updated_at` y mueve a papelera; `POST /api/sources/{id}/restore` recibe lo mismo y restaura. Devuelven fuente actualizada con `updated_at`/`deleted_at`. Bloqueo por fila y versión previa; conflicto 409, validación 422, fuente ausente 404 y base no disponible 503. Respuestas no incluyen credenciales ni detalles SQL. No existe borrado físico público. [Detalle de decisiones](decisions/0004-gestion-de-enlaces.md).

Interfaz en `127.0.0.1:5180`, API en `127.0.0.1:8000`. Vite redirige `/api` al backend; no se habilita CORS global. El backend rechaza orígenes externos y hosts no admitidos. No hay endpoint que active IA.

```mermaid
flowchart TD
  Entrada[Enlaces pegados y archivos locales] --> UI[React + Vite + Tailwind]
  UI --> API[FastAPI]
  Remoto[Supabase: pendientes, Fase 4] --> API
  API --> DB[(PostgreSQL local)]
  API --> Archivos[Almacenamiento local configurable]
  DB --> Cola[Cola persistente, inicio manual]
  Cola --> Worker[Trabajador pesado único]
  Worker --> Audio[FFmpeg y transcripción]
  Audio --> Vision[Visión local]
  Vision --> Sintesis[Síntesis e indexación]
  Sintesis --> DB
```

## Responsabilidades

- Frontend: biblioteca, detalle, controles y estados. Solo consume la API; no contiene credenciales de PostgreSQL ni claves privilegiadas de Supabase.
- API: validación, CRUD, consulta, sincronización futura y solicitudes de control. No ejecuta vídeos largos dentro de una petición HTTP.
- Trabajador local: reclama trabajos de PostgreSQL por transacción, conserva checkpoints y coordina una única reserva de recursos pesados.
- Proveedores: adaptadores separados de audio, visión, síntesis, embeddings y chat. Registrar versión, configuración y procedencia.
- PostgreSQL: metadatos, cola, versiones, relaciones y recibos de sincronización. No guardar vídeos completos como filas.
- Archivos: originales y derivados bajo una raíz configurable fuera de OneDrive; rutas relativas comprobadas, cuotas futuras.

## Control y recuperación

Abrir la aplicación deja el motor detenido, incluso si había trabajos activos antes de un fallo. Sincronizar no inicia análisis. Pausar evita nuevos vídeos y lleva el actual a un punto seguro; detener solicita cancelación, guarda lo confirmado y libera recursos. Reanudar o reintentar requiere acción explícita.

Una única tarea pesada incluye al chat: debe esperar o solicitar una pausa mientras el trabajador reserva GPU/RAM. No mantener simultáneamente todos los modelos cargados. Un fallo de IA no impide leer la biblioteca.

## Contrato de información

Cada ficha reúne identificación, clasificación, resumen, transcripción temporal, observaciones visuales, pasos y recursos cuando existan. Cada hallazgo distingue observación de inferencia y verificación externa. Guardar fuente, activo/segmento, tiempo, modelo y versión del análisis. Un trabajo terminado puede producir una ficha parcial: estado operativo y calidad son atributos diferentes.

## Fronteras de red

UI, API y PostgreSQL operan sobre loopback. La biblioteca almacenada funciona sin Supabase. Recuperar enlaces y verificar páginas requiere conexión. Supabase no ejecuta IA ni almacena la biblioteca completa.
