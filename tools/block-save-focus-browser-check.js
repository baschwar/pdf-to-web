/* Disposable block-save-focus-fixture.py project only.
 * BOOTSTRAP_URL PROJECT_DIR EVIDENCE_DIR.
 */
const fs = require('fs'), path = require('path'), assert = require('assert');
const {chromium} = require('./wordpress-roundtrip/node_modules/playwright-core');
const [url, projectArg, evidenceArg] = process.argv.slice(2);
const project = path.resolve(projectArg), evidence = path.resolve(evidenceArg);
fs.mkdirSync(evidence, {recursive:true});
async function main() {
  const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const report = {browser:browser.version(),checks:{},errors:[]};
  page.on('pageerror', error => report.errors.push(error.message));
  const read = () => JSON.parse(fs.readFileSync(path.join(project,'review/current.json')));
  const originalPath = path.join(project,'extraction/normalized/document.json');
  const original = fs.readFileSync(originalPath,'utf8');
  const card = page.locator('#block-instructions');
  const reviewForm = card.locator('.nested-list-review-form');
  const filter = page.locator('#block-review-filter');
  const submit = async button => {
    await button.focus();
    await Promise.all([page.waitForEvent('framenavigated'),page.keyboard.press('Enter')]);
    await page.waitForLoadState('load');
    await page.waitForTimeout(150);
  };
  const selectedFilter = () => filter.locator('[aria-current="true"]').getAttribute('data-filter');
  const anchored = async expectedFilter => {
    assert.equal(await page.evaluate(()=>document.activeElement.id),'block-instructions');
    assert.equal(await selectedFilter(),expectedFilter);
    assert(await card.isVisible());
    assert.equal(await page.locator('#source-page-number').inputValue(),'2');
    assert(await card.evaluate(el=>{
      const card=el.getBoundingClientRect(), header=document.querySelector('.reading-order-header').getBoundingClientRect();
      return card.top >= header.bottom-2 && card.top < innerHeight && scrollY > 0;
    }), 'Saved block must be in view below the sticky toolbar');
  };
  try {
    await page.goto(url); const origin = new URL(url).origin;
    for (const mode of ['all','approved']) {
      await page.goto(origin+'/structure');
      await filter.locator(`[data-filter="${mode}"]`).click();
      await card.focus();
      await submit(reviewForm.locator('button[type="submit"]'));
      await anchored(mode);
      assert.equal(new URL(page.url()).hash,'#block-instructions');
      await page.screenshot({path:path.join(evidence,`unchanged-save-${mode}.png`)});
    }
    report.checks.allAndApprovedUnchangedSaveKeepsBlockInsteadOfCompletionBanner=true;

    for (const mode of ['all','approved']) {
      // Explicitly approve synthetic content before exercising each edit path.
      await page.evaluate(async()=>{
        const csrf=decodeURIComponent(document.cookie.split('; ').find(v=>v.startsWith('pdf_to_web_csrf=')).split('=')[1]);
        const response=await fetch('/api/blocks/instructions',{method:'POST',headers:{'content-type':'application/json','x-csrf-token':csrf},body:JSON.stringify({review_status:'approved'})});
        if (!response.ok) throw new Error(await response.text());
      });
      await page.goto(origin+'/structure');
      await filter.locator(`[data-filter="${mode}"]`).click();
      await card.locator('[name="link_text"]').fill(`Resource library ${mode}`);
      await submit(card.locator('.link-text-form button[type="submit"]'));
      await anchored('all');
      const owner = read().blocks[1];
      assert.equal(owner.review.status,'needs_review');
      assert.equal(owner.children[0].runs[1].text,`Resource library ${mode}`);
      assert.equal(owner.children[0].runs[1].url,'https://example.test/resources');
      await submit(reviewForm.locator('button[type="submit"]'));
      await anchored('all');
      assert.equal(read().blocks[1].review.status,'needs_review');
      await reviewForm.locator('[name="review_status"]').selectOption('approved');
      await submit(reviewForm.locator('button[type="submit"]'));
      await anchored('all');
      assert.equal(read().blocks[1].review.status,'approved');
    }
    report.checks.nestedLinkSaveAndReviewStateSaveStayAtOwningBlockUnderBothFilters=true;
    await submit(page.locator('#reading-order-undo'));
    await anchored('all');
    assert.equal(read().blocks[1].review.status,'needs_review');
    await page.reload(); await page.waitForTimeout(150); await anchored('all');
    report.checks.undoAndReloadKeepSavedBlockAndItsSourcePage=true;

    await page.setViewportSize({width:390,height:844});
    await submit(reviewForm.locator('button[type="submit"]'));
    await anchored('all');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:path.join(evidence,'saved-block-narrow.png')});
    report.checks.narrowSaveKeepsBlockBelowStickyToolbarWithoutOverflow=true;

    await page.goto(origin+'/structure?return_to=accessibility&finding=link%3Aresource%3A2#block-instructions');
    await submit(reviewForm.locator('button[type="submit"]'));
    assert.equal(new URL(page.url()).pathname,'/accessibility');
    assert.equal(new URL(page.url()).hash,'#finding-link%3Aresource%3A2');
    report.checks.accessibilityCorrectionsStillReturnToFinding=true;
    assert.equal(fs.readFileSync(originalPath,'utf8'),original);
    assert.deepEqual(report.errors,[]);report.result='passed';
  } catch(error) {
    report.result='failed';report.failure=error.stack;process.exitCode=1;
    await page.screenshot({path:path.join(evidence,'failure.png')});
  } finally {
    fs.writeFileSync(path.join(evidence,'browser-report.json'),JSON.stringify(report,null,2));
    process.stdout.write(JSON.stringify(report,null,2)+'\n');await browser.close();
  }
}
main().catch(error=>{process.stderr.write(error.stack+'\n');process.exitCode=1;});
