#!/usr/bin/env bash
set -euo pipefail

# Preflight check for system binaries
REQUIRED_CMDS=(docker docker-compose kubectl helm psql rabbitmqctl mc)
declare -A APT_PACKAGES=(
  [docker]=docker.io
  [docker-compose]=docker-compose
  [kubectl]=kubectl
  [helm]=helm
  [psql]=postgresql-client
  [rabbitmqctl]=rabbitmq-server
  [mc]=minio-client
)

missing=()

echo "Running system dependency check..."
for cmd in "${REQUIRED_CMDS[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo " - $cmd: found ($(command -v "$cmd"))"
    else
        echo " - $cmd: MISSING"
        missing+=("$cmd")
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo "Missing dependencies: ${missing[*]}"
    if command -v apt-get >/dev/null 2>&1; then
        echo "Attempting to install via apt-get..."
        apt-get update
        apt_pkgs=()
        for cmd in "${missing[@]}"; do
            pkg=${APT_PACKAGES[$cmd]:-}
            if [ -n "$pkg" ]; then
                apt_pkgs+=("$pkg")
            else
                echo "  no apt package mapping for $cmd"
            fi
        done
        if [ ${#apt_pkgs[@]} -gt 0 ]; then
            apt-get install -y "${apt_pkgs[@]}" || true
        else
            echo "No apt packages to install."
        fi
    else
        echo "apt-get not available. Install manually: ${missing[*]}"
    fi
else
    echo "All system dependencies satisfied."
fi

# Python packages
PY_PACKAGES=(fastapi uvicorn psycopg2 pika minio kubernetes)
missing_py=()

echo "Running Python package check..."
for pkg in "${PY_PACKAGES[@]}"; do
    if python3 -c "import $pkg" >/dev/null 2>&1; then
        echo " - $pkg: installed"
    else
        echo " - $pkg: MISSING"
        missing_py+=("$pkg")
    fi
done

if [ ${#missing_py[@]} -gt 0 ]; then
    echo "Installing missing Python packages..."
    python3 -m pip install -U "${missing_py[@]}"
else
    echo "All Python packages satisfied."
fi

echo "Environment setup complete."
