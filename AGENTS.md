
---

# LoRA Training Orchestration System — Technical Specification

## Overview

We aim to build a distributed, automated LoRA training platform with ephemeral containerized workers. The system will provide a central storage backend for models, datasets, and outputs, as well as an orchestrator that schedules jobs, tracks state in a SQL database, and scales worker nodes automatically. A web-based user interface will allow uploading tagged datasets, selecting the base model type (e.g., Stable Diffusion 1.5 or SDXL), and submitting training jobs. All subsequent steps (hyperparameter selection, worker orchestration, logging, artifact storage) are fully automated.

## System Components

1. **Orchestrator / Control Plane**

   * API Layer: FastAPI (Python)
   * Metadata Database: PostgreSQL
   * Queue: RabbitMQ (robust)
   * Auto-scaling: KEDA on Kubernetes

2. **Execution Layer (Workers)**

   * Ephemeral containers (Docker), running as Kubernetes Jobs
   * Each worker is created on demand and destroyed after job completion
   * Base images for different training families (SD1.5, SDXL)
   * NVIDIA GPU scheduling with Kubernetes device plugin

3. **Storage**

   * MinIO (S3-compatible) for datasets, models, and artifacts
   * PostgreSQL for job and worker metadata
   * Optional: MLflow for metrics and artifact tracking (backed by MinIO)

4. **Web Interface**

   * Frontend: Next.js + Tailwind CSS
   * Backend: FastAPI integration
   * Features: dataset upload, dataset validation, job creation, job monitoring, artifact download, metrics visualization

## Data Model (Core Tables)

* `datasets(id, name, s3_uri, num_images, tags_json, created_at)`
* `models(id, base_type ENUM('sd15','sdxl'), s3_uri, checksum, created_at)`
* `jobs(id, dataset_id, model_id, base_type, params_json, priority, status ENUM('queued','running','succeeded','failed','cancelled'), created_at, started_at, finished_at)`
* `workers(id, node_name, job_id NULL, pod_name, gpu_type, status ENUM('idle','running','done','failed','lost'), last_heartbeat, started_at, finished_at)`
* `events(id, job_id, level, message, ts)`
* `artifacts(id, job_id, kind ENUM('lora','log','tensorboard','preview'), s3_uri, sha256, created_at)`
* `metrics(id, job_id, step, key, value, ts)`

The orchestrator is the single source of truth; Kubernetes is the execution layer.

## Job Lifecycle

1. **Dataset Upload**

   * User uploads tagged dataset via web UI → stored in MinIO (`s3://datasets/...`)
   * Orchestrator validates dataset (count, resolution, tags) → inserts into `datasets`

2. **Job Creation**

   * User selects base type (SD1.5 or SDXL)
   * Orchestrator creates job entry in `jobs` with parameter JSON

3. **Hyperparameter Selection**

   * Based on dataset size:

     * < 80 images: LoCon, low network\_dim (8–16), aggressive regularization
     * 80–400 images: standard LoRA, dim 16–32
     * > 400 images: higher dim (32–64), optional prior loss, face fixes

4. **Queueing & Scaling**

   * Job enters Redis/RabbitMQ queue
   * KEDA scales Kubernetes jobs based on queue length

5. **Worker Execution**

   * Worker pulls dataset and base model from MinIO
   * Runs training with configured parameters
   * Sends regular heartbeats and logs to orchestrator

6. **Metrics & Artifacts**

   * Worker reports metrics (loss, learning rate, step count) → `metrics`
   * Previews and final artifacts stored in MinIO and registered in `artifacts`

7. **Completion & Teardown**

   * Worker updates job status to `succeeded`
   * Pod is deleted automatically (ephemeral execution)
   * Database updated (`workers.status = 'done'`)
   * Artifacts remain in MinIO for download

## Auto-Scaling

* KEDA monitors job queue length
* Spawns new workers when demand increases
* Workers are destroyed after job completion
* PostgreSQL tracks all worker and job state for auditing and reproducibility

## Security & Reliability

* Kubernetes namespaces separate orchestrator, workers, and storage
* RBAC: Orchestrator limited to creating/deleting jobs in worker namespace
* Resource quotas and GPU limits enforced
* Orchestrator retries jobs if workers fail or miss heartbeats (> 60s)
* All artifacts versioned in MinIO (by job ID and commit hash)

## Benefits

* Fully automated LoRA training pipeline
* Ephemeral and reproducible workers (no stale environments)
* Scalable across multiple GPU nodes
* Centralized metadata, logging, and artifact tracking
* User-friendly interface with minimal required inputs

---
