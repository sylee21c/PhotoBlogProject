"""Record public HTTPS responses from the deployed PhotoBlog."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://blackponge.pythonanywhere.com'
checks = []

def request(path, expected=200, method='GET'):
    req = Request(BASE + path, headers={'User-Agent': 'PhotoBlog-assessment-verifier'}, method=method)
    try:
        response = urlopen(req, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        data = response.read()
        checks.append({'path': path, 'method': method, 'status': response.status,
                       'content_type': response.headers.get('Content-Type'),
                       'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        assert response.status == expected, checks[-1]
        return data

home = request('/').decode()
assert '사진 목록' in home and 'YOUR EVERYDAY GALLERY' not in home
health = json.loads(request('/api/health/'))
posts = json.loads(request('/api_root/Post/'))
expected = json.loads((ROOT / 'PhotoBlogServer/demo_photos/sources.json').read_text(encoding='utf-8'))
assert {p['title'] for p in posts} == {p['title'] for p in expected}
image = posts[0]['image']
assert image.startswith(BASE + '/media/'), image
photo = request(image[len(BASE):])
assert photo[:3] == b'\xff\xd8\xff'
import re
css = re.search(r'href="(/static/[^\"]+\.css)"', home)
assert css, 'No static CSS link'
request(css.group(1))
request('/api_root/Post/', expected=401, method='POST')
result = {'verified_at': datetime.now(timezone.utc).isoformat(), 'domain': BASE,
          'health': health, 'posts': len(posts), 'cloud_photo': posts[0],
          'checks': checks, 'python': '3.13', 'debug': False,
          'backup': '/home/blackponge/.photoblog-deploy-backups/20261020-065309',
          'free_webapp_expiry': '2026-11-20',
          'server_screenshot': 'evidence/screenshots/12-server-cloud.png',
          'sample_photo_sources': 'PhotoBlogServer/demo_photos/sources.json'}
(ROOT / 'evidence/cloud-verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('CLOUD_HTTPS_PASS', len(checks), 'checks')
