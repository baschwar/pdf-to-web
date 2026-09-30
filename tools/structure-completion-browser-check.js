/* Run only against a disposable completion fixture. */
const fs=require('fs'),assert=require('assert');
const {chromium}=require('./wordpress-roundtrip/node_modules/playwright-core');
(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 try{
  await page.goto(process.argv[2]);await page.getByRole('link',{name:'Structure',exact:true}).click();
  assert.equal(await page.locator('#structure-review-complete').count(),0);
  const approve=page.locator('#block-context').getByRole('button',{name:'Approve block 2',exact:true});
  await approve.focus();await page.keyboard.press('Enter');
  await page.waitForFunction(()=>document.activeElement?.id==='structure-review-complete');
  assert(await page.getByRole('heading',{name:'All blocks have been reviewed',exact:true}).isVisible());
  await page.screenshot({path:'build/image-drafts/structure-complete.png'});
  await page.getByRole('button',{name:'Continue to Accessibility',exact:true}).focus();await page.keyboard.press('Enter');
  await page.waitForURL('**/accessibility');assert(await page.getByRole('heading',{name:'Accessibility',exact:true}).isVisible());
  await page.getByRole('link',{name:'Structure',exact:true}).click();
  assert(await page.locator('#structure-review-complete').isVisible());
  await page.getByRole('button',{name:'Undo last action',exact:true}).click();
  await page.waitForFunction(()=>!document.getElementById('structure-review-complete'));
  const form=page.locator('.block-form[data-block-id="context"]');
  await form.locator('[name="review_status"]').selectOption('approved');await form.getByRole('button',{name:'Save block 2',exact:true}).click();
  await page.waitForFunction(()=>document.activeElement?.id==='structure-review-complete');
  await page.setViewportSize({width:390,height:844});assert(await page.locator('#structure-review-complete').isVisible());
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:'build/image-drafts/structure-complete-narrow.png'});
  assert.deepEqual(errors,[]);
  fs.writeFileSync('build/image-drafts/structure-completion-browser-report.json',JSON.stringify({passed:true,checks:['absent while review pending','final keyboard approval shows/focuses message','keyboard Accessibility navigation','persists on return','Undo removes message','save-form completion focus','narrow layout'],errors},null,2));
  console.log('Passed 7 Chrome checks; no page errors.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
