"""Package publishable files only; keep the ZIP outside the repository itself."""
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parent.parent


def package():
    result=subprocess.run(['git','-c','safe.directory='+str(ROOT),'-C',str(ROOT),
        'ls-files','-z','--cached','--others','--exclude-standard'],capture_output=True,check=True)
    files=sorted(set(filter(None,result.stdout.decode('utf-8').split('\0'))))
    forbidden={'.git','.venv','.runtime','.gradle','__pycache__','media','staticfiles','build'}
    target=ROOT.parent/'PhotoBlogProject-submission.zip'
    archive_files=[]
    with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=6) as archive:
        for name in files:
            source=ROOT/name;relative=source.relative_to(ROOT)
            if not source.is_file() or source.is_symlink():continue
            if forbidden.intersection(relative.parts) or relative.name in ['db.sqlite3','local.properties','.env']:
                raise RuntimeError('Private/build file found in publishable inventory: '+relative.as_posix())
            if not source.resolve().is_relative_to(ROOT.resolve()):raise RuntimeError('Path escapes project')
            arcname='PhotoBlogProject/'+relative.as_posix()
            archive.write(source,arcname);archive_files.append(relative.as_posix())
    with ZipFile(target) as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            assert not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts
        for required in ['PhotoBlogServer/manage.py','PhotoViewer/app/src/main/java/com/example/photoviewer/MainActivity.java',
                         'artifacts/PhotoViewer-debug.apk','모바일웹서비스 프로젝트_공통평가 01_수행 결과 보고서.docx']:
            assert 'PhotoBlogProject/'+required in archive.namelist(),required
    receipt={'file':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
             'file_count':len(archive_files),'bytes':target.stat().st_size,'excluded_private_and_build_files':True}
    (ROOT.parent/'PhotoBlogProject-package.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))
    return target


if __name__=='__main__':package()
