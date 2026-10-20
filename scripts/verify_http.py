"""Capture an actual unauthenticated HTTP exchange for assessment ID 4.

Run in a terminal and take a screenshot of the output. The saved text is a log,
not a substitute for the required terminal screenshot.
"""
import http.client
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
connection=http.client.HTTPConnection('127.0.0.1',8000,timeout=10)
path='/api_root/Post/?page=1&page_size=1'
connection.request('GET',path,headers={'Accept':'application/json'})
response=connection.getresponse();data=response.read();payload=json.loads(data)
rows=payload['results'] if isinstance(payload,dict) else payload
assert response.status==200 and isinstance(rows,list) and rows,'Run setup.ps1 to create local demo photos first.'
report='REQUEST\nGET '+path+' HTTP/1.1\nHost: 127.0.0.1:8000\nAccept: application/json\n\n'
report+=f'RESPONSE\nHTTP/1.1 {response.status} {response.reason}\n'
report+='\n'.join(f'{k}: {v}' for k,v in response.getheaders())+'\n\n'
report+=json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
connection.close()
(ROOT/'evidence/terminal-api-response.txt').write_text(report,encoding='utf-8')
(ROOT/'evidence/http-verification.json').write_text(json.dumps({'verified_utc':datetime.now(timezone.utc).isoformat(),
    'status':200,'post_count':len(rows),'request_path':path,'actual_terminal_screenshot':False},indent=2),encoding='utf-8')
print(report)
