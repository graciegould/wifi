#!/bin/bash
# install.sh - Install WiFi Speed Monitor CLI globally for your user

set -e

echo "Installing WiFi Speed Monitor CLI..."

# Install in user mode (recommended for most users)
pip install --user .

echo "\nInstallation complete!"
echo "You can now run 'wifi' from anywhere in your terminal."
echo "If you don't see the command, add the following to your shell profile (e.g., ~/.zshrc or ~/.bashrc):"
echo '  export PATH="$HOME/.local/bin:$PATH"'
