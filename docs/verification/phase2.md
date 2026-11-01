# Verificación de Fase 2

Fecha: 2026-10-30, America/Santiago.

**Fase 2 completada y verificada; cierre visual realizado el 2026-10-31.** Las pruebas de audio/API/PostgreSQL siguientes conservan su fecha original. [Decisión y límites](../decisions/0006-audio-motor-manual.md).

## Pruebas automatizadas

Suite de **69 pruebas aprobadas** sobre Python 3.13.15 y esquemas PostgreSQL aislados: regresiones de Fase 1 y pruebas de motor manual. Cubre versiones y persistencia de transcripciones; pausa al terminar el actual; cancelación sin resultado parcial; ausencia de reintentos automáticos; inicios concurrentes con un único ganador; reserva comprobada desde otro proceso Python; recuperación sin afectar otro propietario; nuevas importaciones/restauraciones fuera del lote en ejecución; fallos recuperables; enlaces no disponibles; intervalos y commit atómico; FK de procedencia; terminación de descendientes Windows y caída real del supervisor.

El primer intento de pytest dentro del sandbox no pudo crear su directorio temporal; no fueron fallos de aplicación. Se repitió con acceso autorizado. `alembic check` sin diferencias después de ambas migraciones. TypeScript/Vite compila.

Reproducción adicional: `setup.ps1` ejecutado con dependencias fijadas, manifiesto runtime idéntico por SHA-256 antes/después, `pip check` sin incompatibilidades y `prepare-audio.ps1` reutilizando/verificando el modelo sin actualizarlo. Arranque final con esquema `0004_audio_integrity`, modelo disponible y motor detenido. API/interfaz escuchando en 127.0.0.1; PostgreSQL en 127.0.0.1/::1. Enlaces locales de documentación válidos y PDF/migraciones previas sin cambios.

## Audio real y rendimiento

Modelo small, `faster-whisper 1.2.1`, CTranslate2 4.8.4, PyAV 16.0.1, CPU int8, 4 hilos, beam 5, VAD. FFmpeg `7.1-essentials_build-www.gyan.dev` incluido en `imageio-ffmpeg 0.6.0`. Modelo `Systran/faster-whisper-small`, revisión `536b0662742c02347bc0e980a01041f333bce120`, SHA-256 del modelo `3e305921506d8872816023e4c273e75d2419fb89b24da97b4fe7bce14170d671`.

Corpus: primeras tres filas de cada subconjunto female/male de [Google Chilean Spanish, versión de Hugging Face](https://huggingface.co/datasets/ylacombe/google-chilean-spanish), voces humanas y texto de referencia, licencia CC BY-SA 4.0, reestructurado desde OpenSLR. Revisión de datos observada `082619e99a37715ab8db45b0bc8188ba98a80130`. Se generaron MP4 de imagen negra con ese audio para ejercitar extracción real. No son vídeos personales ni una evaluación amplia de reels.

| Caso | Audio s | Tiempo total s | Pico RSS muestreado MiB | Resultado |
| --- | ---: | ---: | ---: | --- |
| female-0 | 6,144 | 7,780 | 562,4 | Voz; 1 diferencia de representación numérica |
| female-1 | 4,864 | 4,433 | 563,4 | Voz; 0 diferencias léxicas |
| female-2 | 6,741 | 4,434 | 560,8 | Voz; 0 diferencias léxicas |
| male-0 | 6,485 | 4,222 | 562,0 | Voz; 0 diferencias léxicas |
| male-1 | 5,035 | 5,125 | 604,0 | Voz; 1 diferencia léxica |
| male-2 | 3,840 | 4,447 | 632,2 | Voz; 0 diferencias léxicas |
| Silencio | 8 | 2,953 | 555,8 | `no_speech`, cero segmentos |
| Tono 440 Hz | 8 | 2,966 | 594,3 | `no_speech`, cero segmentos |
| Sin pista | 3 | 0,667 | 40,5 | `no_audio`, cero segmentos |

Las seis muestras suman 33,109 s de audio y 30,441 s de tiempo total: aproximadamente 0,92 s por segundo de audio, incluyendo arranque/carga del modelo en cada vídeo. No extrapolar a vídeos largos. WER simple con minúsculas y puntuación eliminada: 2/57 palabras, 3,51%; una diferencia es «ocho» → «8». No normaliza números ni equivale a una revisión humana exhaustiva. Los tiempos de segmentos son positivos, ordenados y conservados por la API.

RSS suma procesos descendientes observados cada ~200 ms; puede omitir picos entre lecturas. No es RAM total del equipo. No se probó inferencia GPU ni se mide aquí su VRAM. La configuración CPU es deliberada y no requiere CUDA/cuDNN. Cancelación real durante trabajo: 1,021 s desde el inicio del ensayo (se pidió al superar 1 s), sin descendientes restantes.

Reproducción: configurar `REELMIND_DATA_ROOT`, usar el Python 3.13 del runtime y ejecutar `backend/evaluate_audio.py` desde backend, con configuración de conexión válida (el ensayo no consulta PostgreSQL). Descarga solo seis muestras públicas cuando faltan. Reporte completo: `verification-phase2/report-small.json` dentro de la raíz de datos; medios y referencias fuera de Git/OneDrive. `prepare-audio.ps1` prepara el modelo por una acción explícita.

## API real, persistencia y caída

La biblioteca estaba vacía antes del ensayo. Se crearon cuatro fuentes de vídeo identificadas y un enlace de prueba sin archivo, usando los endpoints reales a través de `127.0.0.1:5180/api`.

1. Importar dejó el motor detenido. Iniciar y Pausar terminó solo el vídeo actual, conservando cuatro pendientes.
2. Reanudar y Detener canceló el segundo vídeo; quedó `stopped`, sin transcripción parcial.
3. Encolar e Iniciar procesó manualmente el resto: dos resultados de voz, silencio, ausencia de pista y enlace `unavailable`. Sin versiones duplicadas.
4. Se guardó una instantánea de IDs, versiones, segmentos y procedencia. Se reencoló un vídeo ya transcrito y se cerró forzosamente la API propia durante su ejecución.
5. Tras reiniciar frontend/API, motor `stopped`, intento interrumpido `stopped` y todas las transcripciones anteriores idénticas. No se reinició Windows ni el servicio PostgreSQL en este ensayo.

Copias previas a migraciones: `before-migration-20261030-154312-187.dump` y `before-migration-20261030-154914-920.dump`, en el directorio de respaldos del runtime. `0001_sources`, `0002_library` y la ya aplicada `0003_audio` se conservaron intactas; la garantía adicional vive en `0004_audio_integrity`.

Los cinco registros de prueba, sus cuatro copias no compartidas y temporales por intento se retiraron tras verificar IDs, metadatos, hashes y ausencia de otras referencias. Se conservaron informes y muestras públicas fuera del repositorio.

## Cierre visual — 2026-10-31

Navegador integrado conectado a `http://127.0.0.1:5180/`, URL e interfaz observadas directamente. La aplicación estaba apagada; el inicio dentro del entorno restringido falló sin registro de API. El mismo script habitual con ejecución ampliada autorizada inició correctamente, sin modificar credenciales, código ni configuración. Conexión local activa y motor detenido al abrir.

- Biblioteca inicialmente vacía. Importada la muestra pública existente `female-0.mp4`, sin descargas ni activación automática. Se conserva como muestra de esta comprobación en la biblioteca local.
- Iniciar → Transcribiendo; Pausar → Pausando al terminar → En pausa. El vídeo terminó y generó Versión 1, con idioma `es`, duración 0:06, modelo small/faster-whisper 1.2.1 CPU int8 y segmento 0:00–0:03.
- Encolar con confirmación dejó el motor en pausa; Reanudar lo activó explícitamente. Detener → Deteniendo → Detenido; fuente Interrumpido con instrucciones para reintentar. La consulta posterior conservó únicamente Versión 1 y el mismo segmento, sin versión parcial nueva.
- Inspección visual de controles y transcripciones en escritorio y viewport móvil 390 × 844. Botones y texto legibles, cuadro de segmentos dentro del ancho disponible. Es una comprobación responsive en navegador de escritorio, no un teléfono físico. Tamaño normal restaurado al finalizar.
- Evidencias: [escritorio](phase2-desktop.png) y [móvil](phase2-mobile.png). Aplicación disponible al entregar, motor detenido y cero pendientes. No se repitió la suite de 69 pruebas ni se inició Fase 3.

## Límites

- El bloqueo anterior de Computer Use Windows al determinar la URL quedó resuelto para este recorrido usando el navegador integrado; no se afirma haber reparado el controlador Windows. No hubo cambios de producto en esta revisión.
- No se ha comparado calidad con una colección amplia de vídeos, música, ruido o varios hablantes. No hay diarización, interpretación visual, descarga de enlaces ni elección de pista/activo desde UI.
- Pausa por vídeo; detener no conserva progreso parcial dentro de un vídeo. El modelo se vuelve a cargar por trabajo. Se conserva historial completo confirmado.
- Fallos de base y límites de tiempo tienen rutas de cancelación; no se ensayó corte eléctrico, agotamiento real del disco, un vídeo de 2 GiB ni restauración integral de respaldos.
- La evaluación no convierte `no_speech` en certeza de ausencia de voz; la interfaz lo indica. No se declara listo ningún módulo de fases posteriores.
