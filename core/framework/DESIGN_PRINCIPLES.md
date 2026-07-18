# Principios de diseño

1. Knowledge First y source-first.
2. Fail-closed ante ambigüedad.
3. Core portable; consumers dependen de Core, nunca al revés.
4. Git durable, local reconstruible, RAM efímera.
5. Writes atómicos, locks/CAS y digests deterministas.
6. Read-only por defecto; ejecución fuera del control plane.
7. Claims limitados por evidencia.
