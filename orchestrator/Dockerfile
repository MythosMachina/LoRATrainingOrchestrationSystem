FROM python:3.11-slim

WORKDIR /app
COPY orchestrator/ /app/orchestrator

RUN pip install --no-cache-dir kubernetes

ENTRYPOINT ["python", "-m", "orchestrator.k8s_orchestrator"]
