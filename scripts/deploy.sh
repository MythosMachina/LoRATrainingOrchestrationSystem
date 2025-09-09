#!/usr/bin/env bash
set -euo pipefail

# Deployment script for LoRA Training Orchestration System
# Performs preflight checks, installs missing dependencies,
# and provisions a Kubernetes environment with required services.

REQUIRED_CMDS=(docker kubectl helm kind)

missing=()
for cmd in "${REQUIRED_CMDS[@]}"; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    missing+=("$cmd")
  fi
done

if [ ${#missing[@]} -ne 0 ]; then
  echo "Missing dependencies: ${missing[*]}" >&2
  if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root to install dependencies" >&2
    exit 1
  fi

  for cmd in "${missing[@]}"; do
    case "$cmd" in
      docker)
        apt-get update && apt-get install -y docker.io;;
      kubectl)
        curl -L -o /usr/local/bin/kubectl https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl && \
          chmod +x /usr/local/bin/kubectl;;
      helm)
        curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash;;
      kind)
        curl -Lo /usr/local/bin/kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64 && \
          chmod +x /usr/local/bin/kind;;
    esac
  done
else
  echo "All dependencies present." >&2
fi

# Ensure Python dependencies
if ! python -c "import kubernetes" >/dev/null 2>&1; then
  echo "Installing Python dependency: kubernetes" >&2
  pip install kubernetes >/dev/null
fi

echo "\nCreating Kubernetes cluster if absent..."
if ! kind get clusters | grep -q '^lora-cluster$'; then
  kind create cluster --name lora-cluster
else
  echo "Cluster 'lora-cluster' already exists." >&2
fi

helm repo add bitnami https://charts.bitnami.com/bitnami >/dev/null
helm repo add kedacore https://kedacore.github.io/charts >/dev/null
helm repo update >/dev/null

# Deploy core services
helm upgrade --install postgres bitnami/postgresql --namespace lora --create-namespace >/dev/null
helm upgrade --install rabbitmq bitnami/rabbitmq --namespace lora >/dev/null
helm upgrade --install minio bitnami/minio --namespace lora >/dev/null
helm upgrade --install keda kedacore/keda --namespace keda --create-namespace >/dev/null

echo "Deployment complete."
