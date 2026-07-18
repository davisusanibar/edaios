#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="$(git -C "$ROOT" rev-parse --git-path hooks)"
case "$HOOKS_DIR" in
  /*) : ;;
  *) HOOKS_DIR="$ROOT/$HOOKS_DIR" ;;
esac
mkdir -p "$HOOKS_DIR"
HOOK="$HOOKS_DIR/pre-push"

if [ -e "$HOOK" ] && ! grep -q "EDAIOS" "$HOOK"; then
  echo "[hooks] FAIL: pre-push existente no es de EDAIOS; revisa $HOOK" >&2
  exit 1
fi

cat > "$HOOK" <<'EOF'
#!/usr/bin/env bash
# Hook pre-push EDAIOS: ejecuta tests y gates scope pre-push.
# Fail-closed: un test o gate en rojo bloquea el push.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/tools/validation/pre_push_check.py"
EOF
chmod +x "$HOOK"
echo "[hooks] OK: pre-push instalado en $HOOK (ejecuta scripts/validate.sh)"
