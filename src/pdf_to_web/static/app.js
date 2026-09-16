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

async function selectSourceBlock(card) {
  const page = card.dataset.page;
  if (!page || page === 'Unknown') return;
  document.querySelectorAll('.block-card').forEach((item) => item.classList.toggle('source-selected', item === card));
  const sourceImage = document.getElementById('source-image');
  sourceImage.src = `/source-page/${page}.png`;
  sourceImage.alt = `Rendered source PDF page ${page}`;
  const sourceLink = document.getElementById('open-source-page');
  sourceLink.href = `/source.pdf#page=${page}`;
  sourceLink.textContent = `Open source PDF page ${page}`;
  const label = document.getElementById('source-page-label');
  const highlight = document.getElementById('source-highlight');
  label.textContent = `Block ${card.dataset.blockIndex}, ${card.dataset.sourceType}, on source page ${page}.`;
  highlight.hidden = true;
  if (!card.dataset.bbox) return;
  try {
    const bbox = JSON.parse(card.dataset.bbox);
    const dimensions = await api(`/api/source-page/${page}`);
    const [x0, y0, x1, y1] = bbox.map(Number);
    highlight.style.left = `${Math.min(x0, x1) / dimensions.width * 100}%`;
    highlight.style.top = `${(dimensions.height - Math.max(y0, y1)) / dimensions.height * 100}%`;
    highlight.style.width = `${Math.abs(x1 - x0) / dimensions.width * 100}%`;
    highlight.style.height = `${Math.abs(y1 - y0) / dimensions.height * 100}%`;
    highlight.hidden = false;
    label.textContent += ' The approximate source region is outlined.';
  } catch (error) {
    label.textContent += ' Its source region could not be outlined.';
  }
}

document.querySelectorAll('.block-card').forEach((card) => {
  card.addEventListener('click', () => selectSourceBlock(card));
  card.addEventListener('focusin', () => selectSourceBlock(card));
});

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
