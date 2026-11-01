"""Explicit local acceptance exercise. Never called by the app or normal tests.

Downloads six CC-BY-SA 4.0 Chilean Spanish samples from the linked corpus when missing.
Stores media and detailed reports in REELMIND_DATA_ROOT/verification-phase2, outside Git.
Run with the backend Python 3.13 environment and REELMIND_DATA_ROOT configured.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from types import SimpleNamespace
import urllib.request
from uuid import uuid4

import imageio_ffmpeg
import psutil

from app.processing import run_audio, Cancelled


def words(value):
    return re.findall(r"\w+", value.casefold())


def distance(a, b):
    row = list(range(len(b) + 1))
    for i, word in enumerate(a, 1):
        next_row = [i]
        for j, other in enumerate(b, 1):
            next_row.append(min(next_row[-1] + 1, row[j] + 1, row[j - 1] + (word != other)))
        row = next_row
    return row[-1]


def main():
    root = Path(os.environ['REELMIND_DATA_ROOT']).resolve()
    work = root / 'verification-phase2'; work.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    def ff(args):
        subprocess.run([ffmpeg, '-nostdin', '-loglevel', 'error', '-y', *args], check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    cases = []
    for subset in ('female', 'male'):
        metadata = work / f'{subset}.json'
        if not metadata.exists():
            with urllib.request.urlopen(f'https://datasets-server.huggingface.co/rows?dataset=ylacombe/google-chilean-spanish&config={subset}&split=train&offset=0&length=3', timeout=60) as response:
                metadata.write_bytes(response.read())
        for row in json.loads(metadata.read_text(encoding='utf-8'))['rows']:
            name = f'{subset}-{row["row_idx"]}'
            wav, video = work / f'{name}.wav', work / f'{name}.mp4'
            if not wav.exists():
                urllib.request.urlretrieve(row['row']['audio'][0]['src'], wav)
            if not video.exists():
                ff(['-f', 'lavfi', '-i', 'color=c=black:s=320x180:r=10', '-i', str(wav), '-shortest', '-c:v', 'libx264', '-c:a', 'aac', str(video)])
            cases.append((name, row['row']['text'], 'speech'))
    for name, audio in (('silence', 'anullsrc=r=16000:cl=mono'), ('tone', 'sine=frequency=440:sample_rate=16000')):
        ff(['-f', 'lavfi', '-i', 'color=c=black:s=320x180:r=10', '-f', 'lavfi', '-i', audio, '-t', '8', '-c:v', 'libx264', '-c:a', 'aac', str(work / f'{name}.mp4')])
        cases.append((name, '', 'no_speech'))
    ff(['-f', 'lavfi', '-i', 'color=c=black:s=320x180:r=10', '-t', '3', '-an', '-c:v', 'libx264', str(work / 'no-audio.mp4')])
    cases.append(('no-audio', '', 'no_audio'))
    report = []
    parent = psutil.Process()
    for name, reference, expected in cases:
        path = work / f'{name}.mp4'
        with path.open('rb') as stream:
            checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
        asset = SimpleNamespace(file=SimpleNamespace(local_path=path.relative_to(root).as_posix(), checksum=checksum))
        peak = 0
        def monitor():
            nonlocal peak
            memory = 0
            for child in parent.children(recursive=True):
                try:
                    memory += child.memory_info().rss
                except psutil.Error:
                    pass
            peak = max(peak, memory)
            return False
        started = time.monotonic()
        result = run_audio(asset, uuid4(), monitor)
        hypothesis = ' '.join(s['text'] for s in result['segments'])
        errors = distance(words(reference), words(hypothesis))
        record = {'sample': name, 'expected': expected, 'reference': reference, 'hypothesis': hypothesis,
                  'word_errors': errors, 'reference_words': len(words(reference)),
                  'wall_seconds': round(time.monotonic() - started, 3), 'peak_rss_mib': round(peak / 1024**2, 1), **result}
        report.append(record)
        print(json.dumps({k: record[k] for k in ('sample', 'outcome', 'hypothesis', 'word_errors', 'reference_words', 'wall_seconds', 'peak_rss_mib')}, ensure_ascii=False), flush=True)
        assert result['outcome'] == expected
    (work / f'report-{os.environ.get("REELMIND_WHISPER_MODEL", "small")}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    # Exercise actual cancellation during model loading/inference, then release the process tree.
    started = time.monotonic()
    try:
        path = work / 'female-2.mp4'
        with path.open('rb') as stream:
            checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
        asset = SimpleNamespace(file=SimpleNamespace(local_path=path.relative_to(root).as_posix(), checksum=checksum))
        run_audio(asset, uuid4(), lambda: time.monotonic() - started > 1)
        raise AssertionError('Cancellation did not interrupt')
    except Cancelled:
        assert not parent.children(recursive=True)
        print(f'Real cancellation and process release: {time.monotonic() - started:.3f}s', flush=True)


if __name__ == '__main__':
    main()
