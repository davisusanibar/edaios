# Evidencia de validación · Core 3.1.0 baseline portable

Observaciones T0 del incremento de normalización antes del bootstrap de
`edaiosv/main`. Los resultados son reproducibles, pero no afirman adopción,
producción, firma externa, Engram operativo ni una release sellada.

| Control | Resultado | Observación | Límite |
|---|---|---|---|
| Suite contractual | PASS | `./scripts/test.sh`: 127 pruebas en verde | Pruebas locales; no operación productiva |
| Spec Kit | PASS | 275/275 controles sobre siete features resolubles | Coherencia SDD; no aceptación humana implícita |
| Genealogía portable | PASS | `CoreReleaseState` v2 deriva un root único y rechaza shallow, grafts, replace refs y raíces múltiples | El hash remoto solo existe después del commit |
| Superficie Core | PASS | Una raíz lógica, un módulo `edaios-core`, cero attachments; sin dominio, engine, consumer, producto o runtime instalado | No prueba una iniciativa externa |
| Engram | PASS | Adapter opcional/degradable, loopback y sin operaciones de gobierno; tests contractuales en verde | El binario/runtime Engram no está instalado ni operado |
| Estado de release | PASS | Core 3.1.0 `baseline-no-candidate`, `promotion_allowed=false` | Baseline instalado no equivale a release sellada |
| Snapshot de raíz única | PASS | Candidato materializado como un commit sin padres: 127 tests y 14 gates pre-push en verde | Verificación local; la ref remota se observa después del commit definitivo |

## Bootstrap remoto

El remoto `git@bitbucket.org:data_and_ia/edaiosv.git` fue observado vacío antes
del cierre. El push de `main` debe usar un lease que falle si otra ref aparece.
No se crea tag; CI, protección, publicación y sello permanecen fuera del claim
de este baseline.
