# 0015 — Plan de cierre según el uso completo de ReelMind

2026-11-01. Estado: propuesta documentada tras revisión de producto; implementación no iniciada.

El usuario solicita revisar funcionalidades y planificar lo necesario para terminar. Aclara que quiere las tres cosas: reunir sus reels, saber de qué son y guardar lo importante, organizarlos/categorizarlos/conectarlos y conversar con ese contenido. El objetivo es el recorrido completo de biblioteca de conocimiento personal, no solamente un contenedor de vídeos o un chat.

Las fases 0–7 conservan sus evidencias y límites técnicos. Su cierre inicial no implica que la experiencia de producto cubra ya todo ese objetivo. La revisión encontró funciones ausentes y un fallo de navegación reproducible; no se reabren ni repiten por rutina los ensayos anteriores.

Se propone continuar en el roadmap existente: estabilizar navegación/versionado; captura e identificación de reels; ficha con reproducción y apuntes/destacados; recuperación/chat fundamentado; organización/conexiones; operación de escritorio; aceptación final del recorrido completo. Las funciones se implementarán por bloques con resultado observable y pruebas de riesgo acotadas, sin fechas ni porcentajes de completitud inventados.

Separar siempre contenido original, observación automática, cita y nota humana. La síntesis conversacional en español será una ampliación evaluada con evidencia, no una sustitución silenciosa del modo extractivo ni autorización para inventar afirmaciones. Categorías y conexiones sugeridas requerirán revisión; no se descargarán otros modelos ni harán comparativas por iniciativa de esta revisión.

Mantener PostgreSQL local, arquitectura actual, reserva pesada única y análisis/indexación manuales. Móvil, Supabase, equipos/cuentas multiusuario, servicios pagados, agentes autónomos y sincronización quedan fuera. Recuperación de enlaces únicamente cuando sea viable y permitida; conservar alternativa de copia local y mensajes claros cuando falte acceso. Empaquetado nativo se decidirá antes de implementarlo; esta propuesta no instala ni modifica infraestructura.

El inventario, los hallazgos, el orden y las condiciones de cierre están en [el único plan vigente](../roadmap.md#plan-de-cierre-del-producto-10). No se crearon planes de implementación paralelos ni se cambiaron datos/modelos/producto durante esta revisión.
