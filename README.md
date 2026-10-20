# PhotoBlog 공통평가 프로젝트

Django 사진 블로그 서버와 Java Android 앱입니다. 공통평가 Word 양식의 ID 1~14를 기준으로 구현했습니다.

실제 클라우드 서버: https://blackponge.pythonanywhere.com . 2026년 10월 20일 공개 HTTPS 검사와 Android 클라우드 사진 동기화를 완료하고 보고서에 증빙을 추가했습니다. 앱의 설정에서 이 주소를 저장하면 로그인 없이 예시 사진을 조회할 수 있습니다. 클라우드 게시용 계정 생성과 유지 기간 안내는 `docs/DEPLOY.md`를 참고하세요.

## 빠른 실행

Windows PowerShell에서 프로젝트 폴더를 열고 실행합니다. Python 3.10 이상, Android 빌드는 JDK 17 이상과 SDK 35가 필요합니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
powershell -ExecutionPolicy Bypass -File scripts/start-server.ps1
```

브라우저: <http://127.0.0.1:8000/> / API: <http://127.0.0.1:8000/api_root/Post/>

로컬 데모 계정은 최초 설정 때 임의 비밀번호로 생성됩니다. `.runtime/demo-credentials.json`을 본인의 편집기로 열어 아이디·비밀번호를 확인하세요. 이 파일과 토큰은 Git에 포함되지 않습니다. 예시 사진 세 장은 Pexels에서 받은 실제 사진이며, 출처와 이용 조건은 `docs/PHOTO_CREDITS.md`에 있습니다.

## Android

`artifacts/PhotoViewer-debug.apk`를 기기 또는 에뮬레이터에 설치하거나 Android Studio에서 `PhotoViewer` 폴더를 엽니다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-android.ps1
adb install -r artifacts/PhotoViewer-debug.apk
```

앱은 처음에 자동 동기화하지 않습니다. 시작 화면에서 **동기화**를 눌러 서버 사진을 불러옵니다.

**설정 → 아이디/비밀번호 → 로그인 → 닫기 → 새 사진 게시 → 사진 선택 → 제목/내용 입력 → 업로드** 순서입니다. 비밀번호는 저장하지 않으며, 토큰은 Android Keystore 키를 이용한 AES-GCM 암호문으로 저장합니다. 서버 주소를 변경하면 이전 서버의 토큰을 지우므로 새 서버에서 다시 로그인해야 합니다. 앱 백업은 비활성화했습니다.

APK 1.2에서는 장식 문구를 줄이고 사진 목록을 바로 표시합니다. 12장씩 조회하고 **다음 사진 더 불러오기**로 이어서 볼 수 있습니다. 로그인한 본인의 카드에 **수정·삭제**가 표시됩니다. 업로드 창을 닫아도 사진·제목·내용 초안을 보관하며, 앱 재실행 후 **새 사진 게시 → 초안 이어쓰기**로 복원합니다. 마지막 조회 목록과 다운로드된 사진은 서버에 연결되지 않아도 다시 볼 수 있습니다. 캐시는 목록 4 MB, 사진 32 MB로 제한하며, 캐시에서 지워진 사진은 다시 연결해야 받을 수 있습니다.

- Android 에뮬레이터에서 개발 PC: `http://10.0.2.2:8000`
- PythonAnywhere: `https://본인계정.pythonanywhere.com`
- 실제 휴대전화는 `10.0.2.2`로 PC에 접근할 수 없습니다. 같은 네트워크의 PC 주소를 사용하고 개발 서버 바인딩과 `DJANGO_ALLOWED_HOSTS`를 해당 주소로 설정해야 합니다.
- 디버그 APK는 로컬 HTTP 검증용입니다. 릴리스에서는 HTTPS를 기본으로 하며 localhost/에뮬레이터만 HTTP 예외를 둡니다.
- 한글 경로의 Windows JVM 테스트 문제를 피하기 위해 빌드 스크립트가 ASCII 임시 폴더에 빌드합니다. APK는 프로젝트 `artifacts`에 복사합니다.

## 테스트와 실제 증빙

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test.ps1
```

Python 테스트는 Django/unittest 러너와 branch coverage를 사용합니다. 실제 TCP HTTP 왕복, multipart 이미지 원본 보존, 인증·소유권·잘못된 입력·검색·정렬·페이지 조회·웹 작성/수정/삭제·CSRF 차단·커밋 후 파일 삭제·롤백 시 사진 보존을 검증합니다. 테스트 DB와 미디어는 분리되며 기존 데모 DB를 수정하지 않습니다.

- `evidence/python-tests.txt`: 실제 Python 테스트 결과
- `evidence/coverage/index.html`: HTML 커버리지 보고서
- `evidence/test-summary.json`: 테스트 수·실패 수·측정 커버리지
- `evidence/android-unit-tests/index.html`: Java 프로토콜 단위 테스트 결과
- `evidence/android-extended.json`: 에뮬레이터에서 직접 실행한 추가 기능 검증 결과
- `evidence/screenshots/`: 실제 브라우저와 Android 에뮬레이터 캡처
- `evidence/socket/`: 수신 요청 `.bin`, 읽기용 `.txt`, 추출 이미지
- `docs/ASSESSMENT.md`: 평가 항목별 파일·증빙·남은 절차

커버리지는 `.coveragerc`에 명시한 `blog` 및 `api_engine` 코드의 실행 범위입니다. 외부 라이브러리나 Android 전체의 커버리지를 뜻하지 않습니다.

## 독립 API 검증

```powershell
cd PhotoBlogServer
..\.venv\Scripts\python.exe -m api_engine --output ../evidence/api-response.json
```

업로드 검증은 환경변수 `PHOTOBLOG_TOKEN`에 자신의 토큰을 설정한 뒤 `--image 파일경로 --title 제목 --text 내용`을 추가합니다. 토큰을 소스·명령어 캡처에 적지 마세요. 게시글 작성자는 인증 계정으로 서버에서 지정하며, 클라이언트가 `author` 값을 위조해도 반영하지 않습니다.

## Socket 요청 검증

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-socket.ps1
```

서버가 실행 중일 때 Android 앱의 **설정 → 요청 메시지 검증**을 누릅니다. 앱은 같은 호스트의 8001 포트에 GET과 작은 PNG multipart POST를 보내며 `evidence/socket`에 저장됩니다. 이 진단은 Django 서버와 별개입니다. 인증 헤더는 저장 전에 가리고, 이미지 바이트는 그대로 보존합니다. `.txt`를 VS Code에서 열어 캡처하세요. 진단 서버는 로컬 검증용으로만 사용합니다.

## 추가 기능 다섯 개

1. 검색·정렬·페이지 조회: 서버와 앱에서 제목/내용 검색, 최신순·오래된순·제목순 정렬, 12장씩 추가 조회. 기존 수업의 배열형 API도 유지합니다.
2. 본인 게시글 관리: 웹과 Android에서 제목/내용 수정, 삭제 전 확인. 서버가 소유권과 웹 CSRF를 검증하고, DB 커밋 후 사용하지 않는 사진 파일을 정리합니다. 웹에서는 사진 교체도 가능합니다.
3. 오프라인 갤러리와 즐겨찾기: 마지막 목록·사진 디스크 캐시, 프로세스 재시작 후 복원, 연결 실패 시 기존 목록 유지, 서버별 즐겨찾기 보관.
4. 업로드 초안 복원과 미리보기: 시스템 사진 선택·권한 유지, 사진 미리보기, 글자 수·형식·크기 검증, 앱 재실행 후 작성 이어가기.
5. 연결·계정 관리: 서버 주소 변경·연결 확인·로그인·로그아웃, 서버에 결합한 토큰 암호화, 계정 ID를 기준으로 본인 관리 UI 표시.

추가 개발의 사용 방법과 검증 시나리오는 `docs/FEATURES.md`에 있습니다. 위 목록은 전체 구현 기능의 설명이며, 평가표의 추가 기능 다섯 항목은 `docs/ASSESSMENT.md`대로 서버 검색 API와 Android 검색 UI를 별도로 구분했습니다. `scripts/verify_extended_android.py`는 전용 에뮬레이터와 로컬 데모 서버에서만 실행하는 회귀 검증용입니다. `--phase prepare`는 해당 에뮬레이터 앱 데이터를 초기화하고 `V2Fixture` 데모 게시글을 재생성하므로 개인 휴대전화에 사용하지 마세요.

제출 전 `python scripts/audit_submission.py`를 실행하면 폴더·테스트 결과·APK/소스 일치·증빙 이미지·Git 제외 규칙·데모 자격증명 혼입 여부를 검사하고 `evidence/submission-audit.json`을 갱신합니다. 원격 push나 클라우드 배포 여부는 별도 실제 확인이 필요합니다.

## 제출

이 폴더 자체가 GitHub 저장소 ROOT입니다. 상위 수업 폴더 전체를 업로드하지 마세요. `PhotoBlogServer`, `PhotoViewer`, 루트의 보고서를 유지합니다. `.venv`, DB, 미디어, `.runtime`, 토큰, 비밀번호는 제외합니다. 다른 환경은 `setup.ps1`로 데모 데이터를 다시 생성합니다.

현재 폴더는 로컬 Git 저장소로 초기화되어 있습니다. Windows에서 생성 계정 차이로 `dubious ownership` 경고가 나오면 `powershell -File scripts/git.ps1 status`처럼 실행하세요. 이 래퍼는 해당 프로젝트에만 일회성 예외를 적용하며 전역 Git 설정이나 파일 접근 권한을 바꾸지 않습니다. 같은 방식으로 `add .`, `commit -m "Initial PhotoBlog project"`, `remote add origin 본인URL`, `push -u origin main`을 실행할 수 있습니다.

GitHub 저장소는 https://github.com/sylee21c/PhotoBlogProject 입니다. 최종 보고서에 본인 정보, GitHub URL과 지정 앱 캡처를 반영했습니다. PythonAnywhere 실제 배포와 Android 동기화도 완료했습니다. 최종 제출은 학교 과제 게시판에 이 GitHub URL을 등록하는 방식입니다. 배포 예시와 절차는 `PhotoBlogServer/deploy/pythonanywhere_wsgi.py`, `docs/DEPLOY.md`에 있습니다.

기술 참고: [Django 5.2 지원 환경](https://docs.djangoproject.com/en/5.2/releases/5.2/), [Android Gradle Plugin](https://developer.android.com/build/releases/agp-9-0-0-release-notes).
