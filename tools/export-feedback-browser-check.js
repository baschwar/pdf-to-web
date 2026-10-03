/* Synthetic browser check: BOOTSTRAP_URL PROJECT_DIR EVIDENCE_DIR. */
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const { chromium } = require('./wordpress-roundtrip/node_modules/playwright-core');
const [url, projectArg, evidenceArg] = process.argv.slice(2);
const project = path.resolve(projectArg), evidence = path.resolve(evidenceArg);
fs.mkdirSync(evidence, {recursive: true});
async function main() {
  const browser = await chromium.launch({executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}, permissions: ['clipboard-read', 'clipboard-write']});
  const page = await context.newPage();
  const report = {browser: browser.version(), checks: {}, errors: []};
  page.on('pageerror', error => report.errors.push(error.message));
  const read = () => JSON.parse(fs.readFileSync(path.join(project, 'review/current.json')));
  const change = async locator => {
    await locator.focus();
    await Promise.all([page.waitForEvent('framenavigated'), page.keyboard.press('Enter')]);
    await page.waitForLoadState('domcontentloaded');
  };
  try {
    await page.goto(url);
    await page.getByRole('link', {name: 'Arrange Pages', exact: true}).click();
    assert((await page.locator('main').innerText()).includes('Unassigned content: figure'));
    assert(await page.getByRole('button', {name: 'Export page', exact: true}).isDisabled());
    assert.equal(await page.locator('#content-outline').getAttribute('open'), null);
    await change(page.getByRole('button', {name: 'Include unassigned content in this page', exact: true}));
    assert(read().output_pages.pages[0].block_ids.includes('figure'));
    assert.equal(await page.evaluate(() => document.activeElement.id), 'page-editor');
    await change(page.getByRole('button', {name: 'Undo last action', exact: true}));
    assert(!read().output_pages.pages[0].block_ids.includes('figure'));
    await change(page.getByRole('button', {name: 'Keep everything on one page', exact: true}));
    assert.equal(read().output_pages.pages.length, 1);
    assert(read().output_pages.pages[0].block_ids.includes('figure'));
    report.checks.assignmentRecoveryKeyboardFocusUndoAndOnePage = true;
    await page.getByRole('button', {name: 'Preview page', exact: true}).click();
    await page.frameLocator('#output-page-frame').getByRole('heading', {name: 'Handbook', exact: true}).waitFor();
    await page.getByRole('button', {name: 'Export page', exact: true}).click();
    await page.locator('#output-page-message a').first().waitFor();
    await page.getByRole('button', {name: 'Export complete package', exact: true}).click();
    await page.locator('#output-page-message a').filter({hasText: 'output/pages.zip'}).waitFor();
    report.checks.previewsAndBothPageExports = true;
    await page.getByRole('link', {name: 'Export', exact: true}).first().click();
    assert(await page.evaluate(() => {
      const ids = ['media-export-form', 'media-wxr-form', 'export-form'];
      const forms = ids.map(id => document.getElementById(id));
      return !!(forms[0].compareDocumentPosition(forms[1]) & Node.DOCUMENT_POSITION_FOLLOWING) && !!(forms[1].compareDocumentPosition(forms[2]) & Node.DOCUMENT_POSITION_FOLLOWING);
    }));
    await page.getByRole('textbox', {name: 'Image filename prefix', exact: true}).fill('citi-training-');
    await page.getByRole('button', {name: 'Prepare images ZIP and mapping CSV', exact: true}).click();
    await page.getByRole('link', {name: 'Download all images ZIP', exact: true}).waitFor();
    assert((await page.locator('#media-export-result').innerText()).includes('21 images packaged'));
    for (const [name, filename] of [['Download all images ZIP', 'downloaded-images.zip'], ['Download mapping CSV', 'downloaded-mapping.csv']]) {
      const downloadWait = page.waitForEvent('download');
      await page.getByRole('link', {name, exact: true}).click();
      await (await downloadWait).saveAs(path.join(evidence, filename));
    }
    assert.equal(read().media_export.image_prefix, 'citi-training-');
    await page.reload();
    assert.equal(await page.getByRole('textbox', {name: 'Image filename prefix', exact: true}).inputValue(), 'citi-training-');
    await change(page.getByRole('button', {name: 'Undo last change', exact: true}));
    assert(!read().media_export);
    await page.getByRole('textbox', {name: 'Image filename prefix', exact: true}).fill('citi-training-');
    await page.getByRole('button', {name: 'Prepare images ZIP and mapping CSV', exact: true}).click();
    await page.getByRole('link', {name: 'Download all images ZIP', exact: true}).waitFor();
    report.checks.mediaBeforeContentZipDownloadPrefixPersistenceUndo = true;
    const items = Array.from({length: 21}, (_, i) => `<item><wp:post_id>${101+i}</wp:post_id><wp:post_type>attachment</wp:post_type><wp:attachment_url>https://example.test/uploads/citi-training-image${i+1}.png</wp:attachment_url></item>`).join('');
    const mediaFile = path.join(evidence, 'synthetic-wordpress-media.xml');
    fs.writeFileSync(mediaFile, `<rss xmlns:wp="http://wordpress.org/export/1.2/"><channel>${items}</channel></rss>`);
    await page.getByLabel('WordPress media export', {exact: true}).setInputFiles(mediaFile);
    await page.getByRole('button', {name: 'Match WordPress media', exact: true}).click();
    await page.waitForFunction(() => document.getElementById('media-mapping-result').textContent.includes('21 image mappings matched'));
    assert((await page.locator('#media-mapping-status').innerText()).includes('All included images'));
    await page.locator('#export-form [name="target"]').selectOption('gutenberg');
    await page.getByRole('button', {name: 'Export reviewed document', exact: true}).click();
    await page.getByRole('button', {name: 'Copy handbook.html HTML to clipboard', exact: true}).waitFor();
    const markup = fs.readFileSync(path.join(project, 'output/wordpress/blocks/handbook.html'), 'utf8');
    assert.equal((markup.match(/wp:image/g) || []).length, 42);
    assert(!markup.includes('data-pdf-to-web-media="unresolved"'));
    assert(markup.includes('citi-training-image21.png'));
    await page.getByRole('button', {name: 'Copy handbook.html HTML to clipboard', exact: true}).click();
    await page.waitForFunction(() => [...document.querySelectorAll('#export-result button')].some(button => button.textContent === 'Copied'));
    assert.equal(await page.evaluate(() => navigator.clipboard.readText()), markup);
    // Re-mapping clears stale copy/download actions until content is regenerated.
    await page.getByRole('button', {name: 'Match WordPress media', exact: true}).click();
    await page.waitForFunction(() => document.getElementById('export-result').childElementCount === 0);
    report.checks.exactFilenameMatch21ImagesMappedExportClipboardAndStaleOutput = true;
    await page.setViewportSize({width: 390, height: 844});
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({path: path.join(evidence, 'export-narrow.png'), fullPage: true});
    await page.setViewportSize({width: 1440, height: 1000});
    await page.screenshot({path: path.join(evidence, 'export-desktop.png'), fullPage: true});
    report.checks.narrowLayout = true;
    assert.deepEqual(report.errors, []);
    report.result = 'passed';
  } catch (error) { report.result = 'failed'; report.failure = error.stack; process.exitCode = 1; }
  finally {
    fs.writeFileSync(path.join(evidence, 'browser-report.json'), JSON.stringify(report, null, 2));
    process.stdout.write(JSON.stringify(report, null, 2) + '\n');
    await browser.close();
  }
}
main().catch(error => { process.stderr.write(error.stack + '\n'); process.exit(1); });
