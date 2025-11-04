#!/bin/bash

# allsorted Installation Script for Linux/macOS
# Installs allsorted as a system-wide command

set -e  # Exit on error

echo "================================================"
echo "  allsorted Installation"
echo "  Created by orpheus497"
echo "================================================"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION or higher is required"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"
echo ""

# Get script directory (project root/scripts)
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")

echo "Installing from: $PROJECT_ROOT"
echo ""

# Ask user for installation method
echo "Choose installation method:"
echo "  1) pip install (recommended)"
echo "  2) symlink to ~/.local/bin"
echo ""
read -p "Enter choice [1-2]: " -n 1 -r
echo ""
echo ""

if [[ $REPLY == "1" ]]; then
    # pip installation
    echo "Installing via pip..."
    
    # Check if pip is available
    if ! command -v pip3 &> /dev/null; then
        echo "❌ Error: pip3 is not installed"
        echo "Please install pip3 first"
        exit 1
    fi
    
    # Install dependencies
    echo "Installing dependencies..."
    pip3 install -r "$PROJECT_ROOT/requirements.txt"
    
    # Install package
    echo "Installing allsorted..."
    pip3 install -e "$PROJECT_ROOT"
    
    echo ""
    echo "✓ Installation complete!"
    echo ""
    echo "You can now run: allsorted --help"
    
elif [[ $REPLY == "2" ]]; then
    # Symlink installation
    MAIN_SCRIPT_PATH="$PROJECT_ROOT/src/main.py"
    INSTALL_DIR="$HOME/.local/bin"
    COMMAND_NAME="allsorted"
    SYMLINK_PATH="$INSTALL_DIR/$COMMAND_NAME"
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    echo "✓ Installation directory: $INSTALL_DIR"
    
    # Make main script executable
    chmod +x "$MAIN_SCRIPT_PATH"
    echo "✓ Made main script executable"
    
    # Create symlink
    if [ -L "$SYMLINK_PATH" ]; then
        echo "⚠ Existing symlink found, removing..."
        rm "$SYMLINK_PATH"
    fi
    
    ln -s "$MAIN_SCRIPT_PATH" "$SYMLINK_PATH"
    echo "✓ Created symlink: $SYMLINK_PATH"
    
    # Check PATH
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        echo ""
        echo "⚠ IMPORTANT: Add $INSTALL_DIR to your PATH"
        echo ""
        echo "Add this line to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
        echo ""
        echo "    export PATH=\"$INSTALL_DIR:\$PATH\""
        echo ""
        echo "Then restart your terminal or run: source ~/.bashrc"
    else
        echo "✓ Installation directory is in PATH"
    fi
    
    echo ""
    echo "✓ Installation complete!"
    echo ""
    echo "You can now run: allsorted organize --help"
    
else
    echo "Invalid choice. Installation cancelled."
    exit 1
fi

echo ""
echo "================================================"
echo "  Quick Start"
echo "================================================"
echo ""
echo "  Preview:   allsorted organize --dry-run"
echo "  Organize:  allsorted organize"
echo "  Help:      allsorted --help"
echo ""
echo "================================================"
