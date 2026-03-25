"""Bootstrap ML model assets for first-time setup on a new machine.

This script:
1) downloads ViT emotion model weights to python_host/models/vit-emotion
2) warms up DeepFace emotion analysis so model weights are cached locally
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np


def _default_vit_local_dir() -> Path:
    here = Path(__file__).resolve().parent
    return here / "models" / "vit-emotion"


def bootstrap_vit(repo_id: str, local_dir: Path) -> None:
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise RuntimeError(
            "huggingface_hub is not available. Install ML deps first: "
            "python -m pip install -r python_host/requirements-ml.txt"
        ) from exc

    local_dir.mkdir(parents=True, exist_ok=True)
    print(f"[ViT] Downloading {repo_id} -> {local_dir}")
    snapshot_download(
        repo_id=repo_id,
        local_dir=str(local_dir),
        local_dir_use_symlinks=False,
    )
    print("[ViT] Ready")


def warmup_deepface() -> None:
    try:
        from deepface import DeepFace
    except ImportError as exc:
        raise RuntimeError(
            "DeepFace is not available. Install ML deps first: "
            "python -m pip install -r python_host/requirements-ml.txt"
        ) from exc

    # Dummy frame is enough to trigger weight loading/caching.
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    print("[DeepFace] Running one warmup inference for emotion cache")
    DeepFace.analyze(img, actions=["emotion"], enforce_detection=False, silent=True)
    print("[DeepFace] Ready")


def verify_vit_local(local_dir: Path) -> None:
    from python_host.vision.vit_emotion import ViTEmotionDetector

    prev_hf_offline = os.environ.get("HF_HUB_OFFLINE")
    prev_tf_offline = os.environ.get("TRANSFORMERS_OFFLINE")
    try:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        detector = ViTEmotionDetector(repo_id=str(local_dir))
        if not detector.load_model():
            raise RuntimeError("ViT local verification failed: detector.load_model() returned False")
    finally:
        if prev_hf_offline is None:
            os.environ.pop("HF_HUB_OFFLINE", None)
        else:
            os.environ["HF_HUB_OFFLINE"] = prev_hf_offline
        if prev_tf_offline is None:
            os.environ.pop("TRANSFORMERS_OFFLINE", None)
        else:
            os.environ["TRANSFORMERS_OFFLINE"] = prev_tf_offline

    print("[Verify] ViT local-only load passed")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Bootstrap local ML model caches")
    p.add_argument("--repo-id", default="yst007/vit-emotion", help="Hugging Face model repo id")
    p.add_argument(
        "--vit-local-dir",
        default=str(_default_vit_local_dir()),
        help="Local directory for ViT model snapshot",
    )
    p.add_argument("--skip-vit", action="store_true", help="Skip ViT snapshot download")
    p.add_argument("--skip-deepface", action="store_true", help="Skip DeepFace warmup")
    p.add_argument(
        "--verify-vit-local",
        action="store_true",
        help="After download, verify ViT can load in local-only mode",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    local_dir = Path(args.vit_local_dir).expanduser().resolve()

    if args.skip_vit and args.skip_deepface:
        print("Nothing to do: both --skip-vit and --skip-deepface are enabled.")
        return 0

    if not args.skip_vit:
        bootstrap_vit(args.repo_id, local_dir)
        if args.verify_vit_local:
            verify_vit_local(local_dir)

    if not args.skip_deepface:
        warmup_deepface()

    print("Bootstrap complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
