# ADR 0006: audio local y motor manual

Fecha: 2026-10-30, America/Santiago. Estado: implementado; verificación visual pendiente.

## Autorización y alcance

El usuario solicitó «comienza y completa la fase 2 en otro chat». Esta autorización sustituye la indicación anterior de no iniciar Fase 2. Se implementan audio y motor secuencial, conservando React/Vite/Tailwind, FastAPI, SQLAlchemy/Alembic y PostgreSQL local. No se añaden visión, síntesis, Supabase, embeddings ni chat. No se delegó a agentes ni se publicó el proyecto.

## Motor y exclusión

- Supervisor ligero en un hilo de la API; cada vídeo se procesa en un subproceso Python independiente. La API no realiza inferencia dentro de una petición HTTP. El subproceso libera modelo y memoria al salir.
- Una conexión PostgreSQL dedicada mantiene `pg_try_advisory_lock(0x5245454C4D494E44)` durante toda la ejecución, incluyendo reclamación, proceso pesado y confirmación. Los futuros consumidores pesados, incluido chat, deberán usar este mismo bloqueo. No basta con bloquear filas ni deshabilitar botones.
- Cada Iniciar/Reanudar captura los pendientes activos de ese momento mediante `run_id`. Importaciones, restauraciones y reencolados posteriores esperan otro inicio explícito. No hay planificador ni descargas al arrancar.
- Pausar termina el vídeo actual y no reclama el siguiente. El checkpoint es un vídeo confirmado completo; no se persisten fragmentos incompletos. Reanudar requiere acción explícita.
- Detener cancela el árbol de procesos actual y descarta su resultado incompleto. El trabajo queda `stopped`; se reintenta con Encolar e Iniciar. Los pendientes sin empezar conservan su estado.
- Windows Job Object con `KILL_ON_JOB_CLOSE`: el hijo espera una señal por stdin antes de trabajar; el supervisor lo asigna al Job antes de enviar esa señal. Detener o perder la API termina también FFmpeg. El bloqueo se libera después de cerrar los descendientes en la detención normal.
- Arranque siempre detenido. Solo se recuperan filas huérfanas después de obtener el bloqueo global; otra instancia no puede interrumpir un motor que todavía lo tenga. Los intentos `running` huérfanos pasan a `stopped`, conservando historial y resultados previos. No se reencolan automáticamente.
- Un fallo por vídeo queda registrado y la ejecución puede continuar con el siguiente pendiente del lote. El fallo no inicia reintentos. Un fallo de base aborta la ejecución y requiere recuperación manual/arranque.
- Cambiar cola, adjuntar o enviar a papelera un vídeo en ejecución devuelve 409. Títulos y organización siguen disponibles con control de versión.

## Audio y modelos

- FFmpeg 7.1 distribuido con `imageio-ffmpeg 0.6.0`; no se instala infraestructura del sistema. Extracción de la primera pista de audio a WAV mono PCM16 a 16 kHz. Protocolos limitados a archivos locales y pipe.
- Adaptador `Transcriber`; implementación `FasterWhisperTranscriber`. Modelo **small, CPU int8, 4 hilos**, beam 5, VAD y sin condicionar al texto anterior. Selección inicial basada en [pruebas locales](../verification/phase2.md); no se declara modelo definitivo para todo contenido.
- Modelo en `models/small` bajo la raíz de datos fuera de OneDrive. Preparación explícita mediante `scripts/prepare-audio.ps1`. Revisión small fijada y SHA-256 registrado; una preparación repetida verifica y conserva esa versión. Inferencia offline, sin descarga automática.
- Se fija `av==16.0.1`: PyAV 19.0.2 instalado inicialmente resultó incompatible con `faster-whisper 1.2.1` (`metadata_errors`). El fallo se reprodujo con audio real y se resolvió antes de la entrega.
- No se instaló CUDA/cuDNN ni se evaluó GPU. CPU cumple el ensayo inicial con bajo consumo de memoria; optimizar GPU exige una comparación posterior. No se descargaron modelos de otras fases.
- Se verifica SHA-256 del vídeo antes de decodificar. Fuentes sin copia local quedan `unavailable`; no se intenta descargar el enlace. Con varias copias adjuntas se pide crear una fuente local del archivo elegido para evitar atribución arbitraria. Esto es una limitación explícita de esta entrega.
- `no_audio` distingue ausencia de pista; `no_speech` significa que el detector/modelo no devolvió voz, no prueba que no exista habla. No se generan segmentos ficticios. `speech` conserva idioma y tiempos.

## Datos y recuperación

`0003_audio` amplía estados de cola y añade motor, intentos, transcripciones y segmentos. El historial de intentos es separado de la fila de cola única por fuente. Reprocesar crea una nueva versión de transcripción; no reemplaza versiones anteriores. Cada intento solo puede tener una transcripción.

En lugar de una tabla de perfiles compartidos, cada transcripción conserva una instantánea de procedencia: proveedor y versión, CTranslate2, revisión/hash del modelo, configuración, versión de FFmpeg/pipeline, nombre original, activo, hash del vídeo y audio, y tiempo de proceso. La API solo añade/lee estas versiones. Evita perfiles mutables y no adelanta el catálogo de proveedores de Fase 3.

Después de aplicar `0003_audio`, la revisión de integridad motivó **otra migración**, `0004_audio_integrity`, que exige por FK compuesta que el activo pertenezca a la misma fuente que la transcripción. No se modificó la migración ya aplicada. Ambas se aplicaron con respaldo previo y conservando datos.

El WAV y resultado intermedio viven en `work/<attempt_uuid>`. Se retiran únicamente los dos archivos conocidos del intento al terminar/cancelar; un corte abrupto puede dejar temporales. No hay borrado recursivo ni limpieza automática por antigüedad. El vídeo original administrado permanece intacto. Límite de ejecución de 7200 segundos por defecto, configurable; no equivale a una duración máxima de vídeo validada.

## Verificación pendiente

Audio real, API, SQL, pausa/detención, exclusión y caída/reinicio se comprobaron. TypeScript/Vite compila. La herramienta Computer Use se detuvo al no poder verificar con suficiente confianza la URL del navegador en Windows; no se continuó automatizando la interfaz ni se sustituyó por un acceso alternativo para eludir esa restricción. Falta el recorrido visual de botones/transcripciones en escritorio y móvil. **No se declara cerrada la Fase 2** hasta esa comprobación.
