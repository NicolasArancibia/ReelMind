import httpx
import pytest
from app.local_ai import OllamaProvider, VISION_MODEL, TEXT_MODEL, prepared


def test_provider_only_calls_local_structured_chat_and_unloads():
    def handler(request):
        import json
        body = json.loads(request.content)
        assert request.url.host == '127.0.0.1' and request.url.path == '/api/chat'
        assert body['keep_alive'] == 0 and 'think' not in body and body['stream'] is False
        assert body['messages'][0]['role'] == 'system'
        return httpx.Response(200, json={'done': True, 'done_reason': 'stop', 'message': {'content': '{"ok":true}'}})
    with httpx.Client(base_url='http://127.0.0.1:11435', transport=httpx.MockTransport(handler)) as client:
        assert OllamaProvider(client).chat(VISION_MODEL, 'system', 'data', {}) == {'ok': True}


@pytest.mark.parametrize('reply', [
    {'done': True, 'done_reason': 'length', 'message': {'content': '{}'}},
    {'done': False, 'message': {'content': '{}'}},
    {'done': True, 'done_reason': 'stop', 'message': {'content': 'not JSON'}},
    {'done': True, 'done_reason': 'stop', 'message': {'content': '{}', 'thinking': 'unexpected'}},
])
def test_provider_rejects_incomplete_or_invalid_json(reply):
    with httpx.Client(base_url='http://127.0.0.1:11435', transport=httpx.MockTransport(lambda r: httpx.Response(200, json=reply))) as client:
        with pytest.raises(ValueError): OllamaProvider(client).chat(VISION_MODEL, 'system', 'data', {})


def test_preparation_requires_the_explicit_instruct_pair(tmp_path):
    import json
    folder=tmp_path/'models'; folder.mkdir()
    assert not prepared(tmp_path)
    manifest=folder/'audiovisual.json'
    manifest.write_text(json.dumps({'models':[{'name':'qwen3-vl:4b'},{'name':'qwen3:4b'}]}))
    assert not prepared(tmp_path)
    manifest.write_text(json.dumps({'models':[{'name':VISION_MODEL},{'name':TEXT_MODEL}]}))
    assert prepared(tmp_path)


def test_preparation_does_not_certify_thinking_weights(monkeypatch, media_root):
    from contextlib import contextmanager
    from app.prepare_av import prepare
    class Reply:
        def json(self): return {'capabilities':['completion','thinking'], 'thinking':{'default':True,'values':[True]}}
    class Client:
        def post(self,*args,**kwargs): return Reply()
    class Provider:
        client=Client()
        def inventory(self): return [{'name':VISION_MODEL,'digest':'v'}, {'name':TEXT_MODEL,'digest':'t'}]
    @contextmanager
    def provider(root): yield Provider()
    monkeypatch.setattr('app.prepare_av.local_provider', provider)
    with pytest.raises(ValueError,match='Instruct'): prepare(media_root)
    assert not prepared(media_root)


def test_synthesis_unloads_vision_before_loading_text():
    from app.audiovisual import LocalText
    calls=[]
    class Provider:
        def unload(self, model): calls.append(('unload', model))
        def chat(self, model, *args, **kwargs):
            calls.append(('chat', model))
            return {'evidence_ids':['v0']}
    result=LocalText(Provider()).synthesize([{'id':'v0','kind':'visual','description':'Fotograma'}])
    assert calls == [('unload', VISION_MODEL), ('chat', TEXT_MODEL)]
    assert result.claims[0].text == 'En el vídeo se observa: «Fotograma».'
    assert result.claims[0].evidence_ids == ['v0']
