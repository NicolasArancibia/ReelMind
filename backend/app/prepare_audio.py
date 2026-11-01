"""Explicit provisioning command, never imported by API startup."""
import hashlib
import json
import os
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download


def main():
    root = Path(os.environ["REELMIND_DATA_ROOT"]).resolve()
    model = os.environ.get("REELMIND_WHISPER_MODEL", "small")
    if model not in {"tiny", "base", "small", "medium"}:
        raise ValueError("Modelo no admitido.")
    repository = f"Systran/faster-whisper-{model}"
    path = root / "models" / model
    # Pin the immutable revision, record actual model bytes, and operate offline afterwards.
    manifest = path / "reelmind-model.json"
    metadata = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else None
    revision = metadata["revision"] if metadata else (
        "536b0662742c02347bc0e980a01041f333bce120" if model == "small" else HfApi().model_info(repository).sha)
    if metadata and all((path / name).is_file() for name in ("model.bin", "config.json", "tokenizer.json")):
        with (path / "model.bin").open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != metadata["model_sha256"]:
                raise RuntimeError("El modelo local cambió. Conserva sus archivos y revisa la instalación.")
        print(f"Modelo {model} ya preparado y verificado; no se actualiza automáticamente.")
        return
    snapshot_download(repository, revision=revision, local_dir=path,
                      allow_patterns=["config.json", "model.bin", "tokenizer.json", "vocabulary.*"])
    with (path / "model.bin").open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    (path / "reelmind-model.json").write_text(json.dumps({"repository": repository, "revision": revision,
                                                        "model_sha256": checksum}, indent=2), encoding="utf-8")
    print(f"Modelo {model} preparado: revisión {revision}; SHA-256 {checksum}")


if __name__ == "__main__":
    main()
