import hashlib
import json
from pathlib import Path
import pytest
from app.maintenance import contained,validate_bundle,validate_media_path


def bundle(tmp_path):
    root=tmp_path/'copy'; root.mkdir(); (root/'database.dump').write_bytes(b'fixture')
    payload=b'video fixture'; checksum=hashlib.sha256(payload).hexdigest()
    relative=f'media/{checksum[:2]}/{checksum}'
    target=root/'data'/relative; target.parent.mkdir(parents=True);target.write_bytes(payload)
    manifest={'format':1,'schema':'0008_graph','database_sha256':hashlib.sha256(b'fixture').hexdigest(),
        'tables':{'media_files':{'count':1}},
        'files':[{'local_path':relative,'checksum':checksum,'size_bytes':len(payload)}]}
    (root/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    return root,target,manifest


def test_containment_and_strict_media_paths(tmp_path):
    for relative in ('../outside','',str(tmp_path.parent.resolve())):
        with pytest.raises(ValueError): contained(tmp_path,relative)
    with pytest.raises(ValueError): validate_media_path({'checksum':'a'*64,'local_path':'media/../secrets'})


def test_corrupt_same_size_media_rejected_before_restore(tmp_path):
    root,target,_=bundle(tmp_path); validate_bundle(root)
    target.write_bytes(b'X'*target.stat().st_size)
    with pytest.raises(ValueError,match='corrupto'): validate_bundle(root)


def test_dump_corruption_and_duplicate_media_rejected(tmp_path):
    root,_,manifest=bundle(tmp_path)
    manifest['files']*=2;manifest['tables']['media_files']['count']=2;(root/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='repetida'): validate_bundle(root)
    (root/'database.dump').write_bytes(b'changed')
    with pytest.raises(ValueError,match='SQL'): validate_bundle(root)


def test_missing_manifest_entry_rejected(tmp_path):
    root,_,manifest=bundle(tmp_path);manifest['files']=[]
    (root/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='todos los medios'): validate_bundle(root)
