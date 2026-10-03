/* Disposable document-structure-fixture.py project only.
 * BOOTSTRAP_URL PROJECT_DIR EVIDENCE_DIR.
 */
const fs = require('fs'), path = require('path'), assert = require('assert');
const {chromium} = require('./wordpress-roundtrip/node_modules/playwright-core');
const [url, projectArg, evidenceArg] = process.argv.slice(2);
const project = path.resolve(projectArg), evidence = path.resolve(evidenceArg);
fs.mkdirSync(evidence, {recursive:true});
async function main() {
  const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const report = {browser:browser.version(), checks:{}, errors:[]};
  page.on('pageerror', e => report.errors.push(e.message));
  const read = () => JSON.parse(fs.readFileSync(path.join(project,'review/current.json')));
  const activate = async locator => { await locator.focus(); await page.keyboard.press('Enter'); };
  const submit = async locator => {
    await locator.focus();
    await Promise.all([page.waitForEvent('framenavigated'),page.keyboard.press('Enter')]);
    await page.waitForLoadState('domcontentloaded');
  };
  const noOverflow = async () => assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
  const rightAligned = async selector => {
    for (const row of await page.locator(selector).all()) {
      const bounds = await row.evaluate(el => {
        const parent = el.parentElement.getBoundingClientRect(), button = el.querySelector('a').getBoundingClientRect();
        return {parentRight:parent.right-parseFloat(getComputedStyle(el.parentElement).paddingRight), buttonRight:button.right};
      });
      assert(Math.abs(bounds.parentRight-bounds.buttonRight)<2,JSON.stringify(bounds));
    }
  };
  try {
    await page.goto(url); const origin = new URL(url).origin;
    await page.goto(origin+'/structure');
    const before = read();
    const filter = page.locator('#block-review-filter'), shown = page.locator('.block-card:not([hidden])');
    const filterCounts = async (approved = 27, pending = 1, excluded = 0) => {
      for (const [key, label, count] of [['all', 'All', 28], ['approved', 'Approved', approved],
        ['pending', 'Needing review', pending], ['excluded', 'Excluded', excluded]]) {
        assert.equal(await filter.locator(`[data-filter="${key}"]`).innerText(), `${label} (${count})`);
      }
      assert.equal(await page.locator('#block-filter-count').innerText(), `${await shown.count()} of 28 blocks`);
    };
    assert.equal(await filter.locator('select').count(),0);
    assert.equal(await filter.getByRole('link').count(),4);
    assert(await filter.evaluate(el => parseFloat(getComputedStyle(el).fontSize) < 18));
    assert.equal(await shown.count(),28);
    await filterCounts();
    assert(await filter.evaluate(el => {
      const links = [...el.querySelectorAll('a')].map(link => link.getBoundingClientRect());
      const count = el.querySelector('#block-filter-count').getBoundingClientRect();
      return links.every(link => Math.abs(link.top - links[0].top) < 2)
        && Math.abs(count.top - links[0].top) < 5;
    }), 'Desktop filter counts and visible total should fit on one line');
    await activate(filter.locator('[data-filter="pending"]'));
    assert.equal(await shown.count(),1);
    await filterCounts();
    assert.equal(await filter.locator('[aria-current="true"]').getAttribute('data-filter'),'pending');
    await page.getByRole('button',{name:'Next block',exact:true}).click();
    assert.equal(await page.evaluate(() => document.activeElement.id),'block-p2');
    await activate(filter.locator('[data-filter="approved"]'));
    assert.equal(await shown.count(),27);
    await activate(filter.locator('[data-filter="excluded"]'));
    assert.equal(await shown.count(),0);
    await filterCounts();
    assert(await page.locator('#next-block').isDisabled());
    await page.reload();
    await filterCounts();
    assert.equal(await filter.locator('[aria-current="true"]').getAttribute('data-filter'),'excluded');
    await page.goto(origin+'/structure#block-p2');
    await page.waitForFunction(() => document.activeElement.id === 'block-p2');
    assert.equal(await filter.locator('[aria-current="true"]').getAttribute('data-filter'),'all');
    assert.deepEqual(read(),before);
    report.checks.textLinkFiltersKeyboardCountsNavigationReloadAndHiddenBlockFocus = true;

    await page.goto(origin+'/structure');
    await activate(filter.locator('[data-filter="pending"]'));
    await submit(page.locator('#block-p2 [data-action="approve"]'));
    assert.equal(await shown.count(),0);
    await filterCounts(28, 0);
    await submit(page.locator('#reading-order-undo'));
    assert.equal(await shown.count(),1);
    await filterCounts();
    await page.getByRole('button',{name:'Next block',exact:true}).click();
    await submit(page.locator('#block-p2 [data-action="toggle-excluded"]'));
    assert.equal(await shown.count(),0);
    await filterCounts(27, 0, 1);
    await submit(page.locator('#reading-order-undo'));
    assert.equal(await shown.count(),1);
    await filterCounts();
    await page.getByRole('button',{name:'Next block',exact:true}).click();
    assert.equal(await page.evaluate(() => document.activeElement.id),'block-p2');
    assert.equal(read().blocks.find(b=>b.id==='p2').review.status,'needs_review');
    report.checks.filteredApprovalExclusionAndUndo = true;

    const tools = page.locator('#visual-description-tools');
    assert(!(await tools.evaluate(el=>el.open)));
    assert((await tools.locator(':scope > summary').innerText()).includes('Longer image descriptions'));
    await activate(tools.locator(':scope > summary'));
    assert((await tools.innerText()).includes('Choose Not applicable if short alt text is sufficient.'));
    const explanation = tools.locator('details').filter({has:page.getByText('Why these images appear here',{exact:true})});
    assert(!(await explanation.evaluate(el=>el.open)));
    await page.goto(origin+'/structure#visual-visual');
    await page.waitForFunction(()=>document.activeElement.id==='visual-visual');
    assert(await tools.evaluate(el=>el.open));
    report.checks.clearDescriptionGuidanceCollapsedHelpAndDeepLink = true;
    await page.goto(origin+'/structure');
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(evidence,'structure-desktop.png')});

    await page.goto(origin+'/output-pages');
    const actions = page.getByRole('group',{name:'Page arrangement actions',exact:true});
    assert.equal(await actions.getByRole('button').count(),4);
    assert.equal(await actions.getByRole('button',{name:'Continue to Preview',exact:true}).count(),0);
    assert(await page.locator('.workflow-actions').evaluate(el=>{
      const first=el.querySelector('[role="group"]').getBoundingClientRect(), next=el.querySelector('.workflow-next').getBoundingClientRect();
      return next.left-first.right >= 32;
    }));
    await rightAligned('.workflow-next');
    const popupPromise = page.waitForEvent('popup');
    await page.getByRole('button',{name:'Preview contents',exact:true}).click();
    const popup = await popupPromise; await popup.waitForLoadState('domcontentloaded');
    assert((await popup.locator('body').innerText()).includes('Handbook'));await popup.close();
    await page.screenshot({path:path.join(evidence,'arrange-desktop.png')});
    await activate(page.getByRole('button',{name:'Continue to Preview',exact:true}));
    await page.waitForURL(origin+'/preview');
    report.checks.separateRightAlignedPreviewHandoffAndContentsPopup = true;

    assert.equal(await page.getByRole('button',{name:'Continue to Export',exact:true}).count(),2);
    await rightAligned('.workflow-next');
    assert(await page.locator('.segmented-control').evaluate(el=>{
      const buttons=el.querySelectorAll('button');return buttons[1].getBoundingClientRect().left-buttons[0].getBoundingClientRect().right >= 12;
    }));
    await page.frameLocator('.preview-shell iframe').getByRole('heading',{name:'Handbook',exact:true}).waitFor();
    await activate(page.getByRole('button',{name:'WordPress Preview',exact:true}));
    await page.frameLocator('.preview-shell iframe').getByRole('heading',{name:'Handbook',exact:true}).waitFor();
    assert.equal(await page.locator('[data-mode="wordpress"]').getAttribute('aria-pressed'),'true');
    await activate(page.getByRole('button',{name:'Semantic HTML',exact:true}));
    await page.screenshot({path:path.join(evidence,'preview-desktop.png')});
    report.checks.previewModeSpacingSwitchingAndBothExportHandoffs = true;
    await activate(page.getByRole('button',{name:'Continue to Export',exact:true}).first());
    await page.waitForURL(origin+'/export');

    await page.setViewportSize({width:390,height:844});
    for (const route of ['/structure','/output-pages','/preview']) {
      await page.goto(origin+route);await noOverflow();
      if(route==='/structure') {
        await filterCounts();
        await filter.scrollIntoViewIfNeeded();
        await page.screenshot({path:path.join(evidence,'reading-filters-narrow.png')});
      }
      if(route!=='/structure') await rightAligned('.workflow-next');
      await page.screenshot({path:path.join(evidence,route.slice(1)+'-narrow.png')});
    }
    await activate(page.getByRole('button',{name:'Continue to Export',exact:true}).last());
    await page.waitForURL(origin+'/export');
    report.checks.narrowFiltersGroupingRightAlignmentAndBottomExportNavigation = true;
    assert.deepEqual(report.errors,[]);report.result='passed';
  } catch(error) {
    report.result='failed';report.failure=error.stack;process.exitCode=1;
    await page.screenshot({path:path.join(evidence,'failure.png')});
  } finally {
    fs.writeFileSync(path.join(evidence,'browser-report.json'),JSON.stringify(report,null,2));
    process.stdout.write(JSON.stringify(report,null,2)+'\n');await browser.close();
  }
}
main().catch(e=>{process.stderr.write(e.stack+'\n');process.exit(1);});
