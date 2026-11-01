"""Replaceable transcription adapter. Network access is never needed at inference time."""
import hashlib
import importlib.metadata
import json
import subprocess
import time
from pathlib import Path
from typing import Protocol

import av
import imageio_ffmpeg


class Transcriber(Protocol):
    def transcribe(self, audio: Path) -> dict: ...


class FasterWhisperTranscriber:
    def __init__(self, model_path: Path):
        self.model_path = model_path

    def transcribe(self, audio: Path) -> dict:
        from faster_whisper import WhisperModel
        model = WhisperModel(str(self.model_path), device="cpu", compute_type="int8", cpu_threads=4,
                             num_workers=1, local_files_only=True)
        segments, info = model.transcribe(str(audio), beam_size=5, vad_filter=True,
                                         condition_on_previous_text=False)
        rows = []
        for segment in segments:
            start, end = max(0, round(segment.start * 1000)), round(segment.end * 1000)
            if segment.text.strip() and end > start:
                rows.append({"start_ms": start, "end_ms": end, "text": segment.text.strip()})
        return {"language": info.language if rows else None, "segments": rows,
                "duration_ms": round(info.duration * 1000), "outcome": "speech" if rows else "no_speech"}


def analyze(input_path: Path, work: Path, model_path: Path, transcriber: Transcriber | None = None) -> dict:
    started = time.monotonic()
    with av.open(str(input_path), options={"protocol_whitelist": "file,pipe"}) as container:
        has_audio = bool(container.streams.audio)
        duration = max(0, round((container.duration or 0) / 1000))
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    provenance = {"provider": "faster-whisper", "provider_version": importlib.metadata.version("faster-whisper"),
                  "ctranslate2_version": importlib.metadata.version("ctranslate2"),
                  "model": model_path.name, "device": "cpu", "compute_type": "int8", "cpu_threads": 4,
                  "beam_size": 5, "vad_filter": True, "condition_on_previous_text": False,
                  "audio_stream": 0, "sample_rate": 16000, "channels": 1,
                  "ffmpeg_version": imageio_ffmpeg.get_ffmpeg_version(), "pipeline_version": 1}
    manifest = model_path / "reelmind-model.json"
    if manifest.is_file():
        metadata = json.loads(manifest.read_text(encoding="utf-8"))
        provenance["model_revision"] = metadata["revision"]
        provenance["model_sha256"] = metadata["model_sha256"]
    if not has_audio:
        result = {"outcome": "no_audio", "language": None, "duration_ms": duration, "segments": []}
    else:
        audio = work / "audio.wav"
        # Disable network protocols and playlists; paths are managed local copies, never URLs.
        subprocess.run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                        "-protocol_whitelist", "file,pipe", "-i", str(input_path), "-map", "0:a:0",
                        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        with audio.open("rb") as stream:
            provenance["audio_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
        result = (transcriber or FasterWhisperTranscriber(model_path)).transcribe(audio)
    provenance["elapsed_seconds"] = round(time.monotonic() - started, 3)
    result["provenance"] = provenance
    return result
