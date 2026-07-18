# Doctrina operativa de EDAIOS Core

## Convenciones heredadas

- **Knowledge First:** lo que debe sobrevivir una sesion se expresa como KO o
  artefacto tipado antes de automatizarse.
- **Architecture before implementation:** una decision que cambia fronteras,
  autoridad o contratos se resuelve con RFC/ADR.
- **Human signed:** alcance, plan, inicio de implementacion y publicacion tienen
  un responsable humano identificable.
- **One source, many views:** Git conserva la forma canonica; portales, grafos,
  prompts e indices son vistas regenerables.
- **Adopt or adapt:** se adopta un estandar externo cuando cubre el contrato; se
  crea un adapter cuando falta contexto; se construye solo la capacidad residual.
- **Fail closed:** una ausencia de evidencia, version, owner o contrato no se
  interpreta como aprobacion.
- **Append over overwrite:** decisiones y memoria durable evolucionan por
  versiones, supersesion o nuevos registros; no borran el razonamiento previo.
- **Receipts over claims:** el avance se reduce de evidencia ligada a bytes y
  commits; una fase declarada por un chat o executor no habilita la siguiente.
- **Ports before products:** runtimes y backends se integran por capacidades y
  contratos; ningun proveedor externo se vuelve autoridad del core.

## Supuestos explicitos

1. El repositorio consumidor usa Git y puede ejecutar Python 3.11 o superior.
2. Los agentes y herramientas externas pueden fallar, cambiar o desaparecer.
3. La concurrencia se resuelve con ramas/worktrees y revision optimista; los
   locks locales solo protegen escrituras dentro de un workspace.
4. El dominio conoce su semantica mejor que el core y debe declarar su perfil.
5. La velocidad es una politica de evidencia, no permiso para saltar controles.
6. Toda salida externa entra como borrador hasta que un gate EDAIOS la verifica.

## Regla de autonomia

La IA puede descubrir, proponer, planificar, validar y producir borradores. La
autoridad humana conserva priorizacion, aceptacion de riesgo, decisiones de
arquitectura, habilitacion de implementacion y veredicto de publicacion.
