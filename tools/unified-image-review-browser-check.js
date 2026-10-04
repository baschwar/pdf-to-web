/* Independent UI actions on a disposable synthetic 21-image project only. */
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const {chromium} = require('./wordpress-roundtrip/node_modules/playwright-core');
const [bootstrap, projectArg, evidenceArg] = process.argv.slice(2);
const root = path.resolve(projectArg), evidence = path.resolve(evidenceArg);
fs.mkdirSync(evidence, {recursive: true});
async function main() {
  const browser = await chromium.launch({executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true});
  const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
  const page = await context.newPage();
  const origin = new URL(bootstrap).origin;
  const report = {browser: browser.version(), checks: [], errors: [], dialogs: []};
  context.on('page', p => p.on('pageerror', error => report.errors.push(error.message)));
  page.on('pageerror', error => report.errors.push(error.message));
  page.on('dialog', async d => {report.dialogs.push(d.message()); await d.dismiss();});
  await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  const read = () => JSON.parse(fs.readFileSync(path.join(root, 'review/current.json')));
  const original = fs.readFileSync(path.join(root, 'extraction/normalized/document.json'));
  const pending = () => read().review.complex_visuals.filter(v => !['reviewed', 'not_applicable', 'excluded'].includes(v.status)).length;
  const image = (p, id='image-2') => p.locator(`.image-block-form[data-block-id="${id}"]`);
  async function submit(p, button, endpoint, status=200, reload=true, keyboard=false) {
    const response = p.waitForResponse(r => r.url().includes(endpoint) && r.request().method() === 'POST');
    const navigation = reload && status===200 ? p.waitForEvent('load') : null;
    if (navigation) navigation.catch(() => {});
    if (keyboard) {await button.focus(); await p.keyboard.press('Enter');} else await button.click();
    const result = await response;
    if (result.status() !== status) assert.equal(result.status(), status, await result.text());
    if (navigation) {await navigation; await p.waitForLoadState('domcontentloaded');}
    if (status !== 200) {
      const error = (await result.json()).error;
      await p.waitForFunction(message => [...document.querySelectorAll('.block-action-message, #bulk-review-message')].some(el => el.textContent.includes(message)), error);
    }
  }
  async function visit(p, url) {
    const response = await p.goto(url, {waitUntil:'load'});
    if (!response) await p.reload({waitUntil:'load'});
    if (new URL(url).pathname === '/accessibility') {
      await p.locator('#bulk-review-tools').evaluate(tools => { tools.open = true; });
      await p.locator('#bulk-review-visibility').selectOption('all');
    }
  }
  async function undo(p, accessibility=false) {
    await submit(p, p.locator(accessibility ? '#bulk-review-undo' : '#reading-order-undo'), '/api/review/undo');
    if (accessibility) await p.locator('#bulk-review-visibility').selectOption('all');
  }
  async function selectDescription(id) {await page.locator(`.bulk-review-select[value="description:${id}"]`).check();}
  async function prepareBatch() {
    await page.locator('#bulk-review-state').selectOption('reviewed');
    await page.locator('#bulk-review-apply').focus(); await page.keyboard.press('Enter');
    await page.locator('#bulk-review-confirm').waitFor({state:'visible'});
  }
  try {
    await visit(page, bootstrap);
    const baseline = fs.readFileSync(path.join(root, 'review/current.json'));
    for (const route of ['/document','/structure','/accessibility','/export']) {
      await visit(page, origin+route);
      assert((await page.locator('#review-task-counts').innerText()).includes('19 description reviews'));
    }
    assert(fs.readFileSync(path.join(root,'review/current.json')).equals(baseline));
    assert.equal(read().blocks.filter(b=>b.type==='image'&&b.review.status==='approved').length,21);
    report.checks.push('21 approved images / 2 Reviewed descriptions / 19 pending remain unchanged on read across four screens');
    await visit(page, origin+'/structure#block-image-2');
    assert.equal(await page.locator('.complex-visual-form').count(),0);
    assert.equal(await image(page).locator('[name="review_status"]').count(),0);
    assert.equal(await page.locator('#block-image-2 [data-action="approve"]').count(),0);
    await page.locator('#block-review-filter [data-filter="pending"]').click();
    assert.equal(await page.locator('.block-card:not([hidden])').count(),19);
    assert(await page.locator('#block-image-2').isVisible());
    await page.locator('#block-review-filter [data-filter="approved"]').click();
    assert.equal(await page.locator('.block-card:not([hidden])').count(),3);
    await page.evaluate(()=>{location.hash='visual-description-2';});
    await page.waitForFunction(()=>document.activeElement.id==='visual-description-2');
    assert(await page.locator('#block-image-2').isVisible());
    assert.equal(await page.locator('#visual-description-2').count(),1);
    assert((await page.locator('#review-task-counts').innerText()).includes('19 image reviews'));
    assert((await image(page).innerText()).includes('Text provided; awaiting manual review'));
    report.checks.push('pending linked descriptions keep 19 images in Needing review; one inline owner/approval; old description link reveals and focuses image');
    await image(page).locator('[data-description-field="long_description"]').fill('Saved edited description');
    await submit(page,image(page).getByRole('button',{name:'Save image block 4',exact:true}),'/api/blocks/image-2');
    assert.equal(read().review.complex_visuals[2].accessibility.long_description,'Saved edited description');
    assert.equal(pending(),19); assert.equal(read().blocks[3].review.status,'needs_review');
    await undo(page); assert.equal(pending(),19);
    const untouched = read().review.complex_visuals.slice(3);
    await submit(page,image(page).locator('[data-save-and-approve]'),'/save-and-approve',200,true,true);
    assert.equal(pending(),18); assert.deepEqual(read().review.complex_visuals.slice(3),untouched);
    assert.equal(read().blocks[3].review.status,'approved');
    for (const route of ['/document','/accessibility','/export']) {await visit(page, origin+route); assert((await page.locator('#review-task-counts').innerText()).includes('18 description reviews'));}
    await visit(page, origin+'/structure#block-image-2'); await undo(page); assert.equal(pending(),19);
    report.checks.push('ordinary Save remains pending; explicit keyboard Save and approve changes one description only; counts/reopen/Undo agree');
    for (const field of ['[name="alt"]','[data-description-field="long_description"]']) {
      await visit(page, origin+'/structure#block-image-2');
      await image(page).locator(field).fill('');
      const before = fs.readFileSync(path.join(root,'review/current.json'));
      await submit(page,image(page).locator('[data-save-and-approve]'),'/save-and-approve',400,false);
      assert(fs.readFileSync(path.join(root,'review/current.json')).equals(before));
      assert((await page.locator('#block-image-2 .block-action-message').innerText()).length>0);
    }
    await visit(page, origin+'/structure#block-image-2');
    await image(page).locator('[name="decorative"]').check();
    await submit(page,image(page).locator('[data-save-and-approve]'),'/save-and-approve');
    assert(read().blocks[3].decorative); assert.equal(read().review.complex_visuals[2].status,'not_applicable');
    await undo(page);
    report.checks.push('missing alt/long description reject without writes; decorative approval is recoverable');
    await visit(page, origin+'/structure#block-image-2');
    await image(page).locator('[data-description-field="long_description"]').fill('');
    await image(page).locator('[data-description-field="disposition"]').selectOption('not_applicable');
    await submit(page,image(page).locator('[data-save-and-approve]'),'/save-and-approve');
    assert.equal(read().review.complex_visuals[2].status,'not_applicable');
    assert.equal(read().blocks[3].review.status,'approved'); assert.equal(pending(),18);
    await undo(page); assert.equal(pending(),19);
    report.checks.push('No separate description needed is explicitly approved with the image in one action; Undo restores both');
    const other = await context.newPage();
    await visit(page, origin+'/structure#block-image-2');
    await visit(other, origin+'/structure#block-image-3');
    await image(other,'image-3').locator('[name="caption"]').fill('Concurrent edit');
    await submit(other,image(other,'image-3').getByRole('button',{name:'Save image block 5',exact:true}),'/api/blocks/image-3');
    const concurrent = fs.readFileSync(path.join(root,'review/current.json'));
    await submit(page,image(page).locator('[data-save-and-approve]'),'/save-and-approve',400,false);
    assert(fs.readFileSync(path.join(root,'review/current.json')).equals(concurrent));
    assert((await page.locator('#block-image-2 .block-action-message').innerText()).includes('project changed'));
    await page.reload(); await undo(page); await other.close();
    report.checks.push('two-tab stale approval rejected with exact recovery; Undo preserves concurrent content');
    await visit(page, origin+'/accessibility#bulk-review-heading');
    await page.locator('#bulk-review-select-all').focus(); await page.keyboard.press('Space');
    assert.equal(await page.locator('.bulk-review-select:checked').count(),43);
    assert(await page.locator('#bulk-review-state').isDisabled());
    await page.locator('#bulk-review-filter').selectOption('Descriptions · image');
    assert.equal(await page.locator('.bulk-review-select:checked').count(),0);
    await selectDescription('description-2');
    await prepareBatch();
    assert((await page.locator('#bulk-review-confirmation').innerText()).includes('1 selected description records'));
    await submit(page,page.locator('#bulk-review-confirm'),'/api/accessibility/bulk-review');
    assert.equal(pending(),18);
    await undo(page,true); assert.equal(pending(),19);
    report.checks.push('mixed select-all disables invalid states; filter clears selection; explicit scoped confirmation and one-step Undo');
    await visit(page, origin+'/structure#block-image-3');
    await image(page,'image-3').locator('[data-description-field="long_description"]').fill('');
    await submit(page,image(page,'image-3').getByRole('button',{name:'Save image block 5',exact:true}),'/api/blocks/image-3');
    await visit(page, origin+'/accessibility#bulk-review-heading');
    await page.locator('#bulk-review-filter').selectOption('Descriptions · image');
    await selectDescription('description-2'); await selectDescription('description-3'); await prepareBatch();
    const incomplete = fs.readFileSync(path.join(root,'review/current.json'));
    await submit(page,page.locator('#bulk-review-confirm'),'/api/accessibility/bulk-review',400,false);
    assert(fs.readFileSync(path.join(root,'review/current.json')).equals(incomplete));
    assert((await page.locator('#bulk-review-message').innerText()).includes('description-3'));
    await undo(page,true); assert.equal(pending(),19);
    report.checks.push('eligible + incomplete batch rejects atomically with exact description reason');
    await page.setViewportSize({width:390,height:844});
    await page.locator('#bulk-review-filter').selectOption('Descriptions · image');
    await page.locator('#bulk-review-select-all').focus(); await page.keyboard.press('Space');
    assert.equal(await page.locator('.bulk-review-select:checked').count(),21);
    assert.equal(await page.locator('.bulk-review-group:not([hidden])').count(),1);
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await page.locator('#bulk-review-filter').selectOption('Blocks · image');
    assert.equal(await page.locator('.bulk-review-select:checked').count(),0);
    await page.locator('.bulk-review-select[value="block:image-2"]').check();
    await page.locator('#bulk-review-state').selectOption('approved');
    await page.locator('#bulk-review-apply').click();
    assert((await page.locator('#bulk-review-confirmation').innerText()).includes('associated descriptions'));
    await submit(page,page.locator('#bulk-review-confirm'),'/api/accessibility/bulk-review');
    assert.equal(pending(),18); await undo(page,true);
    await page.locator('#bulk-review-heading').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(evidence,'bulk-narrow.png')});
    report.checks.push('narrow keyboard select-all is visible classification only; image batch displays its associated review scope');
    await page.setViewportSize({width:1440,height:1000});
    await page.locator('#bulk-review-filter').selectOption('Descriptions · image');
    await page.locator('#bulk-review-select-all').check(); await prepareBatch();
    await submit(page,page.locator('#bulk-review-confirm'),'/api/accessibility/bulk-review');
    assert.equal(pending(),0);
    await visit(page, origin+'/export'); assert((await page.locator('#review-task-counts').innerText()).includes('Pending 0 review tasks'));
    await visit(page, origin+'/preview');
    await page.getByRole('button',{name:'WordPress Preview',exact:true}).click();
    await page.locator('#preview-profile').selectOption('wsuwp');
    assert((await page.locator('#preview-description').innerText()).includes('local minimal CSS'));
    assert((await page.locator('#preview-profile option:checked').innerText()).includes('approximate'));
    await visit(page, origin+'/accessibility#bulk-review-heading'); await undo(page,true); assert.equal(pending(),19);
    report.checks.push('explicit complete batch resolves export review gate; WSUWP approximate label and local CSS explanation; Undo restores 19');
    await visit(page, origin+'/structure#block-image-2');
    await page.setViewportSize({width:390,height:844});
    await page.locator('#visual-description-2').scrollIntoViewIfNeeded();
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await image(page).locator('[data-save-and-approve]').focus();
    await page.waitForFunction(()=>{const el=document.activeElement; const rect=el.getBoundingClientRect(); const sticky=document.querySelector('.reading-order-header').getBoundingClientRect(); return el.matches('[data-save-and-approve]') && rect.top>=sticky.bottom && rect.bottom<=innerHeight;});
    await page.screenshot({path:path.join(evidence,'image-narrow.png')});
    await page.setViewportSize({width:1440,height:1000});
    await page.locator('#block-image-2').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(evidence,'image-desktop.png')});
    await page.locator('#back-to-top').waitFor({state:'visible'});
    await page.locator('#back-to-top').focus(); await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(()=>document.activeElement.id),'app-top');
    assert(fs.readFileSync(path.join(root,'extraction/normalized/document.json')).equals(original));
    assert.equal(report.errors.length,0); assert.equal(report.dialogs.length,0);
    report.checks.push('floating Back to top keyboard focus preserved; immutable synthetic extraction unchanged; zero script errors/dialogs');
  } finally {
    fs.writeFileSync(path.join(evidence,'browser-report.json'),JSON.stringify(report,null,2));
    await browser.close();
  }
  console.log(JSON.stringify(report,null,2));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
