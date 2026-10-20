# 공통평가 항목별 구현과 증빙

학번·이름과 최종 GitHub URL은 본인 정보로 작성합니다. Word의 적/부 판정 칸은 비워 둡니다.

| ID | 구현/검증 위치 | 제출 증빙과 남은 일 |
|---|---|---|
| 1 | ROOT의 PhotoBlogServer/PhotoViewer/보고서 | 탐색기 또는 Git 저장소 구조 화면 캡처 |
| 2 | 독립 프로젝트 폴더와 .gitignore | 본인 GitHub 원격 생성·push 후 URL 입력 |
| 3 | 웹 `/post/new/`, API `/api_root/Post/` | 실제 작성 전·게시 후 캡처 저장. 최종 제출은 주소창 포함 재캡처 |
| 4 | `api_engine`, `evidence/terminal-api-response.txt` | 실제 HTTP 검증 완료. 터미널에서 실행한 화면을 최종 캡처 |
| 5 | `evidence/api-response.json` | 승인된 데모 JSON으로 Valid JSON 확인, `05-codebeautify.png` 저장 |
| 6 | `blog/tests`, `api_engine`, `run_tests.py` | `evidence/coverage/index.html` 및 실제 캡처 |
| 7 | `tools/socket_capture.py`, Android DiagnosticClient | `evidence/socket/*.txt`를 VS Code로 열어 최종 캡처 |
| 8 | Django 갤러리 | `08-server-local.png` |
| 9 | Android MainActivity 시작 | `09-client-start.png` |
| 10 | Android 목록·이미지 다운로드 | `10-client-synced.png` |
| 11 | UI 사진 선택·multipart 업로드 | 업로드 미리보기와 완료 화면. 하드코딩 방식은 선택하지 않음 |
| 12 | PythonAnywhere 실제 배포와 HTTPS 검사 완료 | `12-server-cloud.png`, `evidence/cloud-verification.json`, 보고서 반영 |
| 13 | Android 실제 클라우드 사진 동기화 완료 | `13-client-cloud-synced.png`, `evidence/cloud-android.json`, 보고서 반영 |
| 14 | README의 추가 기능 다섯 개 | 기능 정의·구현 파일·관련 실제 화면 |

자동화된 브라우저 캡처는 브라우저 콘텐츠를 촬영하므로 주소창은 포함하지 않습니다. 주소창/터미널/VS Code 등 공지에 특정 앱의 UI가 요구되는 증빙은 원본 실행 결과를 해당 앱에서 열어 추가 캡처하세요. 캡처를 조작해 해당 앱 화면처럼 만들지 않습니다.

## 추가 기능 정의

| 번호 | 기능 | 코드 |
|---|---|---|
| 1 | 검색·정렬·페이지 조회 | `blog/pagination.py`, `blog/views.py`, `ApiClient::page`, `MainActivity::loadPage` |
| 2 | 웹/앱 본인 게시글 수정·삭제와 파일 정리 | `post_edit`, `post_delete`, `blog/signals.py`, `MainActivity::editPost`, `deletePost` |
| 3 | 오프라인 목록·사진과 즐겨찾기 복원 | `CacheStore`, `saveFeed`, `loadCachedFeed`, `favoriteKey` |
| 4 | 사진 미리보기·입력 검증·업로드 초안 복원 | `showUpload`, `persistDraft`, `readDraft`, `blog/validation.py` |
| 5 | 서버 연결·계정 관리·토큰 암호화 | `showSettings`, `saveServer`, `TokenVault`, `/api/me/` |

테스트 결과와 실제 검증 상태는 `evidence/test-summary.json`, `evidence/android-smoke.json`, `evidence/android-extended.json`, `evidence/web-verification.json`을 기준으로 확인합니다. 추가 기능은 서로 겹치는 검색 API/UI를 별개로 세는 대신 위의 다섯 기능군으로 정리했습니다. 최종 인정 여부는 평가 기준에 따릅니다.
