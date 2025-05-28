# Uninstalling TunaCode

This guide covers how to completely remove TunaCode from your system, depending on how you installed it.

## Table of Contents

- [Before Uninstalling](#before-uninstalling)
- [Method 1: One-Line Installer](#method-1-one-line-installer)
- [Method 2: pip/pipx Installation](#method-2-pippipx-installation)
- [Manual Cleanup](#manual-cleanup)
- [Troubleshooting](#troubleshooting)

## Before Uninstalling

Before removing TunaCode, consider backing up any important configuration:

```bash
# Backup your configuration (optional)
cp ~/.config/tunacode.json ~/tunacode-config-backup.json

# List your TunaCode directories
ls -la ~/.tunacode*
ls -la ~/.config/tunacode*
```

## Method 1: One-Line Installer

If you installed TunaCode using the one-line installer (`curl` or `wget` command), follow these steps:

### Step 1: Remove the Virtual Environment

```bash
# Remove the TunaCode virtual environment
rm -rf ~/.tunacode-venv
```

### Step 2: Remove the Command Wrapper

```bash
# Remove the tunacode command from your PATH
rm -f ~/.local/bin/tunacode
```

### Step 3: Clean Up Configuration and Data

```bash
# Remove configuration files
rm -f ~/.config/tunacode.json

# Remove TunaCode data directory
rm -rf ~/.tunacode

# Remove any project-specific TunaCode directories (optional)
# Note: This will remove .tunacode folders in your projects
find ~ -name ".tunacode" -type d -exec rm -rf {} + 2>/dev/null
```

### Step 4: Update Shell Profile (if modified)

If you manually added `~/.local/bin` to your PATH for TunaCode, you may want to remove it:

```bash
# Edit your shell profile
nano ~/.bashrc  # or ~/.zshrc

# Remove or comment out this line if it was added for TunaCode:
# export PATH="$HOME/.local/bin:$PATH"

# Reload your shell
source ~/.bashrc  # or source ~/.zshrc
```

## Method 2: pip/pipx Installation

If you installed TunaCode using `pip` or `pipx`:

### For pip installations:

```bash
# Uninstall the package
pip uninstall tunacode-cli

# Clean up configuration and data (same as Method 1, Step 3)
rm -f ~/.config/tunacode.json
rm -rf ~/.tunacode
```

### For pipx installations:

```bash
# Uninstall the package
pipx uninstall tunacode-cli

# Clean up configuration and data (same as Method 1, Step 3)
rm -f ~/.config/tunacode.json
rm -rf ~/.tunacode
```

## Manual Cleanup

If you want to ensure everything is removed, here's a comprehensive cleanup:

```bash
#!/bin/bash
# Complete TunaCode removal script

echo "🗑️  Removing TunaCode completely..."

# Remove virtual environment
if [ -d ~/.tunacode-venv ]; then
    echo "Removing virtual environment..."
    rm -rf ~/.tunacode-venv
fi

# Remove command wrapper
if [ -f ~/.local/bin/tunacode ]; then
    echo "Removing command wrapper..."
    rm -f ~/.local/bin/tunacode
fi

# Uninstall via pip if installed globally
if pip show tunacode-cli &>/dev/null; then
    echo "Uninstalling via pip..."
    pip uninstall tunacode-cli -y
fi

# Uninstall via pipx if installed
if command -v pipx &>/dev/null && pipx list | grep -q tunacode-cli; then
    echo "Uninstalling via pipx..."
    pipx uninstall tunacode-cli
fi

# Remove configuration
if [ -f ~/.config/tunacode.json ]; then
    echo "Removing configuration..."
    rm -f ~/.config/tunacode.json
fi

# Remove data directory
if [ -d ~/.tunacode ]; then
    echo "Removing data directory..."
    rm -rf ~/.tunacode
fi

# Remove project directories (optional - prompts user)
echo "Do you want to remove .tunacode directories from all your projects? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Removing project .tunacode directories..."
    find ~ -name ".tunacode" -type d -exec rm -rf {} + 2>/dev/null
    echo "Removed project directories."
fi

echo "✅ TunaCode removal complete!"
echo ""
echo "Note: If you manually added ~/.local/bin to your PATH for TunaCode,"
echo "you may want to remove it from your ~/.bashrc or ~/.zshrc file."
```

Save this as `uninstall_tunacode.sh` and run:

```bash
chmod +x uninstall_tunacode.sh
./uninstall_tunacode.sh
```

## Troubleshooting

### Command Still Available After Uninstall

If `tunacode` command is still available after uninstall:

```bash
# Check where the command is located
which tunacode
type tunacode

# If it shows multiple locations, remove them manually
# Common locations:
rm -f ~/.local/bin/tunacode
rm -f /usr/local/bin/tunacode
```

### Permission Errors

If you get permission errors:

```bash
# For files in your home directory, you shouldn't need sudo
# If you do, something was installed incorrectly

# Check ownership
ls -la ~/.local/bin/tunacode
ls -la ~/.tunacode-venv

# Fix ownership if needed (replace 'username' with your username)
sudo chown -R $USER:$USER ~/.local/bin/tunacode
sudo chown -R $USER:$USER ~/.tunacode-venv

# Then retry removal
rm -rf ~/.tunacode-venv ~/.local/bin/tunacode
```

### Verifying Complete Removal

To verify TunaCode is completely removed:

```bash
# These should all fail or return "not found"
tunacode --version
which tunacode
pip show tunacode-cli
find ~ -name "*tunacode*" 2>/dev/null
```

### Reinstalling After Issues

If you need to reinstall TunaCode cleanly:

```bash
# Make sure it's completely removed first (use steps above)
# Then reinstall with the one-line installer
curl -sSL https://raw.githubusercontent.com/alchemiststudiosDOTai/tunacode/master/scripts/install_linux.sh | bash
```

## What Gets Removed

When you follow this uninstall guide, the following will be removed:

- ✅ TunaCode executable and virtual environment
- ✅ Configuration files (`~/.config/tunacode.json`)
- ✅ Session data and logs (`~/.tunacode/`)
- ✅ Command wrapper (`~/.local/bin/tunacode`)
- ✅ Project-specific directories (`.tunacode/` in projects, if chosen)

## What Doesn't Get Removed

- Your project files and git history (TunaCode never modifies these without your permission)
- Any manual changes you made to shell profiles
- API keys stored in environment variables
- MCP servers you may have installed separately

---

**Need help?** [Open an issue](https://github.com/alchemiststudiosDOTai/tunacode/issues) if you have trouble uninstalling TunaCode.