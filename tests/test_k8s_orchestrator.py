import types
from unittest import mock

from orchestrator import KubernetesOrchestrator, WorkerSpec


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
