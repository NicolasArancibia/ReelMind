# 0009 — Comprensión audiovisual local

Fecha: 2026-10-31. Estado: inicio autorizado; evaluación en curso.

La Fase 3 conserva arquitectura y motor manual. Se evaluarán los candidatos del plan Qwen3-VL 4B (visión) y Qwen3 4B (síntesis), uno cargado a la vez. Ollama 0.40.13 ya está instalado; su consulta inició su aplicación existente, sin modelos instalados. No se modifica su configuración global.

ReelMind usará procesos propios de `ollama serve`, loopback 127.0.0.1:11435 y `OLLAMA_MODELS` bajo la raíz local de datos. Es un proveedor local necesario para esta fase, no un servicio remoto ni infraestructura de cola. Los procesos de inferencia deben quedar bajo la cancelación del trabajador. Preparación/descargas únicamente explícitas; abrir la app nunca descarga ni analiza.

El muestreo de fotogramas es cobertura parcial: cada evidencia registra tiempo y hash. El texto importado/OCR es dato no confiable y no activa herramientas. La síntesis deberá referenciar IDs de evidencias existentes; rechazar referencias inexistentes y respuestas incompletas. La revisión humana sigue siendo necesaria: validar la estructura no demuestra que una descripción sea verdadera.

Fuentes oficiales consultadas: [Qwen3-VL 4B](https://ollama.com/library/qwen3-vl:4b), [API de generación](https://docs.ollama.com/api/chat). API permite formato estructurado y `keep_alive: 0`; no implica garantía de fidelidad ni de encaje en VRAM.

## Ajuste tras inferencia real — 2026-11-01

Las etiquetas cortas resolvieron a Thinking: la visión agotó salida en razonamiento pese a `think:false`; texto declara únicamente `thinking.values=[true]`. Se descartó esa resolución como proveedor de esta ficha acotada. Se fijan explícitamente `qwen3-vl:4b-instruct-q4_K_M` y `qwen3:4b-instruct-2507-q4_K_M`, variantes de los mismos candidatos 4B, sin cambiar arquitectura ni transcriptor. Preparación comprueba capacidades y rechaza Thinking; disponibilidad exige el par explícito, no solo un manifiesto cualquiera. Pesos anteriores se conservan fuera de OneDrive; no se borran modelos del usuario.

La generación usa muestreo recomendado por las fichas oficiales, límite de salida 1536 y contexto 4096; no se aumenta indefinidamente para ocultar truncamientos. OCR elimina solo líneas exactamente duplicadas y registra cantidad/hash del texto original; eso no valida fidelidad. Los errores de etapa conservan diagnóstico local y evidencias intermedias fuera de Git, sin publicarlas como ficha ni reanudar automáticamente.

Fuentes: [etiquetas de visión](https://ollama.com/library/qwen3-vl/tags), [etiquetas de texto](https://ollama.com/library/qwen3/tags), [parámetros Qwen3-VL](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct), [generación Qwen3](https://huggingface.co/Qwen/Qwen3-4B).

## Síntesis extractiva inicial

La primera ficha completa conservó IDs existentes pero atribuyó una afirmación al fotograma equivocado. La validez estructural de una cita no prueba que la paráfrasis esté sustentada. El pipeline 2 cambia a selección extractiva: el modelo de texto elige hasta cuatro IDs de observaciones claras mediante un enum cerrado; la aplicación cita literalmente la observación de cada ID, sin permitirle generar otra afirmación. Las observaciones visuales siguen siendo automáticas y necesitan contraste humano. La versión experimental previa se conserva con aviso de revisión, sin reescribir historial.

Se conserva visión cargada dentro del mismo vídeo y se descarga explícitamente antes de texto; cierre o cancelación termina ambos mediante Job Object. La preparación usa la misma reserva PostgreSQL para su ensayo breve. Una capacidad genérica `thinking` sin configuración no basta para rechazar Instruct: se inspeccionan configuración y respuesta real; la inferencia rechaza razonamiento interno no solicitado. OCR con repetición corrupta de escapes se marca no recuperado, sin reconstruir texto supuesto.
