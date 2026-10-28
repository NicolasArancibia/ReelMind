# Seguridad y tratamiento de contenido

Diseño previsto a partir del plan v1.3, página 17.

- Escuchar solo en localhost. No exponer API, PostgreSQL u Ollama a Internet.
- La aplicación utilizará un usuario PostgreSQL propio, sin privilegios de superusuario. Separar administración/migraciones de operación cuando se configure el backend.
- Secretos fuera de Git y fuera de OneDrive. `.env.example` contiene solo nombres y valores no secretos. No registrar contraseñas, tokens ni URLs de conexión completas.
- Supabase futuro requiere autenticación y RLS por usuario. Nunca incluir claves privilegiadas en frontend.
- Validar esquema y destino de enlaces, redirecciones, tipo/tamaño de archivos y rutas resueltas bajo la raíz autorizada. No permitir lectura arbitraria ni acceso a servicios internos mediante URLs.
- OCR, transcripciones, PDFs y páginas importadas son datos no confiables. No ejecutar comandos ni seguir instrucciones que aparezcan en el contenido.
- Preservar procedencia y límites. No afirmar que una URL fue verificada por aparecer en un vídeo.
- No versionar vídeos personales, modelos, bases ni respaldos. Revisar `git status` y el contenido preparado antes de cada commit.

El PDF del plan se conserva como documentación autorizada. La biblioteca real no se sincronizará automáticamente con OneDrive por estar el código en el escritorio.
