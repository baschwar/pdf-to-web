// Local provider-settings regression check; no provider transmission.
const fs=require('fs'), path=require('path'), assert=require('assert');
const {chromium}=require('./wordpress-roundtrip/node_modules/playwright-core');
const url=process.argv[2],root=path.resolve(process.argv[3]);
const report={checks:{},errors:[]};
(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1280,height:1000}});
 const read=()=>JSON.parse(fs.readFileSync(path.join(root,'review/current.json')));
 page.on('pageerror',e=>report.errors.push(e.message));
 const save=async()=>{
   const before=await page.evaluate(()=>scrollY);
   let navigations=0;const navigation=()=>navigations++;page.on('framenavigated',navigation);
   const button=page.getByRole('button',{name:'Save provider settings',exact:true});await button.focus();await page.keyboard.press('Enter');
   await page.getByText('Provider settings saved for this project.',{exact:true}).waitFor();
   await page.waitForTimeout(150);
   assert.equal(navigations,0);assert(Math.abs(await page.evaluate(()=>scrollY)-before)<5);
   assert.equal(await page.evaluate(()=>document.activeElement.textContent),'Save provider settings');
   page.off('framenavigated',navigation);
 };
 try{
   await page.goto(url);await page.getByRole('link',{name:'Structure',exact:true}).click();
   await page.getByText('Provider setup',{exact:true}).click();
   await page.locator('#draft-provider').selectOption('openai');
   assert(await page.locator('#draft-model-label').isHidden());
   await save();assert.equal(read().image_description_drafts.settings.provider,'openai');
   report.checks.keyboardSaveWithoutNavigationScrollOrFocusChange=true;
   await page.reload();await page.getByText('Provider setup',{exact:true}).click();
   assert.equal(await page.locator('#draft-provider').inputValue(),'openai');
   report.checks.selectionPersistsAcrossReload=true;
   await page.locator('#draft-provider').selectOption('manual');
   assert(await page.locator('#draft-model-label').isHidden());
   assert.equal(await page.locator('#draft-provider-setup > summary').evaluate(el=>getComputedStyle(el).fontWeight),'700');
   assert.equal(await page.locator('#draft-manual-import > summary').evaluate(el=>getComputedStyle(el).fontWeight),'700');
   report.checks.manualChoiceHidesModelAndAccordionHeadingsAreBold=true;
   await save();
   const photo=page.locator('.image-draft-panel[data-block-id="photo"]');
   await photo.getByRole('button',{name:'Generate drafts',exact:true}).click();
   await page.getByRole('link',{name:'Download drafting request ZIP'}).waitFor();
   const download=await page.request.get(new URL(await page.getByRole('link',{name:'Download drafting request ZIP'}).getAttribute('href'),url).href);
   assert.equal(download.status(),200);
   const zip=await download.body();assert(zip.includes(Buffer.from('review-sheet.csv')));
   fs.writeFileSync('build/image-drafts/manual-review-sample.zip',zip);
   report.checks.manualDownloadIncludesCSVCompanion=true;
   const state=read().image_description_drafts;
   assert.equal(state.requests[state.active.photo].provider,'manual');
   report.checks.manualSelectionExportsInsteadOfCallingProvider=true;
   await page.getByRole('link',{name:'Projects',exact:true}).click();
   await page.locator('.open-project').first().click();await page.waitForLoadState('domcontentloaded');
   await page.getByRole('link',{name:'Structure',exact:true}).click();await page.getByText('Provider setup',{exact:true}).click();
   assert.equal(await page.locator('#draft-provider').inputValue(),'manual');
   report.checks.projectReopenKeepsProvider=true;
   // Simulate slow source-page load plus a pending block advance. Provider input wins.
   await page.evaluate(()=>sessionStorage.setItem('pdf-to-web-review-next-block','block-chart'));
   await page.route('**/source-page/*.png?*',async route=>{await new Promise(resolve=>setTimeout(resolve,600));await route.continue();});
   await page.reload({waitUntil:'domcontentloaded'});
   await page.getByText('Provider setup',{exact:true}).click();await page.locator('#draft-provider').focus();
   await page.waitForLoadState('load');await page.waitForTimeout(150);
   assert.equal(await page.evaluate(()=>document.activeElement.id),'draft-provider');
   assert(await page.locator('#draft-provider').isVisible());
   report.checks.providerInteractionPreventsDelayedBlockJump=true;
   await page.getByText('Import manual responses',{exact:true}).click();
   await page.screenshot({path:'build/image-drafts/provider-settings.png',fullPage:false});
   assert.equal(report.errors.length,0);report.passed=true;
 }catch(error){report.passed=false;report.failure=error.stack;throw error;}
 finally{fs.writeFileSync('build/image-drafts/provider-browser-report.json',JSON.stringify(report,null,2));await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
