import types
from pathlib import Path
from unittest import mock
import sys

# Ensure the package root is importable when tests are executed from the tests
# directory.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from orchestrator import KubernetesOrchestrator, WorkerSpec, VolumeSpec


def test_run_worker_lifecycle():
    # Prepare mock BatchV1Api
    batch_api = mock.Mock()

    # read_namespaced_job will be called and should report success once
    job_status = types.SimpleNamespace(succeeded=1, failed=0)
    job = types.SimpleNamespace(status=job_status)
    batch_api.read_namespaced_job.return_value = job

    orchestrator = KubernetesOrchestrator(batch_api=batch_api)

    spec = WorkerSpec(name="test-job", image="alpine:latest", command=["echo", "hi"])
    orchestrator.run_worker(spec, timeout=1)

    # ensure lifecycle methods were called
    batch_api.create_namespaced_job.assert_called_once()
    batch_api.read_namespaced_job.assert_called()
    batch_api.delete_namespaced_job.assert_called_once()


def test_spawn_worker_with_volume():
    batch_api = mock.Mock()
    orchestrator = KubernetesOrchestrator(batch_api=batch_api)
    spec = WorkerSpec(
        name="train-job",
        image="trainer:latest",
        volumes=[VolumeSpec(name="data", mount_path="/data", persistent_volume_claim="minio-pvc")],
    )

    orchestrator.spawn_worker(spec)

    batch_api.create_namespaced_job.assert_called_once()
    job = batch_api.create_namespaced_job.call_args[0][1]
    container = job.spec.template.spec.containers[0]
    assert container.volume_mounts[0].mount_path == "/data"
    assert job.spec.template.spec.volumes[0].persistent_volume_claim.claim_name == "minio-pvc"
