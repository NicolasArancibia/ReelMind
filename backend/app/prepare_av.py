"""Explicit preparation; models stay outside the repository."""
import json
from app.config import get_settings
from app.local_ai import local_provider, VISION_MODEL, TEXT_MODEL
from app.db import get_engine
from app.processing import ManualEngine


def prepare(root):
    with local_provider(root) as provider:
        for model in (VISION_MODEL, TEXT_MODEL):
            installed = {row['name'] for row in provider.inventory()}
            if model not in installed:
                print(f"Preparando {model}…", flush=True)
                provider.pull(model)
        selected = [row for row in provider.inventory() if row['name'] in {VISION_MODEL, TEXT_MODEL}]
        if len(selected) != 2:
            raise ValueError('Preparación incompleta.')
        for row in selected:
            info = provider.client.post('/api/show', json={'model': row['name']}).json()
            thinking = info.get('thinking') or {}
            if thinking.get('default') is True or thinking.get('values') == [True]:
                raise ValueError('Se requiere una variante Instruct sin razonamiento interno.')
            row['capabilities'] = info['capabilities']
            row['thinking'] = info.get('thinking')
        smoke = provider.chat(TEXT_MODEL, 'Devuelve solo el JSON solicitado.', 'Devuelve ok verdadero.',
            {'type':'object','properties':{'ok':{'type':'boolean','const':True}},'required':['ok'],'additionalProperties':False}, num_predict=64)
        if smoke != {'ok': True}:
            raise ValueError('El modelo de síntesis no respondió al ensayo estructurado.')
        manifest = {"ollama_version": provider.version(), "models": selected}
    target = root / "models" / "audiovisual.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Modelos preparados; no se inició análisis.")


def main():
    engine = get_engine()
    processor = ManualEngine(engine)
    reservation = processor.acquire()
    if reservation is None:
        raise RuntimeError('Los recursos están reservados; detén el motor antes de preparar modelos.')
    try:
        prepare(get_settings().data_root)
    finally:
        processor.release(reservation)
        engine.dispose()


if __name__ == '__main__':
    main()
