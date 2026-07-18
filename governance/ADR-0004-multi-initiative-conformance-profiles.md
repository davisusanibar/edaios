# ADR-0004 — Core como kernel y perfiles de conformidad acumulativos

**Estado:** Aceptado
**Fecha:** 2026-07-15
**Owner:** Principal Architect
**Deriva de:** RFC-0001

## Contexto

Los gates de Core Base fijan exactamente un módulo y ausencia de consumers. Esa
certificación debe permanecer reproducible, pero no puede ser también el
contrato de adopción de todas las iniciativas.

## Decisión

Core es un kernel de contratos, no un catálogo de runtimes. La conformidad se
divide en perfiles acumulativos:

- `core-release`: certifica Foundation, contratos públicos y distribución;
- `initiative-adoption`: hereda Core y valida el attachment de una iniciativa;
- `federation`: hereda adopción y valida mounts, namespaces y colisiones.

Los perfiles se resuelven desde una fuente versionada y solo pueden agregar
controles. Templates, catálogos y gates derivan de schemas comunes. Una
iniciativa nunca se instala dentro de Core por copiar una fixture.

## Alternativas

- debilitar los gates del baseline: rechazada porque vuelve ambiguo qué release
  está certificado;
- introducir un módulo por tecnología: rechazado por acoplamiento;
- mantener revisión manual: rechazada por deriva y falta de reproducibilidad.

## Consecuencias

Core puede crecer sin conocer Flink, Spark, IA o una institución. Cada iniciativa
declara un manifest y ejecuta conformance contra una versión/digest de Core.
Los gates de conteo fijo se sustituyen por validación de perfiles y schemas.

## Evidencia y frontera del claim

Contract tests y fixtures locales prueban resolución e herencia de perfiles. No
prueban adopción organizacional, operación remota ni producción.

## Aprobación

Principal Architect · 2026-07-15 · instrucción humana de implementar todos los
cambios recomendados y publicar el branch después de gates verdes.
