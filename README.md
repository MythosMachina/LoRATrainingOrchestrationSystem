# LoRATrainingOrchestrationSystem
We will build an automated LoRA training platform with ephemeral container workers. A central orchestrator manages jobs, SQL tracks state, and storage holds models, datasets, and outputs. A web UI enables dataset upload, model selection (SD1.5/SDXL), and job submission. All training steps run fully automated.

## Orchestrator

`orchestrator` contains a `KubernetesOrchestrator` class that spawns worker jobs on a Kubernetes cluster and deletes them after completion. Example usage:

```python
from orchestrator import KubernetesOrchestrator, WorkerSpec

orch = KubernetesOrchestrator()
spec = WorkerSpec(name="demo", image="alpine:latest", command=["echo", "hello"])
orch.run_worker(spec)
```

This ensures each worker is created, monitored until it finishes, and then cleaned up.

## Deployment

Run `scripts/deploy.sh` to perform preflight checks, install any missing system
dependencies, and bootstrap a local Kubernetes cluster with PostgreSQL,
RabbitMQ, MinIO, and KEDA:

```bash
sudo ./scripts/deploy.sh
```

The script installs required CLI tools (Docker, kubectl, helm, kind) and the
Python `kubernetes` package if they are missing, then provisions the cluster and
services using Helm charts.

## Images

Use the helper scripts in `scripts/` to build container images:

- `build_orchestrator_image.sh` produces the control-plane image.
- `build_worker_image.sh` builds a GPU-enabled training image that accepts its configuration via the `JOB_CONFIG` environment variable and can train SD1.5 or SDXL models based on that configuration.
