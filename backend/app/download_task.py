"""Network-only child: no DB credentials, browser cookies, shell or model access."""
import ipaddress
import json
from pathlib import Path
import socket
import sys
import urllib.request
from urllib.parse import urlsplit


def public_url(url):
    parsed=urlsplit(url)
    if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password or parsed.port not in {None,80,443}:
        raise ValueError('network')
    addresses=socket.getaddrinfo(parsed.hostname,parsed.port or (443 if parsed.scheme=='https' else 80),type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global or ipaddress.ip_address(row[4][0]).is_multicast for row in addresses):raise ValueError('network')
    return url


def main():
    if sys.stdin.buffer.read(1)!=b'1':return
    work=Path(sys.argv[1]);limit=int(sys.argv[2]);url=sys.stdin.buffer.readline().decode('utf-8').strip()
    from yt_dlp import YoutubeDL
    from yt_dlp.networking._urllib import UrllibRH
    from yt_dlp.version import __version__
    class Quiet:
        def debug(self,*args,**kwargs):pass
        info=warning=error=debug
    class Guard(urllib.request.BaseHandler):
        def http_request(self,request):public_url(request.full_url);return request
        https_request=http_request
    class PublicUrllibRH(UrllibRH):
        def _create_instance(self,*args,**kwargs):
            opener=super()._create_instance(*args,**kwargs);opener.add_handler(Guard());return opener
    def progress(data):
        if data.get('downloaded_bytes',0)>limit:raise ValueError('size')
    result={'error':'unavailable'};stage='configure'
    try:
        options={'logger':Quiet(),'quiet':True,'noprogress':True,'noplaylist':True,'playlistend':1,
            'format':'best[ext=mp4][protocol=https]/best[ext=mp4][protocol=http]',
            'outtmpl':str(work/'video.%(ext)s'),'max_filesize':limit,'socket_timeout':15,
            'retries':1,'fragment_retries':0,'progress_hooks':[progress],'proxy':'',
            'continuedl':False,'overwrites':False,'cachedir':False,'usenetrc':False,'enable_file_urls':False,
            'fixup':'never','postprocessors':[]}
        with YoutubeDL(options) as ydl:
            # A single pinned transport checks every request, including redirected requests.
            ydl._request_director.handlers.clear()
            ydl._request_director.add_handler(PublicUrllibRH(logger=Quiet(),headers=ydl.params['http_headers'],cookiejar=ydl.cookiejar,timeout=15,proxies={}))
            stage='extract';info=ydl.extract_info(public_url(url),download=False)
            if not isinstance(info,dict) or info.get('_type','video')!='video' or info.get('is_live'):raise ValueError('unsupported')
            stage='download';ydl.process_info(info)
        path=work/'video.mp4'
        if not path.is_file() or not 0<path.stat().st_size<=limit:raise ValueError('size')
        result={'file':'video.mp4','provider':'yt-dlp','version':__version__}
    except Exception as exc:
        import traceback
        result.update(error_type=type(exc).__name__,stage=stage,frames=[r.name for r in traceback.extract_tb(exc.__traceback__)[-4:]])
        # Only a fixed classification, never a raw provider message or signed URL.
        message=str(exc).lower()
        result['diagnostic']=[word for word in ('unsupported','handler','certificate','format','http error','unable to download','429','403','404','connection','name resolution','timed out','no video','json','login','cookie') if word in message]
        result['reason']='access' if any(x in message for x in ('login','log in','rate-limit','rate limit','private','not available')) else 'retrieval'
    (work/'download-result.json').write_text(json.dumps(result),encoding='utf-8')

if __name__=='__main__':main()
