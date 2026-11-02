# Descarga manual — 2026-11-01

## Resultado comprobado

17 casos dirigidos distintos aprobados: cuatro pruebas iniciales del adaptador/integración más doce del trabajador existente; después un caso adicional de conservación de copia y hash compartido. Ese último caso se corrigió para consultar el contrato real de la API y la fila física en base. Build TypeScript/Vite, compilación Python y pip check aprobados. No se repitió la suite completa ni análisis ya aprobados.

La prueba real inicial detectó un fallo del transporte: no conservaba las cabeceras HTTP de yt-dlp. Se comprobó extracción estándar y se corrigió el adaptador para compartir cabeceras y cookies anónimas de sesión. No se accedió a credenciales/cookies del navegador. Diagnóstico persistido acotado a códigos/funciones, sin mensajes ni URLs firmadas.

Un reel público ya guardado, fuente `353e9182-e27e-407e-a511-54da3ab252bc`, se descargó con el adaptador: MP4, 2.199.499 bytes. Después se verificó el trabajador real para **solo esa fuente**, manteniendo la reserva pesada y sin tomar el resto de pendientes: copia asociada, trabajo completed y transcripción v1 de 25.195 ms con ocho segmentos. Procedencia: yt-dlp 2026.10.26. Datos leídos nuevamente por API; enlace original conservado. La prueba real usó audio; el recorrido audiovisual reutiliza el trabajador existente, sin repetir visión en esta comprobación.

Cancelación durante descarga, exclusión entre ejecuciones, continuidad tras error y reutilización de copia al reintentar se verificaron con descargas controladas en esquemas aislados. Otro caso comprobó que detener el análisis conserva la copia y que dos fuentes con el mismo contenido usan una sola fila física. No se prueba aquí la fidelidad humana de los ocho segmentos ni se declara aceptación final de 1.0.

## Límites

Solo reels públicos HTTPS de Instagram con variante MP4 recuperable. No descarga garantizada de todos los enlaces: Instagram puede limitar solicitudes, cambiar el acceso o exigir cuenta. Sin acceso privado ni elusión: se conserva el error y se ofrece reintentar/adjuntar copia. Otros proveedores, formatos separados/HLS, listas y directos quedan fuera de esta entrega. Límite de tres minutos por descarga y tamaño máximo de importación; pueden quedar temporales propios para revisión. No se reanudan descargas parciales automáticamente.

Iniciar mantiene su instantánea de cola; Pausar termina el vídeo actual y Detener cancela el actual. La copia confirmada se conserva; ningún resultado audiovisual incompleto sustituye versiones anteriores. El índice de Chat se actualiza por orden separada. No se ejecutó toda la colección del usuario durante las pruebas.
