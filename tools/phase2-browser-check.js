const fs = require('fs');
const path = require('path');
const { chromium } = require('./wordpress-roundtrip/node_modules/playwright-core');

const bootstrapUrl = process.argv[2];
const label = process.argv[3] || 'phase2';
if (!bootstrapUrl) throw new Error('Pass the one-time bootstrap URL');
const outputDir = path.resolve(__dirname, '../build/phase2-screenshots');

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const browser = await chromium.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const consoleErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  const clickAndReload = async (locator) => {
    await Promise.all([page.waitForEvent('framenavigated'), locator.click()]);
    await page.waitForLoadState('domcontentloaded');
  };

  await page.goto(bootstrapUrl, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.documentElement.dataset.appReady === 'true');
  await page.screenshot({ path: path.join(outputDir, `${label}-projects.png`), fullPage: true });

  await page.goto(new URL('/document', bootstrapUrl).href, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.documentElement.dataset.appReady === 'true');
  const documentHeading = await page.getByRole('heading', { level: 1 }).textContent();
  const documentText = await page.locator('main').innerText();
  const conversionBlockedVisible = documentText.includes('Conversion Blocked');
  await page.screenshot({ path: path.join(outputDir, `${label}-document.png`), fullPage: true });

  await page.goto(new URL('/structure', bootstrapUrl).href, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.documentElement.dataset.appReady === 'true');
  const blockCount = await page.locator('.block-card').count();
  await page.waitForFunction(() => document.querySelector('#source-image')?.naturalWidth > 0, null, { timeout: 45000 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: path.join(outputDir, `${label}-structure.png`), fullPage: false });
  const tableCard = page.locator('.block-card').filter({ hasText: 'Table' }).first();
  if (await tableCard.count()) {
    await tableCard.scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(outputDir, `${label}-table.png`), fullPage: false });
    await page.evaluate(() => window.scrollTo(0, 0));
  }
  await page.locator('.block-card').first().click();
  const sourceUrl = await page.locator('#source-image').getAttribute('src');

  let firstBlockRestoredAfterReorderUndo = true;
  if (!conversionBlockedVisible) {
    const headingForm = page.locator('.block-form').filter({ has: page.locator('select[name="type"] option:checked', { hasText: 'Heading' }) }).first();
    if (await headingForm.count()) {
      const level = headingForm.locator('select[name="level"]');
      const originalLevel = await level.inputValue();
      await level.selectOption(originalLevel === '2' ? '3' : '2');
      await clickAndReload(headingForm.getByRole('button', { name: 'Save block' }));
      await clickAndReload(page.getByRole('button', { name: 'Undo last action' }));
    }

    const firstBlockId = await page.locator('.block-card').first().getAttribute('id');
    await clickAndReload(page.locator('.block-card').first().getByRole('button', { name: /Move block 1 down/ }));
    await clickAndReload(page.getByRole('button', { name: 'Undo last action' }));
    const restoredFirstBlockId = await page.locator('.block-card').first().getAttribute('id');
    firstBlockRestoredAfterReorderUndo = firstBlockId === restoredFirstBlockId;
  }

  await page.goto(new URL('/preview', bootstrapUrl).href, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.documentElement.dataset.appReady === 'true');
  await page.screenshot({ path: path.join(outputDir, `${label}-preview-desktop.png`), fullPage: true });
  await page.getByRole('button', { name: 'WordPress Preview' }).click();
  await page.locator('iframe[title="WordPress Gutenberg preview"]').waitFor();
  await page.waitForTimeout(300);
  const wordpressFrame = page.frameLocator('iframe[title="WordPress Gutenberg preview"]');
  const wordpressPreviewText = await wordpressFrame.locator('main').innerText();
  await page.screenshot({ path: path.join(outputDir, `${label}-preview-wordpress.png`), fullPage: true });
  await page.getByRole('button', { name: 'Narrow' }).click();
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(outputDir, `${label}-preview-wordpress-mobile.png`), fullPage: true });

  await page.goto(new URL('/export', bootstrapUrl).href, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => document.documentElement.dataset.appReady === 'true');
  let blockedWordPressDisabled = false;
  if (conversionBlockedVisible) {
    await page.locator('select[name="target"]').selectOption('gutenberg');
    blockedWordPressDisabled = await page.getByRole('button', { name: 'Export reviewed document' }).isDisabled();
    await page.locator('select[name="target"]').selectOption('html');
  }
  const exportDisabled = await page.getByRole('button', { name: 'Export reviewed document' }).isDisabled();
  if (!exportDisabled) {
    await page.getByRole('button', { name: 'Export reviewed document' }).click();
    await page.locator('#export-result').getByText('Export complete.').waitFor();
  }
  await page.screenshot({ path: path.join(outputDir, `${label}-export.png`), fullPage: true });

  const report = {
    label,
    documentHeading,
    blockCount,
    sourceUrl,
    firstBlockRestoredAfterReorderUndo,
    conversionBlockedVisible,
    needsReviewVisible: documentText.includes('Needs Review'),
    exportDisabled,
    blockedWordPressDisabled,
    wordpressPreviewHasContent: wordpressPreviewText.trim().length > 0,
    consoleErrors
  };
  fs.writeFileSync(path.join(outputDir, `${label}-report.json`), JSON.stringify(report, null, 2) + '\n');
  process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  await browser.close();
  if (consoleErrors.length || blockCount === 0 || !report.firstBlockRestoredAfterReorderUndo || !report.wordpressPreviewHasContent) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
