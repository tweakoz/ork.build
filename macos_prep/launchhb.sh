#!/usr/bin/env bash

# Check if already in custom homebrew environment
if [[ -n "$CUSTOM_HOMEBREW_ACTIVE" ]]; then
    echo "Warning: Already in a custom Homebrew environment. Exiting to prevent nesting."
    exit 1
fi

BREW_PATH="${1:-.brew}"
if [[ -d "$BREW_PATH" ]]; then
    export HOMEBREW_PREFIX="$(cd "$BREW_PATH" && pwd)"
else
    # If directory doesn't exist, construct absolute path manually
    if [[ "$BREW_PATH" = /* ]]; then
        # Already absolute
        export HOMEBREW_PREFIX="$BREW_PATH"
    else
        # Make it absolute relative to current directory
        export HOMEBREW_PREFIX="$(pwd)/$BREW_PATH"
    fi
fi

echo HOMEBREW_PREFIX:
echo $HOMEBREW_PREFIX

export CUSTOM_HOMEBREW_ACTIVE=1
export HOMEBREW_NO_AUTO_UPDATE=1  # Prevent automatic updates
export HOMEBREW_NO_ANALYTICS=1    # Disable analytics

# Remove /opt/homebrew/bin from PATH
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v "^/opt/homebrew/bin$" | tr '\n' ':' | sed 's/:$//')

# Add custom brew to PATH
export PATH="${HOMEBREW_PREFIX}/bin:$PATH"

# Set custom prompt - use default if PS1 not set
if [[ -z "$PS1" ]]; then
    # Construct default prompt: machinename:folder user$
    export PS1='[HB]\h:\W \u\$ '
else
    export PS1="[HB]${PS1}"
fi

exec bash
