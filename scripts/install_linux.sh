#!/usr/bin/env bash
# install_linux.sh - helper to install tunacode-cli in a private virtualenv
set -euo pipefail

VENV_DIR="${HOME}/.tunacode-venv"
BIN_DIR="${HOME}/.local/bin"
PYTHON=${PYTHON:-python3}

printf "Setting up virtual environment in %s\n" "$VENV_DIR"
"$PYTHON" -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
"$VENV_DIR/bin/pip" install tunacode-cli >/dev/null

mkdir -p "$BIN_DIR"
cat <<EOW >"$BIN_DIR/tunacode"
#!/usr/bin/env bash
"$VENV_DIR/bin/tunacode" "$@"
EOW
chmod +x "$BIN_DIR/tunacode"

cat <<EOM
\nInstallation complete. Ensure \"$BIN_DIR\" is in your PATH to use 'tunacode'.
EOM
