# Modelos: audio evaluado y candidatos futuros

Tomado del plan v1.3, página 7. Fase 2 descargó y probó faster-whisper small; Fase 3 tiene variantes Instruct 4B y verificación inicial aceptada. Fase 5 preparó BGE-M3 y reutiliza texto Instruct para selección de citas; evaluación inicial español/inglés comprobada. Modelos provisionales: [Fase 3](verification/phase3.md) y [Fase 5](verification/phase5.md). Los tamaños del PDF son históricos y no equivalen a VRAM.

| Función | Candidato | Alternativas |
| --- | --- | --- |
| Texto y chat | Qwen3 4B mediante Ollama | Gemma 3 4B si mejora calidad o estabilidad |
| Visión | Qwen3-VL 4B | Qwen3-VL 2B; comparación con Gemma 3 4B |
| Audio, implementado | faster-whisper small, CPU int8, 4 hilos | GPU/medium y otros tamaños no evaluados; no se consideran definitivos |
| Embeddings, implementado | BGE-M3 567M, 1024 dimensiones, normalización L2 | Alternativa multilingüe prevista al candidato nomic; sin comparativa ni evaluación general |

Hardware informado por el plan: ASUS TUF Dash F15, i7-12650H, 16 GB de RAM y RTX 3060 Laptop con 6 GB de VRAM. El diagnóstico del 28-10-2026 confirmó RTX 3060 Laptop con 6144 MiB de VRAM y 15,6 GiB de RAM visible por Windows; en esa lectura había 5439 MiB de VRAM y 5,8 GiB de RAM disponibles. Las lecturas fueron consecutivas, no una medición simultánea ni un ensayo de IA. Revalidar antes de cada ensayo. El tamaño de descarga no incluye caché, contexto o imágenes.

## Protocolo futuro

Usar los mismos vídeos y preguntas: código, interfaz, texto pequeño, explicación hablada y contenido principalmente visual; añadir ruido, ausencia de audio y acceso incompleto. Registrar versión, cuantización, contexto, resolución y muestreo.

Medir tiempo por etapa/minuto, RAM/VRAM máximas, temporales, errores y liberación de memoria. Revisar transcripción en español, comandos literales, texto visual, herramientas, resúmenes y evidencias contra el original. Elegir el modelo más pequeño que cumpla calidad estable.

## pgvector en Windows

La [documentación oficial](https://github.com/pgvector/pgvector#windows) describe compilación nativa con C++ de Visual Studio y PostgreSQL. El 2026-11-01 se compiló e instaló v0.8.7 con las herramientas existentes, extensión habilitada en ReelMind y consulta real por coseno comprobada. Preparación explícita, sin Docker ni cambio de base. Perfil BGE-M3 y texto por digest en `models/search.json` externo; cambiar modelo exige preparación e indexación manual del nuevo perfil.

## Selección inicial de audio, 2026-10-30

Small CPU int8, beam 5 y VAD: seis muestras humanas chilenas, 33,109 s de audio en 30,441 s totales, pico RSS muestreado 632,2 MiB. WER simple 2/57, una diferencia numérica. Silencio/tono sin texto; ausencia de pista reconocida. [Método, versiones, hashes y límites](verification/phase2.md).

Se elige esta configuración inicial porque funciona en Python 3.13 con el equipo disponible y evita instalar CUDA/cuDNN. No es una comparación contra GPU ni prueba de superioridad de small frente a otros tamaños. Modelo intercambiable mediante adaptador; no se evaluaron ruido, música, vídeos largos ni habla superpuesta. Revisión fijada por el script de preparación, inferencia offline y liberación entre trabajos. No descargar anticipadamente los modelos de fases posteriores.

## Chat explicativo con evidencia — 2026-11-01

Se conserva el modelo local de texto Instruct ya preparado; no se cambia el modelo de audio. El nuevo modo explicativo redacta en español con hasta cuatro afirmaciones, cada una vinculada a una cita literal exacta y un fragmento permitido. Rechaza números nuevos y somete el resultado a una verificación adicional del mismo modelo. Si falla la validación, devuelve selección extractiva. Un saludo o petición de ayuda de uso no ejecuta modelos. Los apuntes personales se identifican como origen humano en recuperación.

La verificación automática puede equivocarse: no certifica veracidad ni permite completar datos ausentes. Caso real de Figma/Notion respondió con cita e instante correctos; una pregunta de receta inexistente devolvió falta de evidencia. No se hizo benchmark/comparación ni una evaluación general de calidad. [Evidencias y límites](verification/product1.md).

## Resumen general de una fuente seleccionada — aceptación 2026-11-01

Las peticiones generales de resumen/temas, con exactamente una fuente elegida, no usan similitud como criterio de inclusión: no contienen necesariamente las palabras del vídeo. Se toman hasta ocho fragmentos indexados vigentes distribuidos por tiempo en esa fuente, con los mismos filtros de papelera/proyecto/perfil/versiones. Se informa número muestreado/disponible y que el contexto/respuesta puede usar solo parte. No se presenta como cobertura completa ni se asigna una puntuación semántica al muestreo. Las preguntas concretas conservan recuperación semántica y rechazo por falta de evidencia; la generación mantiene citas exactas/verificación y fallback extractivo. No se cambia ni descarga ningún modelo.
