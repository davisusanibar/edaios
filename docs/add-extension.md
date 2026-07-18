# Adoptar una iniciativa o extensión

Core 3.1.0 no instala extensiones ni consumidores. Publica un attachment y una
suite de conformidad para que cada iniciativa conserve implementación y verdad
en su propio scope Git.

1. Captura intención verbatim, owner de valor y owner técnico.
2. Declara fuentes con fecha, alcance, sensibilidad y método de validación.
3. Inicializa un attachment desde `core/framework/core/templates/initiative/`
   y abre una feature Spec Kit; el template permanece ilustrativo hasta firma.
4. Si define una frontera nueva, compara opciones en RFC y acepta un ADR.
5. Ejecuta `initiative-adoption`; prueba que la extensión depende de Core y que
   Core no la importa.
6. Registra authority/delegation, sensibilidad, políticas, mappings, calidad,
   lineage, reversa y evidencia sin inferir verdad.
7. Usa `federation` únicamente si existen mounts gobernados y namespaces
   distintos; el índice resultante es derivado.
8. Solo entonces crea el módulo en el repositorio de la iniciativa y actualiza
   sus catálogos/lock; hasta ese momento no está instalado ni reclamado.

Una plantilla, fixture o gate local no prueba adopción ni producción.
