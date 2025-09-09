"""Kubernetes-based orchestrator for spawning and cleaning up workers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import time

# The kubernetes dependency is heavy and not always available in test
# environments.  We attempt to import it but fall back to lightweight stand-ins
# that mimic the attributes we need.  This keeps the module functional for
# unit tests without requiring the real Kubernetes package.
try:  # pragma: no cover - exercised implicitly when dependency exists
    from kubernetes import client, config  # type: ignore
except Exception:  # pragma: no cover - the stubbed fallback is tested
    class _Model(dict):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.__dict__ = self

    class client:  # type: ignore
        V1EnvVar = _Model
        V1Container = _Model
        V1VolumeMount = _Model
        V1PersistentVolumeClaimVolumeSource = _Model
        V1Volume = _Model
        V1PodSpec = _Model
        V1ObjectMeta = _Model
        V1PodTemplateSpec = _Model
        V1JobSpec = _Model
        V1Job = _Model
        BatchV1Api = object

    class config:  # type: ignore
        @staticmethod
        def load_incluster_config() -> None:
            return None

        @staticmethod
        def load_kube_config() -> None:
            return None


@dataclass
class WorkerSpec:
    """Configuration for a worker Job."""

    name: str
    image: str
    command: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    volumes: Optional[List["VolumeSpec"]] = None


@dataclass
class VolumeSpec:
    """Description of a volume to mount into the worker container."""

    name: str
    mount_path: str
    persistent_volume_claim: str


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

        volume_mounts = []
        volumes = []
        for v in spec.volumes or []:
            volume_mounts.append(client.V1VolumeMount(name=v.name, mount_path=v.mount_path))
            pvc_src = client.V1PersistentVolumeClaimVolumeSource(claim_name=v.persistent_volume_claim)
            volumes.append(client.V1Volume(name=v.name, persistent_volume_claim=pvc_src))

        container = client.V1Container(
            name="worker",
            image=spec.image,
            command=spec.command,
            env=env_vars,
            volume_mounts=volume_mounts or None,
        )
        pod_spec = client.V1PodSpec(
            restart_policy="Never",
            containers=[container],
            volumes=volumes or None,
        )
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"job": spec.name}),
            spec=pod_spec,
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
