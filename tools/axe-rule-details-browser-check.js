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
  const context = await browser.newContext({viewport:{width:1440,height:1000}});
  const page = await context.newPage(), report = {browser:browser.version(), checks:{}, errors:[]};
  page.on('pageerror', error => report.errors.push(error.message));
  const reviewFile = path.join(project,'review/current.json');
  let before;
  const scan = () => page.waitForFunction(() => document.getElementById('axe-status').textContent.startsWith('Check complete'));
  const compareRules = async () => {
    const results = await page.locator('#axe-preview').evaluate(async frame => {
      const raw = await frame.contentWindow.axe.run(frame.contentDocument, {
        runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}, iframes:false
      });
      return Object.fromEntries(['violations','incomplete','passes','inapplicable'].map(key=>[key,raw[key].map(f=>({id:f.id,help:f.help,description:f.description,nodes:f.nodes.length,helpUrl:f.helpUrl,tags:f.tags}))]));
    });
    const button = page.getByRole('button',{name:'View tested rules',exact:true});
    await button.click();
    const dialog = page.getByRole('dialog',{name:'Tested HTML rules',exact:true});
    assert(await dialog.isVisible());
    assert.equal(await page.evaluate(()=>document.activeElement.textContent),'Close');
    assert.equal(await dialog.locator('select').inputValue(),results.passes.length?'passes':'all');
    for(const [key, findings] of Object.entries(results)) {
      await dialog.locator('select').selectOption(key);
      const rows = dialog.locator('.axe-rules-list > li');
      assert.equal(await rows.count(),findings.length,key);
      assert.equal(Number(await page.locator('#axe-results > table tbody tr').nth(Object.keys(results).indexOf(key)).locator('td').first().innerText()),findings.length);
      for(const finding of findings) {
        const row = rows.filter({has:page.locator('code').filter({hasText:new RegExp('^'+finding.id+'$')})});
        assert.equal(await row.count(),1,finding.id);
        assert.equal(await row.locator('h3').innerText(),finding.help);
        const text = await row.innerText();
        assert(text.includes(finding.description),finding.id);
        assert(text.includes(finding.nodes+' '+(key==='inapplicable'?'matching':'affected')+' elements'),finding.id);
        assert.equal(await row.locator('a').getAttribute('href'),finding.helpUrl);
        for(const tag of finding.tags.filter(t=>/^wcag\d{3,4}$/.test(t))) {
          const digits=tag.slice(4); assert(text.includes(`${digits[0]}.${digits[1]}.${digits.slice(2)}`));
        }
      }
      if(!findings.length)assert.equal(await dialog.locator('#axe-rules-count').innerText(),'No rule results in this category.');
    }
    await dialog.locator('select').selectOption('all');
    assert.equal(await dialog.locator('.axe-rules-list > li').count(),Object.values(results).flat().length);
    await page.keyboard.press('Shift+Tab'); // From select back to Close.
    await page.keyboard.press('Shift+Tab'); // Wrap to the last link, not the underlying page.
    assert(await page.evaluate(()=>document.activeElement.closest('dialog')?.open===true));
    await page.keyboard.press('Escape');
    assert(!(await dialog.isVisible()));
    assert.equal(await page.evaluate(()=>document.activeElement.textContent),'View tested rules');
    await button.click(); await dialog.getByRole('button',{name:'Close',exact:true}).click();
    assert.equal(await page.evaluate(()=>document.activeElement.textContent),'View tested rules');
    return Object.fromEntries(Object.entries(results).map(([key,findings])=>[key,findings.length]));
  };
  try {
    await page.goto(url); const origin = new URL(url).origin;
    await page.goto(origin+'/accessibility'); await scan();
    before=fs.readFileSync(reviewFile,'utf8');
    report.checks.actualScanRulesAndCounts = await compareRules();
    await page.getByRole('button',{name:'View tested rules',exact:true}).click();
    await page.locator('#axe-rules-filter').selectOption('passes');
    await page.screenshot({path:path.join(evidence,'rules-desktop.png')});
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    assert(await page.locator('.axe-rules-content').evaluate(el=>el.scrollHeight>el.clientHeight&&el.scrollWidth<=el.clientWidth));
    assert(await page.getByRole('dialog').getByRole('button',{name:'Close',exact:true}).evaluate(el=>{
      const rect=el.getBoundingClientRect(); return rect.top>=0&&rect.bottom<=innerHeight;
    }));
    await page.screenshot({path:path.join(evidence,'rules-narrow.png')});
    await page.keyboard.press('Escape');
    report.checks.keyboardFocusEscapeCloseAndNarrowScrolling = true;
    await page.reload(); await scan();
    assert(!(await page.getByRole('dialog',{name:'Tested HTML rules',exact:true}).isVisible()));
    assert.equal(fs.readFileSync(reviewFile,'utf8'),before);
    report.checks.reopenAndReviewStateUnchanged = true;
    // Only the test's preview response changes; saved document/source remain intact.
    await page.route('**/api/accessibility/preview',async route=>{
      const response=await route.fetch();
      await route.fulfill({response,body:(await response.text()).replace('</main>','<button></button><p style="color:#777;background-image:linear-gradient(white,black)">Synthetic contrast review</p></main>')});
    });
    await page.reload(); await scan();
    report.checks.detectedAndIncompleteRuleDetails = await compareRules();
    assert(report.checks.detectedAndIncompleteRuleDetails.violations>0);
    assert(report.checks.detectedAndIncompleteRuleDetails.incomplete>0);
    assert.equal(fs.readFileSync(reviewFile,'utf8'),before);
    await page.unroute('**/api/accessibility/preview');
    await page.route('**/static/axe.min.js',route=>route.abort());
    await page.reload();
    await page.waitForFunction(()=>document.getElementById('axe-status').textContent.startsWith('Automated check unavailable'));
    assert.equal(await page.getByRole('button',{name:'View tested rules',exact:true}).count(),0);
    assert.equal(await page.locator('#axe-rules-dialog').count(),0);
    assert.equal(fs.readFileSync(reviewFile,'utf8'),before);
    report.checks.failedScanNeverOffersRuleResults = true;
    assert.deepEqual(report.errors,[]); report.result='passed';
  }catch(error){report.result='failed';report.failure=error.stack;await page.screenshot({path:path.join(evidence,'failure.png')});process.exitCode=1;}
  finally{fs.writeFileSync(path.join(evidence,'browser-report.json'),JSON.stringify(report,null,2));process.stdout.write(JSON.stringify(report,null,2)+'\n');await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
