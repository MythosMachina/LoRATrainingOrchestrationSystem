import json
import os
from pathlib import Path


def load_config():
    """Load job configuration from JOB_CONFIG environment variable."""
    raw = os.getenv("JOB_CONFIG")
    if not raw:
        raise RuntimeError("JOB_CONFIG environment variable not set")
    return json.loads(raw)


def download_resources(cfg):
    """Simulate pulling dataset and model as described in the job lifecycle."""
    dataset = cfg.get("dataset_uri")
    model = cfg.get("model_uri")
    print(f"Pulling dataset from {dataset}")
    print(f"Pulling base model from {model}")


def train(cfg):
    base_type = cfg.get("base_type", "sdxl")
    print(f"Starting {base_type} training")
    # Placeholder: actual training logic would go here


def upload_artifacts(cfg):
    out_dir = Path(cfg.get("output_path", "./outputs"))
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Uploading artifacts from {out_dir}")


def main():
    cfg = load_config()
    download_resources(cfg)
    train(cfg)
    upload_artifacts(cfg)


if __name__ == "__main__":
    main()
