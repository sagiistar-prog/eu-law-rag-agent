import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const base=process.env.EU_LAW_BASE_URL||'http://127.0.0.1:8892';
const output=`output/browser-${Date.now()}`;await fs.mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true,...(process.env.BROWSER_CHANNEL?{channel:process.env.BROWSER_CHANNEL}:{})});
const reports=[];
try {
 for(const width of [1440,390]) {
  const context=await browser.newContext({viewport:{width,height:1000},acceptDownloads:true});const page=await context.newPage();const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(base);await page.locator('#coverage').filter({hasText:'30'}).waitFor();
  assert.equal(await page.locator('#catalog li').count(),30);
  await page.locator('#instrument').selectOption('gdpr');
  await page.locator('#query').fill('What information must a controller provide when personal data are collected from the data subject?');
  const responsePromise=page.waitForResponse(r=>r.url().endsWith('/search')&&r.request().method()==='POST');
  await page.locator('#query').press('Enter');const response=await responsePromise;assert.equal(response.status(),200);
  const result=await response.json();assert.equal(result.storage,'postgres-pgvector');
  assert(result.evidence.some(h=>h.source_id==='gdpr-oj-art-13'));
  assert(result.evidence.every(h=>h.instrument_id==='gdpr'));
  await page.locator('#result .source').first().waitFor();
  await page.locator('#result .source').filter({hasText:'Article 13:'}).getByRole('button').click();
  await page.locator('#source-status').filter({hasText:'已显示完整条文'}).waitFor();
  assert((await page.locator('#details .original').textContent()).length>3000);
  assert.equal(await page.evaluate(()=>document.activeElement.id),'details');
  await page.getByRole('button',{name:'返回检索结果'}).click();assert.equal(await page.evaluate(()=>document.activeElement.textContent),'核对完整条文');
  const downloadPromise=page.waitForEvent('download');await page.locator('#export').click();const download=await downloadPromise;
  const target=`${output}/review-${width}.md`;await download.saveAs(target);const markdown=await fs.readFile(target,'utf8');
  assert(markdown.includes('32016R0679'));assert(markdown.includes(result.corpus_sha256));
  await page.screenshot({path:`${output}/desktop-${width}.png`,fullPage:true});
  const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  assert.deepEqual(axe.violations.map(v=>v.id),[]);
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);assert.equal(overflow,false);
  await page.locator('#query').fill('Are we currently compliant?');assert(await page.locator('#export').isDisabled());
  await page.locator('#submit').click();await page.locator('#result').filter({hasText:'核对修订'}).waitFor();
  assert.equal(await page.locator('#result .source').count(),0);
  await page.locator('#query').fill('What is the import duty for roasted coffee from Brazil?');await page.locator('#instrument').selectOption('all');
  await page.locator('#submit').click();await page.locator('#result h3').filter({hasText:'进一步核对'}).waitFor();assert.equal(await page.locator('#result .source').count(),0);
  await page.locator('#query').fill('数据如何删除');await page.locator('#submit').click();await page.locator('#result').filter({hasText:'请用英文'}).waitFor();
  await page.locator('#instrument').selectOption('gdpr');await page.locator('#query').fill('Can people move a copy of their information to another provider?');
  await page.locator('#submit').click();await page.locator('#candidates summary').waitFor();await page.locator('#candidates summary').click();
  await page.locator('#candidates').getByRole('button',{name:/Article 20:/}).click();await page.locator('#source-status').filter({hasText:'已显示完整条文'}).waitFor();
  assert((await page.locator('#details .original').textContent()).includes('portability'));
  // Explicit failure simulation: positive retrieval above uses real PostgreSQL.
  await page.route('**/search',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'检索暂不可用，请重试。'})}));
  await page.locator('#query').fill('Keep this question');await page.locator('#submit').click();await page.locator('#status').filter({hasText:'问题已保留'}).waitFor();
  assert.equal(await page.locator('#query').inputValue(),'Keep this question');assert(await page.locator('#export').isDisabled());await page.unroute('**/search');
  assert.deepEqual(errors,[]);reports.push({width,axe_violations:0,page_errors:errors,overflow,storage:result.storage,full_article:true,markdown_export:true,version_refusal:true,missing_source_refusal:true,simulated_503_recovery:true});
  await context.close();
 }
 await fs.writeFile(`${output}/report.json`,JSON.stringify(reports,null,2));console.log(JSON.stringify({output,reports}));
}finally {await browser.close();}
