/* Disposable merge/filter fixture only. BOOTSTRAP_URL PROJECT_DIR OTHER_PROJECT_DIR EVIDENCE_DIR. */
const fs = require('fs'), path = require('path'), assert = require('assert');
const {chromium} = require('./wordpress-roundtrip/node_modules/playwright-core');
const [url, projectArg, otherArg, evidenceArg] = process.argv.slice(2);
const project = path.resolve(projectArg), other = path.resolve(otherArg), evidence = path.resolve(evidenceArg);
fs.mkdirSync(evidence, {recursive: true});
async function main() {
  const browser = await chromium.launch({executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true});
  const page = await browser.newPage();
  const report = {browser: browser.version(), checks: [], errors: []};
  page.on('pageerror', error => report.errors.push(error.message));
  const read = () => JSON.parse(fs.readFileSync(path.join(project, 'review/current.json')));
  const card = identity => page.locator('#block-' + identity);
  const merge = identity => card(identity).locator('[data-action="merge"]');
  const review = value => page.locator(`#block-review-filter [data-filter="${value}"]`);
  const type = value => page.locator(`#block-type-filter [data-type-filter="${value}"]`);
  const active = async () => [await page.locator('#block-review-filter [aria-current="true"]').getAttribute('data-filter'),
    await page.locator('#block-type-filter [aria-current="true"]').getAttribute('data-type-filter')];
  const shown = () => page.locator('.block-card:not([hidden])');
  const keyboard = async locator => { await locator.focus(); await page.keyboard.press('Enter'); };
  const submit = async locator => {
    await locator.focus();
    await Promise.all([page.waitForEvent('framenavigated'), page.keyboard.press('Enter')]);
    await page.waitForLoadState('load');
    await page.waitForTimeout(100);
  };
  const api = async (endpoint, body) => page.evaluate(async ({endpoint, body}) => {
    const csrf = decodeURIComponent(document.cookie.split('; ').find(s => s.startsWith('pdf_to_web_csrf=')).split('=')[1]);
    const response = await fetch(endpoint, {method: 'POST', headers: {'content-type': 'application/json', 'x-csrf-token': csrf}, body: JSON.stringify(body)});
    return {status: response.status, data: await response.json()};
  }, {endpoint, body});
  const checkCounts = async () => {
    const document = read();
    const [state, kind] = await active();
    const group = b => ['heading', 'paragraph', 'list', 'image', 'table'].includes(b.type) ? b.type : 'other';
    const matchState = (b, filter) => filter === 'all' || (filter === 'pending' ? ['needs_review', 'unreviewed'].includes(b.review.status) : filter === b.review.status);
    const matchType = (b, filter) => filter === 'all' || group(b) === filter;
    const expected = document.blocks.filter(b => matchState(b, state) && matchType(b, kind));
    assert.deepEqual(await shown().evaluateAll(cards => cards.map(c => c.id.slice(6))), expected.map(b => b.id));
    assert.equal(await page.locator('#block-filter-count').innerText(), `${expected.length} of ${document.blocks.length} blocks`);
    for (const value of ['all', 'pending', 'approved', 'excluded']) {
      const count = document.blocks.filter(b => matchState(b, value) && matchType(b, kind)).length;
      assert((await review(value).innerText()).endsWith(`(${count})`));
    }
    for (const value of ['all', 'heading', 'paragraph', 'list', 'image', 'table', 'other']) {
      const count = document.blocks.filter(b => matchState(b, state) && matchType(b, value)).length;
      assert((await type(value).innerText()).endsWith(`(${count})`));
    }
  };
  const firstResult = async (waitForSource = true) => {
    if (!await shown().count()) {
      assert.equal(await page.evaluate(() => document.activeElement.id), 'show-all-blocks');
      assert.equal(await page.locator('.block-card.source-selected').count(), 0);
      assert(await page.locator('#next-block').isDisabled());
      assert(await page.locator('#previous-block').isDisabled());
      return;
    }
    const identity = await shown().first().getAttribute('id');
    await page.waitForFunction(({identity, waitForSource}) => {
      const selected = document.getElementById(identity);
      const rect = selected.getBoundingClientRect();
      const bottom = document.querySelector('.reading-order-header').getBoundingClientRect().bottom;
      const loading = document.querySelector('.source-image-stage').getAttribute('aria-busy') === 'true';
      const rendered = !document.getElementById('source-image').hidden && document.getElementById('source-page-render-status').hidden;
      return document.activeElement === selected && selected.classList.contains('source-selected')
        && rect.top >= bottom - 2 && rect.top < innerHeight && (!waitForSource || !loading && rendered);
    }, {identity, waitForSource});
    const index = await shown().first().getAttribute('data-block-index');
    assert((await page.locator('#selected-block-position').innerText()).startsWith('Block ' + index));
    if (waitForSource) assert((await page.locator('#source-page-label').innerText()).startsWith('Block ' + index + ','));
  };
  try {
    await page.goto(url);
    const origin = new URL(url).origin;
    for (const width of [1440, 390]) {
      await page.setViewportSize({width, height: 1000});
      await page.emulateMedia({reducedMotion: width === 390 ? 'reduce' : 'no-preference'});
      await page.goto(origin + '/structure');
      await review('all').click(); await type('all').click();
      await checkCounts();
      assert(!await merge('first').isDisabled());
      for (const identity of ['third', 'list', 'heading-second', 'before-excluded', 'excluded', 'linked', 'last']) {
        assert(await merge(identity).isDisabled(), identity);
        const described = await merge(identity).getAttribute('aria-describedby');
        assert(await page.locator('#' + described).isVisible());
        assert((await page.locator('#' + described).innerText()).length);
      }
      await card('list').locator('[data-action="end"]').focus();
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => document.activeElement.dataset.action), 'split');
      report.checks.push(`${width}px: unsupported pairs, lists, last/excluded/rich/different-level boundaries have disabled, explained controls and keyboard skips them`);
      await page.evaluate(() => {
        for (const identity of ['first', 'list']) {
          const button = document.querySelector('#block-' + identity + ' [data-action="merge"]');
          button.removeAttribute('data-merge-reason');
        }
        updateMergeControls();
      });
      assert(await merge('first').isDisabled());
      assert((await page.locator('#merge-help-first').innerText()).includes('Relaunch PDF to Web'));
      assert(await merge('list').isDisabled());
      assert((await page.locator('#merge-help-list').innerText()).includes('List blocks'));
      await page.reload();
      report.checks.push(`${width}px: older server markup keeps list merges disabled and requires relaunch for unknown availability`);

      const beforeFilters = fs.readFileSync(path.join(project, 'review/current.json'));
      for (const state of ['all', 'pending', 'approved', 'excluded']) {
        await keyboard(review(state));
        for (const kind of ['all', 'heading', 'paragraph', 'list', 'image', 'table', 'other']) {
          await keyboard(type(kind)); await checkCounts(); await firstResult();
        }
      }
      assert(fs.readFileSync(path.join(project, 'review/current.json')).equals(beforeFilters));
      report.checks.push(`${width}px: all 28 review/type intersections and contextual counts match saved blocks without writes`);
      report.checks.push(`${width}px: each explicit filter action selects and focuses the first result below sticky controls; empty intersections focus Reset`);
      await keyboard(review('pending')); await keyboard(type('paragraph'));
      assert(await merge('first').isDisabled());
      assert((await page.locator('#merge-help-first').innerText()).includes('hidden by this filter'));
      assert.equal(await merge('first').getAttribute('data-next-block-id'), 'second');
      assert((await page.locator('#merge-help-third').innerText()).includes('List blocks cannot be merged here'));
      await page.reload(); await page.waitForLoadState('load');
      assert.deepEqual(await active(), ['pending', 'paragraph']);
      await checkCounts();
      report.checks.push(`${width}px: filters persist on reload; actual merge candidates remain saved neighbors, including hidden lists`);
      await card('third').focus();
      await keyboard(review('all')); await firstResult();
      assert.equal(await page.evaluate(() => document.activeElement.id), 'block-first');
      await card('third').focus();
      await keyboard(review('pending')); await firstResult();
      assert.equal(await page.evaluate(() => document.activeElement.id), 'block-first');
      await card('third').focus();
      await page.reload(); await page.waitForLoadState('load');
      await page.waitForFunction(() => document.activeElement.id === 'block-third');
      report.checks.push(`${width}px: an already-matching later selection returns to the first result on filter change, while reload keeps the later selection`);

      await keyboard(review('excluded')); await keyboard(type('image'));
      assert.equal(await shown().count(), 0);
      assert(await page.locator('#block-filter-empty').isVisible());
      assert(await page.locator('#previous-block').isDisabled()); assert(await page.locator('#next-block').isDisabled());
      await keyboard(page.locator('#show-all-blocks'));
      assert.deepEqual(await active(), ['all', 'all']);
      report.checks.push(`${width}px: zero results remain explicit and Reset filters clears both rows`);

      const editor = card('first').locator('[name="content"]');
      await editor.fill('Unsaved retained text.');
      assert(await merge('first').isDisabled());
      await page.waitForFunction(() => document.querySelector('.source-image-stage').getAttribute('aria-busy') === 'false');
      await type('list').focus();
      const beforeCancel = await page.evaluate(() => ({scrollX, scrollY, selected: selectedSourceCard?.id}));
      await page.keyboard.press('Enter');
      assert(await page.locator('#block-filter-dialog').isVisible());
      assert.equal(await page.evaluate(() => document.activeElement.id), 'block-filter-cancel');
      await page.keyboard.press('Escape');
      assert.deepEqual(await active(), ['all', 'all']);
      assert.equal(await editor.inputValue(), 'Unsaved retained text.');
      assert.deepEqual(await page.evaluate(() => ({scrollX, scrollY, selected: selectedSourceCard?.id})), beforeCancel);
      await keyboard(type('list'));
      await keyboard(page.locator('#block-filter-confirm'));
      assert.deepEqual(await active(), ['all', 'list']);
      assert.equal(await editor.inputValue(), 'Unsaved retained text.');
      assert(await page.locator('#block-filter-notice').isVisible());
      await firstResult();
      await keyboard(type('all'));
      await editor.fill('first retained text.');
      assert(!await merge('first').isDisabled());
      const selector = card('first').locator('[name="type"]');
      await selector.selectOption('list');
      assert(await merge('first').isDisabled());
      assert((await page.locator('#merge-help-first').innerText()).includes('unsaved edits'));
      await selector.selectOption('paragraph');
      await card('second').locator('[name="review_status"]').selectOption('excluded');
      assert(await merge('first').isDisabled());
      await card('second').locator('[name="review_status"]').selectOption('approved');
      assert(!await merge('first').isDisabled());
      report.checks.push(`${width}px: dirty type/review/text changes disable merging; filter confirmation preserves text and Escape cancels`);
      report.checks.push(`${width}px: dirty cancel preserves both filters, selected block, scroll and entered text; confirmation focuses the first permitted result`);

      await type('paragraph').click(); await review('pending').click();
      const beforeSave = read();
      await card('third').locator('[name="type"]').selectOption('list');
      await submit(card('third').getByRole('button', {name: /^Save block /}));
      assert.deepEqual(await active(), ['pending', 'paragraph']);
      assert(!await card('third').isVisible());
      assert(await shown().count() > 0);
      await page.waitForFunction(() => document.activeElement.id === 'block-after-list');
      assert.equal(read().blocks.find(b => b.id === 'third').children[0].content, 'third retained text.');
      await submit(page.locator('#reading-order-undo'));
      assert.deepEqual(await active(), ['pending', 'paragraph']);
      assert.deepEqual(read().blocks, beforeSave.blocks);
      report.checks.push(`${width}px: classification save advances within the intersection; Undo restores IDs/text/approval and keeps both filters`);

      await type('list').click();
      assert.equal(await shown().count(), 0);
      await page.goto(origin + '/structure#block-list');
      await page.waitForFunction(() => document.activeElement.id === 'block-list');
      assert.deepEqual(await active(), ['all', 'list']);
      assert((await page.locator('#block-filter-notice').innerText()).includes('linked block'));
      report.checks.push(`${width}px: an explicit link reveals its target with a visible explanation of filter changes`);

      await type('image').click(); await review('pending').click();
      assert.equal(await shown().count(), 1);
      const beforeApprove = read();
      await card('image').locator('[name="decorative"]').check();
      await submit(card('image').locator('[data-save-and-approve]'));
      assert.deepEqual(await active(), ['pending', 'image']);
      assert.equal(await shown().count(), 0);
      assert.equal(await page.evaluate(() => document.activeElement.id), 'show-all-blocks');
      assert((await page.locator('#block-filter-empty-message').innerText()).includes('these filters'));
      await submit(page.locator('#reading-order-undo'));
      assert.deepEqual(await active(), ['pending', 'image']);
      assert.deepEqual(read().blocks, beforeApprove.blocks);
      await page.reload(); assert.deepEqual(await active(), ['pending', 'image']);
      report.checks.push(`${width}px: last matching Save and approve leaves an empty view with focused Reset; Undo/reopen preserve filters`);

      await review('all').click(); await type('all').click();
      const beforeStale = read();
      const newer = await api('/api/blocks/third', {review_status: 'approved'});
      assert.equal(newer.status, 200);
      await editor.fill('Stale attempted text.');
      const response = page.waitForResponse(r => r.url().endsWith('/api/blocks/first'));
      await card('first').getByRole('button', {name: /^Save block /}).click();
      assert.equal((await response).status(), 400);
      assert.equal(await editor.inputValue(), 'Stale attempted text.');
      assert.equal(read().blocks.find(b => b.id === 'first').content, 'first retained text.');
      assert.equal(read().blocks.find(b => b.id === 'third').review.status, 'approved');
      await page.reload(); await page.waitForLoadState('load');
      await merge('first').focus();
      const changedAgain = await api('/api/blocks/third', {review_status: 'needs_review'});
      assert.equal(changedAgain.status, 200);
      const rejected = page.waitForResponse(r => r.url().endsWith('/api/blocks/first/merge'));
      await page.keyboard.press('Enter'); assert.equal((await rejected).status(), 400);
      assert(read().blocks.some(b => b.id === 'second'));
      await page.waitForFunction(() => document.querySelector('#block-first [data-action="merge"]').disabled);
      assert((await page.locator('#merge-help-first').innerText()).includes('Reload Structure'));
      report.checks.push(`${width}px: stale saves keep entered text and newer decisions; stale merge is rejected and disabled until reload`);
      await page.reload(); await page.waitForLoadState('load');
      const beforeMerge = read();
      await submit(merge('first'));
      assert.equal(read().blocks[0].content, 'first retained text.\n\nsecond retained text.');
      assert.equal(read().blocks[0].review.status, 'needs_review');
      assert.equal(read().blocks[0].id, 'first');
      await submit(page.locator('#reading-order-undo'));
      assert.deepEqual(read().blocks, beforeMerge.blocks);
      await checkCounts();
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await review('pending').click(); await type('paragraph').click();
      await page.locator('.reading-order-header').scrollIntoViewIfNeeded();
      await page.screenshot({path: path.join(evidence, `filters-${width}.png`)});
      report.checks.push(`${width}px: supported keyboard merge requires review, Undo restores both originals, and compact rows fit without overflow`);

      let releaseSource, sourceRequested;
      const gate = new Promise(resolve => { releaseSource = resolve; });
      const started = new Promise(resolve => { sourceRequested = resolve; });
      await page.route('**/source-page/1.png?*', async route => {
        sourceRequested(); await gate; await route.continue();
      });
      await page.goto(origin + '/structure');
      await started;
      await keyboard(type('heading'));
      await firstResult(false);
      assert.equal(await page.evaluate(() => document.activeElement.id), 'block-heading-first');
      releaseSource();
      await firstResult();
      assert.equal(await page.evaluate(() => document.activeElement.id), 'block-heading-first');
      await page.unroute('**/source-page/1.png?*');
      report.checks.push(`${width}px: late source rendering resettles the first matching block below sticky controls without changing its selection`);
      await keyboard(type('paragraph'));
      await firstResult();
      await keyboard(review('pending'));
      await firstResult();
      if (width === 390) {
        assert(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches));
        report.checks.push('390px: first-result navigation remains visible and keyboard usable with reduced motion');
      }
    }
    const selectProject = async root => {
      await page.goto(new URL(url).origin + '/');
      const target = page.locator('.project-list li').filter({has: page.getByText(root, {exact: true})});
      await Promise.all([page.waitForEvent('framenavigated'), target.locator('.open-project').click()]);
      await page.goto(new URL(url).origin + '/structure');
    };
    await selectProject(other);
    assert.deepEqual(await active(), ['all', 'all']);
    await review('approved').click(); await type('list').click();
    await selectProject(project);
    assert.deepEqual(await active(), ['pending', 'paragraph']);
    report.checks.push('Projects with the same source filename retain separate filter and selection preferences');
    assert.deepEqual(report.errors, []);
    report.result = 'passed';
  } catch (error) {
    report.result = 'failed'; report.failure = error.stack; process.exitCode = 1;
    await page.screenshot({path: path.join(evidence, 'failure.png')});
  } finally {
    fs.writeFileSync(path.join(evidence, 'browser-report.json'), JSON.stringify(report, null, 2));
    process.stdout.write(JSON.stringify(report, null, 2) + '\n');
    await browser.close();
  }
}
main().catch(error => { process.stderr.write(error.stack + '\n'); process.exitCode = 1; });
