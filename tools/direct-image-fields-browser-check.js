/* Disposable local fixture only; no provider or external calls. */
const fs = require('fs');
const assert = require('assert');
const {chromium} = require('./wordpress-roundtrip/node_modules/playwright-core');
(async () => {
 const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
 const page = await browser.newPage(); const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 const root=process.argv[3]; const read=()=>JSON.parse(fs.readFileSync(root+'/review/current.json'));
 const post=async(action,data)=>page.evaluate(async({action,data})=>{
  const csrf=document.cookie.split('; ').find(x=>x.startsWith('pdf_to_web_csrf=')).split('=')[1];
  const r=await fetch('/api/image-drafts/'+action,{method:'POST',headers:{'content-type':'application/json','x-csrf-token':csrf},body:JSON.stringify(data)});
  if(!r.ok) throw new Error(await r.text());return r.json();
 },{action,data});
 const form=()=>page.locator('.image-block-form[data-block-id="photo"]');
 try {
  await page.goto(process.argv[2]); await page.getByRole('link',{name:'Structure',exact:true}).click();
  const documentId=read().output_pages.project_id;
  await post('export',{document_id:documentId,block_ids:['photo','approved']});
  const doc=read(); const store=doc.image_description_drafts;
  const payload={schema_version:'pdf-to-web-image-exchange-v1',responses:['photo','approved'].map(id=>{
   const e=store.requests[store.active[id]];
   return Object.fromEntries(['document_id','block_id','asset_hash','context_hash','request_id'].map(k=>[k,e[k]]).concat([['alt','Synthetic alt'],['caption','Synthetic caption'],['long_description','Synthetic long equivalent'],['warnings',[]],['decorative',false]]));
  })};
  await page.getByText('Import manual responses',{exact:true}).click();
  await page.locator('#draft-response-file').setInputFiles({name:'response.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(payload))});
  await page.getByRole('button',{name:'Validate responses',exact:true}).click();
  await page.locator('#draft-import-confirm').waitFor({state:'visible'});
  await page.waitForFunction(()=>!document.getElementById('draft-import-confirm').disabled);
  await page.getByRole('button',{name:'Import drafts into image fields',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('.image-block-form[data-block-id="photo"] textarea[name="alt"]')?.value==='Synthetic alt');
  assert.equal(await form().locator('[name="caption"]').inputValue(),'Synthetic caption');
  assert.equal(await form().locator('[name="long_description"]').inputValue(),'Synthetic long equivalent');
  assert.equal(await form().locator('[name="review_status"]').inputValue(),'needs_review');
  assert.equal(await page.locator('.image-block-form[data-block-id="approved"] [name="alt"]').inputValue(),'Existing approved portrait description');
  await page.reload(); assert.equal(await form().locator('[name="long_description"]').inputValue(),'Synthetic long equivalent');
  await form().locator('[name="long_description"]').fill('Edited equivalent');
  await form().getByRole('button',{name:/Save image block/}).click();
  await page.waitForTimeout(500); assert(read().review.complex_visuals.some(v=>v.accessibility.long_description==='Edited equivalent'));
  await page.getByRole('button',{name:'Undo last action',exact:true}).click(); await page.waitForTimeout(500);
  assert.equal(await form().locator('[name="long_description"]').inputValue(),'Synthetic long equivalent');
  await page.getByRole('button',{name:'Undo last action',exact:true}).click(); await page.waitForTimeout(500);
  assert.equal(await form().locator('[name="alt"]').inputValue(),'');
  assert.equal(await form().locator('[name="caption"]').inputValue(),'');
  assert.equal(await form().locator('[name="long_description"]').inputValue(),'');
  assert.deepEqual(errors,[]);
  fs.writeFileSync('build/image-drafts/direct-fields-browser-report.json',JSON.stringify({passed:true,checks:['import without Apply','alt/caption/long description visible','review required','existing text preserved','reload persistence','edit/save','Undo edit','Undo import'],errors},null,2));
  console.log('Passed 8 Chrome workflow checks; no page errors.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
