# Arquitectura del programa

```text
core/foundation                 autoridad normativa
       ↓
core/framework                  kernel, schemas, perfiles, harnesses y gates

Git → manifest/spec → código → gates → evidence receipt → aprobación humana
                                      ↓
                 baseline ── candidato explícito ── sello Git observado
```

Invariantes:

- Foundation gobierna y Core materializa; la dependencia nunca se invierte.
- No hay iniciativas ni consumers instalados.
- Una iniciativa entra por attachment, contrato público, spec, decisión y
  evidencia gobernada; su implementación permanece fuera de Core.
- Los perfiles heredan `core-release → initiative-adoption → federation` sin
  retirar controles.
- Federación e índice son vistas derivadas de mounts explícitos y namespaced.
- Un release se construye de forma reproducible y separa evidencia técnica,
  aprobación humana y cutover Git.
- El baseline day-zero es estado instalado, no un candidato ni una release;
  `.specify/release.json` mantiene esa frontera explícita.
- No hay semántica institucional instalada.
- Demos y reportes son vistas regenerables.
- Estado local/externo nunca supera a Git como autoridad.
