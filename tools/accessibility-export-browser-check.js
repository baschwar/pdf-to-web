/* Synthetic fixture from accessibility-export-fixture.py only.
 * BOOTSTRAP_URL PROJECT_DIR EVIDENCE_DIR.
 */
const fs = require('fs'), path = require('path'), assert = require('assert');
const {chromium} = require('./wordpress-roundtrip/node_modules/playwright-core');
const [url, projectArg, evidenceArg] = process.argv.slice(2);
const project = path.resolve(projectArg), evidence = path.resolve(evidenceArg);
fs.mkdirSync(evidence, {recursive:true});
async function main() {
  const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless:true});
  const context = await browser.newContext({viewport:{width:1440,height:1000}, permissions:['clipboard-read','clipboard-write']});
  const page = await context.newPage(), report = {date:'2026-10-01', browser:browser.version(), checks:{}, errors:[]};
  page.on('pageerror', error => report.errors.push(error.message));
  const read = () => JSON.parse(fs.readFileSync(path.join(project,'review/current.json')));
  const submit = async locator => {
    await locator.focus();
    await Promise.all([page.waitForEvent('framenavigated'), page.keyboard.press('Enter')]);
    await page.waitForLoadState('domcontentloaded');
  };
  const scan = () => page.waitForFunction(() => document.getElementById('axe-status').textContent.startsWith('Check complete'));
  const expand = async selector => {
    if (!(await page.locator(selector).evaluate(el => el.open))) await page.locator(selector + ' > summary').click();
  };
  try {
    await page.goto(url);
    const origin = new URL(url).origin;
    await page.goto(origin+'/accessibility'); await scan();
    assert.equal(await page.locator('section[aria-labelledby="accessibility-diagnostics"]').count(),0);
    assert(!(await page.locator('.diagnostic-history').evaluate(el => el.open)));
    assert(!(await page.locator('#accessibility-complete').isVisible()));
    const finding = page.locator('[id="finding-link:resource-2:2"]');
    assert(await finding.getByRole('button',{name:'Open block',exact:true}).isVisible());
    assert(await finding.getByRole('button',{name:'Save decision',exact:true}).evaluate(el=>el.getBoundingClientRect().width<220));
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(evidence,'accessibility-pending.png'),fullPage:true});
    report.checks.compactBlockButtonsAndResolvedDiagnosticHistory = true;

    await finding.getByRole('button',{name:'Open block',exact:true}).click();
    assert(page.url().includes('return_to=accessibility'));
    await page.waitForFunction(()=>document.activeElement.id==='block-p2');
    const linkForm=page.locator('.link-text-form[data-block-id="resource-2"]');
    await linkForm.locator('[name="link_text"]').fill('Student help');
    await submit(linkForm.getByRole('button',{name:'Save link text',exact:true}));
    assert.equal(new URL(page.url()).pathname,'/accessibility'); await scan();
    assert.equal(await page.locator('[id="finding-link:resource-2:2"]').count(),0);
    assert.equal(await page.evaluate(()=>document.activeElement.id),'document-review-heading');
    assert(await page.evaluate(()=>document.activeElement.getBoundingClientRect().top>=document.querySelector('.app-header').getBoundingClientRect().bottom-1));
    assert.equal(read().blocks.find(b=>b.id==='p2').review.status,'needs_review');
    assert(!(await page.locator('#accessibility-complete').isVisible()));
    await page.locator('[id="finding-structure:p2"]').getByRole('button',{name:'Open block',exact:true}).click();
    await submit(page.locator('#block-p2 [data-action="approve"]'));
    assert.equal(new URL(page.url()).pathname,'/accessibility'); await scan();
    assert(await page.locator('#accessibility-complete').isVisible());
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(evidence,'accessibility-complete.png'),fullPage:true});
    report.checks.linkEditAndApprovalReturnToIssuesWithFreshScanAndCompletionGate = true;

    await page.getByRole('button',{name:'Continue to Arrange Pages',exact:true}).click();
    assert(await page.locator('#output-page-undo').evaluate(el=>getComputedStyle(el).backgroundColor==='rgb(229, 231, 235)'));
    const popupEvent=page.waitForEvent('popup');
    await page.getByRole('button',{name:'Preview contents',exact:true}).click();
    const popup=await popupEvent; await popup.waitForLoadState('domcontentloaded');
    await popup.locator('a[href^="/output-preview/"]').first().click();
    await popup.waitForFunction(()=>Array.from(document.images).length===21 && Array.from(document.images).every(img=>img.complete&&img.naturalWidth>0));
    assert(await popup.locator('img').evaluateAll(images=>images.every(img=>img.getAttribute('src').startsWith('/api/'))));
    await popup.screenshot({path:path.join(evidence,'arranged-preview.png'),fullPage:true});
    await popup.close();
    report.checks.arrangeNeutralUndoContentsNavigationAndAllMappedOrUnmappedLocalImages = true;

    await page.getByRole('button',{name:'Continue to Preview',exact:true}).click();
    assert.equal(await page.getByRole('button',{name:'Continue to Export',exact:true}).count(),2);
    await page.frameLocator('iframe').locator('body').waitFor();
    await page.getByRole('button',{name:'Continue to Export',exact:true}).first().click();
    assert.equal(await page.locator('#readiness-heading').count(),0);
    assert(!(await page.locator('main').innerText()).includes('0 unresolved'));
    assert.equal(await page.locator('#unmapped-media li').count(),3);
    await page.getByRole('button',{name:'Copy page title',exact:true}).click();
    await page.waitForFunction(()=>document.getElementById('copy-page-title-status').textContent==='Copied');
    assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),'Handbook');
    report.checks.previewTopBottomHandoffsExportOnlyActualIssuesAndClipboardFeedback = true;

    await page.locator('#export-form [name="target"]').selectOption('gutenberg');
    await page.getByRole('button',{name:'Export reviewed document',exact:true}).click();
    await page.locator('#export-result a').first().waitFor();
    const downloadEvent=page.waitForEvent('download');
    await page.locator('#export-result a').filter({hasText:'.html'}).first().click();
    await (await downloadEvent).saveAs(path.join(evidence,'gutenberg.html'));
    const markup=fs.readFileSync(path.join(evidence,'gutenberg.html'),'utf8');
    assert.equal((markup.match(/<img /g)||[]).length,18);
    assert.equal((markup.match(/pdf-to-web-unresolved-media/g)||[]).length,3);
    assert.equal((markup.match(/<img(?![^>]*\bsrc=)/g)||[]).length,0);
    for(const [url,label] of [['resources','Resource library'],['student-help','Student help'],['contact','Contact support']]) assert(markup.includes(`<a href="https://example.test/${url}">${label}</a>`));
    await page.locator('#export-result button').first().click();
    await page.waitForFunction(()=>document.querySelector('#export-result button').textContent==='Copied');
    assert((await page.evaluate(()=>navigator.clipboard.readText())).includes('<a href="https://example.test/student-help">Student help</a>'));
    report.checks.actualGutenbergDownloadCopyEighteenImageSourcesThreePlaceholdersAndThreeLinks = true;

    await page.goto(origin+'/structure#block-p2');
    await page.waitForFunction(()=>document.activeElement.id==='block-p2');
    const firstLink=page.locator('.link-text-form[data-block-id="resource-1"]');
    await firstLink.locator('[name="link_text"]').fill('Research resources');
    await submit(firstLink.getByRole('button',{name:'Save link text',exact:true}));
    assert.equal(new URL(page.url()).pathname,'/structure');
    const whole=page.locator('#block-p2 form.block-form').filter({has:page.locator('[name="content"]')}).first();
    await whole.locator('[name="content"]').fill((await whole.locator('[name="content"]').inputValue()).replace('Student help','Student help desk'));
    await whole.locator('[name="review_status"]').selectOption('approved');
    await submit(whole.getByRole('button',{name:'Save block 3',exact:true}));
    const resources=read().blocks.find(b=>b.id==='p2').children;
    assert.equal(resources.flatMap(b=>b.runs.filter(r=>r.type==='link')).length,3);
    assert(resources[1].runs.some(r=>r.type==='link'&&r.text==='Student help desk'&&r.url==='https://example.test/student-help'));
    await expand('.review-history'); await submit(page.locator('#undo-action'));
    assert(read().blocks.find(b=>b.id==='p2').children[1].runs.some(r=>r.text==='Student help'));
    report.checks.directStructureEditingKeepsItsNavigationAndListLinksPersistWithUndo = true;

    await page.setViewportSize({width:390,height:844});
    for(const route of ['/accessibility','/output-pages','/preview','/export']){
      await page.goto(origin+route);
      if(route==='/accessibility')await scan();
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),route);
      await page.screenshot({path:path.join(evidence,route.slice(1)+'-narrow.png')});
    }
    report.checks.narrowWorkflows = true;
    assert.deepEqual(report.errors,[]); report.result='passed';
  }catch(error){report.result='failed';report.failure=error.stack;await page.screenshot({path:path.join(evidence,'failure.png'),fullPage:true});process.exitCode=1;}
  finally{fs.writeFileSync(path.join(evidence,'browser-report.json'),JSON.stringify(report,null,2));process.stdout.write(JSON.stringify(report,null,2)+'\n');await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
