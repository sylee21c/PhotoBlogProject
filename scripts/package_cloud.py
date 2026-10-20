"""Create a server-only upload ZIP, without local DB, photos or credentials."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parent.parent
private=ROOT/'.runtime';private.mkdir(exist_ok=True)
target=private/'photoblog-server.zip'
blocked={'__pycache__','media','staticfiles','.venv','.runtime','.git'}
allowed={'.py','.html','.css','.js','.txt','.md','.sh','.json','.jpg'}
files=[]
with ZipFile(target,'w',ZIP_DEFLATED) as package:
    for source in sorted((ROOT/'PhotoBlogServer').rglob('*')):
        relative=source.relative_to(ROOT)
        if not source.is_file() or source.is_symlink() or blocked.intersection(relative.parts):continue
        if source.name!='.coveragerc' and source.suffix not in allowed:continue
        content=source.read_bytes()
        if source.suffix=='.sh':content=content.replace(b'\r\n',b'\n')
        package.writestr('PhotoBlogProject/'+relative.as_posix(),content)
        files.append(relative.as_posix())
with ZipFile(target) as package:
    assert package.testzip() is None
    assert 'PhotoBlogProject/PhotoBlogServer/manage.py' in package.namelist()
    assert all('db.sqlite3' not in n and '/media/' not in n and '/.runtime/' not in n for n in package.namelist())
receipt={'file':target.name,'files':len(files),'bytes':target.stat().st_size,
         'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'contains_local_credentials':False}
(private/'cloud-package.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt))
