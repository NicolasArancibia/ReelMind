# 0017 — Descarga dentro de la ejecución manual

Fecha: 2026-11-01. Autorizado tras preflight y «continúa».

Guardar un enlace no descarga ni analiza. Iniciar toma la cola actual y procesa secuencialmente cada fuente: si no tiene copia y es un reel público HTTPS de Instagram, intenta recuperarla; después ejecuta el análisis existente. Otros enlaces requieren adjuntar copia. No se usan cuentas, cookies de navegador, servicios de pago ni actualizaciones automáticas del descargador.

Adaptador yt-dlp 2026.10.26 fijado en requirements.in/lock e instalado solo en el entorno de ReelMind. Se consultó la [documentación oficial](https://github.com/yt-dlp/yt-dlp) y su [API de transporte](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/networking/_urllib.py). El adaptador de transporte es privado y queda cubierto por la versión fijada; debe revisarse al actualizar la dependencia.

La extracción/descarga vive en un proceso sin credenciales PostgreSQL y protegido por el Job Object existente. Comparte la reserva pesada del análisis/chat, límite de 180 segundos y tamaño máximo de importación. Solo descarga una variante MP4 HTTP(S) de vídeo, sin listas, directos, ejecutables o postprocesadores externos. Comprueba direcciones públicas en solicitudes y redirecciones; conserva cabeceras y cookies anónimas de esa sesión para interoperar con Instagram. No carga cookies de cuentas.

La copia se valida por tamaño/cabecera/hash, se publica en el almacén inmutable y se asocia al enlace original antes del análisis. Transacción y reserva por hash reutilizan bytes entre fuentes. Un reintento con copia asociada no vuelve a descargar. Detener mata el proceso; si la copia ya se confirmó, permanece. Tras caída de API, la recuperación existente detiene trabajos y nunca los reanuda sola. Los temporales de descarga incompleta permanecen bajo work/UUID/download para revisión, sin purga automática ni reanudación de bytes parciales.

Se conservan los estados de trabajos y el esquema 0010; no requiere migración. Errores recuperables por elemento no detienen los demás. La procedencia de la descarga se añade a la transcripción cuando termina el análisis; origen y asociación permanecen aun si este falla. Chat sigue requiriendo Actualizar índice manualmente. [Verificación](../verification/downloads.md).
