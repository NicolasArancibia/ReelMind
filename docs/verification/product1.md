# Producto de escritorio ampliado — comprobaciones

Fecha: 2026-11-01. Plan 8–14 autorizado. Implementación funcional integrada; aceptación personal de 1.0 pendiente.

## Evidencias técnicas

- Punto de recuperación Git local antes de ampliar el producto; sin publicación. Migraciones `0009_personal_library` y `0010_idea_connections` aplicadas con respaldos previos. Alembic Check sin diferencias.
- 25 pruebas dirigidas aprobadas: apuntes/versiones/citas cruzadas, archivo y búsquedas, conflicto optimista, índice/perfiles, recuperación/cancelación/reserva pesada, proyectos/grafo, lotes/taxonomía, exportación y limpieza/configuración. Después se añadieron dos comprobaciones aprobadas de reanudación por lotes y alcance actual de proyectos (27 casos distintos). No se presenta como una nueva ejecución de toda la suite histórica.
- Caso de indexación de 130 fragmentos con inferencia simulada: primero se confirman 128, se interrumpe el segundo lote y quedan dos pendientes; nuevo inicio procesa únicamente esos dos. Nunca se reanuda al abrir.
- Compilación TypeScript/Vite aprobada. Python compila e incluye Tkinter sin instalar dependencias nuevas.

## Recorrido real en este equipo

- Conversación existente → Guardar destacado → ficha: se conserva la cita visual exacta de Figma/Notion, comentario identificado como ensayo de aceptación y revisiones. El reproductor abrió en 37,167 segundos sobre duración 59,433; lectura del elemento confirmó reproducción disponible.
- Foco de ficha en Cerrar; Escape desde Mis ideas devuelve el foco al botón de apertura, comprobado en interfaz.
- Referencia `[v5]` dentro de la ficha y cierre mantienen `#chat` y la conversación. El índice reconoce el nuevo apunte pendiente: de ocho a nueve fragmentos, actualización manual real 9/9 sin reprocesar vídeos.
- Pregunta real «¿Qué tarea se muestra con Figma y Notion? Explícalo en español y cita el momento»: respuesta local completada, en español, describe redactar copy de lanzamiento y resumir resultados para el equipo; indica 0:37 y mantiene cita exacta y versión. Fue contrastada con la evidencia visual ya revisada. No demuestra calidad general de resumen/comparación en otras colecciones.
- Pregunta real sobre gramos de harina/minutos de horno sin receta en las fuentes: terminó sin citas y mostró evidencia insuficiente, conservando el historial.
- Ventana de mantenimiento abierta y revisada visualmente. Copia creada desde su selector de carpeta: `library-20261101T100038Z-969d1a85`, 23 tablas y dos medios. Detuvo/reabrió los servicios y conservó el motor detenido.
- Restauración de esa copia en `reelmind_restore_e272b00fb79e4b999a89645e7eaaabbd`, raíz aislada bajo recovery. Huellas exactas de las 23 tablas y checksums de los dos medios coinciden, incluidos apuntes e historial.
- Se activó temporalmente la copia mediante la misma función de configuración que usa la ventana: inicio y API de recuperación correctos, dos fuentes, dos rangos de medios, dos conversaciones y un proyecto. Lecturas de notas/exportación/diagnóstico aprobadas. Se volvió a la configuración original y se conservaron ambas bases y las configuraciones anteriores.
- Origen externo para escritura y Host no permitido siguen bloqueados. API/frontend en loopback. Ningún modelo se descargó ni se inició análisis por abrir/reiniciar.

## Límites y aceptación pendiente

Solo hay dos vídeos de referencia, uno personal sin pista de audio y una muestra pública hablada. Falta la aceptación del usuario con una colección más representativa para resumen, comparación, falta de evidencia, idioma y utilidad cotidiana. No se afirma evaluación general de calidad, rendimiento a miles de vídeos, accesibilidad certificada o compatibilidad con todos los formatos.

La recuperación se ensayó en este Windows con las dependencias existentes; no es una instalación desde cero en otra máquina. La ventana de copia y el cambio de configuración fueron comprobados; no se recorrieron todas las combinaciones de diálogos de Windows. El respaldo permanece en el mismo disco; el usuario debe elegir otro destino para protegerse frente a fallo de disco. No hay retención automática ni copias cifradas.

Los enlaces solos no se descargan; pueden adjuntarse copias. Las sugerencias se revisan antes de guardar; no hay clasificación o conexiones automáticas. La reproducción usa el navegador y tiempos de fuentes con una única copia; archivos no compatibles pueden abrirse externamente. Móvil/Supabase siguen aplazados.

## Aceptación dirigida posterior

2026-11-01, tras autorización «continúa». Sin repetir respaldo/restauración ni suite histórica aprobada.

- Arranque desde app cerrada: health ok, esquema 0010, motor detenido e índice sin pendientes. Durante la revisión el usuario añadió enlaces a su biblioteca; no se descargaron ni analizaron automáticamente. La copia de vídeo personal disponible en VideoPrueba sigue siendo la ya revisada; el usuario indicó que añadirá más reels.
- Fallo reproducido: pregunta general de resumen, limitada al reel personal, terminó con cero hits aunque había evidencia. Causa: se aplicaba el umbral semántico de preguntas concretas. Otro fallo reproducido: al recargar la misma conversación, Fuente volvía a Todas, pese a que el backend había guardado un source_id concreto.
- Corrección: peticiones generales de resumen/temas con exactamente una fuente seleccionada usan hasta ocho fragmentos vigentes en orden temporal. Mantienen filtros de proyecto/papelera/perfil y citas/verificación. Muestra y total se comunican en pantalla, copia y exportación; no es cobertura completa. Preguntas concretas mantienen el umbral existente. Historial restaura última fuente/modo y bloquea envío durante carga; saludo/cancelación conservan metadatos de alcance. Reabrir el chat ya seleccionado no vacía los mensajes.
- Cuatro pruebas dirigidas aprobadas (dos nuevas y dos regresiones pertinentes): muestra acotada/perfil/fuente, cancelación conservando alcance, proyecto y falta de evidencia en preguntas concretas. Una se repitió tras añadir comprobación de aviso exportado/saludo; no se cuentan ejecuciones repetidas como casos nuevos. Build aprobado.
- Caso real corregido: recuperó ocho de ocho fragmentos disponibles del reel. La explicación no pasó la validación; fallback conservó cuatro citas sobre marcas visibles, panel de ventas, mensaje de Muse y tarea Figma/Notion. Esto verifica recuperación/fallback, **no acredita un resumen explicativo satisfactorio**. Se conserva el resultado fallido inicial para trazabilidad.
- Recarga real después de saludo: source_id original y modo extractive se conservaron; después se devolvió el modo habitual grounded mediante ayuda local, sin nueva inferencia. Copia por botón y exportación real incluyen aviso 8/8, cobertura parcial y fuente. Conversación propia de ensayo identificada como «Ensayo de aceptación: resumen y alcance»; no se editaron chats previos del usuario.

Pendiente: archivos nuevos en VideoPrueba para revisar variedad, resumen y comparación con fuentes representativas; revisión humana del usuario. No se declara 1.0 aceptada. Los enlaces de Instagram por sí solos no aportan audio/fotogramas: adjuntar sus copias locales. No se cambiaron modelos ni esquema y no se descargaron pesos.
