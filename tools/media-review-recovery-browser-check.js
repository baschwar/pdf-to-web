// Run against an isolated synthetic recovery project; never the live app.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('./wordpress-roundtrip/node_modules/playwright-core');
const [bootstrap, projectArg, outputArg] = process.argv.slice(2);
if (!bootstrap || !projectArg || !outputArg) throw new Error('Supply bootstrap URL, synthetic project and evidence directory.');
const root = path.resolve(projectArg), output = path.resolve(outputArg);
assert.equal(JSON.parse(fs.readFileSync(path.join(root, 'qa-fixture.json'))).synthetic, true);
const origin = new URL(bootstrap).origin;
const read = () => JSON.parse(fs.readFileSync(path.join(root, 'review/current.json')));
const stored = () => JSON.stringify([
  'project.json', 'review/current.json',
  ...fs.readdirSync(path.join(root, 'review/revisions')).sort().map(file => `review/revisions/${file}`)
].map(file => [file, fs.readFileSync(path.join(root, file)).toString('base64')]));
const report = {checks: [], errors: []};
fs.mkdirSync(output, {recursive: true});
async function main() {
  const browser = await chromium.launch({executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true});
  report.browser = browser.version();
  const context = await browser.newContext();
  await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  const page = await context.newPage();
  page.on('pageerror', error => report.errors.push(error.message));
  try {
    await page.goto(bootstrap);
    await page.goto(`${origin}/export`);
    const before = stored(), initial = read();
    for (const width of [1440, 390]) {
      await page.setViewportSize({width, height: width === 390 ? 844 : 1000});
      await page.locator('#media-review-recovery-preview').focus();
      await page.keyboard.press('Enter');
      const notice = page.locator('#media-review-recovery-undo-notice');
      await notice.waitFor({state: 'visible'});
      const text = await notice.innerText();
      assert.match(text, /Undo returns these images to pending review/);
      assert.match(text, /removes a saved history snapshot/);
      assert.match(text, /Restoring them again may be unavailable, requiring manual review before export/);
      const confirm = page.locator('#media-review-recovery-confirm');
      assert.equal(await confirm.getAttribute('aria-describedby'), 'media-review-recovery-undo-notice');
      assert(await confirm.evaluate(button => !!(document.getElementById(button.getAttribute('aria-describedby')).compareDocumentPosition(button) & Node.DOCUMENT_POSITION_FOLLOWING)));
      assert.equal(stored(), before);
      assert.equal(await page.locator('#media-review-recovery-selection li').count(), 20);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await confirm.focus();
      await page.screenshot({path: path.join(output, `confirmation-${width}.png`)});
      report.checks.push(`${width}px: Undo consequence visible before Confirm, associated accessible description, exact20 rows, no writes or overflow`);
      if (width === 1440) {
        await page.locator('#media-review-recovery-cancel').focus();
        await page.keyboard.press('Enter');
        assert.equal(stored(), before);
        assert.equal(await page.evaluate(() => document.activeElement.id), 'media-review-recovery-preview');
      }
    }
    const restored = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/api/media-review-recovery'));
    await page.keyboard.press('Enter');
    assert.equal((await restored).status(), 200);
    await page.waitForFunction(() => document.activeElement.id === 'readiness-heading');
    assert.equal(read().blocks.filter(block => block.review?.status === 'needs_review').length, 0);
    assert.equal(read().review_session.revision, initial.review_session.revision + 1);
    await page.goto(`${origin}/structure`);
    const undone = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/api/review/undo'));
    const loaded = page.waitForEvent('load');
    await page.locator('#reading-order-undo').focus();
    await page.keyboard.press('Enter');
    assert.equal((await undone).status(), 200);
    await loaded;
    assert.deepEqual(read().blocks, initial.blocks);
    assert.deepEqual(read().review.complex_visuals, initial.review.complex_visuals);
    await page.goto(`${origin}/export`);
    assert(await page.locator('#export-form button[type="submit"]').isDisabled());
    const afterUndo = stored();
    assert.equal((await (await page.request.get(`${origin}/api/media-review-recovery`)).json()).rows.length, 0);
    assert.equal(await page.locator('#media-review-recovery-preview').count(), 0);
    assert.equal(stored(), afterUndo);
    report.checks.push('Keyboard Confirm and Undo restore exact pending decisions/mappings/descriptions; Export blocked, repeat recovery refused, read-only GET unchanged');
    assert.deepEqual(report.errors, []);
  } catch (error) {
    report.failure = error.stack;
    throw error;
  } finally {
    fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify(report, null, 2));
    await browser.close();
  }
  console.log(JSON.stringify(report));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
