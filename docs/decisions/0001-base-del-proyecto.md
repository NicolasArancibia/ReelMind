# ADR 0001: preparación y arquitectura base

Fecha: 2026-10-28. Estado: decisiones del plan conservadas; detalles operativos documentados para implementación.

## Contexto

El usuario aportó el Plan Maestro v1.3 y confirmó la carpeta ReelMind del escritorio. Pidió terminar documentación, Git y herramientas antes de empezar la aplicación. La carpeta contenía únicamente el PDF.

## Decisión

- Conservar el PDF original en `docs/referencias/`, sin editar su contenido.
- Mantener React/Vite/Tailwind, FastAPI, PostgreSQL local y SQLAlchemy/Alembic.
- Mantener Supabase solo para pendientes en Fase 4 y la IA local para fases posteriores.
- Separar la preparación actual (0A) del arranque mínimo de aplicación (0B). Esto no elimina requisitos del PDF ni declara cerrada toda la Fase 0.
- Seleccionar Python 3.13 para el proyecto, conservando Python 3.14 del usuario. Mantener Node 24 LTS ya instalado.
- Conservar la carpeta del código en OneDrive, pero instalar y almacenar PostgreSQL y credenciales fuera de ella.
- Crear solo repositorio local. No publicar, añadir servicios pagos ni descargar modelos.

## Consecuencias

El siguiente chat puede continuar leyendo documentos versionados. La documentación distingue diseño de implementación y evidencia local de información histórica. Antes de Fase 0B se verifican herramientas; al crear la aplicación se fijarán dependencias y archivos de bloqueo tras comprobar compatibilidad real.
