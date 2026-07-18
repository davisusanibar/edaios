# Checklist de calidad de requisitos

Evaluación inicial contra `spec.md`, `feature.spec.yaml`, ADR-0013 y la
Constitución operativa.

- [x] Alcance limitado a baseline, gobierno, release gate, documentación, demo y CI.
- [x] Owner y autoridad humana están declarados.
- [x] La identidad 3.1.0 y la genealogía observada tienen fuente y fecha.
- [x] Cada FR posee al menos un SC verificable.
- [x] Se distingue baseline, candidato, tag, CI y release sin equivalencias falsas.
- [x] Foundation → Core → Consumer permanece sin inversión.
- [x] Flink, dominios, engines y productos quedan explícitamente fuera.
- [x] Sensibilidad T0; no se procesan datos institucionales ni PII.
- [x] CI ejecuta el registro canónico y no introduce un segundo gobierno.
- [x] La reversa y los límites de evidencia pueden expresarse sin inventar estado remoto.
- [x] No quedan `TBD` ni preguntas bloqueantes para planificar.
- [x] La raíz única evita autorreferencias y separa bootstrap de publicación.

**Resultado:** checklist en verde; habilita plan técnico.
