#!/usr/bin/env bash

export brew_root="${1:-.brew}"
   
if [[ ! -d "$brew_root" ]]; then
    git clone --depth=1000 https://github.com/Homebrew/brew.git "$brew_root"
fi
cd $brew_root
git fetch
# sep 02, 2025
git checkout 4.6.8 

    
export HOMEBREW_PREFIX="$brew_root"
export HOMEBREW_NO_AUTO_UPDATE=1  # Prevent automatic updates
export HOMEBREW_NO_ANALYTICS=1    # Disable analytics
export PATH="${HOMEBREW_PREFIX}/bin:$PATH"

brew bundle install --file=Brewfile --cleanup

cd ${HOMEBREW_PREFIX}/bin
ln -sf python3.14 python3

# Fix wget certificates
if [[ -f "${HOMEBREW_PREFIX}/etc/wgetrc" ]] && [[ -f "${HOMEBREW_PREFIX}/etc/ca-certificates/cert.pem" ]]; then
    if ! grep -q "ca_certificate=" "${HOMEBREW_PREFIX}/etc/wgetrc"; then
        echo "ca_certificate=${HOMEBREW_PREFIX}/etc/ca-certificates/cert.pem" >> "${HOMEBREW_PREFIX}/etc/wgetrc"
    fi
fi

# Fix OpenSSL certificates
if [[ -d "${HOMEBREW_PREFIX}/etc/openssl@3" ]]; then
    ln -sf "${HOMEBREW_PREFIX}/etc/ca-certificates/cert.pem" \
           "${HOMEBREW_PREFIX}/etc/openssl@3/cert.pem" 2>/dev/null
fi

# Fix curl certificates
if command -v curl &>/dev/null; then
    echo "cacert=${HOMEBREW_PREFIX}/etc/ca-certificates/cert.pem" > "${HOMEBREW_PREFIX}/etc/curlrc"
fi

# Set up Python certificates
if command -v python3 &>/dev/null; then
    python3 -m pip config set global.cert "${HOMEBREW_PREFIX}/etc/ca-certificates/cert.pem" 2>/dev/null || true
fi