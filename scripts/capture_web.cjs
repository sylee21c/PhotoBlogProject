// Real browser screenshots of the local running app; no fabricated result pages.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'evidence', 'screenshots');
fs.mkdirSync(output, { recursive: true });
(async () => {
  const credentials = JSON.parse(fs.readFileSync(path.join(root, '.runtime', 'demo-credentials.json'), 'utf8'));
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1060 }, deviceScaleFactor: 1 });
    await page.goto('http://127.0.0.1:8000/');
    await page.screenshot({ path: path.join(output, '08-server-local.png'), fullPage: false });
    await page.goto('http://127.0.0.1:8000/accounts/login/');
    await page.locator('#id_username').fill(credentials.username);
    await page.locator('#id_password').fill(credentials.password);
    await Promise.all([page.waitForURL('http://127.0.0.1:8000/'), page.getByRole('button', { name: '로그인', exact: true }).click()]);
    await page.goto('http://127.0.0.1:8000/post/new/');
    await page.locator('#id_title').fill('웹에서 기록한 새로운 순간');
    await page.locator('#id_text').fill('브라우저의 사진 게시 폼에서 실제로 업로드한 검증 게시글입니다.');
    const files = [];
    function walk(folder) { for (const item of fs.readdirSync(folder, { withFileTypes: true })) { const name = path.join(folder, item.name); if (item.isDirectory()) walk(name); else if (name.endsWith('.jpg')) files.push(name); } }
    walk(path.join(root, 'PhotoBlogServer', 'media'));
    await page.locator('#id_image').setInputFiles(files[0]);
    await page.locator('#preview').waitFor({ state: 'visible' });
    await page.screenshot({ path: path.join(output, '03-post-form.png'), fullPage: true });
    await Promise.all([page.waitForURL(/\/post\/\d+\//), page.getByRole('button', { name: '사진 게시하기' }).click()]);
    await page.screenshot({ path: path.join(output, '03-post-result.png'), fullPage: true });
    const postUrl = page.url();
    await page.goto(postUrl + 'edit/');
    await page.locator('#id_text').fill('기존 사진을 유지하며 웹 편집 폼에서 수정한 검증 게시글입니다.');
    await page.screenshot({ path: path.join(output, '14-web-edit.png'), fullPage: true });
    await Promise.all([page.waitForURL(postUrl), page.getByRole('button', { name: '수정 저장', exact: true }).click()]);
    if (!(await page.getByText('기존 사진을 유지하며 웹 편집 폼에서 수정한 검증 게시글입니다.').count())) throw new Error('Web edit not persisted');
    await page.goto(postUrl + 'delete/');
    await page.screenshot({ path: path.join(output, '14-web-delete.png'), fullPage: true });
    await page.getByRole('link', { name: '취소', exact: true }).click();
    await page.waitForURL(postUrl);
    await page.goto('http://127.0.0.1:8000/?q=' + encodeURIComponent('바다'));
    await page.screenshot({ path: path.join(output, '14-server-search.png'), fullPage: true });
    await page.goto('file:///' + path.join(root, 'evidence', 'coverage', 'index.html').replace(/\\/g, '/'));
    await page.screenshot({ path: path.join(output, '06-coverage.png'), fullPage: true });
    fs.writeFileSync(path.join(root, 'evidence', 'web-verification.json'), JSON.stringify({ server: 'http://127.0.0.1:8000/', postUrl, webPostCreated: true, webEditPersisted: true, webDeleteCancelled: true, screenshotsIncludeBrowserChrome: false }, null, 2));
    console.log('Captured local web form, posted result, gallery, search and actual coverage report.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
