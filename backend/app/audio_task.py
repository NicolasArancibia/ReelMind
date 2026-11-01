"""Isolated heavy process: no DB credentials and no automatic model downloads."""
import hashlib
import json
import sys
from pathlib import Path


def main():
    # Parent assigns this process to a kill-on-close job before letting it do work.
    if sys.stdin.buffer.read(1) != b"1":
        return
    from app.audio import analyze
    path, work, model, checksum = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
    stage = 'audio'
    def progress(value):
        nonlocal stage
        stage = value
        (work/'progress.json').write_text(json.dumps({'stage':value}),encoding='utf-8')
    def checkpoint(rows):
        (work / 'evidence.json').write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
    try:
        with path.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != checksum:
                raise ValueError("checksum")
        progress('audio')
        result = analyze(path, work, model)
        if len(sys.argv) > 5 and sys.argv[5] == 'audiovisual':
            from app.audiovisual import analyze as analyze_av, LocalVision, LocalText
            from app.local_ai import local_provider
            root = model.parents[1]
            manifest = json.loads((root / 'models' / 'audiovisual.json').read_text(encoding='utf-8'))
            with local_provider(root) as provider:
                actual = {m['name']: m['digest'] for m in provider.inventory()}
                if any(actual.get(m['name']) != m['digest'] for m in manifest['models']):
                    raise ValueError('Cambió el modelo preparado.')
                result['analysis'] = analyze_av(path, result, LocalVision(provider), LocalText(provider), progress, checkpoint)
                result['analysis']['provenance'].update(ollama_version=provider.version(), models=manifest['models'], source_sha256=checksum)
    except Exception as exc:
        # Metadata only; never log prompts, imported text, credentials or model output.
        diagnosis = {'stage': stage, 'error_type': type(exc).__name__}
        if hasattr(exc, 'reason'):
            diagnosis['reason'] = exc.reason
        if hasattr(exc, 'response'):
            diagnosis['http_status'] = exc.response.status_code
        if type(exc).__name__ == 'ValidationError':
            diagnosis['fields'] = [list(e['loc']) for e in exc.errors(include_input=False)]
        diagnostics = model.parents[1] / 'diagnostics'
        diagnostics.mkdir(exist_ok=True)
        (diagnostics / f'{work.name}.json').write_text(json.dumps(diagnosis), encoding='utf-8')
        if (work / 'evidence.json').is_file():
            (diagnostics / f'{work.name}-evidence.json').write_bytes((work / 'evidence.json').read_bytes())
        result = {"error": "No se pudo leer o transcribir el vídeo. Comprueba el archivo y el modelo local; puedes reintentar."}
    (work / "result.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
