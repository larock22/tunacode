#!/usr/bin/env bash
# TunaCode Uninstaller
# 
# One-line uninstall:
# curl -sSL https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/uninstall_linux.sh | bash
# 
# Or with wget:
# wget -qO- https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/uninstall_linux.sh | bash

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

VENV_DIR="${HOME}/.tunacode-venv"
BIN_DIR="${HOME}/.local/bin"

echo -e "${RED}🗑️  TunaCode Uninstaller${NC}"
echo "================================"

# Check for --force flag
FORCE_MODE=false
if [[ "$1" == "--force" ]]; then
    FORCE_MODE=true
    echo -e "${YELLOW}Running in force mode (no confirmations)${NC}"
fi

# Function to safely remove if exists
safe_remove() {
    local path="$1"
    local description="$2"
    
    if [ -e "$path" ]; then
        echo -e "${YELLOW}Removing $description...${NC}"
        rm -rf "$path"
        echo -e "${GREEN}✓${NC} Removed $description"
    else
        echo -e "${BLUE}○${NC} $description not found (already clean)"
    fi
}

# Skip confirmation if in force mode
if [ "$FORCE_MODE" = false ]; then
    # Check if we're being piped/curled
    if [ -t 0 ]; then
        # Interactive mode - ask for confirmation
        echo -e "${YELLOW}This will remove TunaCode and all its data from your system.${NC}"
        echo -e "Are you sure you want to continue? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Uninstall cancelled.${NC}"
            exit 0
        fi
    else
        # Non-interactive mode (piped) - show warning and instructions
        echo -e "${YELLOW}This will remove TunaCode and all its data from your system.${NC}"
        echo -e ""
        echo -e "To confirm uninstall, download and run the script directly:"
        echo -e "${GREEN}wget https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/uninstall_linux.sh${NC}"
        echo -e "${GREEN}chmod +x uninstall_linux.sh${NC}"
        echo -e "${GREEN}./uninstall_linux.sh${NC}"
        echo -e ""
        echo -e "Or force uninstall without confirmation:"
        echo -e "${GREEN}curl -sSL https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/uninstall_linux.sh | bash -s -- --force${NC}"
        exit 0
    fi
fi

echo ""

# Remove virtual environment
safe_remove "$VENV_DIR" "TunaCode virtual environment"

# Remove command wrapper
safe_remove "$BIN_DIR/tunacode" "TunaCode command wrapper"

# Uninstall via pip if installed globally
if command -v pip &>/dev/null && pip show tunacode-cli &>/dev/null; then
    echo -e "${YELLOW}Uninstalling tunacode-cli via pip...${NC}"
    pip uninstall tunacode-cli -y
    echo -e "${GREEN}✓${NC} Uninstalled tunacode-cli via pip"
else
    echo -e "${BLUE}○${NC} tunacode-cli not installed via pip"
fi

# Uninstall via pipx if installed
if command -v pipx &>/dev/null && pipx list 2>/dev/null | grep -q tunacode-cli; then
    echo -e "${YELLOW}Uninstalling tunacode-cli via pipx...${NC}"
    pipx uninstall tunacode-cli
    echo -e "${GREEN}✓${NC} Uninstalled tunacode-cli via pipx"
else
    echo -e "${BLUE}○${NC} tunacode-cli not installed via pipx"
fi

# Remove configuration
safe_remove "$HOME/.config/tunacode.json" "TunaCode configuration"

# Remove data directory  
safe_remove "$HOME/.tunacode" "TunaCode data directory"

# Ask about project directories
if [ "$FORCE_MODE" = true ]; then
    # In force mode, skip project directories by default for safety
    echo -e "${BLUE}○${NC} Skipping project .tunacode directories (use interactive mode to remove)"
else
    echo ""
    echo -e "${YELLOW}Do you want to remove .tunacode directories from all your projects?${NC}"
    echo -e "This will remove undo history and backups from projects where you used TunaCode."
    echo -e "Type 'yes' to confirm, or anything else to skip:"
    read -r project_response

    if [[ "$project_response" == "yes" ]]; then
        echo -e "${YELLOW}Removing .tunacode directories from projects...${NC}"
        # Find and remove .tunacode directories, but don't fail if there are permission issues
        found_dirs=$(find "$HOME" -name ".tunacode" -type d 2>/dev/null | wc -l)
        if [ "$found_dirs" -gt 0 ]; then
            find "$HOME" -name ".tunacode" -type d -exec rm -rf {} + 2>/dev/null || true
            echo -e "${GREEN}✓${NC} Removed $found_dirs .tunacode project directories"
        else
            echo -e "${BLUE}○${NC} No .tunacode project directories found"
        fi
    else
        echo -e "${BLUE}○${NC} Skipped removing project .tunacode directories"
    fi
fi

echo ""
echo -e "${GREEN}✨ TunaCode uninstall complete!${NC}"

# Final verification
if command -v tunacode &>/dev/null; then
    tunacode_location=$(which tunacode)
    echo -e "${YELLOW}⚠️  Warning: 'tunacode' command still found at: $tunacode_location${NC}"
    echo -e "You may need to manually remove it or restart your terminal."
else
    echo -e "${GREEN}✓${NC} TunaCode command successfully removed"
fi

# Check if ~/.local/bin is still in PATH and now empty
if [[ ":$PATH:" == *":$BIN_DIR:"* ]] && [ -d "$BIN_DIR" ]; then
    bin_contents=$(ls -la "$BIN_DIR" 2>/dev/null | wc -l)
    if [ "$bin_contents" -le 3 ]; then  # Only . and .. entries
        echo ""
        echo -e "${BLUE}💡 Note: ${NC}~/.local/bin is in your PATH but appears empty."
        echo -e "You may want to remove it from your ~/.bashrc or ~/.zshrc file."
    fi
fi

echo ""
echo -e "To reinstall TunaCode later, run:"
echo -e "${GREEN}curl -sSL https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/install_linux.sh | bash${NC}"