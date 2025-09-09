# LoRATrainingOrchestrationSystem

We will build an automated LoRA training platform with ephemeral container workers. A central orchestrator manages jobs, SQL tracks state, and storage holds models, datasets, and outputs. A web UI enables dataset upload, model selection (SD1.5/SDXL), and job submission. All training steps run fully automated.

## Development environment

Use `deploy_env.sh` to perform a preflight check and install required system and Python dependencies. After the check, you can launch core infrastructure services (PostgreSQL, RabbitMQ, MinIO) with Docker Compose:

```bash
./deploy_env.sh
# once dependencies are installed
docker-compose up -d
```

This brings up the storage and messaging services needed for development.
