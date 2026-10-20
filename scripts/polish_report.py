"""Reorganize the user's saved report without discarding their new captures.

The saved copy under .runtime/report-polish is the immutable input. Only the
document body changes; all source media, relationships, styles and page settings
are preserved. Output is staged for visual review before replacing the report.
"""
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / '.runtime/report-polish'
SOURCE = WORK / 'user-saved-original.docx'
TARGET = WORK / 'polished-report.docx'
NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
}

def el(tag, attrs=None, text=None):
    prefix, name = tag.split(':')
    node = E.Element('{' + NS[prefix] + '}' + name)
    for key, value in (attrs or {}).items():
        if ':' in key:
            p, key = key.split(':')
            key = '{' + NS[p] + '}' + key
        node.set(key, str(value))
    if text is not None:
        node.text = text
    return node

def run(text, size=20, bold=False):
    node = el('w:r')
    pr = el('w:rPr')
    pr.extend([
        el('w:rFonts', {'w:ascii': '맑은 고딕', 'w:hAnsi': '맑은 고딕', 'w:eastAsia': '맑은 고딕'}),
        el('w:b', {'w:val': int(bold)}), el('w:bCs', {'w:val': int(bold)}),
        el('w:color', {'w:val': '000000'}), el('w:sz', {'w:val': size}),
        el('w:szCs', {'w:val': size}),
    ])
    node.append(pr)
    t = el('w:t', text=text)
    t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    node.append(t)
    return node

def para(text='', size=20, bold=False, page=False, center=False, after=100):
    p = el('w:p')
    pr = el('w:pPr')
    pr.extend([el('w:snapToGrid', {'w:val': 0}),
               el('w:spacing', {'w:before': 0, 'w:after': after, 'w:line': 280, 'w:lineRule': 'auto'})])
    if page: pr.append(el('w:pageBreakBefore'))
    if bold:
        pr.append(el('w:keepNext'))
        pr.append(el('w:outlineLvl', {'w:val': 0}))
    if center: pr.append(el('w:jc', {'w:val': 'center'}))
    p.append(pr)
    if text: p.append(run(text, size, bold))
    return p

with ZipFile(SOURCE) as z:
    parts = {name: z.read(name) for name in z.namelist()}
    infos = z.infolist()
doc = E.fromstring(parts['word/document.xml'])
body = doc.find('w:body', NS)
rels = E.fromstring(parts['word/_rels/document.xml.rels'])
image_rel = {Path(x.get('Target')).name: x.get('Id') for x in rels
             if x.get('Type', '').endswith('/image')}

# The first ten paragraphs and the assessment table are the supplied form.
# They include the identity fields the user has already completed.
form = [deepcopy(x) for x in list(body)[:11]]
section = deepcopy(body.find('w:sectPr', NS))
for child in list(body): body.remove(child)
body.extend(form)
table = body.find('w:tbl', NS)
rows = table.findall('w:tr', NS)

def cell(row, col, text):
    c = rows[row].findall('w:tc', NS)[col]
    p = c.find('w:p', NS)
    for child in list(p):
        if child.tag != '{' + NS['w'] + '}pPr': p.remove(child)
    p.append(run(text, 14))

for index, evidence in {2:'증빙 01',4:'증빙 03',5:'증빙 04',6:'증빙 05',
                        7:'증빙 06',8:'증빙 07',9:'증빙 08',10:'증빙 09',
                        11:'증빙 10',13:'증빙 11',14:'증빙 12',15:'증빙 13'}.items():
    cell(index, 6, evidence)
features = [
    ('검색과 정렬 및 페이지 조회', '제목과 본문 검색, 3종 정렬, 앱에서 12개씩 이어받기.'),
    ('게시글 수정 및 삭제', '본인 게시글 관리, 삭제 확인, 서버의 소유권 검사.'),
    ('오프라인 보관과 즐겨찾기', '사진과 목록 캐시, 앱 재실행 후 복원, 서버별 즐겨찾기.'),
    ('사진 미리보기와 초안', '사진 선택 후 미리보기, 입력 검사, 앱 재실행 후 초안 복원.'),
    ('서버 및 계정 설정', '서버 주소 변경, 연결 확인, 로그인, 토큰 암호화 저장.'),
]
for row, (title, description) in zip(range(16, 21), features):
    cell(row, 2, title)
    cell(row, 3, description)
    cell(row, 6, '증빙 14-' + str(row - 15))

picture_id = 3000
used_images = []
def picture(filename, width, centered_app=False):
    global picture_id
    picture_id += 1
    used_images.append(filename)
    with Image.open(WORK / filename) as im: w, h = im.size
    # Display crop only removes empty side margins outside the application.
    # The complete original screenshot bytes remain in word/media unchanged.
    visible_width = min(w, 1200) if centered_app else w
    margin = round((w - visible_width) / 2 / w * 100000)
    cx = int(width * 914400)
    cy = int(cx * h / visible_width)
    r = el('w:r')
    drawing = el('w:drawing')
    inline = el('wp:inline', {'distT': 0, 'distB': 0, 'distL': 0, 'distR': 0})
    inline.extend([el('wp:extent', {'cx': cx, 'cy': cy}),
                   el('wp:docPr', {'id': picture_id, 'name': filename, 'descr': filename})])
    frame = el('wp:cNvGraphicFramePr')
    frame.append(el('a:graphicFrameLocks', {'noChangeAspect': 1}))
    inline.append(frame)
    graphic = el('a:graphic')
    data = el('a:graphicData', {'uri': NS['pic']})
    pic = el('pic:pic')
    nv = el('pic:nvPicPr')
    nv.append(el('pic:cNvPr', {'id': picture_id, 'name': filename}))
    nv.append(el('pic:cNvPicPr'))
    pic.append(nv)
    fill = el('pic:blipFill')
    fill.append(el('a:blip', {'r:embed': image_rel[filename]}))
    if margin: fill.append(el('a:srcRect', {'l': margin, 'r': margin}))
    stretch = el('a:stretch'); stretch.append(el('a:fillRect')); fill.append(stretch)
    pic.append(fill)
    sp = el('pic:spPr'); xf = el('a:xfrm')
    xf.append(el('a:off', {'x': 0, 'y': 0})); xf.append(el('a:ext', {'cx': cx, 'cy': cy}))
    sp.append(xf)
    geom = el('a:prstGeom', {'prst': 'rect'}); geom.append(el('a:avLst')); sp.append(geom)
    pic.append(sp); data.append(pic); graphic.append(data); inline.append(graphic)
    drawing.append(inline); r.append(drawing)
    return r

sections = []
def page(title, text, images, captions=None):
    sections.append(title)
    body.append(para(title, 28, True, page=True, after=140))
    body.append(para(text, after=140))
    p = para(center=True, after=100)
    p.find('w:pPr', NS).append(el('w:keepNext'))
    for i, (filename, width, *crop) in enumerate(images):
        if i: p.append(run('  '))
        p.append(picture(filename, width, bool(crop and crop[0])))
    body.append(p)
    if captions: body.append(para(captions, 18, center=True, after=0))
    else: body.append(para(after=0))

page('증빙 01 폴더 구조',
     '저장소 루트에 Django 서버인 PhotoBlogServer, Android 앱인 PhotoViewer, 수행 결과 보고서를 배치했습니다.',
     [('image2.png', 6.1)])

page('증빙 03 API 게시 작성 화면',
     'Django REST Framework의 HTML form에서 제목, 내용, 사진 파일을 입력한 화면입니다. 사진은 multipart/form-data 형식으로 전송하며 작성자는 로그인한 계정으로 지정합니다.',
     [('image6.png', 6.1)])
page('증빙 03 API 게시 성공 응답',
     '추가 게시 테스트에서 midterm-upload를 전송해 HTTP 201 Created 응답을 받았습니다. 응답에는 게시글 ID 54와 저장된 이미지 주소가 포함돼 있습니다.',
     [('image3.png', 6.1)],
     '요청 주소: http://127.0.0.1:8000/api_root/Post/?q=midterm-upload')

page('증빙 04 터미널에서 API 응답 확인',
     'PowerShell에서 scripts/verify_http.py를 실행했습니다. 로컬 목록 API가 HTTP 200 OK를 반환했고, JSON의 results에서 midterm-upload 게시글과 이미지 주소를 확인했습니다.',
     [('image4.png', 6.1)],
     '요청: GET /api_root/Post/?page=1&page_size=1')
page('증빙 05 API JSON 검증',
     'API 응답을 CodeBeautify JSON Viewer에 입력했습니다. 화면 상단의 Valid JSON 표시로 JSON 형식이 올바른 것을 확인했습니다.',
     [('image10.jpeg', 6.1)])
page('증빙 06 서버 자동 테스트와 커버리지',
     'Django와 unittest로 작성한 서버 테스트 48개가 통과했습니다. blog와 api_engine을 대상으로 분기를 포함해 측정한 커버리지는 90.75%이며, 아래는 HTML 보고서입니다.',
     [('image11.png', 6.1)],
     '검증 기록: evidence/python-tests.txt, evidence/coverage/index.html')
page('증빙 07 Socket 요청 수신 파일',
     'Android에서 보낸 multipart POST 요청의 수신 파일을 VS Code에서 열었습니다. 요청 경로, Content-Type, 제목, 내용과 image 필드의 파일 정보를 확인할 수 있습니다.',
     [('image5.png', 6.1)],
     '수신 파일: evidence/socket/2026-10-16-14-10-54-405793.txt')
page('증빙 08 로컬 서버 브라우저 화면',
     '로컬 Django 서버의 사진 목록입니다. 목록에는 예시 사진 3개가 표시되며, 검색과 정렬을 사용할 수 있습니다. 접속 주소는 http://127.0.0.1:8000/입니다.',
     [('image12.jpeg', 6.1, True)],
     '예시 사진 출처와 이용 조건: docs/PHOTO_CREDITS.md')

page('증빙 09와 10 Android 시작 및 동기화',
     '왼쪽은 앱을 처음 실행한 화면으로 사진 목록이 비어 있습니다. 오른쪽은 로컬 서버 http://10.0.2.2:8000에서 목록과 이미지를 받아 사진 3개를 표시한 화면입니다.',
     [('image13.png', 2.65), ('image14.png', 2.65)],
     '왼쪽: 증빙 09 시작 화면     오른쪽: 증빙 10 동기화 완료')
page('증빙 11 Android 사진 업로드',
     '사진을 선택하고 제목과 내용을 입력하는 UI 방식을 구현했습니다. 왼쪽은 선택한 사진과 작성 내용의 미리보기이며, 오른쪽은 인증된 multipart 요청으로 게시한 뒤 다시 조회한 결과입니다.',
     [('image15.png', 2.65), ('image16.png', 2.65)],
     '검증 기록: evidence/android-smoke.json, evidence/android-extended.json')
page('증빙 12 PythonAnywhere 서버 실행',
     'https://blackponge.pythonanywhere.com에 Django 서버를 배포했습니다. Python 3.13에서 DEBUG를 끄고 실행하며 홈페이지, 상태 API, 목록 API, 사진과 CSS의 정상 응답을 확인했습니다.',
     [('image17.jpeg', 6.1, True)],
     '검증 기록: evidence/cloud-verification.json')
page('증빙 13 Android 클라우드 동기화',
     '앱의 서버 주소를 https://blackponge.pythonanywhere.com으로 변경했습니다. 실제 HTTPS API와 이미지 주소에서 사진을 내려받아 동기화 완료 상태와 사진 3개를 확인했습니다.',
     [('image18.png', 2.8)],
     '검증 기록: evidence/cloud-android.json')

page('증빙 14 1 서버 검색과 정렬',
     '제목이나 본문에 포함된 단어로 게시글을 검색합니다. 아래는 해변을 검색한 결과이며, 최신순, 오래된순, 제목순 정렬을 제공합니다.',
     [('image19.jpeg', 6.1, True)])
page('증빙 14 1 Android 페이지 이어받기',
     '검색 결과 13개 중 첫 페이지에서 12개를 받았습니다. 다음 사진 더 불러오기를 누르면 나머지 1개를 받아 총 13개가 표시됩니다.',
     [('image22.png', 2.65), ('image23.png', 2.65)],
     '왼쪽: 첫 페이지 12개     오른쪽: 다음 페이지까지 13개')
page('증빙 14 2 본인 게시글 수정과 삭제',
     '본인 게시글의 제목과 내용을 수정하고 서버에 저장된 결과를 확인했습니다. 삭제 취소 시 게시글이 유지되고, 삭제 확인 시 제거됩니다. 서버는 다른 사용자의 수정을 차단합니다.',
     [('image24.png', 2.65), ('image25.png', 2.65)],
     '왼쪽: 게시글 수정     오른쪽: 삭제 확인 창')
page('증빙 14 3 즐겨찾기와 오프라인 사진',
     '즐겨찾기는 서버 주소별로 저장됩니다. 네트워크를 끄고 앱을 다시 실행한 뒤에도 저장된 즐겨찾기와 사진을 확인했습니다.',
     [('image20.png', 2.65), ('image26.png', 2.65)],
     '왼쪽: 오프라인 즐겨찾기     오른쪽: 저장된 사진 확대')
page('증빙 14 3 연결 실패 후 목록 유지',
     '오프라인에서 동기화를 시도하면 연결 실패를 알리고 저장된 사진 목록을 유지합니다. 검증을 마친 뒤 네트워크를 다시 켰습니다.',
     [('image27.png', 2.8)])
page('증빙 14 4 작성 초안 복원',
     '사진과 제목, 내용을 입력한 뒤 창을 닫고 앱을 종료했습니다. 앱을 다시 실행해 초안 이어쓰기를 선택하자 입력 내용과 사진이 복원됐으며, 복원한 초안으로 실제 게시까지 확인했습니다.',
     [('image15.png', 2.8)])
page('증빙 14 5 서버 주소와 계정 설정',
     '서버 주소 변경, 연결 확인, 로그인과 로그아웃을 제공합니다. 비밀번호는 저장하지 않으며 인증 토큰은 Android Keystore 키로 암호화해 저장합니다. 서버를 바꾸면 이전 서버의 인증 정보를 지웁니다.',
     [('image21.png', 2.8)])

body.append(para('검증 결과와 실행 정보', 28, True, page=True, after=160))
for heading, text in [
    ('자동 테스트', '서버 테스트는 48개 통과했고 실패와 오류는 0개입니다. 분기 측정을 포함한 커버리지는 90.75%입니다. Android Java 단위 테스트 9개도 통과했습니다.'),
    ('기기 검증', '전용 Android 에뮬레이터에서 로컬 동기화, 로그인, 사진 업로드, 페이지 조회, 수정, 삭제 취소와 확인, 초안 복원, 오프라인 사진 보관을 확인했습니다. 클라우드 서버에서도 사진 3개를 동기화했습니다.'),
    ('저장 범위', '목록 캐시는 최대 4 MB, 사진 캐시는 최대 32 MB입니다. 캐시에 없는 사진은 오프라인에서 볼 수 없습니다. 즐겨찾기 필터는 현재 불러온 목록을 대상으로 하며 게시, 수정, 삭제에는 서버 연결이 필요합니다.'),
    ('확인 주소', '로컬 서버: http://127.0.0.1:8000/\n목록 API: http://127.0.0.1:8000/api_root/Post/\n클라우드 서버: https://blackponge.pythonanywhere.com'),
    ('실행 환경과 원본 기록', '서버는 Python 3.13과 Django 5.2 환경이며 Android 앱 버전은 1.2입니다. 테스트 원본은 evidence/test-summary.json, evidence/android-build.json, evidence/android-extended.json에 있습니다. 사진 출처는 docs/PHOTO_CREDITS.md에 정리했습니다.'),
]:
    body.append(para(heading, 22, True, after=70))
    for line in text.split('\n'): body.append(para(line, after=150))
body.append(section)

# User-requested copy cleanup, including feature descriptions inside the form.
for node in doc.findall('.//w:t', NS):
    if node.text and '·' in node.text: node.text = node.text.replace('·', ', ')
assert not any('·' in (x.text or '') for x in doc.findall('.//w:t', NS))
assert all(name in used_images for name in ['image2.png','image3.png','image4.png','image5.png'])
assert len(doc.findall('.//wp:anchor', NS)) == 0

parts['word/document.xml'] = E.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)
with ZipFile(TARGET, 'w') as z:
    for info in infos: z.writestr(info, parts[info.filename])
with ZipFile(SOURCE) as before, ZipFile(TARGET) as after:
    changed = [name for name in before.namelist() if before.read(name) != after.read(name)]
    assert changed == ['word/document.xml'], changed
audit = {
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'output_sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest(),
    'changed_package_parts': changed,
    'all_source_media_preserved': True,
    'user_added_captures_in_correct_sections': True,
    'inline_images': len(used_images),
    'unique_visible_images': len(set(used_images)),
    'middle_dots_in_document_text': 0,
    'sections': sections,
    'remaining_submission_steps': ['API response capture with browser address bar', 'GitHub URL and push'],
}
(WORK/'polish-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'output': str(TARGET), 'image_occurrences': len(used_images), 'evidence_pages': len(sections)}, ensure_ascii=False))
