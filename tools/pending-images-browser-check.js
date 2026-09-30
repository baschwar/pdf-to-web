const assert = require('assert');
const {chromium} = require('./wordpress-roundtrip/node_modules/playwright-core');
(async () => {
 const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const page = await browser.newPage(); const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 try {
  await page.goto(process.argv[2]); await page.getByRole('link',{name:'Structure',exact:true}).click();
  assert(await page.getByRole('button',{name:'Cancel selected requests',exact:true}).isHidden());
  assert(await page.locator('[data-draft-action="cancel"]').first().isHidden());
  for(const input of await page.locator('.draft-selection').all()) await input.uncheck();
  assert((await page.locator('#draft-selection-summary').innerText()).startsWith('0 images selected'));
  assert(await page.getByRole('button',{name:'Export selected images ZIP',exact:true}).first().isDisabled());
  assert(await page.getByRole('button',{name:'Export pending images ZIP',exact:true}).isEnabled());
  await page.getByRole('button',{name:'Export pending images ZIP',exact:true}).click();
  const link=page.getByRole('link',{name:'Download drafting request ZIP'}); await link.waitFor();
  assert.equal(await link.evaluate(el=>document.activeElement===el),true);
  assert((await page.locator('#draft-message').innerText()).includes('ZIP ready'));
  const response=await page.request.get(new URL(await link.getAttribute('href'),process.argv[2]).href); assert.equal(response.status(),200);
  assert((await response.body()).includes(Buffer.from('review-sheet.csv')));
  await page.locator('.draft-selection').first().check();
  await page.waitForTimeout(2800);
  assert(await page.getByRole('button',{name:'Cancel selected requests',exact:true}).isVisible());
  assert.deepEqual(errors,[]); console.log('Passed: empty selection, pending export, download focus and ZIP, active-request cancellation visibility; no page errors.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
