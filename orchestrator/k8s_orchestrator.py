"""Kubernetes-based orchestrator for spawning and cleaning up workers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from kubernetes import client, config
import time


@dataclass
class WorkerSpec:
    """Configuration for a worker Job."""

    name: str
    image: str
    command: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None


class KubernetesOrchestrator:
    """Controls lifecycle of training workers on Kubernetes."""

    def __init__(self, namespace: str = "lora-workers", batch_api: Optional[client.BatchV1Api] = None):
        # Allow dependency injection for testing
        if batch_api is None:
            try:
                config.load_incluster_config()
            except Exception:
                # Fall back to local config; tests may not have any config
                try:
                    config.load_kube_config()
                except Exception:
                    pass
            batch_api = client.BatchV1Api()
        self.batch_api = batch_api
        self.namespace = namespace

    # -------------------- core lifecycle methods --------------------
    def spawn_worker(self, spec: WorkerSpec) -> client.V1Job:
        """Create a Kubernetes Job for the worker."""
        env_vars = [client.V1EnvVar(name=k, value=v) for k, v in (spec.env or {}).items()]
        container = client.V1Container(
            name="worker",
            image=spec.image,
            command=spec.command,
            env=env_vars,
        )
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"job": spec.name}),
            spec=client.V1PodSpec(restart_policy="Never", containers=[container]),
        )
        job_spec = client.V1JobSpec(template=template, backoff_limit=0)
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=spec.name),
            spec=job_spec,
        )
        return self.batch_api.create_namespaced_job(self.namespace, job)

    def wait_for_completion(self, name: str, timeout: int = 3600) -> None:
        """Block until the job succeeds or fails."""
        start = time.time()
        while True:
            job = self.batch_api.read_namespaced_job(name, self.namespace)
            status = job.status
            if status.succeeded:
                return
            if status.failed:
                raise RuntimeError(f"Worker {name} failed")
            if time.time() - start > timeout:
                raise TimeoutError(f"Timed out waiting for job {name}")
            time.sleep(5)

    def cleanup_worker(self, name: str) -> None:
        """Delete the worker Job and its pods."""
        self.batch_api.delete_namespaced_job(
            name=name,
            namespace=self.namespace,
            propagation_policy="Background",
        )

    def run_worker(self, spec: WorkerSpec, timeout: int = 3600) -> None:
        """Spawn, wait for completion, and clean up the worker."""
        self.spawn_worker(spec)
        try:
            self.wait_for_completion(spec.name, timeout=timeout)
        finally:
            self.cleanup_worker(spec.name)
