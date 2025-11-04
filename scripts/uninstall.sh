#!/bin/bash

# Define the installation directory and the command name
INSTALL_DIR="$HOME/.local/bin"
COMMAND_NAME="allsorted"
SYMLINK_PATH="$INSTALL_DIR/$COMMAND_NAME"

echo "Uninstalling allsorted..."

# Check if the symbolic link exists and remove it
if [ -L "$SYMLINK_PATH" ]; then
    echo "Found symlink at $SYMLINK_PATH. Removing it."
    rm "$SYMLINK_PATH"
    if [ $? -eq 0 ]; then
        echo "Successfully removed the 'allsorted' command."
    else
        echo "Error: Failed to remove the symbolic link." >&2
        exit 1
    fi
else
    echo "Warning: 'allsorted' command not found at $SYMLINK_PATH. Nothing to do."
fi

# Optional: Advise user about the PATH entry
echo "\nNote: If you manually added '$INSTALL_DIR' to your shell profile (~/.bashrc, ~/.zshrc), you may want to remove it."

echo "Uninstallation complete."
