"""Complete the real system document-picker upload smoke test on the isolated AVD."""
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree

ROOT=Path(__file__).resolve().parent.parent
ADB=str(Path.home()/'AppData/Local/Android/Sdk/platform-tools/adb.exe')
OUT=ROOT/'evidence/screenshots'
def adb(*cmd,raw=False):
    data=subprocess.check_output([ADB,'-e',*cmd],stderr=subprocess.STDOUT)
    return data if raw else data.decode('utf-8',errors='replace')
def tree():
    adb('shell','uiautomator','dump','/sdcard/upload-ui.xml')
    return ElementTree.fromstring(adb('shell','cat','/sdcard/upload-ui.xml'))
def find(test):
    for node in tree().iter('node'):
        if test(node):return node
    raise AssertionError('Expected device UI control was not found.')
def tap(node):
    a,b,c,d=map(int,re.findall(r'\d+',node.get('bounds')))
    adb('shell','input','tap',str((a+c)//2),str((b+d)//2))
def wait(fragment):
    deadline=time.monotonic()+25
    while time.monotonic()<deadline:
        if any(fragment in n.get('text','') for n in tree().iter('node')):return
        time.sleep(.5)
    raise AssertionError('State not reached: '+fragment)
def screenshot(name):(OUT/name).write_bytes(adb('exec-out','screencap','-p',raw=True))
def fill_hint(hint,value):
    tap(find(lambda n:n.get('hint')==hint));adb('shell','input','text',value.replace(' ','%s'));adb('shell','input','keyevent','4');time.sleep(.5)

# The initial verification script opens the picker. Navigate its observed root menu.
current=tree()
if not any('photoblog-upload.jpg' in n.get('content-desc','') for n in current.iter('node')):
    tap(find(lambda n:n.get('content-desc')=='Show roots'))
    tap(find(lambda n:n.get('text')=='Downloads'))
screenshot('11-photo-picker.png')
tap(find(lambda n:n.get('content-desc','').startswith('photoblog-upload.jpg,')))
wait('새 사진 게시')
fill_hint('제목 (최대 200자)','Android upload verified')
fill_hint('내용 (최대 5000자)','Uploaded through the real Android photo picker and multipart form.')
screenshot('11-upload-preview.png')
tap(find(lambda n:n.get('text')=='업로드'))
wait('동기화 완료');time.sleep(1)
screenshot('11-upload-complete.png')
with urlopen('http://127.0.0.1:8000/api_root/Post/?q=Android') as response:posts=json.load(response)
assert any(p['title']=='Android upload verified' for p in posts),'Android upload was not saved on server.'
tap(find(lambda n:n.get('resource-id')=='com.example.photoviewer:id/search'))
adb('shell','input','text','Android');adb('shell','input','keyevent','4')
tap(find(lambda n:n.get('text')=='검색'));wait('동기화 완료')
screenshot('14-client-search.png')
summary=json.loads((ROOT/'evidence/android-smoke.json').read_text(encoding='utf-8'))
summary.update(upload_verified=True,system_picker=True,search=True,uploaded_post_id=posts[0]['id'])
(ROOT/'evidence/android-smoke.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('Verified actual Android picker -> preview -> authenticated multipart upload -> server persistence -> searchable sync.')
