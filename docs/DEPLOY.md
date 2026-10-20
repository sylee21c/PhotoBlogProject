# PythonAnywhere 배포

2026년 10월 20일 실제 배포와 Android 동기화를 완료했습니다. 접속 주소는 https://blackponge.pythonanywhere.com 이며 Python 3.13으로 실행됩니다. 공개 홈페이지, 상태 API, 목록 API, 사진, CSS와 비인증 게시 차단을 검사했습니다. 실제 결과는 `evidence/cloud-verification.json`, `evidence/cloud-android.json`에 있습니다.

클라우드에는 로그인할 수 없는 예시 작성자 `gallery_demo`와 Pexels에서 받은 사진 3개를 넣었습니다. 출처는 `PHOTO_CREDITS.md`에 있습니다. 본인 계정은 아래 `createsuperuser` 명령으로 직접 생성하면 웹·앱에서 사진을 게시할 수 있습니다. 로컬 데모 계정은 클라우드에 복사하지 않았습니다. 무료 웹 앱 유지 기한은 2026년 11월 20일이며 Web 화면에서 연장할 수 있습니다.

기존 `web_blog` 소스와 DB는 그대로 보관돼 있습니다. 전환 전 WSGI와 설정 백업은 `/home/blackponge/.photoblog-deploy-backups/20261020-065309`에 있습니다. 현재 서버 경로는 `/home/blackponge/PhotoBlogProject/PhotoBlogServer`, 가상환경은 `/home/blackponge/PhotoBlogProject/.venv`입니다. 아래는 재배포 절차입니다.

## 준비 스크립트 사용

GitHub에 올린 뒤 PythonAnywhere Bash Console에서 저장소를 clone하고 아래 스크립트를 실행하면 가상환경, 패키지, DB 테이블, 정적 파일과 본인 계정용 WSGI 파일을 준비합니다. `PYTHON_BIN`은 Web 앱에서 선택한 Python과 같은 버전으로 지정합니다. 스크립트가 생성하는 비밀키와 WSGI 파일은 Git에서 제외되는 `.runtime`에만 저장됩니다. 재실행해도 비밀키를 바꾸지 않습니다.

```bash
cd ~/PhotoBlogProject
PYTHON_BIN=python3.10 bash PhotoBlogServer/deploy/setup_pythonanywhere.sh
```

EU 계정 등 도메인이 다르면 끝에 `--domain 본인계정.eu.pythonanywhere.com`을 붙입니다. 생성 결과에 표시되는 `.runtime/pythonanywhere_wsgi.py`의 내용을 **Web 탭의 WSGI 파일**에 복사하고, 출력된 virtualenv 및 static/media 경로를 설정한 뒤 Reload합니다. 웹 앱은 Manual configuration을 선택합니다. 이 스크립트는 웹 앱 생성과 Reload를 대신하지 않습니다.

```bash
.venv/bin/python PhotoBlogServer/manage.py createsuperuser
```

비밀번호는 위 명령의 입력 프롬프트에서 직접 정합니다. 배포 후 웹 로그인·사진 게시·API·이미지 다운로드를 확인하고, Android 설정에 본인 HTTPS 주소를 입력해 동기화합니다. 로컬 데모 비밀번호나 토큰을 클라우드에 복사하지 않습니다.

## 직접 설정하는 경우

1. GitHub에 이 프로젝트를 push합니다. 저장소 ROOT 아래 `PhotoBlogServer/manage.py`가 있어야 합니다.
2. PythonAnywhere Bash Console에서 저장소를 clone합니다.
3. Web 앱과 같은 Python 버전(3.10 이상)을 선택해 가상환경을 만들고 의존성을 설치합니다.

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git PhotoBlogProject
cd ~/PhotoBlogProject/PhotoBlogServer
mkvirtualenv --python=/usr/bin/python3.10 photoblog-env
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Python 3.10 경로는 예시입니다. 계정에서 제공하는 Python 중 3.10 이상을 사용하고 Web 탭과 가상환경의 버전을 맞추세요.

4. Web 탭에서 Manual configuration으로 웹 앱을 만들고 Virtualenv에 `~/.virtualenvs/photoblog-env`의 실제 절대 경로를 넣습니다.
5. Web 탭의 WSGI 파일을 열어 `deploy/pythonanywhere_wsgi.py`를 기준으로 작성합니다. 저장소의 `config/wsgi.py`를 수정하는 것만으로 Web 탭의 WSGI 설정이 바뀌지는 않습니다.
6. `YOUR_USERNAME`, 프로젝트 경로, 긴 임의 `DJANGO_SECRET_KEY`를 본인 값으로 바꿉니다. 운영 비밀키를 GitHub에 올리지 마세요. `DJANGO_DEBUG=0`에서 비밀키를 설정하지 않으면 앱은 의도적으로 시작을 거부합니다.
7. Static files 매핑을 두 개 추가합니다.

| URL | Directory 예시 |
|---|---|
| `/static/` | `/home/YOUR_USERNAME/PhotoBlogProject/PhotoBlogServer/staticfiles` |
| `/media/` | `/home/YOUR_USERNAME/PhotoBlogProject/PhotoBlogServer/media` |

8. Reload 후 HTTPS 도메인을 열고 로그인하여 사진을 게시합니다. `/api/health/`, `/api_root/Post/`, 이미지 URL도 확인합니다.
9. Android 설정에서 클라우드 HTTPS 주소를 저장하고 **클라우드에서 만든 계정**으로 다시 로그인합니다. 로컬 DB와 클라우드 DB는 별개입니다.
10. ID 12용 서버 브라우저 화면과 ID 13용 앱 동기화 완료 화면을 실제로 캡처하고 보고서에 추가합니다.

공식 참고: [기존 Django 프로젝트 배포](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/), [정적 파일과 미디어 매핑](https://help.pythonanywhere.com/pages/DjangoStaticFiles/).
