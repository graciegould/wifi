#!/bin/bash
# install.sh - Install wifi CLI globally for your user

set -e

echo "Installing wifi CLI..."

# Install in user mode (recommended for most users)
pip install --user .

echo "\nInstallation complete!"
echo "You can now run 'wifi' from anywhere in your terminal."
echo "If you don't see the 'wifi' command, add the following to your shell profile (e.g., ~/.zshrc or ~/.bashrc):"
echo '  export PATH="$HOME/.local/bin:$PATH"'
