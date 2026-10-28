# IA futura: candidatos y evaluación

Tomado del plan v1.3, página 7. No se han descargado ni probado modelos para ReelMind. Los tamaños del PDF son históricos y no equivalen a VRAM; verificar distribución y compatibilidad al instalar.

| Función | Candidato | Alternativas |
| --- | --- | --- |
| Texto y chat | Qwen3 4B mediante Ollama | Gemma 3 4B si mejora calidad o estabilidad |
| Visión | Qwen3-VL 4B | Qwen3-VL 2B; comparación con Gemma 3 4B |
| Audio | faster-whisper small | medium solo si se justifica; CPU cuantizada si GPU no es viable |
| Embeddings | nomic-embed-text | Alternativa multilingüe si recuperación en español es insuficiente |

Hardware informado por el plan: ASUS TUF Dash F15, i7-12650H, 16 GB de RAM y RTX 3060 Laptop con 6 GB de VRAM. El diagnóstico del 28-10-2026 confirmó RTX 3060 Laptop con 6144 MiB de VRAM y 15,6 GiB de RAM visible por Windows; en esa lectura había 5439 MiB de VRAM y 5,8 GiB de RAM disponibles. Las lecturas fueron consecutivas, no una medición simultánea ni un ensayo de IA. Revalidar antes de cada ensayo. El tamaño de descarga no incluye caché, contexto o imágenes.

## Protocolo futuro

Usar los mismos vídeos y preguntas: código, interfaz, texto pequeño, explicación hablada y contenido principalmente visual; añadir ruido, ausencia de audio y acceso incompleto. Registrar versión, cuantización, contexto, resolución y muestreo.

Medir tiempo por etapa/minuto, RAM/VRAM máximas, temporales, errores y liberación de memoria. Revisar transcripción en español, comandos literales, texto visual, herramientas, resúmenes y evidencias contra el original. Elegir el modelo más pequeño que cumpla calidad estable.

## pgvector en Windows

La [documentación oficial](https://github.com/pgvector/pgvector#windows), consultada el 28-10-2026, describe compilación nativa con las herramientas de C++ de Visual Studio y PostgreSQL. La viabilidad documental está establecida; compilación, instalación y consulta vectorial en este equipo siguen pendientes de su fase. No se instala Docker ni se cambia de base de datos para resolverlo anticipadamente.
