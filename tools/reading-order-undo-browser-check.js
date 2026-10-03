/* Disposable accessibility-export-fixture.py project only.
 * BOOTSTRAP_URL PROJECT_DIR EVIDENCE_DIR.
 */
const fs = require('fs'), path = require('path'), assert = require('assert');
const {chromium} = require('./wordpress-roundtrip/node_modules/playwright-core');
const [url, projectArg, evidenceArg] = process.argv.slice(2);
const project = path.resolve(projectArg), evidence = path.resolve(evidenceArg);
fs.mkdirSync(evidence, {recursive:true});
async function main() {
  const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless:true});
  const context = await browser.newContext({viewport:{width:1440,height:1000}}), page = await context.newPage();
  const report = {browser:browser.version(), checks:{}, errors:[]};
  page.on('pageerror',error=>report.errors.push(error.message));
  const read=()=>JSON.parse(fs.readFileSync(path.join(project,'review/current.json')));
  const content=doc=>{const copy=structuredClone(doc);delete copy.review_session;return copy;};
  const activate=async locator=>{
    await locator.focus();
    await Promise.all([page.waitForEvent('framenavigated'),page.keyboard.press('Enter')]);
    await page.waitForLoadState('domcontentloaded');
  };
  const undo=page.locator('#reading-order-undo');
  const restored=async(before,id)=>{
    await activate(undo);
    await page.waitForFunction(id=>document.activeElement.id==='block-'+id,id);
    assert.deepEqual(content(read()),content(before));
    assert(await undo.isDisabled());
    assert(await page.locator('#undo-action').isDisabled());
    assert(await page.locator('#block-'+id).evaluate(el=>el.getBoundingClientRect().top>=document.querySelector('.reading-order-header').getBoundingClientRect().bottom-1));
  };
  try {
    await page.goto(url);const origin=new URL(url).origin;
    await page.goto(origin+'/structure#block-h1');
    await page.waitForFunction(()=>document.activeElement.id==='block-h1');
    assert(await undo.isDisabled());
    assert(!(await page.locator('.review-history').evaluate(el=>el.open)));
    assert(await undo.evaluate(el=>getComputedStyle(el).backgroundColor==='rgb(229, 231, 235)'&&el.closest('.reading-order-header')));
    const initial=read(), originalPath=path.join(project,'extraction/normalized/document.json'), original=fs.readFileSync(originalPath,'utf8');
    const previewBefore=await (await page.request.get(origin+'/api/accessibility/preview')).text();
    const heading=page.locator('#block-h1 .block-form');
    await heading.locator('[name="content"]').fill('Edited heading');
    await heading.locator('[name="review_status"]').selectOption('needs_review');
    await activate(heading.locator('button[type="submit"]'));
    assert.equal(read().blocks.find(b=>b.id==='h1').content,'Edited heading');
    await page.goto(origin+'/document'); await page.goto(origin+'/structure#block-h1');
    await page.waitForFunction(()=>document.activeElement.id==='block-h1');
    assert(await undo.isEnabled());
    await page.screenshot({path:path.join(evidence,'undo-desktop.png')});
    // A rejected Undo request must keep saved data and both controls usable.
    const after=read();
    await page.route('**/api/review/undo',route=>route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({status:'error',error:'Synthetic Undo failure'})}));
    page.once('dialog',dialog=>dialog.dismiss());
    await undo.click();
    await page.waitForFunction(()=>document.getElementById('app-status').textContent==='Synthetic Undo failure');
    assert(await undo.isEnabled());assert(await page.locator('#undo-action').isEnabled());
    assert.deepEqual(read(),after);await page.unroute('**/api/review/undo');
    await restored(initial,'h1');
    report.checks.savedTextReopenKeyboardUndoFocusEmptyHistoryAndFailureRecovery=true;

    await page.goto(origin+'/structure#block-p2');
    const link=page.locator('.link-text-form[data-block-id="resource-1"]');
    await link.locator('[name="link_text"]').fill('Changed resource label');
    await activate(link.locator('button[type="submit"]'));
    assert(read().blocks.find(b=>b.id==='p2').children[0].runs.some(r=>r.text==='Changed resource label'));
    await restored(initial,'p2');
    report.checks.linkLabelsDestinationsNestedIdsAndApprovalsRestored=true;

    await page.goto(origin+'/structure#block-figure');
    const image=page.locator('#block-figure .image-block-form');
    await image.locator('[name="alt"]').fill('Edited image alternative');
    await image.locator('[name="caption"]').fill('Edited caption');
    await image.locator('[name="review_status"]').selectOption('needs_review');
    await activate(image.locator('button[type="submit"]'));await restored(initial,'figure');
    await page.goto(origin+'/structure#block-table');
    const table=page.locator('#block-table .table-accessibility-form');
    await table.locator('[name="table_caption"]').fill('Edited data caption');
    await table.locator('[name="table_header_column"]').check();
    await activate(table.locator('button[type="submit"]'));await restored(initial,'table');
    report.checks.imageAlternativesCaptionsMappingsAndTableSemanticsRestored=true;

    await page.goto(origin+'/structure#block-p2');
    await activate(page.locator('#block-p2 [data-action="down"]'));
    assert.notDeepEqual(read().blocks.map(b=>b.id),initial.blocks.map(b=>b.id));
    await restored(initial,'p2');
    report.checks.readingOrderRestoredWithoutChangingBlockOrPageIdentities=true;

    await page.goto(origin+'/structure#block-figure');
    await page.locator('#visual-description-tools > summary').click();
    const visual=page.locator('#visual-visual .complex-visual-form');
    await visual.locator('[name="long_description"]').fill('Updated synthetic chart description.');
    await visual.locator('button[type="submit"]').click();
    await page.waitForFunction(()=>document.querySelector('.visual-save-message').textContent.startsWith('Saved.'));
    assert(await undo.isEnabled());assert(await page.locator('#undo-action').isEnabled());
    await page.locator('#block-figure').focus();await restored(initial,'figure');
    report.checks.asyncDescriptionSaveEnablesBothUndoControls=true;

    await page.setViewportSize({width:390,height:844});
    await page.goto(origin+'/structure#block-p2');
    await page.waitForFunction(()=>document.activeElement.id==='block-p2');
    const text=page.locator('#block-p2 form.block-form').filter({has:page.locator('[name="content"]')}).first();
    await text.locator('[name="content"]').fill((await text.locator('[name="content"]').inputValue()).replace('Resource library','Resource center'));
    await text.locator('[name="review_status"]').selectOption('needs_review');
    await activate(text.locator('button[type="submit"]'));
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    assert(await undo.evaluate(el=>{const r=el.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;}));
    await page.screenshot({path:path.join(evidence,'undo-narrow.png')});await restored(initial,'p2');
    report.checks.narrowToolbarAndListUndo=true;
    assert.equal(fs.readFileSync(originalPath,'utf8'),original);
    assert.equal(await (await page.request.get(origin+'/api/accessibility/preview')).text(),previewBefore);
    report.checks.immutableSourceAndRestoredSemanticHtmlUnchanged=true;
    assert.deepEqual(report.errors,[]);report.result='passed';
  }catch(error){report.result='failed';report.failure=error.stack;await page.screenshot({path:path.join(evidence,'failure.png')});process.exitCode=1;}
  finally{fs.writeFileSync(path.join(evidence,'browser-report.json'),JSON.stringify(report,null,2));process.stdout.write(JSON.stringify(report,null,2)+'\n');await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
