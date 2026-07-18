# ADR-0015 — Proyecciones renderizadas y superficie de publicación

**Estado:** Aceptado
**Fecha:** 2026-07-17
**Owner:** Principal Architect

## Contexto

Core proyecta conocimiento a vistas derivadas y verifica cada proyección
comparando el derivado con su recompilación: la Constitución mediante
`FND-PROJECTION`, los catálogos mediante `CATALOG-PROJECTION` y la guía day-zero
mediante `CORE-BASE-DEMO`. Las tres comparten dos propiedades no declaradas hasta
hoy: el derivado es **texto**, y el compilador vive en `tools/` usando
**únicamente la biblioteca estándar**. La verificación de drift se reduce a una
comparación de cadenas:

    destination.read_text(encoding="utf-8") != content

Una charla pública exige llenar un template `.pptx` provisto por un tercero. Ese
artefacto rompe ambas propiedades. Un `.pptx` es un contenedor ZIP cuyos
timestamps, orden de entradas y metadatos varían entre corridas, de modo que la
igualdad byte a byte no es una propiedad natural del formato sino algo que hay
que construir. Renderizarlo exige una dependencia de terceros; hoy `tools/` no
tiene ninguna y esa ausencia sostiene la portabilidad que ADR-0003 reclama.

Existe además una tercera frontera. El repositorio declara que no tiene licencia
raíz ni autorización de publicación, y la Constitución separa commit, push,
release y publicación como permisos distintos. Un deck de conferencia es el
primer artefacto pensado para salir del repositorio y sostener claims sobre
EDAIOS ante una audiencia que no puede leer las fuentes.

Estas tres fronteras no están cubiertas por ningún ADR vigente. El precedente de
`CORE-BASE-DEMO` autoriza una demo como proyección compilada, pero no un derivado
binario, ni una dependencia externa en Core, ni una superficie de publicación.

## Decisión propuesta

Core adoptará los siguientes invariantes:

1. Una **proyección renderizada** es un derivado cuya representación no admite
   comparación textual directa. Core puede gobernar su fuente y sus claims; no
   incorpora su renderizador. La fuente es un artefacto de texto versionado y
   gobernado; el render es responsabilidad de un consumer.
2. Core no adopta dependencias de terceros para renderizar vistas. `tools/`
   permanece acotado a la biblioteca estándar y a módulos del propio repositorio.
   Un formato que exija un motor externo se rinde fuera de Core.
3. La jerarquía `Foundation → Core → Consumer` gobierna la dirección del render.
   Core publica conocimiento; un consumer produce vistas. Una vista no ratifica
   el conocimiento que la origina y su ausencia no degrada el canon.
4. La fuente de una proyección renderizada declara explícitamente sus fuentes de
   conocimiento y su frontera de claims. Un gate de Core verifica que esas
   fuentes resuelvan y que la frontera esté presente; no verifica el render.
5. La verificación de determinismo del artefacto renderizado pertenece al
   consumer y no puede reclamarse como garantía de Core. Un consumer que afirme
   determinismo debe normalizar su contenedor y demostrarlo con su propio check.
6. Publicar es un permiso separado de commit y push, y no se deriva de la
   existencia del artefacto. Un deck compilado no autoriza su exhibición: la
   autorización es una decisión humana registrada, y su alcance es el evento y
   la versión declarados.
7. Un artefacto que sostiene claims sobre EDAIOS ante terceros declara la misma
   frontera que el repositorio declara sobre sí mismo. Una vista no puede
   reclamar más que la superficie de claims que la origina.

ADR-0015 precisa el alcance de ADR-0007 y del gate `CORE-BASE-DEMO` para
derivados no textuales, y aplica la frontera de dependencias de ADR-0006 y la
portabilidad de ADR-0003 al caso del render. No los sustituye.

## Relaciones

- Amends: ADR-0003, ADR-0006, ADR-0007

## Alternativas

- incorporar el renderizador a `tools/publishing/`: rechazada porque introduce la
  primera dependencia de terceros en Core para una capacidad que no es de Core, y
  degrada la portabilidad que ADR-0003 sostiene;
- comparar el `.pptx` byte a byte con el mecanismo textual vigente: rechazada; la
  igualdad no es una propiedad del contenedor ZIP y un check que falle por
  timestamps enseña a ignorar el gate;
- renunciar al formato y proyectar solo HTML: rechazada porque un template
  provisto por un tercero es un requisito externo, no una preferencia; Core no
  puede redefinir el contrato de un evento;
- tratar el deck como documentación no gobernada: rechazada; un artefacto que
  hace claims públicos sobre EDAIOS sin frontera declarada contradice el Artículo
  IV y la propia superficie de claims;
- derivar la autorización de publicación del merge del artefacto: rechazada;
  invierte la separación de permisos y convierte un commit en una publicación.

## Compatibilidad y migración

Las proyecciones vigentes no cambian: Constitución, catálogos y guía day-zero
siguen siendo texto verificado por comparación textual, y sus gates conservan su
contrato. La decisión es aditiva: define una clase de proyección que antes no
existía y la ubica fuera de Core.

`tools/` conserva su superficie stdlib. Un consumer que renderice vistas declara
sus propias dependencias y no las propaga hacia Core; la ausencia de ese consumer
no afecta gates, canon ni distribución.

## Consecuencias

Core podrá gobernar la narrativa y los claims de un deck sin aprender a producir
PowerPoint. El costo es que el artefacto queda repartido: la fuente y su gate en
Core, el render y su determinismo en el consumer. Regenerar exige dos pasos y dos
repositorios, y Core no puede demostrar que el `.pptx` exhibido corresponde a la
fuente que gobierna: esa correspondencia la sostiene el check del consumer.

Un consumer que quiera reclamar determinismo deberá normalizar el contenedor en
lugar de heredar la garantía. Quien esperaba que Core sellara el artefacto final
deberá tratar esa expectativa como no instalada.

## Evidencia y frontera del claim

La suite puede demostrar que la fuente de una proyección renderizada valida
contra su schema, que sus fuentes de conocimiento resuelven y que su frontera de
claims está presente. No demuestra determinismo del render, fidelidad del
artefacto exhibido, autorización de publicación, licencia, derechos sobre el
template de un tercero ni exactitud de lo que un expositor afirme en vivo.

Este ADR no autoriza publicar el deck. La autorización es una decisión humana
posterior y separada, con evento y versión declarados.

## Aprobación

Principal Architect · 2026-07-17 · autorización humana expresa de ADR-0015 para
habilitar la feature que implemente la fuente gobernada y su gate. La aceptación
alcanza la frontera estructural; no autoriza tag, push, release ni publicación
del deck, que siguen siendo decisiones separadas.
