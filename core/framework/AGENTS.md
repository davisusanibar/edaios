# AGENTS — Core

Foundation manda. Mantén Core agnóstico de consumidores, negocio, proveedor y red.
Nuevas APIs públicas requieren spec, tests y ADR cuando cambian la frontera.
Desde `core/framework/`, ejecuta `python3 -m unittest discover -s tests -v` y el
wheel smoke antes de promover cambios. El export conserva el layout canónico
`core/foundation` y `core/framework`; no inventes aliases de autoridad.
