const authoringForms = [...document.querySelectorAll('.block-form, .complex-visual-form')];
const authoringValue = form => JSON.stringify([...form.querySelectorAll('input, textarea, select')].map(field => [field.name, field.type === 'checkbox' ? field.checked : field.value]));
const authoringBaselines = new WeakMap(authoringForms.map(form => [form, authoringValue(form)]));
function requireSavedAuthoring() {
  const dirty = authoringForms.find(form => authoringBaselines.get(form) !== authoringValue(form));
  if (dirty) throw new Error('Save or undo unsaved authoring edits before importing, populating, or refreshing drafts.');
}

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

const backToTop = document.getElementById('back-to-top');
if (backToTop) {
  const topTarget = document.getElementById('app-top');
  const updateBackToTop = () => {
    const atTop = window.scrollY <= 200;
    if (atTop && document.activeElement === backToTop) topTarget?.focus({preventScroll: true});
    backToTop.hidden = atTop;
  };
  backToTop.addEventListener('click', () => {
    topTarget?.focus({preventScroll: true});
    window.scrollTo({top: 0, behavior: 'instant'});
    updateBackToTop();
  });
  window.addEventListener('scroll', updateBackToTop, {passive: true});
  window.addEventListener('resize', updateBackToTop);
  window.addEventListener('pageshow', updateBackToTop);
  updateBackToTop();
}

function retainProjectWarning(result) {
  if (!result.warning) return;
  try { sessionStorage.setItem('pdf-to-web-project-warning', result.warning); }
  catch { announce(result.warning); }
}
try {
  const message = sessionStorage.getItem('pdf-to-web-project-warning');
  if (message) {
    const notice = document.createElement('p');
    notice.className = 'status-banner';
    notice.setAttribute('role', 'status');
    notice.textContent = message;
    document.querySelector('main')?.prepend(notice);
    sessionStorage.removeItem('pdf-to-web-project-warning');
  }
} catch { /* Opening a project also works when browser storage is unavailable. */ }

async function openProject(token) {
  const result = await api('/api/projects/open', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ selection_token: token }) });
  retainProjectWarning(result);
  window.location.assign(result.next || '/document');
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

const newProjectForm = document.getElementById('new-project-form');
let chosenDestination = null;
let choosingDestination = false;
let creatingProject = false;
function updateProjectDestination() {
  if (!newProjectForm) return;
  const chosen = newProjectForm.elements.destination_mode.value === 'chosen';
  const path = document.getElementById('project-destination-path');
  const token = newProjectForm.elements.destination_token;
  token.value = chosen ? chosenDestination?.token || '' : '';
  path.replaceChildren();
  if (chosen && !chosenDestination) {
    path.textContent = 'Choose a destination folder before creating the project.';
  } else {
    const name = newProjectForm.elements.title.value.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/(^-+|-+$)/g, '') || 'document';
    const code = document.createElement('code');
    code.textContent = chosen ? chosenDestination.path : `${newProjectForm.dataset.defaultRoot}/${name}`;
    path.append(chosen ? 'Selected project folder: ' : 'Default project folder: ', code);
    if (chosenDestination?.has_existing_files && chosen) path.append(' Existing files will be preserved.');
  }
  newProjectForm.querySelector('button[type="submit"]').disabled = choosingDestination || creatingProject || (chosen && !chosenDestination);
  document.getElementById('choose-project-destination').disabled = choosingDestination || creatingProject;
  newProjectForm.elements.title.disabled = creatingProject;
  newProjectForm.querySelectorAll('[name="destination_mode"]').forEach(input => {input.disabled = choosingDestination || creatingProject;});
}
newProjectForm?.elements.title.addEventListener('input', updateProjectDestination);
newProjectForm?.querySelectorAll('[name="destination_mode"]').forEach(input => input.addEventListener('change', updateProjectDestination));
updateProjectDestination();
document.getElementById('choose-project-destination')?.addEventListener('click', async event => {
  const button = event.currentTarget;
  const output = document.getElementById('project-message');
  newProjectForm.querySelector('[name="destination_mode"][value="chosen"]').checked = true;
  choosingDestination = true;
  button.disabled = true;
  updateProjectDestination();
  try {
    const data = await api('/api/picker/destination', {method: 'POST', headers: csrfHeaders(), body: '{}'});
    chosenDestination = data.destination;
    newProjectForm.querySelector('[name="destination_mode"][value="chosen"]').checked = true;
    output.textContent = `Project files will be created inside ${data.destination.path}. Choose PDF and create project when ready.`;
    announce(output.textContent);
  } catch (error) { output.textContent = error.message; announce(error.message); }
  finally { choosingDestination = false; button.disabled = false; updateProjectDestination(); button.focus(); }
});

document.getElementById('new-project-form')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (creatingProject || choosingDestination) return;
  const form = event.currentTarget;
  const output = document.getElementById('project-message');
  const button = form.querySelector('button[type="submit"]');
  let failed = false;
  try {
    const values = Object.fromEntries(new FormData(form));
    creatingProject = true;
    updateProjectDestination();
    const folder = document.querySelector('#project-destination-path code')?.textContent;
    output.textContent = `Choose the input PDF. Its original will be preserved; project files will be created at ${folder}. Conversion may take a few minutes.`;
    const result = await api('/api/projects/create', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values) });
    retainProjectWarning(result);
    output.textContent = `Project created at ${result.project.path}. Opening document…`;
    window.location.assign('/document');
  } catch (error) {
    failed = true;
    output.textContent = error.message;
    announce(error.message);
  } finally {
    creatingProject = false;
    updateProjectDestination();
    if (failed) {
      output.scrollIntoView({block: 'nearest'});
      button.focus({preventScroll: true});
    }
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

let sourceSelection = 0;
let sourceImageRequest = null;
let sourceObjectUrl = null;
async function loadSourcePageImage(url) {
  const image = document.getElementById('source-image');
  if (sourceImageRequest?.url !== url) sourceImageRequest?.controller.abort();
  if (image.dataset.loadedSourceUrl === url && image.complete && image.naturalWidth) return;
  if (sourceImageRequest?.url === url && !sourceImageRequest.controller.signal.aborted) return sourceImageRequest.promise;
  sourceImageRequest?.controller.abort();
  const request = {url, controller: new AbortController()};
  sourceImageRequest = request;
  request.promise = (async () => {
    const response = await fetch(url, {cache: 'no-store', signal: request.controller.signal});
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Source page request failed (${response.status}).`);
    }
    if (!response.headers.get('content-type')?.startsWith('image/')) throw new Error('The source-page response was not an image.');
    const blob = await response.blob();
    if (request.controller.signal.aborted) throw new DOMException('Source page changed', 'AbortError');
    const objectUrl = URL.createObjectURL(blob);
    if (sourceObjectUrl) URL.revokeObjectURL(sourceObjectUrl);
    sourceObjectUrl = objectUrl;
    image.src = objectUrl;
    try { await image.decode(); }
    catch (error) {
      if (request.controller.signal.aborted) throw new DOMException('Source page changed', 'AbortError');
      throw new Error('The rendered source-page image could not be read.');
    }
    if (request.controller.signal.aborted) throw new DOMException('Source page changed', 'AbortError');
    image.dataset.loadedSourceUrl = url;
  })();
  try { await request.promise; }
  finally { if (sourceImageRequest === request) sourceImageRequest = null; }
}

async function showSourcePage(page, card = selectedSourceCard) {
  const pane = document.querySelector('.source-pane');
  if (!pane) return;
  const selection = ++sourceSelection;
  const pageCount = Number(pane.dataset.pageCount || 1);
  const sourceKey = encodeURIComponent(pane.dataset.sourceKey || 'source');
  const requestedPage = Math.max(1, Math.min(pageCount, Number(page) || 1));
  document.querySelectorAll('.block-card').forEach((item) => item.classList.toggle('source-selected', item === card));
  const sourceImage = document.getElementById('source-image');
  sourceImage.alt = `Rendered source PDF page ${requestedPage}`;
  sourceImage.hidden = true;
  const sourceLink = document.getElementById('open-source-page');
  sourceLink.href = `/source.pdf?v=${sourceKey}#page=${requestedPage}`;
  sourceLink.textContent = `Open source PDF page ${requestedPage}`;
  document.getElementById('source-page-number').value = requestedPage;
  document.getElementById('source-page-previous').disabled = requestedPage === 1;
  document.getElementById('source-page-next').disabled = requestedPage === pageCount;
  const label = document.getElementById('source-page-label');
  const highlights = document.getElementById('source-highlights');
  const status = document.getElementById('source-page-render-status');
  const retry = document.getElementById('source-page-retry');
  const stage = document.querySelector('.source-image-stage');
  const retryFocused = document.activeElement === retry;
  highlights.replaceChildren();
  status.hidden = false;
  status.textContent = `Loading source page ${requestedPage}…`;
  retry.hidden = !retryFocused;
  retry.disabled = true;
  stage.setAttribute('aria-busy', 'true');
  label.textContent = `Source page ${requestedPage}. Waiting for its rendered image.`;
  try {
    await loadSourcePageImage(`/source-page/${requestedPage}.png?v=${sourceKey}`);
    if (selection !== sourceSelection) return;
    sourceImage.hidden = false;
    stage.setAttribute('aria-busy', 'false');
    status.hidden = true;
    retry.disabled = false;
    if (retryFocused) sourceLink.focus({preventScroll: true});
    retry.hidden = true;
  } catch (error) {
    if (selection !== sourceSelection || error.name === 'AbortError') return;
    stage.setAttribute('aria-busy', 'false');
    status.textContent = `Source page ${requestedPage} could not be displayed. ${error.message} Open the source PDF below to continue reviewing.`;
    retry.hidden = false;
    retry.disabled = false;
    if (retryFocused) retry.focus({preventScroll: true});
    label.textContent = `Source page ${requestedPage}. Its source region is not outlined.`;
    return;
  }
  if (!card || Number(card.dataset.page) !== requestedPage) {
    label.textContent = card
      ? `Source page ${requestedPage}. The selected block is on page ${card.dataset.page}; no region is outlined.`
      : `Source page ${requestedPage}. Select a block to outline its source region.`;
    return;
  }
  const blockLabel = `Block ${card.dataset.blockIndex}, ${card.dataset.sourceType}, on source page ${requestedPage}.`;
  const coverage = card.dataset.sourceCoverage ? ` ${card.dataset.sourceCoverage}` : '';
  label.textContent = blockLabel + coverage;
  if (!card.dataset.bboxes) return;
  try {
    const regions = JSON.parse(card.dataset.bboxes);
    const dimensions = await api(`/api/source-page/${requestedPage}`);
    if (selection !== sourceSelection) return;
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
    label.textContent = `${blockLabel} ${regions.length === 1 ? 'The approximate source region is' : `${regions.length} source regions are`} outlined.${coverage}`;
  } catch (error) {
    if (selection === sourceSelection) label.textContent = `${blockLabel} Its source region could not be outlined.`;
  }
}

async function selectSourceBlock(card) {
  const page = card.dataset.page;
  selectedSourceCard = card;
  sessionStorage.setItem(blockSelectionKey, card.id);
  updateBlockNavigation();
  if (!page || page === 'Unknown') return;
  await showSourcePage(page, card);
}

function blockCards() {
  return Array.from(document.querySelectorAll('.block-card')).filter(card => !card.hidden);
}

const blockFilter = document.getElementById('block-review-filter');
const blockFilterKey = `pdf-to-web-block-filter:${document.querySelector('.current-document')?.textContent || ''}`;
const blockSelectionKey = `${blockFilterKey}:selected`;
let selectedBlockFilter = 'all';
function applyBlockFilter() {
  if (!blockFilter) return;
  const cards = Array.from(document.querySelectorAll('.block-card'));
  const counts = { all: cards.length, approved: 0, pending: 0, excluded: 0 };
  for (const card of cards) {
    const status = card.dataset.reviewStatus;
    if (['unreviewed', 'needs_review'].includes(status)) counts.pending += 1;
    else if (status in counts) counts[status] += 1;
    card.hidden = selectedBlockFilter !== 'all' && (selectedBlockFilter === 'pending' ? !['unreviewed', 'needs_review'].includes(status) : status !== selectedBlockFilter);
  }
  blockFilter.querySelectorAll('[data-filter]').forEach(link => {
    link.querySelector('[data-filter-count]').textContent = `(${counts[link.dataset.filter]})`;
    if (link.dataset.filter === selectedBlockFilter) link.setAttribute('aria-current', 'true');
    else link.removeAttribute('aria-current');
  });
  document.getElementById('block-filter-count').textContent = `${blockCards().length} of ${cards.length} blocks`;
  if (selectedSourceCard?.hidden) {
    const index = cards.indexOf(selectedSourceCard);
    const replacement = cards.slice(index + 1).find(card => !card.hidden)
      || cards.slice(0, index).reverse().find(card => !card.hidden);
    selectedSourceCard = null;
    document.querySelectorAll('.source-selected').forEach(card => card.classList.remove('source-selected'));
    if (replacement) selectSourceBlock(replacement);
    else showSourcePage(document.getElementById('source-page-number')?.value || 1, null);
  }
  sessionStorage.setItem(blockFilterKey, selectedBlockFilter);
  updateBlockNavigation();
}
if (blockFilter) {
  const saved = sessionStorage.getItem(blockFilterKey);
  if (['all', 'approved', 'pending', 'excluded'].includes(saved)) selectedBlockFilter = saved;
  applyBlockFilter();
  blockFilter.querySelectorAll('[data-filter]').forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    selectedBlockFilter = link.dataset.filter;
    applyBlockFilter();
  }));
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
  if (position) position.textContent = index >= 0 ? `Block ${cards[index].dataset.blockIndex} · ${index + 1} of ${cards.length} shown`
    : cards.length ? 'No block selected. Use Next block to begin.'
      : document.querySelector('.block-card') ? '0 blocks shown' : 'No blocks are available.';
  const empty = document.getElementById('block-filter-empty');
  const emptyFilter = cards.length === 0 && !!document.querySelector('.block-card') && selectedBlockFilter !== 'all';
  if (empty) {
    empty.hidden = !emptyFilter;
    document.getElementById('block-filter-empty-message').textContent = emptyFilter
      ? selectedBlockFilter === 'pending' ? 'No items left to review in this filter.' : 'No blocks match this filter.'
      : '';
  }
  [previous, next].forEach(button => {
    if (!button) return;
    if (emptyFilter) button.setAttribute('aria-describedby', 'block-filter-empty-message');
    else button.removeAttribute('aria-describedby');
  });
}

document.getElementById('show-all-blocks')?.addEventListener('click', event => {
  event.preventDefault();
  const remembered = document.getElementById(sessionStorage.getItem(blockSelectionKey));
  selectedBlockFilter = 'all';
  applyBlockFilter();
  const target = remembered?.classList.contains('block-card') ? remembered : blockCards()[0];
  if (target) {
    selectSourceBlock(target);
    focusBlock(target);
  }
});

function focusEmptyBlockFilter() {
  const recovery = document.getElementById('show-all-blocks');
  if (blockCards().length || !recovery || recovery.closest('[hidden]')) return false;
  recovery.focus({preventScroll: true});
  recovery.scrollIntoView({block: 'center'});
  return true;
}

function focusBlock(card) {
  if (!card) return;
  if (card.hidden && blockFilter) { selectedBlockFilter = 'all'; applyBlockFilter(); }
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

document.getElementById('source-page-retry')?.addEventListener('click', () => {
  showSourcePage(document.getElementById('source-page-number').value, selectedSourceCard);
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

if (document.getElementById('source-image')) showSourcePage(1, null);

document.querySelectorAll('.block-card').forEach((card) => {
  card.addEventListener('click', () => selectSourceBlock(card));
  card.addEventListener('focusin', () => selectSourceBlock(card));
});

function selectDescription(card) {
  document.querySelectorAll('.complex-visual').forEach(visual => {
    const selected = visual === card;
    visual.classList.toggle('description-selected', selected);
    const notice = visual.querySelector('.description-selection-notice');
    if (notice) notice.hidden = !selected;
  });
}
document.querySelectorAll('.complex-visual').forEach(card => {
  card.addEventListener('focusin', () => selectDescription(card));
  card.addEventListener('click', () => selectDescription(card));
});
function focusLinkedBlock() {
  if (location.hash === '#image-description-tools') {
    const tools = document.getElementById('image-description-tools');
    const heading = document.getElementById('image-draft-heading');
    if (tools && heading) {
      tools.open = true;
      heading.focus({preventScroll: true});
      heading.scrollIntoView({block: 'start'});
    }
    return;
  }
  if (!location.hash.startsWith('#block-') && !location.hash.startsWith('#visual-')) return;
  const card = document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (card?.classList.contains('block-card')) {
    // A saved action/reload must not turn an empty chosen filter into All.
    // Explicit incoming block links still reveal their target as before.
    if (card.hidden && !blockCards().length && (pendingBlockId || performance.getEntriesByType('navigation')[0]?.type === 'reload')) return;
    selectDescription(null);
    focusBlock(card);
  }
  else if (card?.classList.contains('complex-visual')) {
    for (let parent = card.parentElement; parent; parent = parent.parentElement) {
      if (parent.tagName === 'DETAILS') parent.open = true;
    }
    selectDescription(card);
    card.focus({preventScroll: true});
    card.scrollIntoView({block: 'start'});
  }
}
document.addEventListener('click', event => {
  const link = event.target.closest('a[href]');
  if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  const target = new URL(link.href, location.href);
  if (target.pathname !== location.pathname || target.search !== location.search || (!target.hash.startsWith('#visual-') && target.hash !== '#image-description-tools')) return;
  event.preventDefault();
  if (target.hash !== location.hash) history.pushState(null, '', target.hash);
  focusLinkedBlock();
});
window.addEventListener('load', focusLinkedBlock, {once: true});
window.addEventListener('hashchange', focusLinkedBlock);

const reviewAdvanceKey = 'pdf-to-web-review-next-block';
const accessibilityParams = new URLSearchParams(location.search);
const accessibilityReturn = accessibilityParams.get('return_to') === 'accessibility';
const accessibilityBlock = accessibilityReturn ? decodeURIComponent(location.hash.slice(1)) : '';
function returnToAccessibility(card) {
  if (!accessibilityReturn || card?.id !== accessibilityBlock) return false;
  sessionStorage.removeItem(reviewAdvanceKey);
  const finding = accessibilityParams.get('finding') || '';
  location.assign(`/accessibility${finding ? '#finding-' + encodeURIComponent(finding) : ''}`);
  return true;
}
function focusAccessibilityFinding() {
  if (location.pathname !== '/accessibility' || !location.hash.startsWith('#finding-')) return;
  const target = document.getElementById(decodeURIComponent(location.hash.slice(1))) || document.getElementById('document-review-heading');
  if (!target) return;
  for (let parent = target.parentElement; parent; parent = parent.parentElement) if (parent.tagName === 'DETAILS') parent.open = true;
  target.focus({preventScroll: true});
  target.scrollIntoView({block: 'start'});
}
window.addEventListener('load', focusAccessibilityFinding, {once: true});
const pendingBlockId = sessionStorage.getItem(reviewAdvanceKey);
window.addEventListener('load', () => {
  if (!pendingBlockId && performance.getEntriesByType('navigation')[0]?.type === 'reload' && focusEmptyBlockFilter()) return;
  if (pendingBlockId || location.hash.startsWith('#block-') || location.hash.startsWith('#visual-') || location.hash === '#image-description-tools') return;
  const card = document.getElementById(sessionStorage.getItem(blockSelectionKey));
  if (!card?.classList.contains('block-card')) return;
  selectedSourceCard = card;
  applyBlockFilter();
  if (selectedSourceCard) focusBlock(selectedSourceCard);
}, {once: true});
if (pendingBlockId) {
  sessionStorage.removeItem(reviewAdvanceKey);
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  window.addEventListener('load', () => setTimeout(() => {
    if (location.hash === '#image-description-tools') return;
    // A reviewer who has entered provider setup keeps focus there.
    if (document.activeElement?.closest('#image-draft-toolbar')) return;
    if (focusEmptyBlockFilter()) return;
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
  if (form.dataset.saving === 'true') return;
  const values = Object.fromEntries(new FormData(form));
  const decorative = form.querySelector('input[name="decorative"]');
  if (decorative) values.decorative = decorative.checked;
  ['table_header_row', 'table_header_column', 'table_reviewed'].forEach((name) => {
    const checkbox = form.querySelector(`input[name="${name}"]`);
    if (checkbox) values[name] = checkbox.checked;
  });
  if (values.type === 'heading') values.level = Number(values.level);
  else delete values.level;
  const saveAndApprove = event.submitter?.hasAttribute('data-save-and-approve');
  try {
    if (saveAndApprove) {
      const otherDirty = authoringForms.find(other => other !== form && authoringBaselines.get(other) !== authoringValue(other));
      if (otherDirty) throw new Error('Save or undo changes in the other editor before saving and approving this block.');
      delete values.review_status;
    }
    form.dataset.saving = 'true';
    const saved = await api(`/api/blocks/${encodeURIComponent(form.dataset.blockId)}${saveAndApprove ? '/save-and-approve' : ''}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values) });
    if (returnToAccessibility(form.closest('.block-card'))) return;
    const owner = form.closest('.block-card');
    sessionStorage.removeItem(reviewAdvanceKey);
    if (owner) {
      sessionStorage.setItem(blockSelectionKey, owner.id);
      history.replaceState(null, '', location.pathname + location.search + '#' + encodeURIComponent(owner.id));
      if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    }
    announce(saveAndApprove ? 'Block saved and approved.' : saved.block_status === 'needs_review' ? 'Changes saved. Review the saved content, then approve it.' : 'Block saved.');
    window.location.reload();
  } catch (error) {
    const message = form.closest('.block-card')?.querySelector('.block-action-message');
    if (message) { message.textContent = error.message; message.hidden = false; }
    announce(error.message);
  } finally {
    delete form.dataset.saving;
  }
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
    const data = await api(`/api/complex-visuals/${encodeURIComponent(form.dataset.visualId)}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values) });
    message.textContent = `Saved.${data.block_status === 'needs_review' ? ' The linked image block needs approval.' : ''}`;
    const card = form.closest('.complex-visual');
    if (returnToAccessibility(card)) return;
    card.classList.toggle('visual-complete', data.visual.complete);
    card.classList.toggle('visual-pending', !data.visual.complete);
    const visualCards = document.querySelectorAll('.complex-visual');
    const pendingVisuals = document.querySelectorAll('.complex-visual.visual-pending').length;
    document.getElementById('visual-description-counts').textContent = `${pendingVisuals} to review · ${visualCards.length - pendingVisuals} complete or not applicable`;
    document.querySelectorAll('#undo-action, #reading-order-undo').forEach(undo => { undo.disabled = false; });
    document.querySelector('.review-history .undo-empty')?.remove();
    document.getElementById('structure-completion-region').innerHTML = data.completion_html;
    const counts = data.progress;
    document.getElementById('review-summary').outerHTML = data.review_summary_html;
    document.querySelector('.review-overall-status').textContent = counts.pending_tasks || !counts.total ? 'Review in progress' : 'Structure reviewed';
    document.querySelector('.review-overall-status').hidden = counts.pending_tasks === 0 && counts.total > 0;
    announce('Complex visual review saved.');
    for (const field of form.querySelectorAll('input, textarea')) field.defaultValue = values[field.name];
    form.elements.namedItem('status').value = data.visual.status;
    authoringBaselines.set(form, authoringValue(form));
    const state = form.closest('.complex-visual').querySelector('.visual-state');
    state.textContent = data.visual.label;
    card.querySelector('.description-context').textContent = data.visual.context;
    const linkedStatus = card.querySelector('.linked-image-status');
    if (linkedStatus && data.block_status) linkedStatus.textContent = data.block_status.replaceAll('_', ' ');
    for (const [selector, value] of [['.description-review-reason', data.visual.reason], ['.description-review-action', data.visual.action]]) {
      const text = card.querySelector(selector);
      text.textContent = value;
      text.hidden = !value;
    }
    const imageForm = form.dataset.blockId && document.querySelector(`.image-block-form[data-block-id="${CSS.escape(form.dataset.blockId)}"]`);
    if (imageForm) {
      const wasClean = authoringBaselines.get(imageForm) === authoringValue(imageForm);
      for (const [key, value] of Object.entries({alt: values.short_alt, long_description: values.long_description})) {
        const field = imageForm.elements.namedItem(key);
        if (field && field.value === field.defaultValue) { field.value = value; field.defaultValue = value; }
      }
      const review = imageForm.elements.namedItem('review_status');
      review.value = data.block_status;
      if (wasClean) authoringBaselines.set(imageForm, authoringValue(imageForm));
      const blockCard = imageForm.closest('.block-card');
      const old = blockCard.dataset.reviewStatus;
      blockCard.dataset.reviewStatus = data.block_status;
      blockCard.classList.replace(`status-${old}`, `status-${data.block_status}`);
      const badge = blockCard.querySelector('.block-status');
      badge.className = `block-status status-${data.block_status}`;
      badge.textContent = data.block_status.replaceAll('_', ' ');
      const exclude = blockCard.querySelector('[data-action="toggle-excluded"]');
      if (exclude) exclude.dataset.currentStatus = data.block_status;
      const approve = blockCard.querySelector('[data-action="approve"]');
      if (approve) approve.disabled = data.block_status === 'approved';
      applyBlockFilter();
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
    location.hash = 'finding-' + encodeURIComponent(form.dataset.itemId);
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
    if (action === 'approve') {
      const dirty = authoringForms.find(form => authoringBaselines.get(form) !== authoringValue(form));
      if (dirty) {
        dirty.closest('.block-card')?.querySelector('[data-save-and-approve]')?.focus();
        throw new Error('There are unsaved edits. Use Save and approve for the edited block, or save its other edited fields first.');
      }
    }
    await api(`/api/blocks/${encodeURIComponent(blockId)}/${action}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(body) });
    if (returnToAccessibility(button.closest('.block-card'))) return;
    if (['approve', 'flag', 'exclude', 'include'].includes(action)) {
      const currentCard = button.closest('.block-card');
      const nextId = nextReviewBlockId(currentCard);
      sessionStorage.setItem(reviewAdvanceKey, nextId || currentCard.id);
      if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    }
    announce('Review action saved.');
    window.location.reload();
  } catch (error) {
    announce(error.message);
    const message = button.closest('.block-card')?.querySelector('.block-action-message');
    if (message) { message.textContent = error.message; message.hidden = false; }
  }
}));

let undoInProgress = false;
document.querySelectorAll('#undo-action, #reading-order-undo').forEach(button => button.addEventListener('click', async () => {
  if (undoInProgress) return;
  undoInProgress = true;
  const controls = Array.from(document.querySelectorAll('#undo-action, #reading-order-undo'));
  const disabledStates = controls.map(control => control.disabled);
  controls.forEach(control => { control.disabled = true; });
  try {
    await api('/api/review/undo', { method: 'POST', headers: csrfHeaders(), body: '{}' });
    sessionStorage.removeItem(reviewAdvanceKey);
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    if (selectedSourceCard) history.replaceState(null, '', location.pathname + location.search + '#' + encodeURIComponent(selectedSourceCard.id));
    announce('Last action undone.');
    window.location.reload();
  } catch (error) {
    undoInProgress = false;
    controls.forEach((control, index) => { control.disabled = disabledStates[index]; });
    announce(error.message); alert(error.message);
  }
}));

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
let exportMutationPending = false;
function updateExportAvailability() {
  if (!exportForm) return;
  exportForm.querySelector('button[type="submit"]').disabled = exportMutationPending || exportForm.dataset.publicationReady !== 'true';
}
exportForm?.querySelector('[name="target"]')?.addEventListener('change', updateExportAvailability);
updateExportAvailability();

function setExportMutationPending(pending) {
  exportMutationPending = pending;
  for (const button of document.querySelectorAll('#media-wxr-form button, #media-mapping-form button, #media-export-undo')) {
    button.disabled = pending || (button.id === 'media-export-undo' && exportForm.dataset.conversionBlocked === 'true');
  }
  updateExportAvailability();
}
function applyExportReviewState(state) {
  document.getElementById('export-review-state').innerHTML = state.html;
  document.getElementById('unmapped-media').innerHTML = state.unmapped_html;
  exportForm.dataset.publicationReady = String(state.publication_ready);
  updateExportAvailability();
}

async function copyText(content) {
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
async function copyExportHtml(file) {
  const response = await fetch(file.url, {cache: 'no-store'});
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Could not read the exported HTML file.');
  }
  await copyText(await response.text());
}
document.getElementById('copy-page-title')?.addEventListener('click', async () => {
  const message = document.getElementById('copy-page-title-status');
  message.textContent = '';
  try { await copyText(document.getElementById('export-page-title').value); message.textContent = 'Copied'; announce('Page title copied.'); }
  catch (error) { message.textContent = 'Copy failed'; announce(error.message); }
});
exportForm?.querySelectorAll('[name="title_in_template"], [name="heading_style"]').forEach(field => field.addEventListener('change', invalidateContentExport));

exportForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const output = document.getElementById('export-result');
  try {
    const prefixField = document.querySelector('#media-export-form [name="image_prefix"]');
    if (prefixField && prefixField.value !== prefixField.defaultValue) throw new Error('Prepare the images ZIP and mapping CSV to save the new image prefix before exporting content.');
    const values = Object.fromEntries(new FormData(event.currentTarget));
    values.title_in_template = event.currentTarget.elements.title_in_template.checked;
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
      unresolved.textContent = data.media.unresolved ? `${data.media.unresolved} image${data.media.unresolved === 1 ? '' : 's'} require upload.` : '';
      media.append(unresolved, ` ${data.media.copied_assets} extracted asset${data.media.copied_assets === 1 ? '' : 's'} included.`);
    }
    const files = document.createElement('ul');
    const downloads = data.downloads || data.files.map((path) => ({ path, url: `/download/${path.split('/').map(encodeURIComponent).join('/')}` }));
    const hasTemplateBody = downloads.some(file => file.kind === 'template_body');
    downloads.forEach((file) => {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = file.url;
      link.download = '';
      link.textContent = file.kind === 'template_body' ? 'Download content for your template' : `Download ${file.path.split('/').pop()}`;
      const actions = document.createElement('span');
      actions.className = 'export-file-actions';
      actions.append(link);
      if (/\.html$/i.test(file.path) && (!hasTemplateBody || file.kind === 'template_body')) {
        const copyButton = document.createElement('button');
        copyButton.type = 'button';
        copyButton.className = 'secondary';
        copyButton.textContent = file.kind === 'template_body' ? 'Copy content for template' : 'Copy HTML';
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

function invalidateContentExport() {
  document.getElementById('export-result')?.replaceChildren();
}
function showMappingStatus(remaining) {
  const initialMissing = document.getElementById('unmapped-media');
  if (initialMissing) initialMissing.hidden = remaining === 0;
  document.getElementById('media-mapping-status').textContent = remaining
    ? `${remaining} images still need WordPress URLs. Unmapped images appear as upload placeholders in Gutenberg and WXR.`
    : 'All included images that need WordPress URLs are mapped.';
  invalidateContentExport();
}
function showMappingFeedback(message, data = {}) {
  const output = document.getElementById('media-mapping-result');
  output.hidden = false;
  const missing = [...(data.unmatched_images || []), ...(data.ambiguous_images || [])];
  output.className = `media-mapping-feedback${missing.length ? ' has-unmatched' : ''}`;
  document.getElementById('media-mapping-announcement').textContent = message;
  const detail = document.getElementById('media-mapping-details');
  detail.replaceChildren();
  const add = (parent, tag, text) => { const element = document.createElement(tag); element.textContent = text; parent.append(element); return element; };
  if (data.matched !== undefined) {
    const table = document.createElement('table'); table.className = 'result-table';
    add(table, 'caption', 'Media matching summary');
    const body = document.createElement('tbody');
    for (const [key, label] of [['matched', 'Matched'], ['unmatched', 'Unmatched'], ['ambiguous', 'Ambiguous']]) {
      const row = document.createElement('tr'); add(row, 'th', label).scope = 'row';
      add(row, 'td', String(data[key])).className = 'result-count'; body.append(row);
    }
    table.append(body); detail.append(table);
  }
  if (missing.length) {
    const wrap = document.createElement('div'); wrap.className = 'result-table-wrap';
    const table = document.createElement('table');
    add(table, 'caption', 'Images needing manual mapping');
    const head = document.createElement('thead'), headers = document.createElement('tr');
    for (const label of ['Filename and description', 'Source', 'Reason']) add(headers, 'th', label).scope = 'col';
    head.append(headers); table.append(head);
    const body = document.createElement('tbody');
    for (const image of missing) {
      const row = document.createElement('tr'), name = add(row, 'td', image.asset_filename || 'Filename unavailable');
      add(name, 'p', image.alt_text || 'No alternative text');
      const source = add(row, 'td', `Source page ${image.source_page || 'unknown'} `);
      const link = add(source, 'a', `Open block ${image.position || image.block_id}`);
      link.href = `/structure#block-${encodeURIComponent(image.block_id)}`;
      add(row, 'td', image.reason); body.append(row);
    }
    table.append(body); wrap.append(table); detail.append(wrap);
    add(detail, 'p', 'Enter the correct WordPress URLs for these images in the mapping CSV, then import it under “Map images manually with a CSV”.');
    const csv = add(detail, 'a', 'Download current mapping CSV');
    csv.href = '/download/output/wordpress/reports/media-mapping.csv'; csv.download = '';
  }
  output.focus({preventScroll: true}); output.scrollIntoView({block: 'start'}); announce(message);
}
const mediaExportForm = document.getElementById('media-export-form');
mediaExportForm?.querySelector('[name="image_prefix"]').addEventListener('input', () => {
  document.getElementById('media-export-result').replaceChildren();
  invalidateContentExport();
});
mediaExportForm?.addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const output = document.getElementById('media-export-result');
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  try {
    const data = await api('/api/media-export', {method: 'POST', headers: csrfHeaders(), body: JSON.stringify(Object.fromEntries(new FormData(form)))});
    const field = form.querySelector('[name="image_prefix"]');
    field.value = field.defaultValue = data.image_prefix;
    output.replaceChildren(document.createTextNode(`${data.media.copied_assets} images packaged. Unzip and upload them to WordPress, then map their URLs in step 2. `));
    for (const file of data.downloads) {
      const link = document.createElement('a');
      link.href = file.url; link.download = '';
      link.textContent = file.path.endsWith('.zip') ? 'Download all images ZIP' : 'Download mapping CSV';
      output.append(document.createElement('br'), link);
    }
    showMappingStatus(data.media.unresolved);
    announce('Images ZIP and mapping CSV are ready.');
  } catch (error) { output.textContent = error.message; announce(error.message); }
  finally { button.disabled = false; }
});
document.getElementById('media-export-undo')?.addEventListener('click', async () => {
  setExportMutationPending(true);
  try {
    const data = await api('/api/media-export/undo', {method: 'POST', headers: csrfHeaders(), body: '{}'});
    applyExportReviewState(data.export_state);
    const prefix = mediaExportForm.querySelector('[name="image_prefix"]');
    prefix.value = prefix.defaultValue = data.image_prefix;
    exportForm.elements.title_in_template.checked = data.publication.title_in_template ?? true;
    exportForm.elements.heading_style.value = data.publication.heading_style || 'nested';
    document.getElementById('export-page-title').value = data.page_title;
    document.getElementById('copy-page-title-status').textContent = '';
    document.getElementById('media-export-result').replaceChildren();
    document.getElementById('media-mapping-result').hidden = true;
    showMappingStatus(data.remaining);
    announce(`Last saved change undone. ${data.export_state.announcement}`);
  } catch (error) { announce(error.message); }
  finally { setExportMutationPending(false); document.getElementById('media-export-undo').focus(); }
});

document.getElementById('media-mapping-form')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const output = document.getElementById('media-mapping-result');
  const file = new FormData(event.currentTarget).get('mapping');
  setExportMutationPending(true);
  try {
    if (!(file instanceof File)) throw new Error('Choose a media mapping CSV.');
    const data = await api('/api/media-mapping', {
      method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ csv: await file.text() })
    });
    applyExportReviewState(data.export_state);
    showMappingFeedback(`${data.mapped} image mapping${data.mapped === 1 ? '' : 's'} imported; ${data.remaining} images still need URLs. ${data.export_state.announcement}`, data);
    showMappingStatus(data.remaining);
  } catch (error) { showMappingFeedback(error.message); }
  finally { setExportMutationPending(false); }
});

document.getElementById('media-wxr-form')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const output = document.getElementById('media-mapping-result');
  const file = new FormData(event.currentTarget).get('media_wxr');
  setExportMutationPending(true);
  try {
    if (!(file instanceof File)) throw new Error('Choose a WordPress media XML file.');
    const data = await api('/api/media-mapping-wxr', {
      method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ xml: await file.text() })
    });
    applyExportReviewState(data.export_state);
    showMappingFeedback(`${data.matched} image mapping${data.matched === 1 ? '' : 's'} matched; ${data.unmatched} unmatched and ${data.ambiguous} ambiguous. ${data.export_state.announcement}`, data);
    showMappingStatus(data.remaining);
  } catch (error) { showMappingFeedback(error.message); }
  finally { setExportMutationPending(false); }
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
  const postDraft = (action, data) => { if (['populate', 'associate', 'edit', 'apply', 'reject', 'cancel'].includes(action) || action === 'import' && data.commit) requireSavedAuthoring(); return api(`/api/image-drafts/${action}`, {method: 'POST', headers: csrfHeaders(), body: JSON.stringify({document_id: docId, ...data})}); };
  const panelFor = id => [...document.querySelectorAll('.image-draft-panel')].find(p => p.dataset.blockId === id);
  const reloadDraft = id => { requireSavedAuthoring(); if (id) sessionStorage.setItem(reviewAdvanceKey, `block-${id}`); location.reload(); };
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
    const saved = document.createElement('p'); saved.className = 'draft-saved-path';
    const location = document.createElement('code'); location.textContent = result.saved_path;
    saved.append('Saved in this project: ', location);
    document.getElementById('draft-downloads').replaceChildren(saved, link);
    message.textContent = 'Drafting request ZIP saved. Download a copy to attach to your drafting tool. This is not a publication export; imported descriptions still need manual approval.';
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
    try { requireSavedAuthoring(); const result = await postDraft('import', {response: importPayload, commit: true});
      if (!result.valid_count) throw new Error(result.findings.map(f => f.error).join(' '));
      reloadDraft();
    } catch (error) { message.textContent = error.message; }
  });
  document.getElementById('draft-populate').addEventListener('click', async () => {
    try { requireSavedAuthoring(); await postDraft('populate', {}); reloadDraft(); } catch (error) { message.textContent = error.message; }
  });
  document.getElementById('draft-refresh').addEventListener('click', () => { try { reloadDraft(); } catch (error) { message.textContent = error.message; announce(error.message); } });
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
