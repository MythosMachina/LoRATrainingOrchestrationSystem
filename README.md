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
