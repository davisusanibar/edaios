#!/usr/bin/env bash
# Inyecta EDAIOS Core en un proyecto consumer (perfil consumer-release, ADR-0016).
#
# Automatiza las 4 capas de inyeccion:
#   A. instala/verifica el paquete edaios-core
#   B. proyecta la constitucion + crea el attachment de iniciativa
#   C. instala el bundle Spec Kit gobernado + vendoriza el gate
#   D. instala la memoria de agente (bloque en CLAUDE.md)
#
# Es idempotente: re-ejecutarlo no rompe un consumer ya inyectado.
#
# INTERIM (RFC-0002): los pasos marcados [manual] copian el gate y el lock
# porque hoy NO viajan en el wheel ni en el bundle. Cuando RFC-0002 shipee el
# gate via adapter, esas copias desaparecen.
set -euo pipefail

# --- CORE se deriva de la ubicacion del script (vive dentro de edaiosv) ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE_DEFAULT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"   # sdd-adapter -> edaiosv
SK="$SCRIPT_DIR/spec-kit"
ADAPTER_SRC="$SCRIPT_DIR/src"

usage() {
  cat <<USAGE
Uso: inject-consumer.sh --workspace DIR --id ID --namespace NS \\
                        --owner OWNER --value-owner VALUE_OWNER [--core DIR]

  --workspace DIR      raiz del proyecto consumer donde inyectar
  --id ID              id de iniciativa, kebab-case [a-z][a-z0-9-]{2,63}
  --namespace NS       namespace global punteado (ej. com.org.miproyecto)
  --owner OWNER        actor owner (humano)
  --value-owner VO     actor value-owner (DEBE ser distinto de owner)
  --core DIR           raiz de EDAIOS Core (default: $CORE_DEFAULT)
USAGE
  exit 1
}

WS="" ID="" NS="" OWNER="" VOWNER="" CORE="$CORE_DEFAULT"
while [ $# -gt 0 ]; do
  case "$1" in
    --workspace) WS="$2"; shift 2;;
    --id) ID="$2"; shift 2;;
    --namespace) NS="$2"; shift 2;;
    --owner) OWNER="$2"; shift 2;;
    --value-owner) VOWNER="$2"; shift 2;;
    --core) CORE="$2"; shift 2;;
    -h|--help) usage;;
    *) echo "[inject] arg desconocido: $1" >&2; usage;;
  esac
done

fail() { echo "[inject] FAIL: $*" >&2; exit 1; }

# --- Validacion de argumentos (fail-closed) ---
[ -n "$WS" ] && [ -n "$ID" ] && [ -n "$NS" ] && [ -n "$OWNER" ] && [ -n "$VOWNER" ] || usage
[ -d "$WS" ] || fail "workspace no existe: $WS"
echo "$ID" | grep -qE '^[a-z][a-z0-9-]{2,63}$' || fail "id no es kebab-case: $ID"
[ "$OWNER" != "$VOWNER" ] || fail "owner y value-owner deben ser actores distintos (el attachment falla con actor_id duplicado)"
WS="$(cd "$WS" && pwd)"

# --- Prechecks del entorno ---
command -v specify >/dev/null || fail "'specify' (Spec Kit) no esta en PATH; instala Spec Kit >=0.12.11"
[ -f "$CORE/.specify/memory/constitution.md" ] || fail "constitucion compilada ausente en Core; corre: (cd $CORE && python3 tools/publishing/compile_constitution.py)"
[ -f "$CORE/.specify/integrations.lock.json" ] || fail "integrations.lock.json ausente en Core; corre: (cd $CORE && python3 tools/publishing/sync_spec_kit_integrations.py)"
[ -f "$CORE/tools/validation/spec_kit_gate.py" ] || fail "gate ausente en Core: $CORE/tools/validation/spec_kit_gate.py"

echo "== Inyectando EDAIOS Core en $WS =="

# --- Capa A: instalar/verificar el paquete ---
if ! command -v edaios-core >/dev/null; then
  echo "[A] edaios-core no esta en PATH; instalando el wheel en el entorno actual..."
  python3 -m pip install "$CORE/core/framework" || fail "no se pudo instalar edaios-core; instala en un venv y reintenta"
fi
edaios-core doctor >/dev/null || fail "edaios-core doctor rojo"
echo "[A] edaios-core OK"

# --- Capa B: proyectar constitucion + attachment ---
python3 - "$ADAPTER_SRC" "$CORE" "$WS" "$ID" <<'PY'
import sys
from pathlib import Path
adapter_src, core, ws, project = sys.argv[1:5]
sys.path.insert(0, adapter_src)
from edaios_sdd_adapter.spec_kit import seed_speckit_constitution
dest = seed_speckit_constitution(Path(core), Path(ws), project=project)
print(f"[B] constitucion proyectada -> {dest}")
PY

if [ -f "$WS/edaios.initiative.json" ]; then
  echo "[B] attachment ya existe; omito init"
else
  ( cd "$WS" && edaios-core init --workspace . --id "$ID" --namespace "$NS" \
      --owner "$OWNER" --value-owner "$VOWNER" --core-version 3.1.0 >/dev/null ) \
    || fail "edaios-core init fallo"
  echo "[B] attachment de iniciativa creado"
fi
( cd "$WS" && edaios-core validate --workspace . --profile initiative-adoption >/dev/null ) \
  || fail "validate --profile initiative-adoption rojo"
echo "[B] attachment validado (initiative-adoption)"

# --- Capa C: bundle Spec Kit gobernado ---
if [ ! -d "$WS/.specify" ] || [ ! -d "$WS/.claude" ]; then
  ( cd "$WS" && specify init --here --integration claude --force --script sh >/dev/null )
fi
( cd "$WS"
  specify preset    add --dev "$SK/preset"  --priority 5 >/dev/null 2>&1 || true
  specify extension add --dev "$SK/extension" --priority 5 >/dev/null 2>&1 || true
  specify workflow  add "$SK/workflow/edaios-delivery.yml" >/dev/null 2>&1 || true
  specify bundle    install "$SK/bundle" --offline >/dev/null )
echo "[C] bundle Spec Kit gobernado instalado"

# [gobernado, ADR-0020] sembrar el gate con procedencia via seed_gate. Sin
# force: una copia divergente DETIENE la inyeccion (la deriva se reporta, no se
# pisa); resolverla exige confirmacion explicita del owner del consumer
# (seed_gate force=True), nunca este script.
PYTHONPATH="$CORE/core/framework/extensions/sdd-adapter/src${PYTHONPATH:+:$PYTHONPATH}" \
python3 - "$CORE" "$WS" <<'PY' || fail "seed_gate detuvo la inyeccion (deriva o contencion reportada arriba)"
import sys
from pathlib import Path
from edaios_sdd_adapter.spec_kit import seed_gate
seed_gate(Path(sys.argv[1]), Path(sys.argv[2]))
PY
echo "[C] gate sembrado con procedencia gobernada (seed_gate, ADR-0020)"

# --- Capa D: memoria de agente ---
cp "$CORE/.specify/integrations.lock.json" "$WS/.specify/integrations.lock.json"
( cd "$WS" && edaios-core agent-setup apply --root . --surface claude-code >/dev/null ) \
  || fail "agent-setup apply fallo"
echo "[D] memoria de agente en CLAUDE.md"

cat <<DONE

== EDAIOS inyectado en $WS ==
  Constitucion proyectada  : .specify/memory/constitution.md
  Attachment (draft T0)    : edaios.initiative.json + .edaios/
  Gate (consumer-release)  : tools/validation/spec_kit_gate.py
  Memoria de agente        : CLAUDE.md

Siguiente: escribe una feature con /speckit.specify; el edaios.gate la valida con
  python3 tools/validation/spec_kit_gate.py . --feature <dir> --profile consumer-release

Nada se commitea ni se acepta: el cierre exige tu firma (Articulo VI).
DONE
