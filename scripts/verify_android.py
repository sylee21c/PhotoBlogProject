"""Smoke-test this isolated emulator through Android's SDK and capture real screens.

No credentials are printed or written to evidence. Run after installing the debug APK.
"""
import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from xml.etree import ElementTree

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser();parser.add_argument('--adb',default=str(Path.home()/'AppData/Local/Android/Sdk/platform-tools/adb.exe'))
parser.add_argument('--serial',default='emulator-5554');args=parser.parse_args()
OUT=ROOT/'evidence/screenshots';OUT.mkdir(parents=True,exist_ok=True)

def adb(*commands,raw=False):
    result=subprocess.check_output([args.adb,'-s',args.serial,*commands],stderr=subprocess.STDOUT)
    return result if raw else result.decode('utf-8',errors='replace')

def dump():
    adb('shell','uiautomator','dump','/sdcard/photoblog-ui.xml')
    return ElementTree.fromstring(adb('shell','cat','/sdcard/photoblog-ui.xml'))

def find(text=None,resource=None,description=None,hint=None):
    for node in dump().iter('node'):
        if ((text is not None and node.get('text')==text) or
            (resource is not None and node.get('resource-id')=='com.example.photoviewer:id/'+resource) or
            (description is not None and node.get('content-desc')==description) or
            (hint is not None and node.get('hint')==hint)):
            return node
    raise AssertionError(f'UI element missing: {text or resource or description or hint}')

def tap(node):
    x1,y1,x2,y2=map(int,re.findall(r'\d+',node.get('bounds')))
    adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2))

def input_text(node,value):
    tap(node);adb('shell','input','text',value.replace(' ','%s'))

def shot(name):
    (OUT/name).write_bytes(adb('exec-out','screencap','-p',raw=True))

def wait_text(fragment,timeout=25):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        ui=dump()
        if any(fragment in node.get('text','') for node in ui.iter('node')):return
        time.sleep(.5)
    raise AssertionError('UI state not reached: '+fragment)

credentials=json.loads((ROOT/'.runtime/demo-credentials.json').read_text(encoding='utf-8'))
adb('shell','am','force-stop','com.example.photoviewer')
adb('shell','am','start','-n','com.example.photoviewer/.MainActivity')
wait_text('아직 불러온 사진')
shot('09-client-start.png')
tap(find(resource='sync'));wait_text('동기화 완료');time.sleep(2)
shot('10-client-synced.png')
tap(find(resource='settings'));wait_text('서버 설정')
input_text(find(hint='아이디'),credentials['username'])
adb('shell','input','keyevent','4')
input_text(find(hint='비밀번호 (저장하지 않음)'),credentials['password'])
adb('shell','input','keyevent','4')
tap(find(text='로그인'));wait_text('로그인 완료')
shot('14-connection-settings.png')
tap(find(text='요청 메시지 검증 (Socket :8001)'));wait_text('GET·POST 전송 완료')
tap(find(text='닫기'))
# Scope favorite evidence to the currently visible post.
ui=dump();stars=[n for n in ui.iter('node') if n.get('content-desc','').endswith(' 즐겨찾기')]
assert stars,'No photo cards were rendered';tap(stars[0]);tap(find(resource='favorites'));wait_text('즐겨찾는 순간')
shot('14-favorites.png');tap(find(resource='favorites'))
# The file picker and upload below are real device UI, not a debug-only bypass.
fixture=next((ROOT/'PhotoBlogServer/media').rglob('*.jpg'))
adb('push',str(fixture),'/sdcard/Download/photoblog-upload.jpg')
adb('shell','am','broadcast','-a','android.intent.action.MEDIA_SCANNER_SCAN_FILE','-d','file:///sdcard/Download/photoblog-upload.jpg')
tap(find(resource='upload'));time.sleep(1)
(ROOT/'.runtime/android-picker.xml').write_bytes(ElementTree.tostring(dump(),encoding='utf-8'))
print('Verified initial screen, live sync, token login, favorites and Android socket GET/POST. Picker is open for upload verification.')
(ROOT/'evidence/android-smoke.json').write_text(json.dumps({'start':True,'sync':True,'login':True,'favorites':True,'socket_get_post':True,'upload_verified':False},indent=2),encoding='utf-8')
