# 0012 — Chat independiente e inicio de proyectos

2026-11-01. Solicitud del usuario: sustituir el salto a una sección por una vista propia con interacción de chat; después avanzar al siguiente punto.

Navegación local por hash para Biblioteca, Chat y Proyectos, sin nueva dependencia. Chat mantiene su estado al cambiar de vista: historial lateral, nuevo chat, mensajes usuario/asistente, editor al pie, Enter para enviar y Mayús+Enter para nueva línea. Mantiene citas, reserva pesada y contexto acotado de Fase 5. Cambia la interacción; no se presenta como asistente general ni se habilita generación libre o herramientas externas. El límite extractivo sigue vigente.

Fase 6 iniciada por proyectos y asociaciones manuales. Migración aditiva `0007_projects`, respaldo previo; FK RESTRICT y clave compuesta impiden duplicados y referencias huérfanas. Quitar del proyecto solo retira la asociación. Papelera oculta fuentes, conserva asociaciones y restaurar las recupera. No añade inferencia ni cambia modelos.

Pendientes de Fase 6: grafo Cytoscape.js, vínculos con evidencia y correcciones versionadas, consultas por proyecto y selección paginada de fuentes (interfaz inicial muestra 100). No se declara cerrada la fase. La documentación oficial de [Cytoscape.js](https://js.cytoscape.org/) se consultó para el próximo bloque; no se instaló todavía.
