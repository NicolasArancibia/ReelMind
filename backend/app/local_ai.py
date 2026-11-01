"""Project-owned Ollama provider. No shared daemon or implicit downloads."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time

import httpx
from app.process_guard import ProcessGuard

VISION_MODEL = "qwen3-vl:4b-instruct-q4_K_M"
TEXT_MODEL = "qwen3:4b-instruct-2507-q4_K_M"
VISION_OPTIONS = {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "repeat_penalty": 1.0, "presence_penalty": 1.5, "seed": 42}
TEXT_OPTIONS = {**VISION_OPTIONS, "min_p": 0}
BASE_URL = "http://127.0.0.1:11435"

class IncompleteResponse(ValueError):
    def __init__(self, reason):
        self.reason = reason if reason in {'length', 'stop', 'load', 'unload'} else 'unknown'
        super().__init__('Respuesta incompleta del modelo.')


@contextmanager
def local_provider(root: Path):
    # Never attach to another project, even if it happens to use the same port.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 11435))
    executable = shutil.which("ollama")
    if not executable:
        raise RuntimeError("Ollama no está disponible.")
    env = {k: v for k, v in os.environ.items() if k not in {"PGPASSWORD", "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"}}
    env.update(OLLAMA_HOST="127.0.0.1:11435", OLLAMA_MODELS=str(root / "models" / "ollama"),
               OLLAMA_NUM_PARALLEL="1", OLLAMA_MAX_LOADED_MODELS="1", OLLAMA_NO_CLOUD="1")
    process = subprocess.Popen([executable, "serve"], env=env, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    guard = None
    try:
        guard = ProcessGuard(process)
        with httpx.Client(base_url=BASE_URL, trust_env=False, timeout=600) as client:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError("No se pudo iniciar el proveedor local.")
                try:
                    response = client.get("/api/version", timeout=1)
                    response.raise_for_status()
                    break
                except httpx.HTTPError:
                    time.sleep(.1)
            else:
                raise TimeoutError("Proveedor local no disponible.")
            yield OllamaProvider(client)
    finally:
        if guard:
            guard.close()
        elif process.poll() is None:
            process.kill()
        process.wait()


class OllamaProvider:
    def __init__(self, client):
        self.client = client

    def chat(self, model, system, prompt, schema, images=None, num_predict=1536):
        if len(prompt) > 9000:
            raise ValueError('La evidencia excede el contexto acotado de síntesis.')
        response = self.client.post("/api/chat", json={"model": model, "stream": False,
            "keep_alive": '5m' if images else 0, "format": schema,
            "options": {"num_ctx": 4096, "num_predict": num_predict, **(VISION_OPTIONS if images else TEXT_OPTIONS)},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": prompt, "images": images or []}]})
        response.raise_for_status()
        data = response.json()
        if data.get('message', {}).get('thinking'):
            raise ValueError('El proveedor activó razonamiento interno no solicitado.')
        if not data.get("done") or data.get("done_reason") != "stop":
            raise IncompleteResponse(data.get('done_reason'))
        return json.loads(data["message"]["content"])

    def unload(self, model):
        response = self.client.post('/api/generate', json={'model':model, 'keep_alive':0, 'stream':False})
        response.raise_for_status()

    def inventory(self):
        response = self.client.get("/api/tags"); response.raise_for_status()
        return response.json()["models"]

    def version(self):
        return self.client.get("/api/version").json()["version"]

    def pull(self, model):
        # Called only by the explicit preparation command.
        with self.client.stream("POST", "/api/pull", json={"model": model}) as response:
            response.raise_for_status()
            last_progress = -1
            for line in response.iter_lines():
                event = json.loads(line)
                if "error" in event:
                    raise RuntimeError(event["error"])
                if event.get('total'):
                    progress = int(event.get('completed', 0) * 100 / event['total']) // 20 * 20
                    if progress != last_progress:
                        print(f"{model}: {progress}%", flush=True)
                        last_progress = progress


def prepared(root):
    try:
        manifest = json.loads((root / "models" / "audiovisual.json").read_text(encoding='utf-8'))
        return {row['name'] for row in manifest['models']} == {VISION_MODEL, TEXT_MODEL}
    except (OSError, ValueError, KeyError, TypeError):
        return False
