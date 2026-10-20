"""Real AVD regression: pagination, owner CRUD, encrypted login, drafts, offline cache.

Creates explicitly named V2Fixture test posts on the local demo server only. Clears
the isolated emulator app when --phase prepare is requested; never use on a phone.
Credentials stay in .runtime and are never emitted into evidence.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'PhotoBlogServer'))
from api_engine.client import PhotoBlogClient

parser=argparse.ArgumentParser()
parser.add_argument('--phase',choices=['prepare','pagination','crud','draft','offline'],required=True)
parser.add_argument('--serial',default='emulator-5554')
args=parser.parse_args()
assert args.serial.startswith('emulator-'),'This destructive fixture script is restricted to an isolated AVD.'
ADB=str(Path.home()/'AppData/Local/Android/Sdk/platform-tools/adb.exe')
OUT=ROOT/'evidence/screenshots'
RESULT=ROOT/'evidence/android-extended.json'
summary=json.loads(RESULT.read_text()) if RESULT.exists() else {}

def adb(*cmd,raw=False):
    data=subprocess.check_output([ADB,'-s',args.serial,*cmd],stderr=subprocess.STDOUT)
    return data if raw else data.decode('utf-8',errors='replace')

def tree():
    adb('shell','uiautomator','dump','/sdcard/v2-ui.xml')
    return ET.fromstring(adb('shell','cat','/sdcard/v2-ui.xml'))

def find(text=None,hint=None,resource=None,desc=None):
    for n in tree().iter('node'):
        if ((text is not None and n.get('text')==text) or (hint is not None and n.get('hint')==hint)
            or (resource and n.get('resource-id')=='com.example.photoviewer:id/'+resource)
            or (desc is not None and n.get('content-desc')==desc)):
            return n
    raise AssertionError('Missing UI control: '+str(text or hint or resource or desc))

def tap(n):
    x,y,a,b=map(int,re.findall(r'\d+',n.get('bounds')))
    assert a>x and b>y,'Control is outside visible viewport'
    adb('shell','input','tap',str((x+a)//2),str((y+b)//2))

def fill(n,value):
    old=n.get('text','');hint=n.get('hint','')
    if old==hint:old=''
    tap(n);adb('shell','input','keyevent','123')
    if old:adb('shell','input','keyevent',*(['67']*len(old)))
    if value:adb('shell','input','text',value.replace(' ','%s'))
    adb('shell','input','keyevent','4');time.sleep(.3)

def wait(fragment,timeout=30):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        ui=tree()
        if any(fragment in n.get('text','') for n in ui.iter('node')):return ui
        time.sleep(.4)
    raise AssertionError('State not reached: '+fragment)

def shot(name):
    OUT.mkdir(exist_ok=True,parents=True)
    (OUT/name).write_bytes(adb('exec-out','screencap','-p',raw=True))

def launch():
    adb('shell','am','force-stop','com.example.photoviewer')
    adb('shell','am','start','-n','com.example.photoviewer/.MainActivity')

def search(value):
    fill(find(resource='search'),value);tap(find(text='검색'));wait('동기화 완료')

credentials=json.loads((ROOT/'.runtime/demo-credentials.json').read_text(encoding='utf-8'))
client=PhotoBlogClient('http://127.0.0.1:8000')
client.login(credentials['username'],credentials['password'])

if args.phase=='prepare':
    for post in client.posts('V2Fixture'):
        client.request('DELETE',f'/api_root/Post/{post["id"]}/')
    for post in client.posts('V2Draft restored'):
        if post['title']=='V2Draft restored':client.request('DELETE',f'/api_root/Post/{post["id"]}/')
    image=next((ROOT/'PhotoBlogServer/media').rglob('*.jpg'))
    for i in range(13):client.upload(f'V2Fixture {i:02}','Pagination and owner-edit regression fixture.',image)
    adb('shell','pm','clear','com.example.photoviewer')
    launch();wait('아직 불러온 사진');shot('09-client-start.png')
    tap(find(resource='sync'));wait('동기화 완료');time.sleep(2);shot('10-client-synced.png')
    tap(find(resource='settings'));wait('서버 설정')
    fill(find(hint='아이디'),credentials['username'])
    fill(find(hint='비밀번호 (저장하지 않음)'),credentials['password'])
    tap(find(text='로그인'));wait('로그인 완료');shot('14-connection-settings.png')
    prefs=ET.fromstring(adb('shell','run-as','com.example.photoviewer','cat','shared_prefs/photoblog.xml'))
    values={n.get('name'):n.text for n in prefs}
    assert values.get('auth_cipher') and values.get('auth_iv')
    assert 'token' not in values and client.token not in ET.tostring(prefs,encoding='unicode')
    assert credentials['password'] not in ET.tostring(prefs,encoding='unicode')
    summary.update(encrypted_token=True,password_not_stored=True)
    tap(find(text='닫기'))

elif args.phase=='pagination':
    search('V2Fixture');wait('12/13');time.sleep(2);shot('14-pagination-first.png')
    tap(find(text='다음 사진 더 불러오기'));wait('13/13');shot('14-pagination-complete.png')
    summary.update(pagination_first=12,pagination_total=13,pagination_second=13)

elif args.phase=='crud':
    search('V2Fixture 12')
    # Scroll the card body into view while keeping the app's fixed controls visible.
    adb('shell','input','swipe','500','1730','500','1100','400')
    tap(find(desc='V2Fixture 12 수정'));wait('게시글 수정')
    fill(find(hint='수정할 제목'),'V2Fixture edited')
    fill(find(hint='수정할 내용'),'Edited on the actual Android client.')
    shot('14-owner-edit.png');tap(find(text='수정 저장'));wait('동기화 완료')
    posts=client.posts('V2Fixture edited');assert len(posts)==1 and posts[0]['text']=='Edited on the actual Android client.'
    search('V2Fixture edited')
    adb('shell','input','swipe','500','1730','500','1100','400')
    tap(find(desc='V2Fixture edited 삭제'));wait('이 사진을 삭제할까요?');shot('14-delete-confirm.png')
    tap(find(text='취소'));assert len(client.posts('V2Fixture edited'))==1
    tap(find(desc='V2Fixture edited 삭제'));tap(find(text='삭제 확인'));wait('동기화 완료')
    assert not client.posts('V2Fixture edited')
    summary.update(owner_edit=True,delete_cancel_preserves=True,owner_delete=True)

elif args.phase=='draft':
    image=next((ROOT/'PhotoBlogServer/media').rglob('*.jpg'))
    adb('push',str(image),'/sdcard/Download/photoblog-upload.jpg')
    tap(find(resource='upload'));time.sleep(1)
    ui=tree()
    if not any(n.get('content-desc','').startswith('photoblog-upload.jpg,') for n in ui.iter('node')):
        tap(find(desc='Show roots'));tap(find(text='Downloads'))
    node=next(n for n in tree().iter('node') if n.get('content-desc','').startswith('photoblog-upload.jpg,'));tap(node)
    wait('새 사진 게시')
    fill(find(hint='제목 (최대 200자)'),'V2Draft restored')
    fill(find(hint='내용 (최대 5000자)'),'Draft survives closing and restarting the app.')
    tap(find(text='닫기 · 초안 저장'));time.sleep(1)
    launch();wait('저장된 목록');tap(find(resource='upload'));tap(find(text='초안 이어쓰기'));wait('새 사진 게시')
    assert find(hint='제목 (최대 200자)').get('text')=='V2Draft restored'
    assert find(hint='내용 (최대 5000자)').get('text')=='Draft survives closing and restarting the app.'
    time.sleep(1);shot('14-draft-restored.png')
    tap(find(text='업로드'));wait('동기화 완료')
    assert len(client.posts('V2Draft restored'))==1
    summary.update(draft_process_restart=True,draft_image_permission_retained=True,restored_draft_upload=True)

elif args.phase=='offline':
    if find(resource='favorites').get('checked')=='true':tap(find(resource='favorites'))
    search('V2Draft restored');time.sleep(3)
    shot('14-client-search.png')
    # Favorite and open the image to prove it decoded before disconnecting.
    star=find(desc='V2Draft restored 즐겨찾기')
    if star.get('text')=='☆':tap(star)
    try:
        adb('shell','svc','wifi','disable');adb('shell','svc','data','disable');time.sleep(2)
        launch();wait('저장된 목록');time.sleep(2)
        tap(find(desc='V2Draft restored'));wait('닫기');shot('14-offline-photo.png');tap(find(text='닫기'))
        tap(find(resource='sync'));wait('저장된 사진 1개 유지',timeout=45);shot('14-offline-retry.png')
        tap(find(resource='favorites'));wait('즐겨찾기 · 1개');shot('14-favorites.png')
        summary.update(offline_process_restart=True,offline_photo_decoded=True,favorite_persisted=True,offline_sync_retains_feed=True)
    finally:
        adb('shell','svc','wifi','enable');adb('shell','svc','data','enable')

summary['last_verified_utc']=datetime.now(timezone.utc).isoformat()
RESULT.write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('Verified Android phase:',args.phase)
