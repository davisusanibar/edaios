# Plan técnico · Core Base Inicial

## Contexto y decisión

El baseline vigente instaló un consumer antes de que existiera una necesidad
real. ADR-0003 fija ahora un único módulo requerido: Core. Se retira el
consumer instalado completo, se sincroniza la versión 1.0.0 y se conserva en
Core únicamente la forma reusable para consumers futuros.

Alternativas descartadas:

1. conservar el consumer técnico como ejemplo: mantiene una decisión
   tecnológica en la base;
2. dejar la raíz del consumer vacía: crea una taxonomía preventiva sin
   instancia;
3. marcar el consumer como opcional: el catálogo seguiría narrando una
   instalación.

## Materialización

1. Reconciliar ADR-0001/0003 y dejar el catálogo en tres ADR, cero RFC.
2. Eliminar el consumer retirado y toda referencia activa a él.
3. Fijar `VERSION`, wheel, manifests, perfiles y recursos Core en 1.0.0.
4. Ajustar Spec Kit, scripts y validadores al único dominio técnico `core`.
5. Regenerar el Operating System desde su JSON y desde las tablas canónicas de
   arquitectura de información, catálogo ADR y evidencia del baseline.
6. Ejecutar tests, gates, barrido de superficie y revisión visual del HTML.

## Estructura esperada

```text
core/foundation/                    autoridad
core/framework/                     control plane portable
governance/                         tres ADR + ledger RFC vacío
specs/archive/001-core-base-initial/        contrato y evidencia del cierre
tools/ + scripts/                   generación y gates
docs/ + program-office/             guía y memoria vigente
```

No existe ninguna raíz fuera de esta topología.

## Constitution Check

| Principio | Veredicto | Evidencia |
|---|---|---|
| I. Conocimiento | PASS | Foundation permanece intacta y Core la materializa. |
| II. Spec | PASS | Esta feature declara alcance y criterios antes de retirar el consumer. |
| III. Decisión | PASS | ADR-0003 aceptado autoriza el módulo único Core. |
| IV. Fuentes | PASS | Versión y conteos derivan de `VERSION` y ledgers versionados. |
| V. Vistas | PASS | El HTML se regenera desde configuración y fuentes canónicas. |
| VI. Firma | PASS | La instrucción del Principal Architect acepta el freeze Foundation → Core. |
| VII. Privacidad | N/A | Sensibilidad T0, sin datos, PII ni consumer instalado. |

Constitucion verificada: sha256:45af1fa889fb66e86198a80205cbc3f5da35d8e97f286bec4039386c2fbbdc86

## Gate Impact

- `FND-PROJECTION`: comprueba derivación de Foundation.
- `SDD-CONTRACT`: comprueba artefactos, cierre y trazabilidad.
- `KOM`: comprueba contratos de Knowledge Objects.
- `MONOREPO-STRUCTURE`: comprueba raíz única, módulo Core y topología
  cerrada.
- `CORE-DISTRIBUTION`: prueba wheel Core 1.0.0 instalado aisladamente.
- `CORE-BASE-DEMO`: comprueba una sola vista source-first y sus tres tablas.
- `TEST` y `VALIDATE`: sellan Core Base sin warnings.

## Impacto y reversa

- Arquitectura: alto; elimina el único consumer instalado.
- Ontología/datos/IA/privacidad: sin cambio material; no existen instancias.
- Costo operativo: disminuye al retirar el toolchain y runtime del consumer.
- Blast radius: manifests, gobierno, validadores, documentación y demo.
- Reversa antes del sello: restaurar el commit raíz previo. El bundle externo de
  transición conserva recuperación, pero no forma parte de la nueva autoridad.
