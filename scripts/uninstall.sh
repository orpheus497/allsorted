#!/bin/bash

# allsorted Uninstallation Script for Linux/macOS
# Removes allsorted from the system

set -e  # Exit on error

echo "================================================"
echo "  allsorted Uninstallation"
echo "================================================"
echo ""

# Check which installation method was used
INSTALL_DIR="$HOME/.local/bin"
COMMAND_NAME="allsorted"
SYMLINK_PATH="$INSTALL_DIR/$COMMAND_NAME"
UNINSTALLED=false

# Method 1: Check for pip installation
if command -v pip3 &> /dev/null; then
    if pip3 show allsorted &> /dev/null; then
        echo "Found pip installation of allsorted."
        echo "Uninstalling via pip..."
        pip3 uninstall -y allsorted
        echo "✓ Successfully uninstalled allsorted via pip"
        UNINSTALLED=true
    fi
fi

# Method 2: Check for symlink installation
if [ -L "$SYMLINK_PATH" ]; then
    echo "Found symlink installation at $SYMLINK_PATH."
    echo "Removing symlink..."
    rm "$SYMLINK_PATH"
    if [ $? -eq 0 ]; then
        echo "✓ Successfully removed symlink installation"
        UNINSTALLED=true
    else
        echo "❌ Error: Failed to remove the symbolic link." >&2
        exit 1
    fi
fi

# Check if anything was uninstalled
if [ "$UNINSTALLED" = false ]; then
    echo "⚠ Warning: No installation of allsorted found."
    echo ""
    echo "Checked for:"
    echo "  - pip installation (pip3 show allsorted)"
    echo "  - symlink at $SYMLINK_PATH"
    echo ""
    exit 0
fi

echo ""
echo "================================================"
echo "  Uninstallation Complete"
echo "================================================"
echo ""
echo "Note: If you manually added '$INSTALL_DIR' to your"
echo "shell profile (~/.bashrc, ~/.zshrc), you may want"
echo "to remove it if no longer needed."
echo ""
