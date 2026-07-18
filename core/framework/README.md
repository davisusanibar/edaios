# EDAIOS Core 3.1.0 · baseline day-zero

Core materializa Foundation como kernel de contratos multi-iniciativa, sin
semántica institucional ni dependencia de un runtime consumidor.

## Superficie

- `edaios_core`: atomic IO, locks y lectura de KOs locales.
- `edaios_conformance`: schemas, profiles y attachments de iniciativa.
- `edaios_core_harness`: control plane, permisos y receipts v2.
- `edaios_ekg` / `edaios_query`: grafo local y federación explícita.
- `edaios_sdk_consumption`: lectura local/federada sin publicador.
- `edaios_supply_chain`: checksum, SBOM y provenance local verificable.
- `edaios_sdd_adapter`: frontera Adoptar-o-Adaptar para Spec Kit.
- `edaios_core.memory`: working memory, conflictos y sesiones sin autoridad.
- `edaios_sdk_consumption.derived_index`: búsqueda FTS5/fallback regenerable.
- `edaios_memory_adapter`: adapter Engram loopback opcional y degradable.

La superficie 3.1 está instalada en el baseline portable gobernado por
ADR-0013. `.specify/release.json` no declara candidato ni publicación. El
adapter Engram forma parte de Core; el runtime no se instala ni se vuelve
dependencia.

Core coordina y valida; no ejecuta runtimes consumidores, modelos, merges,
deploys o agentes remotos. La licencia MIT de este directorio no se extiende a
la raíz.

El export Foundation + Core conserva VERSION, lock, changelog, decisiones de
gobierno, Foundation, documentación, perfiles, templates y módulos Python. No
incluye `.git`, iniciativas, dominios ni runtimes consumidores.

## Perfiles

`core-release → initiative-adoption → federation` es una cadena acumulativa.
Cada hijo agrega controles. Las fixtures demuestran conformance local; no
demuestran que exista una iniciativa real o una operación productiva.
