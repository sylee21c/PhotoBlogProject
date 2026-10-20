"""Verify the real cloud gallery on the isolated PhotoBlogAscii AVD."""
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
ADB = str(Path.home() / 'AppData/Local/Android/Sdk/platform-tools/adb.exe')
DOMAIN = 'https://blackponge.pythonanywhere.com'
SAMPLE_TITLE = '호수의 선착장'

def adb(*args, raw=False):
    data = subprocess.check_output([ADB, '-s', 'emulator-5554', *args], stderr=subprocess.STDOUT)
    return data if raw else data.decode('utf-8', errors='replace')

def tree():
    adb('shell', 'uiautomator', 'dump', '/sdcard/cloud-ui.xml')
    return ET.fromstring(adb('shell', 'cat', '/sdcard/cloud-ui.xml'))

def find(resource=None, text=None):
    for n in tree().iter('node'):
        if resource and n.get('resource-id') == 'com.example.photoviewer:id/' + resource:
            return n
        if text is not None and n.get('text') == text:
            return n
    raise AssertionError('Missing control: ' + str(resource or text))

def tap(n):
    x, y, a, b = map(int, re.findall(r'\d+', n.get('bounds')))
    assert a > x and b > y
    adb('shell', 'input', 'tap', str((x+a)//2), str((y+b)//2))

def fill(n, value):
    old = n.get('text', '')
    if old == n.get('hint'): old = ''
    tap(n)
    adb('shell', 'input', 'keyevent', '123')
    if old: adb('shell', 'input', 'keyevent', *(['67'] * len(old)))
    if value: adb('shell', 'input', 'text', value)
    adb('shell', 'input', 'keyevent', '4')

def shot(name):
    (ROOT / 'evidence/screenshots' / name).write_bytes(adb('exec-out', 'screencap', '-p', raw=True))

assert adb('emu', 'avd', 'name').splitlines()[0].strip() == 'PhotoBlogAscii'
fill(find(resource='search'), '')
favorite = find(resource='favorites')
if favorite.get('checked') == 'true': tap(favorite)
tap(find(resource='settings'))
fill(find(resource='server_url'), DOMAIN)
shot('13-client-cloud-settings.png')
tap(find(text='주소 저장'))
tap(find(resource='sync'))
deadline = time.monotonic() + 45
while time.monotonic() < deadline:
    ui = tree()
    texts = [n.get('text', '') for n in ui.iter('node')]
    if any('동기화 완료' in t for t in texts) and SAMPLE_TITLE in texts:
        break
    if any('동기화 실패' in t for t in texts):
        raise AssertionError('Cloud sync failed: ' + str(texts))
    time.sleep(1)
else:
    raise AssertionError('Cloud photo was not shown in Android')
time.sleep(2)
shot('13-client-cloud-synced.png')
(ROOT / 'evidence/cloud-android.json').write_text(json.dumps({
    'verified_at': datetime.now(timezone.utc).isoformat(),
    'server': DOMAIN,
    'avd': 'PhotoBlogAscii',
    'cloud_photo_title': SAMPLE_TITLE,
    'status': next(t for t in texts if '동기화 완료' in t),
    'cloud_url_visible': DOMAIN in texts,
    'screenshot': 'evidence/screenshots/13-client-cloud-synced.png',
}, ensure_ascii=False, indent=2), encoding='utf-8')
print('CLOUD_ANDROID_SYNC_PASS')
