# Registro de fuentes

| Claim | Fuente | Fecha | Alcance | Rótulo |
|---|---|---|---|---|
| Core Base instala un único módulo y ningún consumer | `README.md`; `repositories.json` | 2026-07-15 | baseline local | Evidencia interna |
| El registry declara doce harnesses, nueve `contracted` y tres `enforced` | `core/framework/modules/harness-core/src/edaios_core_harness/resources/harness-registry.json` | 2026-07-15 | Core Base 1.0.0 | Evidencia interna |
| El KOM declara once reglas normativas | `core/foundation/model/KNOWLEDGE_OBJECT_MODEL.md` | 2026-07-15 | Foundation vigente | Fuente normativa |
| Provenance identifica artefacto, builder, proceso e inputs | `https://slsa.dev/spec/v1.2/provenance` | 2026-07-15 | referencia de supply chain; no certificación | Benchmark externo verificado |
| Perfiles permiten especializar un Core por tecnología, uso o sector | `https://www.nist.gov/itl/ai-risk-management-framework` | 2026-07-15 | analogía de diseño; no adopción normativa | Referencia externa verificada |
| Convenciones semánticas habilitan nombres comunes de telemetría | `https://opentelemetry.io/docs/specs/semconv/` | 2026-07-15 | referencia de interoperabilidad | Referencia externa verificada |

No se declaran baseline de adopción, targets de negocio ni métricas de
producción. Los conteos internos se derivan del estado versionado indicado.
