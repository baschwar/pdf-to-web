/* Disposable synthetic fixture; never calls a provider or WordPress. */
const fs=require('fs'), assert=require('assert');
const {chromium}=require('./wordpress-roundtrip/node_modules/playwright-core');
(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const stateFile='build/image-drafts/complex-review-session.json';
 const page=await browser.newPage({viewport:{width:1440,height:1000},...(fs.existsSync(stateFile)?{storageState:stateFile}:{})});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const root=process.argv[3],read=()=>JSON.parse(fs.readFileSync(root+'/review/current.json'));
 const image=()=>page.locator('.image-block-form[data-block-id="photo"]');
 const visual=()=>page.locator('.complex-visual-form[data-block-id="photo"]');
 const post=async(action,data)=>page.evaluate(async({action,data})=>{
  const csrf=document.cookie.split('; ').find(x=>x.startsWith('pdf_to_web_csrf=')).split('=')[1];
  const r=await fetch('/api/image-drafts/'+action,{method:'POST',headers:{'content-type':'application/json','x-csrf-token':csrf},body:JSON.stringify(data)});if(!r.ok)throw new Error(await r.text());return r.json();
 },{action,data});
 try{
  await page.goto(process.argv[2]);await page.context().storageState({path:stateFile});await page.getByRole('link',{name:'Structure',exact:true}).click();
  const id=read().output_pages.project_id;await post('export',{document_id:id,block_ids:['photo']});
  const store=read().image_description_drafts,e=store.requests[store.active.photo];
  const item={...Object.fromEntries(['document_id','block_id','asset_hash','context_hash','request_id'].map(k=>[k,e[k]])),alt:'Synthetic image alternative',caption:'Synthetic caption',long_description:'Synthetic longer equivalent',warnings:[],decorative:false};
  await post('import',{document_id:id,response:{schema_version:'pdf-to-web-image-exchange-v1',responses:[item]},commit:true});await page.reload();
  await page.waitForFunction(()=>[...document.querySelectorAll('.complex-visual img')].every(i=>i.complete&&i.naturalWidth>0));
  assert.equal(await visual().locator('[name="short_alt"]').inputValue(),'Synthetic image alternative');
  assert.equal(await visual().locator('[name="long_description"]').inputValue(),'Synthetic longer equivalent');
  const url=page.url();await visual().locator('[name="short_alt"]').fill('Reviewed alternative');await visual().locator('[name="long_description"]').fill('Reviewed longer equivalent');
  const save=visual().getByRole('button',{name:'Save complex visual review',exact:true});await save.focus();await page.keyboard.press('Enter');
  await page.waitForFunction(()=>document.querySelector('.complex-visual-form[data-block-id="photo"] .visual-save-message').textContent.startsWith('Review saved'));
  assert.equal(page.url(),url);assert(await save.evaluate(el=>el===document.activeElement));
  assert.equal(await image().locator('[name="alt"]').inputValue(),'Reviewed alternative');assert.equal(await image().locator('[name="long_description"]').inputValue(),'Reviewed longer equivalent');
  assert.equal(read().blocks.find(b=>b.id==='photo').alt,'Reviewed alternative');
  const preview=await page.request.get(new URL('/api/preview/html',page.url()).href);assert((await preview.text()).includes('Reviewed longer equivalent'));
  await page.reload();assert.equal(await visual().locator('[name="short_alt"]').inputValue(),'Reviewed alternative');
  await page.getByRole('button',{name:'Undo last action',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.complex-visual-form[data-block-id="photo"] [name="short_alt"]').value==='Synthetic image alternative');
  const controls=page.locator('#block-photo .block-review-actions');
  assert.deepEqual(await controls.locator('button').allTextContents(),['Needs review','Exclude','Approve']);
  const position=await controls.evaluate(el=>({top:el.getBoundingClientRect().top,header:el.parentElement.querySelector('header').getBoundingClientRect().top,source:el.parentElement.querySelector('.source-provenance').getBoundingClientRect().top,colors:[...el.querySelectorAll('button')].map(b=>getComputedStyle(b).backgroundColor)}));
  assert(position.top<position.header&&position.top<position.source);assert.deepEqual(position.colors,['rgb(250, 204, 21)','rgb(185, 28, 28)','rgb(22, 101, 52)']);
  await controls.getByRole('button',{name:'Approve block 3',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#block-photo').classList.contains('status-approved'));
  await controls.getByRole('button',{name:'Mark block 3 as needs review',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#block-photo').classList.contains('status-needs_review'));
  await controls.getByRole('button',{name:'Exclude block 3',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#block-photo').classList.contains('status-excluded'));
  await controls.getByRole('button',{name:'Include block 3',exact:true}).click();await page.waitForFunction(()=>!document.querySelector('#block-photo').classList.contains('status-excluded'));
  await page.setViewportSize({width:390,height:844});await controls.scrollIntoViewIfNeeded();
  await page.screenshot({path:'build/image-drafts/complex-review-narrow.png'});
  const overflow=await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>({tag:e.tagName,cls:e.className,right:e.getBoundingClientRect().right})).slice(0,20));
  if(overflow.length)console.log(JSON.stringify(overflow));
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  await page.screenshot({path:'build/image-drafts/complex-review-narrow.png'});
  await page.setViewportSize({width:1440,height:1000});await visual().scrollIntoViewIfNeeded();await page.screenshot({path:'build/image-drafts/complex-review-desktop.png'});
  assert.deepEqual(errors,[]);fs.writeFileSync('build/image-drafts/complex-review-browser-report.json',JSON.stringify({passed:true,checks:['both previews decode','imported short and long text','keyboard save feedback/focus without reload','saved image field synchronization','semantic preview','reload persistence','Undo save','top order and colors','approve/flag/exclude/include','narrow layout'],errors},null,2));
  console.log('Passed 10 Chrome checks; no page errors.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
