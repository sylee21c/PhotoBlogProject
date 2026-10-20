# 제출 직전 확인

코드·APK·자동 테스트·로컬 동작 증빙은 준비되어 있습니다. 아래는 본인 입력이나 실제 지정 앱에서 마무리할 항목입니다. 특히 PythonAnywhere 실제 동작과 GitHub push 전에는 전체 평가 완료로 표시하지 않습니다.

1. Word 보고서 첫 페이지의 학번과 이름, 표 ID 2의 GitHub 주소를 작성합니다. 요청에 따라 현재 빈칸으로 두었습니다. 적/부 판정은 평가자 칸이므로 비워 둡니다.
2. 프로젝트 최상위에서 `PhotoBlogServer`, `PhotoViewer`, 보고서가 함께 보이도록 탐색기를 촬영합니다. GitHub에 올린 저장소의 파일 목록 화면으로도 제출할 수 있습니다.
3. 서버를 실행하고 `http://127.0.0.1:8000/api_root/Post/` 또는 게시 완료 페이지를 브라우저에서 엽니다. **브라우저 주소창까지 포함한 화면**을 보고서에 추가합니다. 현재 브라우저 콘텐츠 캡처에는 주소창이 없습니다.
4. 프로젝트 폴더의 PowerShell에서 다음 명령을 실행하고 HTTP 200 응답과 JSON이 보이는 터미널 화면을 촬영합니다.

```powershell
chcp 65001
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe scripts/verify_http.py
```

5. VS Code에서 `evidence/socket/2026-10-16-14-10-54-405793.txt`를 엽니다. Android의 실제 POST 요청, multipart 형식, 수신 이미지 정보가 보이는 편집 화면을 촬영해 보고서에 추가합니다. 원문은 보고서 뒤에도 수록했습니다.
6. `docs/DEPLOY.md`의 준비 스크립트로 PythonAnywhere에 실제 배포합니다. 클라우드 서버 브라우저 화면을 ID 12, 해당 HTTPS 서버에서 사진을 받은 Android 동기화 화면을 ID 13 증빙으로 넣습니다. 로컬 화면을 클라우드 증빙으로 사용하지 않습니다.
7. 완료한 뒤 표 ID 2, 12, 13의 X 표시를 실제 완료 상태에 맞춰 수정합니다. 관련증빙 칸은 해당 페이지 또는 그림 번호를 기입합니다.
8. GitHub에 `PhotoBlogServer`, `PhotoViewer`, 보고서 및 필요한 지원 파일을 push하고 저장소 URL을 제출합니다. 공개 저장소인지, 비공개라면 평가자가 접근할 수 있는지 확인합니다. `.runtime`, `.venv`, DB·사진 원본·비밀번호·토큰은 제외합니다.

추가 기능은 다섯 묶음으로 정리되어 있으며 `docs/FEATURES.md`와 보고서 증빙 14에 설명과 캡처가 있습니다. 테스트 수치는 `evidence/test-summary.json`과 `evidence/android-build.json`에 기록된 실제 결과입니다.

Word 파일은 본인이 최종 편집한 뒤 제출합니다. `scripts/build_report.py`를 다시 실행하면 제공 양식에서 보고서를 재생성하므로 본인이 추가한 이름·캡처·URL을 덮어쓸 수 있습니다.
