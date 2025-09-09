#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=${1:-lora-training-worker:latest}

docker build -f worker/Dockerfile -t "${IMAGE_NAME}" .
