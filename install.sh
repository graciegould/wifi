#!/bin/bash
# install.sh - Install wifi CLI globally for your user

set -e


if [[ "$1" == "--dev" ]]; then
	echo "Installing wifi CLI in development (editable) mode..."
	EDITABLE_MODE=true
else
	echo "Installing wifi CLI..."
	EDITABLE_MODE=false
fi


# Find a working pip command
if command -v pip &>/dev/null; then
	PIP_CMD="pip"
elif command -v pip3 &>/dev/null; then
	PIP_CMD="pip3"
elif command -v python3 &>/dev/null; then
	PIP_CMD="python3 -m pip"
else
	echo "Error: pip or pip3 not found. Please install pip before running this script."
	exit 1
fi

if [ "$EDITABLE_MODE" = true ]; then
	$PIP_CMD install --user -e .
else
	$PIP_CMD install --user .
fi

echo "\nInstallation complete!"
echo "You can now run 'wifi' from anywhere in your terminal."

# Detect the actual pip user base bin directory
USER_BASE=$(python3 -m site --user-base 2>/dev/null || echo "$HOME/.local")
USER_BIN="$USER_BASE/bin"
PATH_LINE="export PATH=\"$USER_BIN:\$PATH\""
ADDED_PATH=false

# Prefer zsh if running under zsh
if [ -n "$ZSH_VERSION" ] || [ "$(basename \"$SHELL\")" = "zsh" ]; then
	PROFILE="$HOME/.zshrc"
	if [ -f "$PROFILE" ] && ! grep -q "$USER_BIN" "$PROFILE"; then
		echo "$PATH_LINE" >> "$PROFILE"
		echo "Added $USER_BIN to PATH in $PROFILE."
		ADDED_PATH=true
	fi
fi

# Otherwise, use bash if running under bash
if [ "$ADDED_PATH" = false ] && { [ -n "$BASH_VERSION" ] || [ "$(basename \"$SHELL\")" = "bash" ]; }; then
	PROFILE="$HOME/.bashrc"
	if [ -f "$PROFILE" ] && ! grep -q "$USER_BIN" "$PROFILE"; then
		echo "$PATH_LINE" >> "$PROFILE"
		echo "Added $USER_BIN to PATH in $PROFILE."
		ADDED_PATH=true
	fi
fi

# Fallback to .profile if neither above worked
if [ "$ADDED_PATH" = false ]; then
	PROFILE="$HOME/.profile"
	if [ -f "$PROFILE" ] && ! grep -q "$USER_BIN" "$PROFILE"; then
		echo "$PATH_LINE" >> "$PROFILE"
		echo "Added $USER_BIN to PATH in $PROFILE."
		ADDED_PATH=true
	fi
fi

if [ "$ADDED_PATH" = true ]; then
	echo "Please restart your terminal or run: source $PROFILE"
fi
