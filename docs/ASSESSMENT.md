# 공통평가 항목별 구현과 증빙

2026년 10월 20일 기준입니다. 최종 보고서는 저장소 최상위의 학번과 이름이 포함된 DOCX입니다. 학번, 이름, GitHub URL과 본인 완료 여부를 작성했으며 평가자의 적/부 판정 칸은 비워 두었습니다.

| ID | 구현 또는 검증 | 보고서 증빙 |
|---|---|---|
| 1 | ROOT에 PhotoBlogServer, PhotoViewer, 보고서 배치 | 증빙 01 탐색기 화면 |
| 2 | 공개 저장소 https://github.com/sylee21c/PhotoBlogProject | 평가표의 제출 URL과 GitHub push |
| 3 | DRF HTML form에서 제목, 내용, 사진 입력 및 POST | 증빙 03 작성 화면과 주소창 포함 HTTP 201 응답, 게시글 ID 56 |
| 4 | Python 검증 엔진의 실제 HTTP 요청과 응답 | 증빙 04 PowerShell의 HTTP 200 및 JSON |
| 5 | CodeBeautify JSON Viewer에서 응답 검증 | 증빙 05 Valid JSON 화면 |
| 6 | 서버 API 자동 테스트와 커버리지 | 증빙 06 커버리지 화면, 서버 테스트 48개, 커버리지 90.75% |
| 7 | Android multipart 요청을 진단 Socket 서버에서 수신 | 증빙 07 수신 파일을 연 VS Code 화면 |
| 8 | 로컬 Django 사진 목록 | 증빙 08 서버 브라우저 화면 |
| 9 | Android 앱 시작 시 동기화 전 상태 | 증빙 09 시작 화면 |
| 10 | 로컬 API 및 이미지 동기화 | 증빙 10 사진 3개 동기화 화면 |
| 11 | Android UI 사진 선택과 multipart 업로드 | 증빙 11 미리보기와 업로드 완료, 상 난이도 방식 선택 |
| 12 | PythonAnywhere HTTPS 서버 배포 | 증빙 12 클라우드 서버 화면 |
| 13 | Android에서 PythonAnywhere API와 이미지 조회 | 증빙 13 클라우드 동기화 완료 화면 |

## 추가 기능 다섯 항목

10/6 수업 1:16:25의 설명과 제공 양식의 지시대로 서버와 클라이언트 구현을 별도 요구사항으로 구분했습니다. 최대 다섯 항목만 추가 기능으로 제시합니다. 서버 주소와 계정 설정은 보조 설명으로 남기며 여섯 번째 항목으로 세지 않습니다.

| ID | 구분과 기능 | 구현과 증빙 |
|---|---|---|
| 14-1 | 서버 검색과 정렬 API | blog/views.py, blog/pagination.py. 검색어, 정렬, 페이지 응답 처리. 증빙 14-1 |
| 14-2 | Android 검색과 페이지 조회 | ApiClient.page, MainActivity.loadPage. 검색과 정렬 UI, 12개에서 13개로 페이지 이어받기. 증빙 14-2 |
| 14-3 | Android 게시글 수정과 삭제 | MainActivity.editPost, deletePost. 본인 글 수정, 삭제 확인과 취소. 증빙 14-3 |
| 14-4 | Android 오프라인과 즐겨찾기 | CacheStore, saveFeed, loadCachedFeed. 앱 재실행 및 연결 실패 후 사진과 즐겨찾기 보존. 증빙 14-4 |
| 14-5 | Android 사진 미리보기와 초안 | showUpload, persistDraft, readDraft. 사진 미리보기와 앱 재실행 후 초안 복원. 증빙 14-5 |

원본 검증 기록은 evidence/test-summary.json, evidence/android-build.json, evidence/android-extended.json, evidence/cloud-verification.json에 있습니다. 최종 Word는 캡처를 내부에 포함하므로 다른 컴퓨터에서도 외부 파일 없이 이미지를 볼 수 있습니다. 추가 기능의 최종 인정과 점수는 평가자가 판단합니다.
