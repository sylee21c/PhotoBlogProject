"""Capture the current local gallery on the isolated test AVD."""
import re
import subprocess
import time
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
ADB = str(Path.home() / 'AppData/Local/Android/Sdk/platform-tools/adb.exe')

def adb(*args):
    return subprocess.check_output([ADB, '-s', 'emulator-5554', *args])

def tree():
    adb('shell', 'uiautomator', 'dump', '/sdcard/sample-ui.xml')
    return ET.fromstring(adb('shell', 'cat', '/sdcard/sample-ui.xml'))

def node(resource):
    return next(n for n in tree().iter('node') if n.get('resource-id') == 'com.example.photoviewer:id/' + resource)

def tap(n):
    a, b, c, d = map(int, re.findall(r'\d+', n.get('bounds')))
    adb('shell', 'input', 'tap', str((a+c)//2), str((b+d)//2))

assert adb('emu', 'avd', 'name').decode().splitlines()[0].strip() == 'PhotoBlogAscii'
field = node('search')
tap(field)
adb('shell', 'input', 'keyevent', '123')
if field.get('text') != field.get('hint'):
    adb('shell', 'input', 'keyevent', *(['67'] * len(field.get('text', ''))))
adb('shell', 'input', 'keyevent', '4')
star_filter = node('favorites')
if star_filter.get('checked') == 'true': tap(star_filter)
tap(node('sync'))
deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    ui = tree()
    texts = [n.get('text', '') for n in ui.iter('node')]
    if any('동기화 완료 · 3/3' in text for text in texts): break
    time.sleep(.5)
else: raise AssertionError('Local sample set was not synchronized')
time.sleep(2)
(ROOT/'evidence/screenshots/10-client-synced.png').write_bytes(adb('exec-out', 'screencap', '-p'))
print('LOCAL_PHOTOS_CAPTURED')
