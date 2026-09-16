const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright-core');

const baseUrl = process.env.WORDPRESS_URL || 'http://localhost:8099';
const adminUser = process.env.WORDPRESS_USER || 'admin';
const adminPassword = process.env.WORDPRESS_PASSWORD || 'pdf-to-web-test';
const chromePath = process.env.CHROME_PATH ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const outputDir = path.resolve(__dirname, '../../build/wordpress-editor');
const postIds = (process.env.WORDPRESS_POST_IDS || '4,5,6,7,8')
  .split(',').map(Number).filter(Boolean);

function flatten(blocks) {
  return blocks.flatMap((block) => [block, ...flatten(block.innerBlocks || [])]);
}

async function editorState(page) {
  return page.evaluate(() => {
    const content = window.wp.data.select('core/editor').getEditedPostContent();
    const blocks = window.wp.blocks.parse(content);
    const flattenBlocks = (values) => values.flatMap(
      (block) => [block, ...flattenBlocks(block.innerBlocks || [])]
    );
    const all = flattenBlocks(blocks);
    return {
      content,
      blockNames: all.map((block) => block.name),
      invalidBlocks: all.filter((block) => block.isValid === false).map((block) => block.name),
      title: window.wp.data.select('core/editor').getEditedPostAttribute('title'),
      status: window.wp.data.select('core/editor').getEditedPostAttribute('status')
    };
  });
}

async function main() {
  fs.mkdirSync(outputDir, { recursive: true });
  const browser = await chromium.launch({ executablePath: chromePath, headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const consoleErrors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });

  await page.goto(`${baseUrl}/wp-login.php`, { waitUntil: 'domcontentloaded' });
  await page.locator('#user_login').fill(adminUser);
  await page.locator('#user_pass').fill(adminPassword);
  await Promise.all([
    page.waitForURL(/wp-admin/, { waitUntil: 'domcontentloaded' }),
    page.locator('#wp-submit').click()
  ]);

  const results = [];
  for (const postId of postIds) {
    consoleErrors.length = 0;
    await page.goto(`${baseUrl}/wp-admin/post.php?post=${postId}&action=edit`, {
      waitUntil: 'domcontentloaded'
    });
    await page.waitForFunction(() => window.wp && wp.data && wp.blocks &&
      wp.data.select('core/editor').getCurrentPostId());
    await page.waitForTimeout(1500);
    await page.keyboard.press('Escape');
    const before = await editorState(page);
    const warningsBefore = await page.locator(
      '.block-editor-warning, .components-notice.is-error, [data-type="core/missing"]'
    ).allTextContents();

    const marker = '\n<!-- wp:paragraph --><p>PDF to Web round-trip marker.</p><!-- /wp:paragraph -->';
    await page.evaluate(async ({ content, marker }) => {
      wp.data.dispatch('core/editor').editPost({ content: content + marker });
      await wp.data.dispatch('core/editor').savePost();
      wp.data.dispatch('core/editor').editPost({ content });
      await wp.data.dispatch('core/editor').savePost();
    }, { content: before.content, marker });

    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.wp && wp.data && wp.blocks &&
      wp.data.select('core/editor').getCurrentPostId());
    await page.waitForTimeout(1000);
    await page.keyboard.press('Escape');
    const after = await editorState(page);
    const warningsAfter = await page.locator(
      '.block-editor-warning, .components-notice.is-error, [data-type="core/missing"]'
    ).allTextContents();
    await page.screenshot({
      path: path.join(outputDir, `${postId}-${before.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.png`),
      fullPage: true
    });
    results.push({
      postId,
      title: before.title,
      status: after.status,
      blockNames: after.blockNames,
      invalidBlocksBefore: before.invalidBlocks,
      invalidBlocksAfter: after.invalidBlocks,
      editorWarningsBefore: warningsBefore,
      editorWarningsAfter: warningsAfter,
      contentRestoredAfterSaveAndReopen: before.content.trim() === after.content.trim(),
      consoleErrors: [...consoleErrors]
    });
  }

  await browser.close();
  const report = {
    wordpressUrl: baseUrl,
    checkedAt: new Date().toISOString(),
    passed: results.every((result) =>
      result.status === 'draft' &&
      result.invalidBlocksBefore.length === 0 &&
      result.invalidBlocksAfter.length === 0 &&
      result.editorWarningsBefore.length === 0 &&
      result.editorWarningsAfter.length === 0 &&
      result.contentRestoredAfterSaveAndReopen
    ),
    results
  };
  fs.writeFileSync(path.join(outputDir, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  if (!report.passed) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
