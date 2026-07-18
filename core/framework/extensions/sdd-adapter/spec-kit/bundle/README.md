# EDAIOS Core Governed Delivery Bundle

Bundle Spec Kit 0.12.11 que registra como una unidad el preset de Foundation,
la extensión de gobierno y el workflow de delivery agnóstico de EDAIOS Core.
Requiere un workspace preparado por una iniciativa; no lo adopta, no aporta su
autoridad y no reemplaza sus ledgers.

## Desarrollo local

Desde un proyecto inicializado con Spec Kit, instalar primero las primitivas
locales y despues el bundle:

```bash
specify preset add --dev /ruta/a/spec-kit/preset --priority 5
specify extension add /ruta/a/spec-kit/extension --dev --priority 5
specify workflow add /ruta/a/spec-kit/workflow/edaios-delivery.yml
specify bundle install /ruta/a/spec-kit/bundle --offline
```

En distribucion, los tres componentes deben publicarse en los catalogos activos
antes de publicar el ZIP del bundle. El bundle fija sus versiones y no sustituye
el mecanismo nativo de distribucion de cada primitiva.

La fuente normativa sigue siendo `core/foundation/`; este paquete solo distribuye su
proyeccion operativa y las puertas de delivery aprobadas por ADR-0003.
