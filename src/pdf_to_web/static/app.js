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

async function showSourcePage(page, card = selectedSourceCard) {
  const pane = document.querySelector('.source-pane');
  if (!pane) return;
  const pageCount = Number(pane.dataset.pageCount || 1);
  const requestedPage = Math.max(1, Math.min(pageCount, Number(page) || 1));
  document.querySelectorAll('.block-card').forEach((item) => item.classList.toggle('source-selected', item === card));
  const sourceImage = document.getElementById('source-image');
  sourceImage.src = `/source-page/${requestedPage}.png`;
  sourceImage.alt = `Rendered source PDF page ${requestedPage}`;
  const sourceLink = document.getElementById('open-source-page');
  sourceLink.href = `/source.pdf#page=${requestedPage}`;
  sourceLink.textContent = `Open source PDF page ${requestedPage}`;
  const pageNumber = document.getElementById('source-page-number');
  pageNumber.value = requestedPage;
  document.getElementById('source-page-previous').disabled = requestedPage === 1;
  document.getElementById('source-page-next').disabled = requestedPage === pageCount;
  const label = document.getElementById('source-page-label');
  const highlight = document.getElementById('source-highlight');
  highlight.hidden = true;
  if (!card || Number(card.dataset.page) !== requestedPage) {
    label.textContent = card
      ? `Source page ${requestedPage}. The selected block is on page ${card.dataset.page}; no region is outlined.`
      : `Source page ${requestedPage}. Select a block to outline its source region.`;
    return;
  }
  const blockLabel = `Block ${card.dataset.blockIndex}, ${card.dataset.sourceType}, on source page ${requestedPage}.`;
  label.textContent = blockLabel;
  if (!card.dataset.bbox) return;
  try {
    const bbox = JSON.parse(card.dataset.bbox);
    const dimensions = await api(`/api/source-page/${requestedPage}`);
    const [x0, y0, x1, y1] = bbox.map(Number);
    highlight.style.left = `${Math.min(x0, x1) / dimensions.width * 100}%`;
    highlight.style.top = `${(dimensions.height - Math.max(y0, y1)) / dimensions.height * 100}%`;
    highlight.style.width = `${Math.abs(x1 - x0) / dimensions.width * 100}%`;
    highlight.style.height = `${Math.abs(y1 - y0) / dimensions.height * 100}%`;
    highlight.hidden = false;
    label.textContent = `${blockLabel} The approximate source region is outlined.`;
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
  const position = document.getElementById('selected-block-position');
  if (previous) previous.disabled = index <= 0;
  if (next) next.disabled = cards.length === 0 || index === cards.length - 1;
  if (position) position.textContent = index >= 0 ? `Block ${index + 1} of ${cards.length}` : 'No block selected';
}

function focusBlock(card) {
  if (!card) return;
  card.focus({ preventScroll: true });
  card.scrollIntoView({ block: 'center' });
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
  values.level = Number(values.level);
  try {
    await api(`/api/blocks/${encodeURIComponent(form.dataset.blockId)}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values) });
    announce('Block saved.');
    window.location.reload();
  } catch (error) { announce(error.message); alert(error.message); }
}));

document.querySelectorAll('.block-form select[name="type"]').forEach((select) => select.addEventListener('change', () => {
  const level = select.closest('form').querySelector('.heading-level');
  level.hidden = select.value !== 'heading';
}));

document.querySelectorAll('.complex-visual-form').forEach((form) => form.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const values = Object.fromEntries(new FormData(form));
    await api(`/api/complex-visuals/${encodeURIComponent(form.dataset.visualId)}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values) });
    announce('Complex visual review saved.');
    window.location.reload();
  } catch (error) { announce(error.message); alert(error.message); }
}));

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

exportForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const output = document.getElementById('export-result');
  try {
    const values = Object.fromEntries(new FormData(event.currentTarget));
    const data = await api('/api/export', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values) });
    output.innerHTML = `<p><strong>Export complete.</strong></p><ul>${data.files.map((file) => `<li><code>${file}</code></li>`).join('')}</ul>`;
    announce('Export complete.');
  } catch (error) { output.textContent = error.message; announce(error.message); }
});

document.documentElement.dataset.appReady = 'true';
