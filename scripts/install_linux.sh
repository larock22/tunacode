#!/usr/bin/env bash
# TunaCode CLI Installer
# 
# One-line install:
# curl -sSL https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/install_linux.sh | bash
# 
# Or with wget:
# wget -qO- https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/install_linux.sh | bash

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

VENV_DIR="${HOME}/.tunacode-venv"
BIN_DIR="${HOME}/.local/bin"
PYTHON=${PYTHON:-python3}

echo -e "${BLUE}🐟 TunaCode CLI Installer${NC}"
echo "================================"

# Check Python version
if ! command -v "$PYTHON" &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found!${NC}"
    echo "Please install Python 3.10 or higher first."
    exit 1
fi

PYTHON_VERSION=$("$PYTHON" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$PYTHON_VERSION < 3.10" | bc) -eq 1 ]]; then
    echo -e "${RED}Error: Python 3.10 or higher required${NC}"
    echo "Found Python $PYTHON_VERSION"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Remove old installation if exists
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Removing old installation...${NC}"
    rm -rf "$VENV_DIR"
fi

# Create virtual environment
echo -e "\n${BLUE}Creating virtual environment...${NC}"
"$PYTHON" -m venv "$VENV_DIR"

# Upgrade pip and install tunacode
echo -e "${BLUE}Installing TunaCode CLI...${NC}"
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install tunacode-cli --quiet

# Create bin directory and wrapper script
mkdir -p "$BIN_DIR"
cat <<'EOW' >"$BIN_DIR/tunacode"
#!/usr/bin/env bash
exec "$HOME/.tunacode-venv/bin/tunacode" "$@"
EOW
chmod +x "$BIN_DIR/tunacode"

# Check if bin directory is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "\n${YELLOW}Note: $BIN_DIR is not in your PATH${NC}"
    echo "Add this line to your ~/.bashrc or ~/.zshrc:"
    echo -e "${GREEN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    echo -e "\nThen run: ${GREEN}source ~/.bashrc${NC} (or source ~/.zshrc)"
fi

echo -e "\n${GREEN}✨ Installation complete!${NC}"
echo -e "\nRun ${BLUE}tunacode${NC} to get started"
echo -e "Run ${BLUE}tunacode --help${NC} for usage information"

# Test if we can run tunacode
if command -v tunacode &> /dev/null; then
    echo -e "\n${GREEN}✓${NC} tunacode command is available"
else
    echo -e "\n${YELLOW}!${NC} tunacode command not found in PATH"
    echo -e "   Try running: ${GREEN}$BIN_DIR/tunacode${NC}"
fi
