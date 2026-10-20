"""Fill only assessment slots in the supplied DOCX and append actual screenshots.

All untouched package parts are retained byte-for-byte. Run with the bundled document
Python runtime (lxml and Pillow); render the resulting DOCX with Word before submission.
"""
import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument('--template',type=Path,default=Path.home()/'Downloads/모바일웹서비스 프로젝트_공통평가 01_수행 결과 보고서.docx')
parser.add_argument('--name',default='');parser.add_argument('--student-id',default='');parser.add_argument('--github-url',default='')
args=parser.parse_args()
target=ROOT/'모바일웹서비스 프로젝트_공통평가 01_수행 결과 보고서.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic':'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'rel':'http://schemas.openxmlformats.org/package/2006/relationships'}
def el(tag,attrs=None,text=None):
    prefix,name=tag.split(':');node=E.Element('{'+NS[prefix]+'}'+name)
    for key,value in (attrs or {}).items():
        if ':' in key:
            prefix,key=key.split(':');key='{'+NS[prefix]+'}'+key
        node.set(key,str(value))
    if text is not None:node.text=text
    return node
def run(text,size=20,bold=False):
    r=el('w:r');pr=el('w:rPr');pr.append(el('w:rFonts',{'w:ascii':'맑은 고딕','w:hAnsi':'맑은 고딕','w:eastAsia':'맑은 고딕'}));pr.append(el('w:sz',{'w:val':size}));pr.append(el('w:color',{'w:val':'000000'}))
    pr.append(el('w:b',{'w:val':'1' if bold else '0'}));pr.append(el('w:bCs',{'w:val':'1' if bold else '0'}))
    r.append(pr);t=el('w:t',text=text);t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');r.append(t);return r
def paragraph(text='',size=20,bold=False,page=False,center=False):
    p=el('w:p');pr=el('w:pPr');pr.append(el('w:spacing',{'w:after':120,'w:line':276,'w:lineRule':'auto'}))
    if page:pr.append(el('w:pageBreakBefore'))
    if bold:pr.append(el('w:keepNext'))
    if center:pr.append(el('w:jc',{'w:val':'center'}))
    p.append(pr)
    if text:p.append(run(text,size,bold))
    return p

with ZipFile(args.template) as source:
    parts={name:source.read(name) for name in source.namelist()};infos=source.infolist()
doc=E.fromstring(parts['word/document.xml']);body=doc.find('w:body',NS)
rels=E.fromstring(parts['word/_rels/document.xml.rels'])
rows=body.find('w:tbl',NS).findall('w:tr',NS)
def cell(row,col,text):
    c=rows[row].findall('w:tc',NS)[col]
    p=c.find('w:p',NS)
    for child in list(p):
        if child.tag!='{'+NS['w']+'}pPr':p.remove(child)
    p.append(run(text,14))
def replace_paragraph(index,text):
    p=body.findall('w:p',NS)[index]
    textnodes=p.findall('.//w:t',NS)
    if textnodes:
        textnodes[0].text=text
        for node in textnodes[1:]:node.text=''
if args.student_id:replace_paragraph(2,'학번 : '+args.student_id)
if args.name:replace_paragraph(3,'이름 : '+args.name)

cloud_file=ROOT/'evidence/cloud-verification.json'
cloud_android_file=ROOT/'evidence/cloud-android.json'
cloud=json.loads(cloud_file.read_text(encoding='utf-8')) if cloud_file.exists() else None
cloud_android=json.loads(cloud_android_file.read_text(encoding='utf-8')) if cloud_android_file.exists() else None
states={2:('O','구조 확인'),3:('O' if args.github_url else 'X',args.github_url),
        4:('O','증빙 03'),5:('O','HTTP 기록 준비'),6:('O','증빙 05'),7:('O','증빙 06'),
        8:('O','수신 파일 준비'),9:('O','증빙 08'),10:('O','증빙 09'),11:('O','증빙 10'),
        12:('','선택하지 않음'),13:('O','증빙 11'),
        14:('O','증빙 12') if cloud else ('X','실제 배포 필요'),
        15:('O','증빙 13') if cloud_android else ('X','클라우드 확인 필요')}
for row,(complete,evidence) in states.items():cell(row,4,complete);cell(row,6,evidence)
features=[('14-1','검색·정렬·페이지','제목/본문 검색, 3종 정렬, 앱 12장씩 추가 조회.','증빙 14 조회'),
          ('14-2','본인 게시글 관리','웹/앱 수정·삭제, 소유권·CSRF 검사, 사진 파일 정리.','증빙 14 관리'),
          ('14-3','오프라인·즐겨찾기','목록·사진 캐시와 별표를 앱 재실행 후 복원.','증빙 14 보관'),
          ('14-4','미리보기·초안','사진 미리보기, 입력 검증, 재실행 후 초안 게시.','증빙 14 초안'),
          ('14-5','연결·계정 관리','주소·연결 확인, 로그인, Keystore 토큰 암호화.','증빙 14 설정')]
for row,(id,name,description,evidence) in zip(range(16,21),features):
    for col,text in [(0,id),(2,name),(3,description),(4,'O'),(6,evidence)]:cell(row,col,text)

# Add appendices before the existing section properties, leaving the section system intact.
def append(node):body.insert(len(body)-1,node)
media={};image_index=0
def picture(path,width):
    global image_index
    image_index+=1;name=f'assessment-{image_index:02}.png';media['word/media/'+name]=path.read_bytes()
    relation='rIdAssessment'+str(image_index)
    rels.append(el('rel:Relationship',{'Id':relation,'Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image','Target':'media/'+name}))
    with Image.open(path) as im:w,h=im.size
    # Keep the full original PNG in the DOCX. Word's display crop removes only
    # the wide browser side margins, so the actual application text is readable.
    browser_shots={'03-post-form.png','03-post-result.png','08-server-local.png',
                   '12-server-cloud.png','14-server-search.png'}
    display_width=min(w,1200) if path.name in browser_shots else w
    margin=int((w-display_width)/2/w*100000)
    cx=int(width*914400);cy=int(cx*h/display_width)
    r=el('w:r');drawing=el('w:drawing');inline=el('wp:inline',{'distT':0,'distB':0,'distL':0,'distR':0})
    inline.append(el('wp:extent',{'cx':cx,'cy':cy}));inline.append(el('wp:docPr',{'id':1000+image_index,'name':name,'descr':path.stem}))
    graphic=el('a:graphic');data=el('a:graphicData',{'uri':'http://schemas.openxmlformats.org/drawingml/2006/picture'})
    pic=el('pic:pic');nv=el('pic:nvPicPr');nv.append(el('pic:cNvPr',{'id':0,'name':name}));nv.append(el('pic:cNvPicPr'));pic.append(nv)
    fill=el('pic:blipFill');fill.append(el('a:blip',{'r:embed':relation}))
    if margin:fill.append(el('a:srcRect',{'l':margin,'r':margin}))
    stretch=el('a:stretch');stretch.append(el('a:fillRect'));fill.append(stretch);pic.append(fill)
    pr=el('pic:spPr');xf=el('a:xfrm');xf.append(el('a:off',{'x':0,'y':0}));xf.append(el('a:ext',{'cx':cx,'cy':cy}));pr.append(xf)
    geom=el('a:prstGeom',{'prst':'rect'});geom.append(el('a:avLst'));pr.append(geom);pic.append(pr)
    data.append(pic);graphic.append(data);inline.append(graphic);drawing.append(inline);r.append(drawing);return r
def page(title,description,images):
    append(paragraph(title,28,True,page=True));append(paragraph(description,19))
    p=paragraph(center=True)
    for i,(filename,width) in enumerate(images):
        if i:p.append(run('   '))
        p.append(picture(ROOT/'evidence/screenshots'/filename,width))
    append(p)

summary=json.loads((ROOT/'evidence/test-summary.json').read_text())
api_browser=ROOT/'evidence/api-browser-verification.json'
if api_browser.exists():
    api_result=json.loads(api_browser.read_text())
    page('증빙 03 API POST 작성 화면','Django REST Framework의 실제 API POST 폼에서 제목·내용과 사진을 입력했습니다. 일반 갤러리 작성 화면과 별도로 API 화면을 검증했습니다.',[('03-api-post-form.png',6.1)])
    page('증빙 03 API POST 성공 응답',f'실제 POST 응답은 HTTP {api_result["status"]} Created입니다. 응답의 게시글과 이미지 주소가 서버에 저장된 것을 다시 조회해 확인했습니다. 브라우저 주소창을 포함한 최종 캡처는 추가해야 합니다.',[('03-api-post-created.png',6.1)])
page('증빙 03 웹 사진 작성 폼','사진·제목·내용을 입력하는 실제 작성 폼입니다. 사진 선택 전 화면이며, API POST 성공 응답과 Android의 사진 선택·업로드 증빙은 별도로 첨부했습니다. 최종 제출 전 주소창을 포함한 화면을 추가합니다.',[('03-post-form.png',6.1)])
post_url=json.loads((ROOT/'evidence/web-verification.json').read_text())['postUrl']
page('증빙 03 웹 게시글 조회',f'예시 사진 게시글의 실제 조회 주소: {post_url}\nPexels 사진을 사용한 게시글입니다. 브라우저의 콘텐츠 캡처이며, 최종 제출용 주소창 포함 화면은 별도 추가합니다.',[('03-post-result.png',6.1)])
if (ROOT/'evidence/screenshots/05-codebeautify.png').exists():
    page('증빙 05 API JSON 검증','CodeBeautify JSON Viewer에 데모 API 응답을 입력하고 Valid JSON 결과를 확인했습니다.',[('05-codebeautify.png',6.1)])
page('증빙 06 Python 자동 테스트와 커버리지',f'Python 테스트 {summary["tests"]}개 통과. 측정 범위 blog 및 api_engine의 branch coverage 포함 결과 {summary["coverage_percent"]}%. 실제 HTML 보고서를 캡처했습니다.\n원본: evidence/coverage/index.html, evidence/python-tests.txt',[('06-coverage.png',6.1)])
page('증빙 08 로컬 서버 브라우저','Django 서버의 사진 목록입니다. 산·해변·선착장 사진은 Pexels에서 받았으며, 출처와 이용 조건은 docs/PHOTO_CREDITS.md에 기록했습니다.\n접속 주소: http://127.0.0.1:8000/',[('08-server-local.png',6.1)])
page('증빙 09 클라이언트 시작 화면','Android 에뮬레이터에서 실행한 실제 시작 화면입니다. 동기화 전에 목록이 비어 있습니다.',[('09-client-start.png',2.8)])
page('증빙 10 로컬 서버 동기화 완료','Android 앱에서 목록 API를 호출하고 이미지 URL로 사진을 내려받아 표시했습니다.\n에뮬레이터 접속 주소: http://10.0.2.2:8000',[('10-client-synced.png',2.8)])
if (ROOT/'evidence/screenshots/11-upload-preview.png').exists():
    page('증빙 11 사진 선택과 업로드 미리보기','시스템 파일 선택기에서 사진을 직접 선택하고, 제목과 내용을 입력한 실제 업로드 화면입니다. UI 제공 방식을 선택했습니다.',[('11-upload-preview.png',2.8)])
    page('증빙 11 Android 게시 완료','Android의 인증된 multipart 요청으로 실제 서버에 게시한 뒤 다시 동기화했습니다. 저장된 게시글은 evidence/android-smoke.json에서 확인할 수 있습니다.',[('11-upload-complete.png',2.8)])
if cloud:
    page('증빙 12 PythonAnywhere 서버 실행',f'실제 배포 주소: {cloud["domain"]}\nPython 3.13 환경에서 DEBUG를 끄고 실행했습니다. HTTPS 홈페이지, 상태 API, 목록 API, 사진과 CSS를 확인했고 비인증 게시 요청은 HTTP 401로 차단됐습니다. Pexels 예시 사진 3개를 서버에 저장했습니다.',[('12-server-cloud.png',6.1)])
if cloud_android:
    page('증빙 13 Android 클라우드 동기화',f'Android 앱의 서버 주소를 {cloud_android["server"]}로 변경하고 실제 HTTPS API와 사진을 내려받았습니다. 화면에 클라우드 주소, 동기화 완료 상태와 테스트 사진이 표시됩니다.\n검증 기록: evidence/cloud-verification.json, evidence/cloud-android.json',[('13-client-cloud-synced.png',2.8)])
page('증빙 14 서버 검색 기능','제목과 본문으로 게시글을 검색하고 정렬 조건을 적용합니다. 검색·정렬·페이지 조회를 하나의 추가 기능으로 정리했습니다.',[('14-server-search.png',6.1)])
if (ROOT/'evidence/screenshots/14-client-search.png').exists():
    page('증빙 14 앱 검색과 즐겨찾기','왼쪽은 앱 검색 결과, 오른쪽은 별표로 저장한 즐겨찾기 필터 결과입니다. 즐겨찾기는 서버 주소별로 구분해 기기에 저장합니다.',[('14-client-search.png',2.75),('14-favorites.png',2.75)])
page('증빙 14 서버 설정과 로그인','서버 주소 변경·연결 확인·계정 로그인을 제공합니다. 토큰은 Android Keystore 키로 AES-GCM 암호화해 보관하며 비밀번호는 저장하지 않습니다.',[('14-connection-settings.png',2.8)])
extended_file=ROOT/'evidence/android-extended.json'
if extended_file.exists():
    extended=json.loads(extended_file.read_text())
    if extended.get('pagination_second')==13:
        page('증빙 14 조회 페이지 이어받기','검색 결과 13개 중 첫 12개를 받은 화면과 다음 페이지까지 13개를 받은 화면입니다. 실제 로컬 API와 Android 앱으로 검증했습니다.',[('14-pagination-first.png',2.75),('14-pagination-complete.png',2.75)])
    if extended.get('owner_delete'):
        page('증빙 14 본인 게시글 관리','앱에서 제목·본문을 수정한 뒤 서버 저장 결과를 확인했습니다. 삭제 취소 시 글이 유지되고 삭제 확인 시 제거되는 것을 검증했습니다. 서버는 다른 계정의 변경을 차단합니다.',[('14-owner-edit.png',2.75),('14-delete-confirm.png',2.75)])
    if extended.get('draft_process_restart'):
        page('증빙 14 작성 초안 복원','사진과 제목·본문을 작성한 뒤 창을 닫고 앱을 강제 종료했습니다. 재실행 후 초안 이어쓰기로 복원하고 실제 서버에 게시했습니다. 사진 읽기 권한도 유지됐습니다.',[('14-draft-restored.png',2.8)])
    if extended.get('offline_photo_decoded'):
        page('증빙 14 오프라인 보관과 재시도','에뮬레이터의 Wi-Fi와 모바일 데이터를 끈 뒤 앱을 재실행했습니다. 보관된 사진 확대 보기와 즐겨찾기를 확인하고, 동기화 실패 후에도 기존 목록이 유지되는 것을 검증했습니다. 검증 후 네트워크를 다시 켰습니다.',[('14-offline-photo.png',2.75),('14-offline-retry.png',2.75)])
    append(paragraph('추가 개발 검증 결과',28,True,page=True))
    for text in [f'서버 자동 테스트 {summary["tests"]}개 통과, 실패 {summary["failures"]}개, 오류 {summary["errors"]}개. branch 포함 커버리지 {summary["coverage_percent"]}%.',
                 'Android Java 단위 테스트 9개 통과. 실제 에뮬레이터에서 페이지 조회, 수정, 삭제 취소 및 확인, 초안 복원과 게시, 오프라인 재실행 및 사진 보관을 확인했습니다.',
                 '서버 테스트에는 인증·소유권, 웹 CSRF, 잘못된 이미지·초과 크기, DB 커밋 후 파일 삭제, 롤백 시 파일 보존, 실제 자동 커밋에서 사진 교체 정리가 포함됩니다.',
                 '캐시는 목록 4 MB와 사진 32 MB 한도입니다. 보관되지 않았거나 정리된 이미지는 오프라인에서 표시할 수 없으며 작성·수정·삭제에는 연결이 필요합니다. 즐겨찾기 필터는 현재 불러온 목록을 대상으로 합니다.',
                 '원본 기록: evidence/test-summary.json, evidence/android-extended.json, evidence/android-unit-tests/index.html. 구현 및 재현 절차: docs/FEATURES.md.',
                 '추가 기능은 검색·정렬·페이지 조회, 본인 게시글 관리, 오프라인·즐겨찾기, 미리보기·초안, 연결·계정 관리의 다섯 가지로 정의했습니다. 최종 인정은 평가 기준에 따릅니다.']:
        append(paragraph(text,20))
append(paragraph('추가 제출 절차',28,True,page=True))
for text in ['학번, 이름, GitHub 저장소 URL을 작성합니다.',
             '폴더 구조는 탐색기 또는 Git 저장소 화면으로 캡처합니다.',
             'ID 3의 게시 완료 화면을 브라우저 주소창이 보이도록 추가 캡처합니다.',
             'ID 4: PhotoBlogServer에서 Python API 엔진 또는 curl을 실행한 터미널을 캡처합니다. 실제 응답 원본은 evidence/terminal-api-response.txt에 있습니다.',
             'ID 7: evidence/socket의 수신 .txt 또는 .bin 파일을 VS Code에서 열어 캡처합니다. multipart 원본과 추출 이미지가 함께 저장되어 있습니다.',
             ('ID 12, 13: 본인 PythonAnywhere 계정의 실제 배포와 Android 동기화를 완료했습니다. 무료 웹 앱 유지 기한은 2026년 11월 20일이며 이후 계정의 Web 화면에서 연장합니다.' if cloud and cloud_android else 'ID 12, 13: docs/DEPLOY.md에 따라 본인 PythonAnywhere 계정에 배포하고, 서버와 앱의 실제 클라우드 연동 화면을 추가합니다.'),
             '상단 표의 O는 해당 구현·테스트 완료를 뜻합니다. 관련 증빙 칸이 준비로 표시된 항목은 지정 앱의 최종 캡처가 필요합니다. GitHub URL은 본인 저장소에 업로드한 뒤 작성합니다.',
             '적/부 판정 칸은 평가자 작성용으로 비워 두었습니다.']:
    append(paragraph(text,20))

append(paragraph('증빙 04 실제 HTTP 요청과 응답 원문',28,True,page=True))
append(paragraph('아래는 로컬 서버와 실제 통신한 기록입니다. 터미널 화면 캡처를 대체하지 않으며, scripts/verify_http.py 실행 화면을 촬영해 추가합니다.',19))
for line in (ROOT/'evidence/terminal-api-response.txt').read_text(encoding='utf-8').splitlines():
    p=paragraph(line,17);p.find('w:pPr/w:spacing',NS).set('{'+NS['w']+'}after','0');append(p)
append(paragraph('증빙 07 Android Socket 수신 원문',28,True,page=True))
append(paragraph('Android에서 전송한 실제 multipart 요청을 Socket 서버가 수신한 기록입니다. 아래 파일을 VS Code로 열어 편집 화면을 촬영해 추가합니다.',19))
socket_file=ROOT/'evidence/socket/2026-10-16-14-10-54-405793.txt'
append(paragraph('원본: '+socket_file.relative_to(ROOT).as_posix(),18))
for line in socket_file.read_text(encoding='utf-8').splitlines():
    p=paragraph(line,17);p.find('w:pPr/w:spacing',NS).set('{'+NS['w']+'}after','0');append(p)

parts['word/document.xml']=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
parts['word/_rels/document.xml.rels']=E.tostring(rels,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(target,'w') as result:
    for info in infos:result.writestr(info,parts[info.filename])
    for name,data in media.items():result.writestr(name,data)
with ZipFile(args.template) as original,ZipFile(target) as result:
    changed=[name for name in original.namelist() if original.read(name)!=result.read(name)]
    assert set(changed)=={'word/document.xml','word/_rels/document.xml.rels'},changed
(ROOT/'.runtime/report-package-audit.json').write_text(json.dumps({'template_sha256':hashlib.sha256(args.template.read_bytes()).hexdigest(),'changed_parts':changed,'embedded_evidence_images':len(media)},indent=2),encoding='utf-8')
print('Prepared report with',len(media),'embedded real evidence screenshots:',target.name)
