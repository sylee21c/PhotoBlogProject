"""Archive the known development fixtures, then show the credited sample set."""
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
server = ROOT / 'PhotoBlogServer'
sys.path.insert(0, str(server))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from blog.models import Post
from blog.management.sample_photos import seed_photos
from django.contrib.auth import get_user_model

expected = {'API POST assessment', '웹에서 기록한 새로운 순간', 'V2Draft restored',
            'Android upload verified', '노을이 머무는 시간', '바다에 남긴 오후', '고요한 산의 아침'}
rows = list(Post.objects.filter(author__username='student'))
fixtures = [p for p in rows if p.title in expected or p.title.startswith('V2Fixture ')]
backup = ROOT / '.runtime' / ('before-real-photos-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(parents=True)
with sqlite3.connect(server / 'db.sqlite3') as src, sqlite3.connect(backup / 'db.sqlite3') as dest:
    src.backup(dest)
shutil.copytree(server / 'media', backup / 'media')
shutil.copytree(ROOT / 'evidence/screenshots', backup / 'screenshots')
(backup / 'archived-posts.json').write_text(json.dumps([{'id': p.pk, 'title': p.title} for p in fixtures], ensure_ascii=False), encoding='utf-8')
for post in fixtures:
    post.delete()
seed_photos(get_user_model().objects.get(username='student'))
print('Archived', len(fixtures), 'development fixtures to', backup.name)
print('Current posts', Post.objects.count())
