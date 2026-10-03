/* Synthetic fixture only. BOOTSTRAP_URL PROJECT_DIR EVIDENCE_DIR.
 * Requires approved blocks except p2, a ready visual linked to figure, no history.
 */
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const {chromium} = require('./wordpress-roundtrip/node_modules/playwright-core');
const [url, projectArg, evidenceArg] = process.argv.slice(2);
const project = path.resolve(projectArg), evidence = path.resolve(evidenceArg);
fs.mkdirSync(evidence, {recursive: true});

async function main() {
  const browser = await chromium.launch({executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true});
  const context = await browser.newContext({viewport: {width:1440, height:1000}});
  const page = await context.newPage();
  const report = {date:'2026-10-01', browser:browser.version(), checks:{}, errors:[]};
  page.on('pageerror', error => report.errors.push(error.message));
  const read = () => JSON.parse(fs.readFileSync(path.join(project, 'review/current.json')));
  const keyboardAction = async locator => {
    await locator.focus();
    await Promise.all([page.waitForEvent('framenavigated'), page.keyboard.press('Enter')]);
    await page.waitForLoadState('domcontentloaded');
  };
  const open = async id => {
    const details = page.locator(id);
    if (!(await details.evaluate(el => el.open))) {
      await details.locator(':scope > summary').focus();
      await page.keyboard.press('Enter');
    }
    assert(await details.evaluate(el => el.open));
  };
  const saveVisual = async () => {
    const response = page.waitForResponse(r => r.url().includes('/api/complex-visuals/') && r.request().method() === 'POST');
    await page.locator('#visual-visual button[type="submit"]').focus();
    await page.keyboard.press('Enter');
    assert.equal((await response).status(), 200);
    await page.waitForFunction(() => document.querySelector('.visual-save-message').textContent.startsWith('Saved.'));
  };
  try {
    await page.goto(url);
    const origin = new URL(url).origin;
    await page.goto(origin + '/document');
    assert.equal(await page.locator('#structure-review-complete').count(), 0);
    assert(!(await page.locator('main').innerText()).includes('0 unresolved diagnostic issues'));
    assert.equal(await page.locator('progress').getAttribute('value'), '27');
    assert.equal(await page.locator('progress').getAttribute('max'), '28');
    assert(await page.locator('.metadata-grid').evaluate(el => {
      const label = el.querySelector('dt'), value = el.querySelector('dd');
      return parseFloat(getComputedStyle(label).fontSize) > parseFloat(getComputedStyle(value).fontSize) && Number(getComputedStyle(label).fontWeight) >= 700;
    }));
    assert(await page.locator('.document-review-progress').evaluate(el => el.getBoundingClientRect().bottom < document.querySelector('.metadata-grid').getBoundingClientRect().top));
    assert.equal((await page.locator('main').innerText()).split('Reviewed 27 · Pending 1').length - 1, 1);
    await page.screenshot({path:path.join(evidence, 'document-pending.png'), fullPage:true});
    report.checks.documentTopProgressLabelsSingleCountsAndNoEmptyWarning = true;

    await page.goto(origin + '/structure');
    for (const id of ['#image-description-tools', '#visual-description-tools', '.review-history']) assert(!(await page.locator(id).evaluate(el => el.open)));
    assert(await page.locator('#undo-action').isDisabled());
    assert(await page.locator('#block-h1 [data-action="approve"]').isDisabled());
    assert(await page.locator('#block-p2 [data-action="approve"]').isEnabled());
    assert(await page.locator('#source-heading').isVisible());
    assert(await page.locator('#source-heading').evaluate(el => el.getBoundingClientRect().top < innerHeight));
    await page.screenshot({path:path.join(evidence, 'structure-desktop.png')});
    report.checks.collapsedToolsPrimaryWorkflowAndDisabledApprovedButtons = true;
    await open('#image-description-tools');
    await open('#draft-manual-import');
    assert.equal(await page.locator('#draft-manual-import > ol > li').count(), 4);
    await page.locator('#image-description-tools > summary').click();
    report.checks.keyboardOrderedManualImportSteps = true;

    await keyboardAction(page.locator('#block-p2 [data-action="approve"]'));
    assert(await page.locator('#structure-review-complete').isVisible());
    assert(await page.locator('#block-p2 [data-action="approve"]').isDisabled());
    await page.goto(origin + '/document');
    assert(await page.getByRole('button', {name:'Continue to Accessibility', exact:true}).isVisible());
    assert.equal(await page.locator('progress').getAttribute('value'), '28');
    await page.screenshot({path:path.join(evidence, 'document-complete.png'), fullPage:true});
    await page.goto(origin + '/structure');
    await open('.review-history');
    assert(await page.locator('#undo-action').isEnabled());
    await keyboardAction(page.locator('#undo-action'));
    assert.equal(read().blocks.find(b => b.id === 'p2').review.status, 'needs_review');
    await page.goto(origin + '/document');
    assert.equal(await page.locator('#structure-review-complete').count(), 0);
    await page.goto(origin + '/structure');
    await open('.review-history');
    assert(await page.locator('#undo-action').isDisabled());
    report.checks.finalApprovalDocumentHandoffReloadPersistedHistoryAndUndo = true;

    await page.goto(origin + '/structure#visual-visual');
    await page.waitForFunction(() => document.activeElement.id === 'visual-visual');
    assert(await page.locator('#visual-description-tools').evaluate(el => el.open));
    const visual = page.locator('#visual-visual');
    await visual.locator('[name="long_description"]').fill('Updated synthetic result: the total is ten in 2026.');
    await saveVisual();
    assert(await page.locator('#block-figure [data-action="approve"]').isDisabled());
    assert(await page.locator('#undo-action').isEnabled());
    await visual.locator('[name="long_description"]').fill('');
    await visual.locator('[name="status"]').selectOption('needs_text_equivalent');
    await saveVisual();
    assert(await page.locator('#block-figure [data-action="approve"]').isEnabled());
    assert((await page.locator('#visual-description-counts').innerText()).startsWith('1 to review'));
    await page.reload();
    await page.waitForFunction(() => document.activeElement.id === 'visual-visual');
    assert.equal(await visual.locator('[name="long_description"]').inputValue(), '');
    await open('.review-history');
    await keyboardAction(page.locator('#undo-action'));
    assert.equal(read().blocks.find(b => b.id === 'figure').review.status, 'approved');
    assert.equal(read().review.complex_visuals[0].accessibility.long_description, 'Updated synthetic result: the total is ten in 2026.');
    report.checks.descriptionDeepLinkFocusSavePendingCountsApprovalReloadAndUndo = true;

    // All blocks reviewed with one incomplete equivalent: Document must link to Structure.
    await keyboardAction(page.locator('#block-p2 [data-action="approve"]'));
    await page.goto(origin + '/structure#visual-visual');
    await page.waitForFunction(() => document.activeElement.id === 'visual-visual');
    await visual.locator('[name="long_description"]').fill('');
    await visual.locator('[name="status"]').selectOption('needs_text_equivalent');
    await saveVisual();
    await keyboardAction(page.locator('#block-figure [data-action="approve"]'));
    await page.goto(origin + '/document');
    assert.equal(await page.locator('#structure-review-complete').count(), 0);
    await page.getByRole('link', {name:'Review description on source page 5', exact:true}).click();
    await page.waitForFunction(() => document.activeElement.id === 'visual-visual');
    assert(await visual.isVisible());
    await visual.locator('[name="status"]').selectOption('not_applicable');
    await saveVisual();
    assert.equal(read().blocks.find(b => b.id === 'figure').review.status, 'approved');
    report.checks.pendingDocumentDescriptionLinkAndNotApplicablePreservesImage = true;

    await page.goto(origin + '/preview');
    await page.frameLocator('iframe').locator('body').waitFor();
    assert((await page.frameLocator('iframe').locator('body').innerText()).includes('Handbook'));
    await page.goto(origin + '/export');
    await page.locator('#export-form [name="target"]').selectOption('html');
    await page.getByRole('button', {name:'Export reviewed document', exact:true}).click();
    await page.locator('#export-result a').first().waitFor();
    const downloaded = page.waitForEvent('download');
    await page.locator('#export-result a').filter({hasText:'.html'}).first().click();
    const download = await downloaded;
    await download.saveAs(path.join(evidence, 'reviewed.html'));
    const markup = fs.readFileSync(path.join(evidence, 'reviewed.html'), 'utf8');
    assert(markup.includes('Handbook'));
    assert(markup.includes('alt='));
    report.checks.semanticPreviewAndActualHtmlDownload = true;

    await page.setViewportSize({width:390, height:844});
    for (const route of ['/document', '/structure']) {
      await page.goto(origin + route);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.screenshot({path:path.join(evidence, route.slice(1) + '-narrow.png'), fullPage:route === '/document'});
    }
    await open('#image-description-tools');
    await open('#draft-manual-import');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await open('#visual-description-tools');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    report.checks.narrowCollapsedAndExpandedLayouts = true;
    assert.deepEqual(report.errors, []);
    report.result = 'passed';
  } catch (error) {
    report.result = 'failed'; report.failure = error.stack;
    await page.screenshot({path:path.join(evidence, 'failure.png'), fullPage:true});
    process.exitCode = 1;
  } finally {
    fs.writeFileSync(path.join(evidence, 'browser-report.json'), JSON.stringify(report, null, 2));
    process.stdout.write(JSON.stringify(report, null, 2) + '\n');
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
