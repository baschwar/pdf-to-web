function cookie(name) {
  return document.cookie.split('; ').find((value) => value.startsWith(`${name}=`))?.split('=')[1] || '';
}

const csrfHeaders = () => ({
  'content-type': 'application/json',
  'x-csrf-token': decodeURIComponent(cookie('pdf_to_web_csrf'))
});

async function api(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok || data.status === 'error') throw new Error(data.error || data.detail || 'Request failed');
  return data;
}

function announce(message) {
  const status = document.getElementById('app-status');
  if (status) status.textContent = message;
}

async function openProject(token) {
  await api('/api/projects/open', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ selection_token: token }) });
  window.location.assign('/document');
}

document.getElementById('choose-project')?.addEventListener('click', async () => {
  const output = document.getElementById('project-message');
  try {
    const picked = await api('/api/picker/project', { method: 'POST', headers: csrfHeaders(), body: '{}' });
    output.textContent = `Selected ${picked.selection.name}. Opening…`;
    await openProject(picked.selection.token);
  } catch (error) { output.textContent = error.message; }
});

document.querySelectorAll('.open-project').forEach((button) => button.addEventListener('click', () => openProject(button.dataset.projectToken)));
document.querySelectorAll('.remove-project').forEach((button) => button.addEventListener('click', async () => {
  const output = document.getElementById('project-message');
  try {
    await api('/api/projects/remove-recent', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ selection_token: button.dataset.projectToken }) });
    window.location.reload();
  } catch (error) { output.textContent = error.message; }
}));

document.getElementById('new-project-form')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const output = document.getElementById('project-message');
  const button = form.querySelector('button[type="submit"]');
  try {
    button.disabled = true;
    output.textContent = 'Choose a PDF in the file window. Conversion may take a few minutes.';
    const values = Object.fromEntries(new FormData(form));
    await api('/api/projects/create', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values) });
    output.textContent = 'Project created. Opening document…';
    window.location.assign('/document');
  } catch (error) {
    output.textContent = error.message;
    button.disabled = false;
  }
});

let selectedSourceCard = null;

function updateStickyHeaderOffset() {
  const header = document.querySelector('.app-header');
  if (!header) return;
  const headerHeight = Math.ceil(header.getBoundingClientRect().height);
  const readingOrderHeader = document.querySelector('.reading-order-header');
  const readingOrderHeight = readingOrderHeader ? Math.ceil(readingOrderHeader.getBoundingClientRect().height) : 0;
  document.documentElement.style.setProperty('--app-header-height', `${headerHeight}px`);
  document.documentElement.style.setProperty('--structure-scroll-offset', `${headerHeight + readingOrderHeight + 8}px`);
}

updateStickyHeaderOffset();
window.addEventListener('resize', updateStickyHeaderOffset);
if ('ResizeObserver' in window) {
  const header = document.querySelector('.app-header');
  if (header) new ResizeObserver(updateStickyHeaderOffset).observe(header);
  const readingOrderHeader = document.querySelector('.reading-order-header');
  if (readingOrderHeader) new ResizeObserver(updateStickyHeaderOffset).observe(readingOrderHeader);
}

async function showSourcePage(page, card = selectedSourceCard) {
  const pane = document.querySelector('.source-pane');
  if (!pane) return;
  const pageCount = Number(pane.dataset.pageCount || 1);
  const sourceKey = encodeURIComponent(pane.dataset.sourceKey || 'source');
  const requestedPage = Math.max(1, Math.min(pageCount, Number(page) || 1));
  document.querySelectorAll('.block-card').forEach((item) => item.classList.toggle('source-selected', item === card));
  const sourceImage = document.getElementById('source-image');
  sourceImage.src = `/source-page/${requestedPage}.png?v=${sourceKey}`;
  sourceImage.alt = `Rendered source PDF page ${requestedPage}`;
  const sourceLink = document.getElementById('open-source-page');
  sourceLink.href = `/source.pdf?v=${sourceKey}#page=${requestedPage}`;
  sourceLink.textContent = `Open source PDF page ${requestedPage}`;
  const pageNumber = document.getElementById('source-page-number');
  pageNumber.value = requestedPage;
  document.getElementById('source-page-previous').disabled = requestedPage === 1;
  document.getElementById('source-page-next').disabled = requestedPage === pageCount;
  const label = document.getElementById('source-page-label');
  const highlights = document.getElementById('source-highlights');
  highlights.replaceChildren();
  if (!card || Number(card.dataset.page) !== requestedPage) {
    label.textContent = card
      ? `Source page ${requestedPage}. The selected block is on page ${card.dataset.page}; no region is outlined.`
      : `Source page ${requestedPage}. Select a block to outline its source region.`;
    return;
  }
  const blockLabel = `Block ${card.dataset.blockIndex}, ${card.dataset.sourceType}, on source page ${requestedPage}.`;
  label.textContent = blockLabel;
  if (!card.dataset.bboxes) return;
  try {
    const regions = JSON.parse(card.dataset.bboxes);
    const dimensions = await api(`/api/source-page/${requestedPage}`);
    regions.forEach((bbox) => {
      const [x0, y0, x1, y1] = bbox.map(Number);
      const highlight = document.createElement('span');
      highlight.className = 'source-highlight';
      highlight.style.left = `${Math.min(x0, x1) / dimensions.width * 100}%`;
      highlight.style.top = `${(dimensions.height - Math.max(y0, y1)) / dimensions.height * 100}%`;
      highlight.style.width = `${Math.abs(x1 - x0) / dimensions.width * 100}%`;
      highlight.style.height = `${Math.abs(y1 - y0) / dimensions.height * 100}%`;
      highlights.append(highlight);
    });
    label.textContent = `${blockLabel} ${regions.length === 1 ? 'The approximate source region is' : `${regions.length} source regions are`} outlined.`;
  } catch (error) {
    label.textContent = `${blockLabel} Its source region could not be outlined.`;
  }
}

async function selectSourceBlock(card) {
  const page = card.dataset.page;
  if (!page || page === 'Unknown') return;
  selectedSourceCard = card;
  updateBlockNavigation();
  await showSourcePage(page, card);
}

function blockCards() {
  return Array.from(document.querySelectorAll('.block-card'));
}

function updateBlockNavigation() {
  const cards = blockCards();
  const index = selectedSourceCard ? cards.indexOf(selectedSourceCard) : -1;
  const previous = document.getElementById('previous-block');
  const next = document.getElementById('next-block');
  const page = document.getElementById('selected-block-page');
  const position = document.getElementById('selected-block-position');
  if (previous) previous.disabled = index <= 0;
  if (next) next.disabled = cards.length === 0 || index === cards.length - 1;
  if (page) page.textContent = index >= 0 ? `Page ${cards[index].dataset.page}` : 'Page -';
  if (position) position.textContent = index >= 0 ? `Block ${index + 1} of ${cards.length}` : 'No block selected';
}

function focusBlock(card) {
  if (!card) return;
  card.focus({ preventScroll: true });
  card.scrollIntoView({ block: 'start' });
}

function navigateSourcePage(page) {
  const pageInput = document.getElementById('source-page-number');
  const pageCount = Number(pageInput?.max || 1);
  const requestedPage = Math.max(1, Math.min(pageCount, Number(page) || 1));
  const firstCard = blockCards().find((card) => Number(card.dataset.page) === requestedPage);
  if (firstCard) {
    selectedSourceCard = firstCard;
    updateBlockNavigation();
    focusBlock(firstCard);
    showSourcePage(requestedPage, firstCard);
    return;
  }
  selectedSourceCard = null;
  updateBlockNavigation();
  showSourcePage(requestedPage, null);
}

document.getElementById('previous-block')?.addEventListener('click', () => {
  const cards = blockCards();
  const index = selectedSourceCard ? cards.indexOf(selectedSourceCard) : cards.length;
  focusBlock(cards[index - 1]);
});
document.getElementById('next-block')?.addEventListener('click', () => {
  const cards = blockCards();
  const index = selectedSourceCard ? cards.indexOf(selectedSourceCard) : -1;
  focusBlock(cards[index + 1]);
});

document.getElementById('source-page-previous')?.addEventListener('click', () => {
  navigateSourcePage(Number(document.getElementById('source-page-number').value) - 1);
});
document.getElementById('source-page-next')?.addEventListener('click', () => {
  navigateSourcePage(Number(document.getElementById('source-page-number').value) + 1);
});
document.getElementById('source-page-controls')?.addEventListener('submit', (event) => {
  event.preventDefault();
  navigateSourcePage(document.getElementById('source-page-number').value);
});
document.getElementById('source-page-number')?.addEventListener('change', (event) => {
  navigateSourcePage(event.currentTarget.value);
});

document.querySelectorAll('.block-card').forEach((card) => {
  card.addEventListener('click', () => selectSourceBlock(card));
  card.addEventListener('focusin', () => selectSourceBlock(card));
});

const reviewAdvanceKey = 'pdf-to-web-review-next-block';
const pendingBlockId = sessionStorage.getItem(reviewAdvanceKey);
if (pendingBlockId) {
  sessionStorage.removeItem(reviewAdvanceKey);
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  window.addEventListener('load', () => setTimeout(() => {
    // A reviewer who has entered provider setup keeps focus there.
    if (document.activeElement?.closest('#image-draft-toolbar')) return;
    const complete = document.getElementById('structure-review-complete');
    if (complete) { complete.focus({preventScroll: true}); complete.scrollIntoView({block: 'center'}); return; }
    const pendingCard = document.getElementById(pendingBlockId);
    if (!pendingCard) return;
    focusBlock(pendingCard);
  }, 50), { once: true });
}

function nextReviewBlockId(card) {
  const cards = Array.from(document.querySelectorAll('.block-card'));
  return cards.slice(cards.indexOf(card) + 1)
    .find((item) => item.classList.contains('status-unreviewed') || item.classList.contains('status-needs_review'))?.id || '';
}

document.querySelectorAll('.block-form').forEach((form) => form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(form));
  const decorative = form.querySelector('input[name="decorative"]');
  if (decorative) values.decorative = decorative.checked;
  ['table_header_row', 'table_header_column', 'table_reviewed'].forEach((name) => {
    const checkbox = form.querySelector(`input[name="${name}"]`);
    if (checkbox) values[name] = checkbox.checked;
  });
  if (values.type === 'heading') values.level = Number(values.level);
  else delete values.level;
  try {
    await api(`/api/blocks/${encodeURIComponent(form.dataset.blockId)}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values) });
    if (['approved', 'excluded'].includes(values.review_status)) sessionStorage.setItem(reviewAdvanceKey, `block-${form.dataset.blockId}`);
    announce('Block saved.');
    window.location.reload();
  } catch (error) { announce(error.message); alert(error.message); }
}));

document.querySelectorAll('.image-block-form input[name="decorative"]').forEach((checkbox) => checkbox.addEventListener('change', () => {
  const alt = checkbox.closest('form').querySelector('textarea[name="alt"]');
  alt.disabled = checkbox.checked;
  if (checkbox.checked) alt.value = '';
}));

document.querySelectorAll('.block-form select[name="type"]').forEach((select) => select.addEventListener('change', () => {
  const level = select.closest('form').querySelector('.heading-level');
  level.hidden = select.value !== 'heading';
  level.querySelector('select').disabled = select.value !== 'heading';
}));

document.querySelectorAll('.complex-visual-form').forEach((form) => form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = form.querySelector('button[type="submit"]');
  const message = form.querySelector('.visual-save-message');
  const restoreFocus = document.activeElement === button;
  button.disabled = true;
  message.textContent = 'Saving…';
  try {
    const values = Object.fromEntries(new FormData(form));
    await api(`/api/complex-visuals/${encodeURIComponent(form.dataset.visualId)}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values) });
    message.textContent = 'Review saved. Image descriptions still need review.';
    announce('Complex visual review saved.');
    for (const field of form.querySelectorAll('input, textarea')) field.defaultValue = values[field.name];
    const state = form.closest('.complex-visual').querySelector('.visual-state');
    state.textContent = form.elements.status.selectedOptions[0].textContent;
    const imageForm = form.dataset.blockId && document.querySelector(`.image-block-form[data-block-id="${CSS.escape(form.dataset.blockId)}"]`);
    if (imageForm) {
      for (const [key, value] of Object.entries({alt: values.short_alt, long_description: values.long_description})) {
        const field = imageForm.elements.namedItem(key);
        if (field && field.value === field.defaultValue) { field.value = value; field.defaultValue = value; }
      }
      const review = imageForm.elements.namedItem('review_status');
      if (review.value === 'approved') review.value = 'needs_review';
    }
  } catch (error) { message.textContent = error.message; announce(error.message); }
  finally {
    button.disabled = false;
    if (restoreFocus && document.activeElement === document.body) button.focus({preventScroll: true});
  }
}));

document.querySelectorAll('.accessibility-decision-form').forEach((form) => form.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const values = Object.fromEntries(new FormData(form));
    await api(`/api/accessibility/${encodeURIComponent(form.dataset.itemId)}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values) });
    announce('Accessibility decision saved.');
    window.location.reload();
  } catch (error) { announce(error.message); alert(error.message); }
}));

document.getElementById('export-accessibility-report')?.addEventListener('click', async () => {
  const output = document.getElementById('accessibility-export-result');
  try {
    const data = await api('/api/accessibility-report', { method: 'POST', headers: csrfHeaders(), body: '{}' });
    const list = document.createElement('ul');
    data.downloads.forEach((file) => {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = file.url;
      link.download = '';
      link.textContent = `Download ${file.path.split('/').pop()}`;
      item.append(link);
      list.append(item);
    });
    output.replaceChildren(list);
    announce('Accessibility reports generated.');
  } catch (error) { output.textContent = error.message; announce(error.message); }
});

document.querySelectorAll('.block-action').forEach((button) => button.addEventListener('click', async () => {
  let action = button.dataset.action;
  const blockId = button.dataset.blockId;
  const body = {};
  if (action === 'toggle-excluded') action = button.dataset.currentStatus === 'excluded' ? 'include' : 'exclude';
  if (action === 'split') {
    const textarea = button.closest('.block-card').querySelector('textarea');
    body.offset = textarea?.selectionStart || 0;
    if (!body.offset) { announce('Place the text cursor where the block should split.'); textarea?.focus(); return; }
  }
  try {
    await api(`/api/blocks/${encodeURIComponent(blockId)}/${action}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(body) });
    if (['approve', 'flag', 'exclude', 'include'].includes(action)) {
      const currentCard = button.closest('.block-card');
      const nextId = nextReviewBlockId(currentCard);
      sessionStorage.setItem(reviewAdvanceKey, nextId || currentCard.id);
      if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    }
    announce('Review action saved.');
    window.location.reload();
  } catch (error) { announce(error.message); alert(error.message); }
}));

document.getElementById('undo-action')?.addEventListener('click', async () => {
  try {
    await api('/api/review/undo', { method: 'POST', headers: csrfHeaders(), body: '{}' });
    announce('Last action undone.');
    window.location.reload();
  } catch (error) { announce(error.message); alert(error.message); }
});

document.querySelectorAll('.preview-width').forEach((button) => button.addEventListener('click', () => {
  const shell = document.getElementById('preview-shell');
  shell.classList.toggle('narrow', button.dataset.width === 'mobile');
  document.querySelectorAll('.preview-width').forEach((item) => item.classList.toggle('secondary', item !== button));
  announce(`${button.textContent} preview selected.`);
}));

const previewFrame = document.querySelector('#preview-shell iframe');
const previewProfile = document.getElementById('preview-profile');
function selectPreviewMode(mode) {
  if (!previewFrame) return;
  const wordpress = mode === 'wordpress';
  document.querySelectorAll('.preview-mode').forEach((button) => {
    const selected = button.dataset.mode === mode;
    button.classList.toggle('secondary', !selected);
    button.setAttribute('aria-pressed', String(selected));
  });
  previewProfile?.closest('label').toggleAttribute('hidden', !wordpress);
  previewFrame.title = wordpress ? 'WordPress Gutenberg preview' : 'Semantic HTML preview';
  previewFrame.src = wordpress
    ? `/api/preview/wordpress?profile=${encodeURIComponent(previewProfile?.value || 'generic')}`
    : '/api/preview/html';
  const description = document.getElementById('preview-description');
  if (description) description.textContent = wordpress
    ? 'WordPress Preview renders the actual Gutenberg export through the local block converter.'
    : 'Semantic Preview shows the reviewed document independently of WordPress.';
  announce(`${wordpress ? 'WordPress' : 'Semantic HTML'} preview selected.`);
}
document.querySelectorAll('.preview-mode').forEach((button) => button.addEventListener('click', () => selectPreviewMode(button.dataset.mode)));
previewProfile?.addEventListener('change', () => selectPreviewMode('wordpress'));

const exportForm = document.getElementById('export-form');
function updateExportAvailability() {
  if (!exportForm) return;
  const blocked = exportForm.dataset.conversionBlocked === 'true';
  const target = exportForm.querySelector('[name="target"]').value;
  exportForm.querySelector('button[type="submit"]').disabled = blocked && target !== 'html';
}
exportForm?.querySelector('[name="target"]')?.addEventListener('change', updateExportAvailability);
updateExportAvailability();

async function copyExportHtml(file) {
  const response = await fetch(file.url);
  if (!response.ok) throw new Error('Could not read the exported HTML file.');
  const content = await response.text();
  try {
    await navigator.clipboard.writeText(content);
  } catch (error) {
    const field = document.createElement('textarea');
    field.value = content;
    field.className = 'visually-hidden';
    field.setAttribute('readonly', '');
    document.body.append(field);
    field.select();
    const copied = document.execCommand('copy');
    field.remove();
    if (!copied) throw error;
  }
}

exportForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const output = document.getElementById('export-result');
  try {
    const values = Object.fromEntries(new FormData(event.currentTarget));
    const data = await api('/api/export', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values) });
    const heading = document.createElement('p');
    const strong = document.createElement('strong');
    strong.textContent = 'Export complete.';
    heading.append(strong);
    const location = document.createElement('p');
    location.append('Project folder: ');
    const projectPath = document.createElement('code');
    projectPath.textContent = data.project_root;
    location.append(projectPath);
    const media = document.createElement('p');
    if (data.media) {
      const unresolved = document.createElement('strong');
      unresolved.textContent = `${data.media.unresolved} image${data.media.unresolved === 1 ? '' : 's'} require upload.`;
      media.append(unresolved, ` ${data.media.copied_assets} extracted asset${data.media.copied_assets === 1 ? '' : 's'} included.`);
    }
    const files = document.createElement('ul');
    const downloads = data.downloads || data.files.map((path) => ({ path, url: `/download/${path.split('/').map(encodeURIComponent).join('/')}` }));
    downloads.forEach((file) => {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = file.url;
      link.download = '';
      link.textContent = `Download ${file.path.split('/').pop()}`;
      const actions = document.createElement('span');
      actions.className = 'export-file-actions';
      actions.append(link);
      if (/\.html$/i.test(file.path)) {
        const copyButton = document.createElement('button');
        copyButton.type = 'button';
        copyButton.className = 'secondary';
        copyButton.textContent = 'Copy HTML';
        copyButton.setAttribute('aria-label', `Copy ${file.path.split('/').pop()} HTML to clipboard`);
        copyButton.addEventListener('click', async () => {
          try {
            await copyExportHtml(file);
            copyButton.textContent = 'Copied';
            announce('Exported HTML copied to clipboard.');
          } catch (error) {
            copyButton.textContent = 'Copy failed';
            announce(error.message || 'Could not copy the exported HTML.');
          }
        });
        actions.append(copyButton);
      }
      const path = document.createElement('code');
      path.textContent = file.path;
      item.append(actions, document.createElement('br'), path);
      files.append(item);
    });
    output.replaceChildren(heading, location, ...(data.media ? [media] : []), files);
    announce('Export complete.');
  } catch (error) { output.textContent = error.message; announce(error.message); }
});

document.getElementById('media-mapping-form')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const output = document.getElementById('media-mapping-result');
  const file = new FormData(event.currentTarget).get('mapping');
  try {
    if (!(file instanceof File)) throw new Error('Choose a media mapping CSV.');
    const data = await api('/api/media-mapping', {
      method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ csv: await file.text() })
    });
    output.textContent = `${data.mapped} image mapping${data.mapped === 1 ? '' : 's'} imported. Regenerate the Gutenberg or WXR export.`;
    announce(output.textContent);
  } catch (error) { output.textContent = error.message; announce(error.message); }
});

document.getElementById('media-wxr-form')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const output = document.getElementById('media-mapping-result');
  const file = new FormData(event.currentTarget).get('media_wxr');
  try {
    if (!(file instanceof File)) throw new Error('Choose a WordPress media XML file.');
    const data = await api('/api/media-mapping-wxr', {
      method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ xml: await file.text() })
    });
    output.textContent = `${data.matched} image mapping${data.matched === 1 ? '' : 's'} matched; ${data.unmatched} unmatched and ${data.ambiguous} ambiguous. Regenerate the Gutenberg or WXR export.`;
    announce(output.textContent);
  } catch (error) { output.textContent = error.message; announce(error.message); }
});

document.documentElement.dataset.appReady = 'true';

const pageEditor = document.getElementById('page-editor');
const pageMessage = document.getElementById('output-page-message');
const selectedPageId = () => pageEditor?.dataset.pageId;
async function pageAction(action, values = {}) {
  try {
    const result = await api(`/api/output-pages/${action}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ page_id: selectedPageId(), ...values }) });
    sessionStorage.setItem('output-page-announcement', 'Changes saved.');
    const destination = `/output-pages?page_id=${encodeURIComponent(result.page_id || '')}`;
    if (location.pathname + location.search === destination) {
      location.hash = 'page-editor';
      location.reload();
    } else window.location.assign(destination + '#page-editor');
  } catch (error) { pageMessage.textContent = error.message; }
}
document.querySelectorAll('[data-page-action]').forEach(button => button.addEventListener('click', () => pageAction(button.dataset.pageAction, { block_id: button.dataset.blockId, direction: button.dataset.direction })));
for (const [id, action] of [['output-page-metadata', 'metadata'], ['output-page-merge', 'merge'], ['output-page-approval', 'approve']]) {
  document.getElementById(id)?.addEventListener('submit', event => {
    event.preventDefault();
    pageAction(action, Object.fromEntries(new FormData(event.currentTarget)));
  });
}
document.getElementById('output-page-undo')?.addEventListener('click', () => pageAction('undo'));
if (pageMessage) {
  pageMessage.textContent = sessionStorage.getItem('output-page-announcement') || '';
  sessionStorage.removeItem('output-page-announcement');
  if (location.hash === '#page-editor') pageEditor?.focus();
}
function previewOutputPage(mode) {
  const slug = document.querySelector('#output-page-metadata [name="slug"]').value;
  const profile = document.getElementById('output-page-profile').value;
  document.getElementById('output-page-frame').src = `/output-preview/${encodeURIComponent(slug)}.html?mode=${mode}&profile=${profile}`;
}
document.getElementById('output-page-preview')?.addEventListener('click', () => previewOutputPage('semantic'));
document.getElementById('output-page-wordpress-preview')?.addEventListener('click', () => previewOutputPage('wordpress'));
document.querySelectorAll('[data-page-export]').forEach(button => button.addEventListener('click', async () => {
  try {
    const result = await api('/api/output-pages/export', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ page_id: button.dataset.pageExport === 'individual' ? selectedPageId() : null, profile: document.getElementById('output-page-profile').value }) });
    pageMessage.replaceChildren(document.createTextNode('Export complete. Review the manifest and manual import instructions. '));
    for (const file of result.downloads) {
      const link = document.createElement('a'); link.href = file.url; link.textContent = file.path;
      pageMessage.append(link, document.createElement('br'));
    }
  } catch (error) { pageMessage.textContent = error.message; }
}));

// Image drafts use the Structure editor and its existing Undo and focus behavior.
const draftToolbar = document.getElementById('image-draft-toolbar');
if (draftToolbar) {
  const message = document.getElementById('draft-message');
  const docId = draftToolbar.dataset.documentId;
  const postDraft = (action, data) => api(`/api/image-drafts/${action}`, {method: 'POST', headers: csrfHeaders(), body: JSON.stringify({document_id: docId, ...data})});
  const panelFor = id => [...document.querySelectorAll('.image-draft-panel')].find(p => p.dataset.blockId === id);
  const reloadDraft = id => { if (id) sessionStorage.setItem(reviewAdvanceKey, `block-${id}`); location.reload(); };
  const providerSelect = document.getElementById('draft-provider');
  const providerMessage = document.getElementById('draft-provider-message');
  const updateProviderSetup = () => {
    document.getElementById('draft-model-label').hidden = providerSelect.value !== 'ollama-local';
    const help = document.getElementById('draft-provider-help');
    help.textContent = JSON.parse(help.dataset.providerHelp)[providerSelect.value];
  };
  providerSelect.addEventListener('change', () => {
    updateProviderSetup();
    providerMessage.textContent = 'Selection changed. Save provider settings to keep it when you reopen this project.';
  });
  document.getElementById('draft-provider-form').addEventListener('submit', async event => {
    event.preventDefault();
    const button = event.currentTarget.querySelector('button[type="submit"]');
    const keepFocus = document.activeElement === button;
    try {
      button.disabled = true;
      await postDraft('settings', {provider: providerSelect.value, model: document.getElementById('draft-model').value});
      providerMessage.textContent = 'Provider settings saved for this project.';
    } catch (error) { providerMessage.textContent = error.message; }
    finally {
      button.disabled = false;
      if (keepFocus && document.activeElement === document.body) button.focus({preventScroll: true});
    }
  });
  updateProviderSetup();
  const selectedIds = () => [...document.querySelectorAll('.draft-selection:checked')].map(input => input.value);
  const pendingIds = () => [...document.querySelectorAll('.image-draft-panel[data-pending="true"]')]
    .filter(panel => !['ready', 'rejected', 'generating'].includes(panel.dataset.requestStatus)).map(panel => panel.dataset.blockId);
  const updateBatchControls = () => {
    const ids = selectedIds();
    const pending = pendingIds();
    document.getElementById('draft-selection-summary').textContent = `${ids.length} images selected · ${pending.length} pending images needing drafts.`;
    document.querySelectorAll('[data-draft-batch]').forEach(button => {
      const action = button.dataset.draftBatch;
      if (action === 'cancel') button.hidden = !ids.some(id => ['requested', 'generating'].includes(panelFor(id)?.dataset.requestStatus));
      else button.disabled = !(action === 'pending' ? pending.length : ids.length);
    });
  };
  document.querySelectorAll('.draft-selection').forEach(input => input.addEventListener('change', updateBatchControls));
  updateBatchControls();
  let cloudRequest = null;
  let importPayload = null;
  const draftValues = form => ({
    alt: form.elements.alt.value,
    caption: form.elements.omit_caption.checked ? null : form.elements.caption.value,
    long_description: form.elements.omit_long_description.checked ? null : form.elements.long_description.value,
    warnings: JSON.parse(form.dataset.warnings || '[]'), decorative: form.dataset.decorative === 'true'
  });
  const showDownload = result => {
    const link = document.createElement('a'); link.href = result.url; link.textContent = 'Download drafting request ZIP'; link.download = result.filename;
    document.getElementById('draft-downloads').replaceChildren(link);
    message.textContent = 'ZIP ready. Use Download drafting request ZIP below to save the images, CSV review sheet and JSON template.';
    link.focus();
    link.scrollIntoView({block: 'nearest'});
    pollDrafts();
  };
  const generate = async (ids, regenerate = false) => {
    const request = {block_ids: ids, provider: document.getElementById('draft-provider').value, model: document.getElementById('draft-model').value, regenerate};
    if (request.provider === 'manual') {
      showDownload(await postDraft('export', {block_ids: ids, regenerate}));
    } else if (request.provider === 'openai') {
      const result = await postDraft('preflight', request);
      cloudRequest = {...request, consent_hash: result.consent_hash};
      const view = document.getElementById('draft-transmission-content');
      view.textContent = JSON.stringify(result.requests, null, 2);
      const images = document.getElementById('draft-transmission-images');
      images.replaceChildren();
      for (const request of result.requests) {
        const figure = document.createElement('figure');
        const image = document.createElement('img'); image.className = 'image-block-preview';
        image.src = `/api/image-drafts/asset?path=${encodeURIComponent(request.image_path)}`;
        image.alt = `Selected image for block ${request.block_id}`;
        const caption = document.createElement('figcaption'); caption.textContent = `Block ${request.block_id}`;
        figure.append(image, caption); images.append(figure);
      }
      document.getElementById('draft-transmission').hidden = false;
      document.getElementById('draft-transmission-send').focus();
      message.textContent = 'Review the selected images and context before sending to OpenAI.';
    } else {
      const result = await postDraft('generate', request);
      message.textContent = `${result.queued} requests queued with local Ollama; ${result.preserved} existing drafts preserved. Refresh to review results.`;
    }
  };
  document.getElementById('draft-transmission-send').addEventListener('click', async () => {
    if (!cloudRequest) return;
    try {
      const result = await postDraft('generate', {...cloudRequest, authorize_cloud: true});
      cloudRequest = null; document.getElementById('draft-transmission').hidden = true;
      message.textContent = `${result.queued} requests queued with OpenAI for the authorized selection; ${result.preserved} existing drafts preserved.`;
    } catch (error) { message.textContent = error.message; }
  });
  document.getElementById('draft-transmission-cancel').addEventListener('click', () => { cloudRequest = null; document.getElementById('draft-transmission').hidden = true; message.textContent = 'Cloud request cancelled.'; });
  document.querySelectorAll('[data-draft-batch]').forEach(button => button.addEventListener('click', async () => {
    const ids = button.dataset.draftBatch === 'pending' ? pendingIds() : selectedIds();
    try {
      if (!ids.length) throw new Error('Select at least one image.');
      message.textContent = 'Preparing image requests…';
      if (['export', 'pending'].includes(button.dataset.draftBatch)) showDownload(await postDraft('export', {block_ids: ids}));
      else if (button.dataset.draftBatch === 'generate') await generate(ids);
      else {
        const current = await api('/api/image-drafts');
        if (current.document_id !== docId) throw new Error('Project changed; reload this screen.');
        for (const entry of current.entries.filter(e => ids.includes(e.block_id) && ['requested', 'generating'].includes(e.status))) await postDraft('cancel', entry);
        reloadDraft(ids[0]);
      }
    } catch (error) {
      message.textContent = error.message;
      message.tabIndex = -1; message.focus(); message.scrollIntoView({block: 'nearest'});
    }
  }));
  document.querySelectorAll('.draft-association-form').forEach(form => form.addEventListener('submit', async event => {
    event.preventDefault();
    try { await postDraft('associate', {...Object.fromEntries(new FormData(form)), block_id: form.dataset.blockId}); reloadDraft(form.dataset.blockId); }
    catch (error) { message.textContent = error.message; announce(error.message); }
  }));
  document.querySelectorAll('.draft-edit-form').forEach(form => form.addEventListener('submit', async event => {
    event.preventDefault();
    try { await postDraft('edit', {block_id: form.dataset.blockId, request_id: form.dataset.requestId, draft: draftValues(form)}); reloadDraft(form.dataset.blockId); }
    catch (error) { message.textContent = error.message; announce(error.message); }
  }));
  document.querySelectorAll('[data-draft-action]').forEach(button => button.addEventListener('click', async () => {
    const panel = button.closest('.image-draft-panel');
    const id = panel.dataset.blockId;
    const action = button.dataset.draftAction;
    try {
      if (action === 'export' || action === 'export-new') showDownload(await postDraft('export', {block_ids: [id], regenerate: action === 'export-new'}));
      else if (action === 'generate' || action === 'regenerate') await generate([id], action === 'regenerate');
      else {
        const current = await api('/api/image-drafts');
        if (current.document_id !== docId) throw new Error('Project changed; reload this screen.');
        const entry = current.entries.find(e => e.block_id === id);
        if (!entry) throw new Error('No draft request exists for this image.');
        if (action === 'apply') {
          // Save edited drafts first; applying reads the saved draft, never the accepted form.
          const form = panel.querySelector('.draft-edit-form');
          if (!form || form.dataset.requestId !== entry.request_id) throw new Error('Draft changed; refresh results.');
          await postDraft('edit', {block_id: id, request_id: entry.request_id, draft: draftValues(form)});
        }
        await postDraft(action, {block_id: id, request_id: entry.request_id, fields: [button.dataset.field]}); reloadDraft(id);
      }
    } catch (error) { message.textContent = error.message; announce(error.message); }
  }));
  document.getElementById('draft-import-preview').addEventListener('click', async () => {
    importPayload = null; document.getElementById('draft-import-confirm').disabled = true;
    try {
      const file = document.getElementById('draft-response-file').files[0];
      if (!file) throw new Error('Choose a response JSON file.');
      if (file.size > 4 * 1024 * 1024) throw new Error('Response exceeds 4 MiB.');
      const payload = JSON.parse(await file.text());
      const result = await postDraft('import', {response: payload});
      document.getElementById('draft-import-findings').textContent = `${result.valid_count} valid drafts. ${result.findings.map(f => `Entry ${f.entry}: ${f.error}`).join(' ')}`;
      importPayload = payload; document.getElementById('draft-import-confirm').disabled = !result.valid_count;
    } catch (error) { document.getElementById('draft-import-findings').textContent = error.message; }
  });
  document.getElementById('draft-import-confirm').addEventListener('click', async () => {
    try { const result = await postDraft('import', {response: importPayload, commit: true});
      if (!result.valid_count) throw new Error(result.findings.map(f => f.error).join(' '));
      reloadDraft();
    } catch (error) { message.textContent = error.message; }
  });
  document.getElementById('draft-populate').addEventListener('click', async () => {
    try { await postDraft('populate', {}); reloadDraft(); } catch (error) { message.textContent = error.message; }
  });
  document.getElementById('draft-refresh').addEventListener('click', () => reloadDraft());
  // Update status only; polling must not discard unsaved reviewer edits or move focus.
  const pollDrafts = async () => {
    try {
      const result = await api('/api/image-drafts');
      if (result.document_id !== docId) { message.textContent = 'Project changed; reload this screen.'; return; }
      for (const entry of result.entries) {
        const panel = panelFor(entry.block_id); if (!panel) continue;
        panel.dataset.requestStatus = entry.status;
        if (entry.status === 'ready' && entry.image_fields) {
          const form = panel.closest('.block-card')?.querySelector('.image-block-form') || document.querySelector(`.image-block-form[data-block-id="${CSS.escape(entry.block_id)}"]`);
          for (const [key, value] of Object.entries(entry.image_fields)) {
            const field = form?.elements.namedItem(key);
            if (field && field.value === field.defaultValue && document.activeElement !== field) {
              field.value = value; field.defaultValue = value;
            }
          }
        }
        panel.querySelector('[data-draft-action="cancel"]').hidden = !['requested', 'generating'].includes(entry.status);
        const label = {ready: 'Draft ready — refresh to review', requested: 'Awaiting response', generating: 'Generating', failed: 'Failed', stale: 'Context changed', cancelled: 'Cancelled', rejected: 'Rejected'}[entry.status];
        const status = panel.querySelector('.draft-status');
        if (!status.textContent.startsWith('Draft ready') || entry.status !== 'ready') status.textContent = label;
        if (entry.error) panel.querySelector('.draft-error')?.replaceChildren(document.createTextNode(entry.error));
      }
      updateBatchControls();
    } catch (error) { message.textContent = error.message; }
  };
  setInterval(pollDrafts, 2500);
}
