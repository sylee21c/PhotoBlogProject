"""Check saved submission evidence and the locally known GitHub report version.

Optionally records an already-built APK and JUnit results from --android-build-root.
Uses Python's standard library; does not install packages or contact a server.
"""
import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parent.parent

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def android_fingerprint():
    files=list((ROOT/'PhotoViewer/app/src').rglob('*'))
    files += list((ROOT/'PhotoViewer').glob('*.gradle'))
    files += [ROOT/'PhotoViewer/app/build.gradle',ROOT/'PhotoViewer/gradle/wrapper/gradle-wrapper.properties']
    h=hashlib.sha256()
    for p in sorted(set(p for p in files if p.is_file())):
        h.update(p.relative_to(ROOT).as_posix().encode());h.update(b'\0');h.update(p.read_bytes());h.update(b'\0')
    return h.hexdigest()

def git(*args):
    return subprocess.run(['git','-c','safe.directory='+str(ROOT),'-C',str(ROOT),*args],capture_output=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--android-build-root',type=Path)
    args=parser.parse_args()
    apk=ROOT/'artifacts/PhotoViewer-debug.apk'
    if args.android_build_root:
        build=args.android_build_root
        suites=[ET.parse(p).getroot() for p in (build/'app/test-results/testDebugUnitTest').glob('TEST-*.xml')]
        assert suites,'No real JUnit result XMLs found'
        tests=sum(int(s.get('tests')) for s in suites)
        failures=sum(int(s.get('failures'))+int(s.get('errors')) for s in suites)
        assert tests>=9 and failures==0,'Android tests must pass before recording build'
        source=build/'app/outputs/apk/debug/app-debug.apk'
        shutil.copy2(source,apk)
        shutil.copytree(build/'app/reports/tests/testDebugUnitTest',ROOT/'evidence/android-unit-tests',dirs_exist_ok=True)
        receipt={'verified_utc':datetime.now(timezone.utc).isoformat(),'version':'1.2','tests':tests,'failures':failures,
                 'apk_sha256':digest(apk),'source_sha256':android_fingerprint()}
        (ROOT/'evidence/android-build.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')

    checks={}
    reports=[p for p in ROOT.glob('*.docx') if not p.name.startswith('~$')]
    if len(reports)!=1:raise RuntimeError('Expected exactly one final report DOCX in the repository root')
    report_path=reports[0]
    required=['PhotoBlogServer/manage.py','PhotoViewer/app/src/main/java/com/example/photoviewer/MainActivity.java',
              report_path.name,'artifacts/PhotoViewer-debug.apk']
    checks['required_layout']=all((ROOT/p).is_file() for p in required)
    python=json.loads((ROOT/'evidence/test-summary.json').read_text())
    checks['server_tests_passed']=python['tests']>=48 and python['failures']==python['errors']==0
    android=json.loads((ROOT/'evidence/android-build.json').read_text())
    checks['android_tests_passed']=android['tests']>=9 and android['failures']==0
    checks['apk_matches_build']=digest(apk)==android['apk_sha256']
    checks['android_sources_match_build']=android_fingerprint()==android['source_sha256']
    extended=json.loads((ROOT/'evidence/android-extended.json').read_text())
    booleans=['encrypted_token','password_not_stored','owner_edit','owner_delete','delete_cancel_preserves',
              'draft_process_restart','draft_image_permission_retained','restored_draft_upload',
              'offline_process_restart','offline_photo_decoded','favorite_persisted','offline_sync_retains_feed']
    checks['device_regressions_passed']=all(extended.get(k) is True for k in booleans) and extended.get('pagination_second')==13
    required_shots=['03-post-form','03-post-result','05-codebeautify','06-coverage','08-server-local',
                    '09-client-start','10-client-synced','11-upload-preview','11-upload-complete',
                    '14-pagination-first','14-pagination-complete','14-owner-edit','14-delete-confirm',
                    '14-draft-restored','14-offline-photo','14-offline-retry']
    checks['actual_capture_files_present']=all((ROOT/'evidence/screenshots'/f'{p}.png').is_file() for p in required_shots)
    with ZipFile(report_path) as doc:
        embedded=len([p for p in doc.namelist() if p.startswith('word/media/')])
        report_xml=ET.fromstring(doc.read('word/document.xml'))
        report_text=''.join(report_xml.itertext())
    checks['report_contains_extended_captures']=embedded>=22
    layout_path=ROOT/'evidence/report-layout.json'
    layout=json.loads(layout_path.read_text(encoding='utf-8')) if layout_path.exists() else {}
    pages=layout.get('pages',0)
    checks['report_layout_review_matches_file']=(layout.get('docx_sha256')==digest(ROOT/required[2])
        and pages>=22 and layout.get('inspected_pages')==list(range(1,pages+1)) and layout.get('layout_issues')==[])
    checks['required_native_captures_reviewed']=(checks['report_layout_review_matches_file']
        and all(layout.get(k) is True for k in ['api_address_bar_capture_verified','folder_capture_verified',
                                               'terminal_capture_verified','socket_editor_capture_verified']))
    checks['five_separate_feature_ids']=all(f'증빙 14-{n}' in report_text for n in range(1,6)) and layout.get('server_client_counted_separately') is True
    api_browser=json.loads((ROOT/'evidence/api-browser-verification.json').read_text())
    checks['browsable_api_post_verified']=api_browser.get('status')==201 and api_browser.get('persisted') is True
    http=json.loads((ROOT/'evidence/http-verification.json').read_text())
    checks['actual_http_exchange_verified']=http.get('status')==200 and http.get('post_count',0)>0
    deploy=json.loads((ROOT/'evidence/deployment-config-tests.json').read_text())
    checks['private_deploy_configuration_tests']=deploy.get('tests')==4 and deploy.get('failures')==deploy.get('errors')==0
    private=['.runtime/demo-credentials.json','.venv/pyvenv.cfg','PhotoBlogServer/db.sqlite3',
             'PhotoBlogServer/media/example.png','PhotoViewer/local.properties']
    checks['private_files_ignored']=all(git('check-ignore','-q',p).returncode==0 for p in private)
    candidates=git('ls-files','-z','--cached','--others','--exclude-standard')
    checks['git_inventory_readable']=candidates.returncode==0
    credentials=json.loads((ROOT/'.runtime/demo-credentials.json').read_text()) if (ROOT/'.runtime/demo-credentials.json').exists() else {}
    secrets=[v for k,v in credentials.items() if k in ['password','token'] and isinstance(v,str) and len(v)>=8]
    database=ROOT/'PhotoBlogServer/db.sqlite3'
    if database.exists():
        with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as connection:
            secrets += [row[0] for row in connection.execute('SELECT key FROM authtoken_token')]
    leaked=[]
    for name in candidates.stdout.decode('utf-8').split('\0'):
        p=ROOT/name
        if p.is_file() and p.suffix.lower() in ['.py','.java','.json','.md','.txt','.xml','.ps1','.cjs','.properties','.gradle','.html']:
            content=p.read_text(encoding='utf-8',errors='replace')
            if any(secret in content for secret in secrets):leaked.append(name)
    checks['demo_credentials_absent_from_publishable_text']=not leaked
    remote=git('remote','get-url','origin')
    cloud_path=ROOT/'evidence/cloud-verification.json'
    cloud_android_path=ROOT/'evidence/cloud-android.json'
    cloud=json.loads(cloud_path.read_text(encoding='utf-8')) if cloud_path.exists() else {}
    cloud_android=json.loads(cloud_android_path.read_text(encoding='utf-8')) if cloud_android_path.exists() else {}
    cloud_done=(cloud.get('domain')==cloud_android.get('server') and bool(cloud.get('domain'))
        and len(cloud.get('checks',[]))>=6 and cloud_android.get('cloud_url_visible') is True
        and all((ROOT/'evidence/screenshots'/name).is_file() for name in ['12-server-cloud.png','13-client-cloud-synced.png']))
    pending=[]
    if not checks['required_native_captures_reviewed']:pending.append('지정 앱 캡처와 최종 보고서 배치 검토')
    if not re.search(r'학번\s*:\s*\d+',report_text) or not re.search(r'이름\s*:\s*\S+',report_text):
        pending.append('보고서 학번과 이름 입력')
    if 'https://github.com/sylee21c/PhotoBlogProject' not in report_text:pending.append('보고서 GitHub URL 입력')
    if not cloud_done:pending.insert(0,'PythonAnywhere 실제 서버 배포 및 서버/Android 클라우드 캡처')
    if remote.returncode!=0:pending.append('본인 GitHub 원격 저장소 연결 및 push')
    local_blob=git('hash-object','--',report_path.name)
    remote_blob=git('rev-parse','origin/main:'+report_path.name)
    report_pushed=(local_blob.returncode==remote_blob.returncode==0 and local_blob.stdout.strip()==remote_blob.stdout.strip())
    if not report_pushed:pending.append('최종 보고서를 GitHub에 push')
    report={'checked_utc':datetime.now(timezone.utc).isoformat(),'local_checks':checks,
            'server_tests':python,'android_tests':android['tests'],'report_embedded_images':embedded,
            'cloud_deployment_verified':cloud_done,'cloud_domain':cloud.get('domain'),
            'credential_leak_files':leaked,'remaining_manual_or_account_steps':pending,
            'all_local_checks_passed':all(checks.values()),
            'report_file':report_path.name,'final_report_matches_origin_main':report_pushed,
            'ready_to_submit':all(checks.values()) and cloud_done and not pending,
            'readiness_note':'Checks cover recorded evidence and the report blob in the locally known origin/main. They do not submit the URL to the course portal.'}
    (ROOT/'evidence/submission-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'local_checks_passed':sum(checks.values()),'local_checks_total':len(checks),
                      'server_tests':python['tests'],'android_tests':android['tests'],'embedded_images':embedded,
                      'pending_steps':len(pending)},ensure_ascii=False))
    return 0 if all(checks.values()) else 1

if __name__=='__main__':raise SystemExit(main())
