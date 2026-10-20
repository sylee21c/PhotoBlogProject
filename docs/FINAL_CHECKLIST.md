# 제출 확인

2026년 10월 20일, 공지와 제공 Word 양식, 10/6 및 10/13 수업 텍스트에 맞춰 확인했습니다.

- ROOT에 Django 서버 PhotoBlogServer, Android 앱 PhotoViewer, 최종 DOCX를 배치했습니다.
- Word에 학번과 이름, GitHub URL, 본인 완료 여부를 작성했습니다. 평가자의 적/부 판정은 비워 두었습니다.
- API 작성 화면, 주소창을 포함한 HTTP 201 성공 응답, PowerShell HTTP 응답, CodeBeautify Valid JSON, 커버리지, VS Code Socket 수신 화면을 넣었습니다.
- 서버 브라우저, 앱 시작, 로컬 동기화, UI 업로드, PythonAnywhere 서버 및 Android 클라우드 동기화를 넣었습니다.
- 추가 기능은 서버 검색 API와 Android 검색 UI를 별도로 구분하고 14-1부터 14-5까지 정확히 다섯 항목으로 기재했습니다.
- 캡처는 문서 안에 포함했고 전체 22쪽의 표, 설명, 이미지 배치를 검토했습니다.
- 서버 48개 테스트와 Android Java 9개 테스트가 통과했습니다. 서버 커버리지는 90.75%입니다.
- 가상환경, 로컬 DB, 계정 비밀번호와 토큰, Word 임시파일은 Git에서 제외했습니다.

최종 제출은 아래 저장소 URL입니다. GitHub 업로드만으로 학교 과제 제출이 완료되지는 않으므로, 과제 게시판의 제출란에 URL을 입력하고 제출 완료를 확인해야 합니다.

https://github.com/sylee21c/PhotoBlogProject

10/6 수업 텍스트에는 10월 20일 23:59까지 제출하라고 설명되어 있습니다. 과제 게시판의 최종 공지와 마감 표시가 우선합니다.

최종 파일을 수정했다면 Word를 저장하고 닫은 뒤 commit과 push를 다시 해야 합니다. scripts/build_report.py는 초기 양식에서 보고서를 다시 생성하므로 최종 편집본에 실행하지 마세요. scripts/audit_submission.py는 현재 저장된 보고서, 검증 기록과 로컬에 알려진 origin/main을 비교합니다.
