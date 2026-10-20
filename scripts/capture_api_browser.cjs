// Capture the actual DRF POST form and HTTP 201 response, in addition to the web gallery form.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
(async () => {
  const credentials = JSON.parse(fs.readFileSync(path.join(root, '.runtime/demo-credentials.json'), 'utf8'));
  const browser = await chromium.launch({ executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true });
  try {
    const page = await browser.newPage({ viewport:{width:1440,height:1150} });
    await page.goto('http://127.0.0.1:8000/accounts/login/');
    await page.locator('#id_username').fill(credentials.username);
    await page.locator('#id_password').fill(credentials.password);
    await Promise.all([page.waitForURL('http://127.0.0.1:8000/'),page.getByRole('button',{name:'로그인',exact:true}).click()]);
    // A search limits the response so the actual POST form can be read in one screenshot.
    const url='http://127.0.0.1:8000/api_root/Post/?q=API%20POST%20assessment';
    await page.goto(url);
    const images=[];
    function walk(folder){for(const e of fs.readdirSync(folder,{withFileTypes:true})){const p=path.join(folder,e.name);if(e.isDirectory())walk(p);else if(p.endsWith('.jpg'))images.push(p);}}
    walk(path.join(root,'PhotoBlogServer/media'));
    await page.locator('form input[name="title"]').fill('API POST assessment');
    await page.locator('form textarea[name="text"]').fill('Created through the actual Django REST Framework browsable POST form.');
    await page.locator('form input[name="image"]').setInputFiles(images[0]);
    await page.screenshot({path:path.join(root,'evidence/screenshots/03-api-post-form.png'),fullPage:true});
    const responsePromise=page.waitForResponse(r=>r.request().method()==='POST' && r.url().includes('/api_root/Post/'));
    await page.getByRole('button',{name:'POST',exact:true}).click();
    const response=await responsePromise;
    if(response.status()!==201)throw new Error('Browsable API POST returned HTTP '+response.status());
    await page.getByText('201 Created',{exact:false}).waitFor();
    await page.screenshot({path:path.join(root,'evidence/screenshots/03-api-post-created.png'),fullPage:true});
    const data=await (await page.request.get('http://127.0.0.1:8000/api_root/Post/?q=API%20POST%20assessment',{headers:{Accept:'application/json'}})).json();
    if(!data.some(p=>p.title==='API POST assessment'))throw new Error('Created API post missing');
    fs.writeFileSync(path.join(root,'evidence/api-browser-verification.json'),JSON.stringify({url,method:'POST',status:201,persisted:true,postIds:data.map(p=>p.id),screenshotsIncludeBrowserChrome:false},null,2));
    console.log('Actual browsable API POST form, HTTP 201 and persistence verified.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
