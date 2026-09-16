const fs = require('fs');
const path = require('path');
const { chromium } = require('./wordpress-roundtrip/node_modules/playwright-core');

const bootstrapUrl = process.argv[2];
if (!bootstrapUrl) throw new Error('Pass the one-time bootstrap URL');

async function main() {
  const browser = await chromium.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const report = { checks: {}, controlNames: [], headingOutline: [] };
  const pressAndReload = async (key = 'Enter') => {
    await Promise.all([page.waitForEvent('framenavigated'), page.keyboard.press(key)]);
    await page.waitForLoadState('domcontentloaded');
  };

  await page.goto(bootstrapUrl, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.documentElement.dataset.appReady === 'true');
  report.checks.primaryNavigationNamed = await page.locator('nav[aria-label="Primary"]').count() === 1;
  report.checks.liveStatusAvailable = await page.locator('[role="status"][aria-live="polite"]').count() >= 1;

  const recent = page.locator('.open-project').first();
  await recent.focus();
  await Promise.all([page.waitForURL('**/document'), page.keyboard.press('Enter')]);
  report.checks.projectOpenedByKeyboard = page.url().endsWith('/document');

  await page.goto(new URL('/structure', bootstrapUrl).href, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.documentElement.dataset.appReady === 'true');
  report.headingOutline = await page.locator('h1, h2, h3').allTextContents();
  report.checks.blockHeadingsAvailable = await page.locator('.block-card h3').count() === await page.locator('.block-card').count();
  report.checks.sourceImageNamed = /^Rendered source PDF page/.test(await page.locator('#source-image').getAttribute('alt'));

  const controls = page.locator('button, input, select, textarea, a[href]');
  const count = await controls.count();
  for (let index = 0; index < count; index += 1) {
    const control = controls.nth(index);
    if (!(await control.isVisible())) continue;
    report.controlNames.push(await control.evaluate((node) => {
      const label = node.labels?.[0]?.innerText?.trim();
      return node.getAttribute('aria-label') || label || node.innerText?.trim() || node.getAttribute('title') || '';
    }));
  }
  report.checks.visibleControlsNamed = report.controlNames.every(Boolean);

  const headingForm = page.locator('.block-form').filter({ has: page.locator('select[name="type"] option:checked', { hasText: 'Heading' }) }).first();
  const typeSelect = headingForm.locator('select[name="type"]');
  const levelSelect = headingForm.locator('select[name="level"]');
  await typeSelect.focus();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('ArrowUp');
  await levelSelect.focus();
  const originalLevel = await levelSelect.inputValue();
  await page.keyboard.press(originalLevel === '6' ? 'ArrowUp' : 'ArrowDown');
  await page.keyboard.press(originalLevel === '6' ? 'ArrowDown' : 'ArrowUp');
  report.checks.typeAndHeadingLevelKeyboardOperable = await levelSelect.inputValue() === originalLevel;

  const firstCard = page.locator('.block-card').first();
  const firstId = await firstCard.getAttribute('id');
  const moveDown = firstCard.getByRole('button', { name: /Move block 1 down/ });
  await moveDown.focus();
  await pressAndReload();
  await page.getByRole('button', { name: 'Undo last action' }).focus();
  await pressAndReload();
  report.checks.reorderAndUndoKeyboardOperable = await page.locator('.block-card').first().getAttribute('id') === firstId;

  const save = page.locator('.block-form').filter({ has: page.locator('select[name="type"] option:checked', { hasText: 'Heading' }) }).first().getByRole('button', { name: /Save block/ });
  await save.focus();
  await pressAndReload();
  report.checks.saveKeyboardOperable = page.url().endsWith('/structure');

  await page.goto(new URL('/preview', bootstrapUrl).href, { waitUntil: 'domcontentloaded' });
  report.checks.previewFrameNamed = await page.locator('iframe[title="Semantic HTML preview"]').count() === 1;
  const wordpressPreview = page.getByRole('button', { name: 'WordPress Preview' });
  await wordpressPreview.focus();
  await page.keyboard.press('Enter');
  report.checks.wordpressPreviewKeyboardOperable = await page.locator('iframe[title="WordPress Gutenberg preview"]').count() === 1;
  const narrow = page.getByRole('button', { name: 'Narrow' });
  await narrow.focus();
  await page.keyboard.press('Enter');
  report.checks.previewKeyboardOperable = await page.locator('#preview-shell').evaluate((node) => node.classList.contains('narrow'));

  await page.goto(new URL('/export', bootstrapUrl).href, { waitUntil: 'domcontentloaded' });
  const exportButton = page.getByRole('button', { name: 'Export reviewed document' });
  await exportButton.focus();
  await page.keyboard.press('Enter');
  await page.locator('#export-result').getByText('Export complete.').waitFor();
  report.checks.exportKeyboardOperable = true;

  report.passed = Object.values(report.checks).every(Boolean);
  const output = path.resolve(__dirname, '../build/phase2-screenshots/accessibility-report.json');
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
  process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  await browser.close();
  if (!report.passed) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
