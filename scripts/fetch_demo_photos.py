"""Download the three credited sample photos selected for this project."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
assets = ROOT / 'PhotoBlogServer/demo_photos'
receipt = []
for photo in json.loads((assets / 'sources.json').read_text(encoding='utf-8')):
    target = assets / photo['file']
    with urlopen(Request(photo['download'], headers={'User-Agent': 'PhotoBlog sample photo download'}), timeout=30) as response:
        data = response.read()
    target.write_bytes(data)
    with Image.open(target) as image:
        image.verify()
    receipt.append({'file': photo['file'], 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
(ROOT / 'evidence/sample-photos.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print('Downloaded', len(receipt), 'sample photos')
