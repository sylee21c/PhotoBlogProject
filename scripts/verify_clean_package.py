"""Reproduce Django setup and real API calls from the exact submission ZIP.

Uses the already installed project dependencies, but a newly extracted source
tree, new SQLite DB and new demo credentials. Does not mutate the working DB.
"""
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parent.parent
archive=ROOT.parent/'PhotoBlogProject-submission.zip'
output=ROOT/'.runtime'/('clean-package-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
output.mkdir(parents=True)
with ZipFile(archive) as package:
    for info in package.infolist():
        assert (output/info.filename).resolve().is_relative_to(output.resolve())
    package.extractall(output)
clean=output/'PhotoBlogProject';server=clean/'PhotoBlogServer'
env=os.environ.copy();env.update(PYTHONIOENCODING='utf-8',DJANGO_DEBUG='1',DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost',PYTHONPATH=str(server))
checks={}
logfile=output/'setup-and-server.log'
with logfile.open('w',encoding='utf-8') as log:
    for command in [['migrate','--noinput'],['check'],['bootstrap_demo']]:
        subprocess.run([sys.executable,str(server/'manage.py'),*command],cwd=server,env=env,
                       check=True,stdout=log,stderr=log)
    checks['fresh_database_and_demo_setup']=True
    with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    process=subprocess.Popen([sys.executable,str(server/'manage.py'),'runserver',f'127.0.0.1:{port}','--noreload'],
        cwd=server,env=env,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    base=f'http://127.0.0.1:{port}'
    def request(path,method='GET',data=None,token=''):
        headers={'Accept':'application/json'}
        if token:headers['Authorization']='Token '+token
        if data is not None:headers['Content-Type']='application/json';data=json.dumps(data).encode()
        with urlopen(Request(base+path,data=data,method=method,headers=headers),timeout=5) as r:
            raw=r.read();return r.status,json.loads(raw) if raw else None
    try:
        deadline=time.monotonic()+15
        while True:
            try:health=request('/api/health/')[1];break
            except (URLError,TimeoutError):
                if time.monotonic()>deadline:raise
                time.sleep(.25)
        assert health['posts']==3;checks['health_and_three_demo_posts']=True
        rows=request('/api_root/Post/')[1];assert len(rows)==3
        page=request('/api_root/Post/?page=1&page_size=1')[1]
        assert len(page['results'])==1 and page['count']==3 and page['next'];checks['legacy_list_and_pagination']=True
        with urlopen(rows[0]['image']) as image:assert image.status==200 and image.headers['Content-Type'].startswith('image/')
        checks['image_download']=True
        credentials=json.loads((clean/'.runtime/demo-credentials.json').read_text(encoding='utf-8'))
        token=request('/api/token/','POST',{'username':credentials['username'],'password':credentials['password']})[1]['token']
        owner=request('/api/me/',token=token)[1];assert owner['username']==credentials['username'];checks['login_and_profile']=True
        post=rows[0];request(f'/api_root/Post/{post["id"]}/','PATCH',{'text':'Verified from the clean submission ZIP'},token)
        assert request(f'/api_root/Post/{post["id"]}/')[1]['text']=='Verified from the clean submission ZIP'
        checks['authenticated_update']=True
        status,_=request(f'/api_root/Post/{post["id"]}/','DELETE',token=token);assert status==204
        assert len(request('/api_root/Post/')[1])==2;checks['authenticated_delete']=True
        try:urlopen(post['image']);raise AssertionError('Deleted image is still served')
        except HTTPError as error:assert error.code==404
        checks['committed_delete_cleans_image']=True
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait()

result={'verified_utc':datetime.now(timezone.utc).isoformat(),'archive':archive.name,
        'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'checks':checks,'all_passed':all(checks.values()),
        'dependency_environment':'Existing project venv; freshly extracted code, DB and media'}
(ROOT.parent/'PhotoBlogProject-package-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
