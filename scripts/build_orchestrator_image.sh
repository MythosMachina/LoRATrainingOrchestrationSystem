#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=${1:-lora-orchestrator:latest}

docker build -f orchestrator/Dockerfile -t "${IMAGE_NAME}" .
