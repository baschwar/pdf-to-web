const authoringForms = [...document.querySelectorAll('.block-form, .complex-visual-form')];
let reviewWriteBusy = false;
let reviewReloadRequired = false;
let reviewClickLockUntil = 0;
const boundBlockForms = new WeakSet();
const boundPreviewAreas = new WeakSet();
const authoringValue = form => JSON.stringify([...form.querySelectorAll('input:not([name="expected_review_token"]), textarea, select')].map(field => [field.name, field.type === 'checkbox' ? field.checked : field.value]));
const authoringBaselines = new WeakMap(authoringForms.map(form => [form, authoringValue(form)]));

function updateSourcePageReview(page) {
  const pane = document.querySelector('.source-pane'), pill = document.getElementById('source-page-review-status');
  if (!pane || !pill) return;
  page = Number(page || document.getElementById('manual-reconstruction-control')?.dataset.sourcePage || document.getElementById('source-page-number')?.value || 1);
  const raw = pane.dataset.pageReviews || '{}';
  if (pane.reviewStatuses?.raw !== raw) {
    try { pane.reviewStatuses = {raw, pages: JSON.parse(raw)}; }
    catch { pane.reviewStatuses = {raw, pages: {}}; }
  }
  const saved = pane.reviewStatuses.pages[String(page)];
  const status = reviewReloadRequired || !saved ? {state: 'needs', label: 'Needs review', detail: `Source page ${page}: review status cannot be confirmed. Reload to inspect saved decisions.`} : saved;
  if (pill.textContent !== status.label) pill.textContent = status.label;
  pill.dataset.state = status.state; pill.dataset.page = String(page);
  pill.title = status.detail; pill.setAttribute('aria-label', status.detail); pill.hidden = false;
  updateSourcePageVisualReviews(page);
}

function updateSourcePageVisualReviews(page) {
  const pane = document.querySelector('.source-pane'), section = document.getElementById('source-page-visual-reviews');
  if (!pane || !section) return;
  const raw = pane.dataset.sourceVisuals || '{}', key = `${page}:${raw}`;
  if (section.dataset.reviewKey === key) return;
  section.dataset.reviewKey = key;
  let items = [];
  try { items = JSON.parse(raw)[String(page)] || []; } catch {}
  section.hidden = !items.length;
  section.querySelector('ul').replaceChildren();
  section.querySelector('p').textContent = `${items.length} visual review check${items.length === 1 ? '' : 's'} still need a decision on source page ${page}. Block approval does not resolve these accessibility requirements.`;
  for (const item of items) {
    const li = document.createElement('li'), link = document.createElement('a');
    link.href = '#' + encodeURIComponent(item.target); link.textContent = item.label + ' — Open description';
    li.append(link); section.querySelector('ul').append(li);
  }
}

function receiveSourcePageVisualReviews(reviews) {
  const pane = document.querySelector('.source-pane');
  if (pane && reviews) pane.dataset.sourceVisuals = JSON.stringify(reviews);
  updateSourcePageVisualReviews(Number(document.getElementById('source-page-number')?.value || 1));
}

const boundVisualReferences = new WeakSet();
function initializeVisualReference(figure) {
  if (boundVisualReferences.has(figure)) return;
  boundVisualReferences.add(figure);
  const img = figure.querySelector('img'), error = figure.querySelector('.visual-reference-error'), retry = figure.querySelector('.visual-reference-retry');
  const original = img.getAttribute('src');
  const state = failed => { figure.setAttribute('aria-busy', 'false'); img.hidden = failed; error.hidden = !failed; retry.hidden = !failed; };
  figure.setAttribute('aria-busy', 'true');
  img.addEventListener('load', () => state(false)); img.addEventListener('error', () => state(true));
  retry.addEventListener('click', () => { const url = new URL(original, location.href); url.searchParams.set('retry', Date.now()); img.hidden = false; error.hidden = true; retry.hidden = true; figure.setAttribute('aria-busy', 'true'); img.src = url.href; });
  if (img.complete) state(img.naturalWidth === 0);
}
document.querySelectorAll('.visual-source-reference').forEach(initializeVisualReference);

function receiveSourcePageReviews(reviews, page) {
  const pane = document.querySelector('.source-pane');
  if (pane && reviews) pane.dataset.pageReviews = JSON.stringify(reviews);
  updateSourcePageReview(page);
}

function updateAuthoringFeedback() {
  updateSourcePageReview();
  const dirtyCards = new Set(authoringForms.filter(form => authoringBaselines.get(form) !== authoringValue(form)).map(form => form.closest('.block-card')));
  document.querySelectorAll('.block-card').forEach(card => {
    const help = card.querySelector('.block-review-dirty-help');
    if (!help) return;
    const dirty = dirtyCards.has(card);
    const text = dirty ? 'Unsaved changes — Save & Approve saves all edited review fields in this block before approval.' : '';
    if (help.textContent !== text) help.textContent = text;
    help.hidden = !dirty;
    const approve = card.querySelector('.block-review-actions [data-action="approve"]');
    if (approve) {
      if (!approve.dataset.saving) {
        approve.textContent = dirty ? 'Save & Approve' : 'Approve';
        approve.setAttribute('aria-label', `${dirty ? 'Save and approve' : 'Approve'} block ${card.dataset.blockIndex}`);
      }
      approve.disabled = reviewWriteBusy || reviewReloadRequired || (!dirty && approve.dataset.approvalComplete === 'true');
      if (dirty) approve.setAttribute('aria-describedby', help.id);
      else approve.removeAttribute('aria-describedby');
    }
  });
}
for (const event of ['input', 'change']) document.addEventListener(event, e => {
  if (e.target.closest('.block-form, .complex-visual-form')) updateAuthoringFeedback();
});
updateAuthoringFeedback();
function initializeBlockContentModes(area) {
  if (boundPreviewAreas.has(area)) {
    area.querySelector('[role="tablist"]').hidden = false;
    return;
  }
  boundPreviewAreas.add(area);
  const tabs = [...area.querySelectorAll('[role="tab"]')];
  const card = area.closest('.block-card');
  const status = area.querySelector('.block-preview-status');
  const frame = area.querySelector('iframe');
  let previewSizeObserver;
  let resizePreview = () => {};
  frame.addEventListener('load', () => {
    previewSizeObserver?.disconnect();
    const body = frame.contentDocument?.body;
    if (!body) return;
    const resize = () => {
      if (!frame.offsetWidth) return;
      // Use the content box, not viewport scrollHeight, so a narrow preview
      // can both grow and shrink without introducing an inner scrolling field.
      frame.style.height = `${Math.max(1, Math.ceil(body.getBoundingClientRect().height))}px`;
    };
    resizePreview = resize;
    previewSizeObserver = new ResizeObserver(resize);
    previewSizeObserver.observe(body);
    resize();
  });
  const updateStatus = () => {
    const dirty = [...card.querySelectorAll('.block-form')].some(form => authoringBaselines.get(form) !== authoringValue(form));
    status.textContent = dirty ? 'Saved content. Unsaved changes are not shown.' : 'Saved content.';
  };
  const select = tab => {
    tabs.forEach(item => {
      const active = item === tab;
      item.setAttribute('aria-selected', String(active));
      item.tabIndex = active ? 0 : -1;
      document.getElementById(item.getAttribute('aria-controls')).hidden = !active;
    });
    updateStatus();
    if (tab === tabs[1]) {
      if (!frame.hasAttribute('srcdoc')) frame.srcdoc = frame.dataset.savedPreview;
      else resizePreview();
    }
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => select(tab));
    tab.addEventListener('keydown', event => {
      let target;
      if (event.key === 'ArrowRight') target = tabs[(index + 1) % tabs.length];
      if (event.key === 'ArrowLeft') target = tabs[(index + tabs.length - 1) % tabs.length];
      if (event.key === 'Home') target = tabs[0];
      if (event.key === 'End') target = tabs.at(-1);
      if (!target) return;
      event.preventDefault(); select(target); target.focus();
    });
  });
  area.addEventListener('input', updateStatus);
  area.addEventListener('change', updateStatus);
  area.querySelector('[role="tablist"]').hidden = false;
}
document.querySelectorAll('.block-content-modes').forEach(initializeBlockContentModes);
let mergeInProgress = false;
let mergeSnapshotStale = false;
function mergeDisabledReason(button) {
  if (button.dataset.mergeReason) return button.dataset.mergeReason;
  if (mergeSnapshotStale) return 'Reload Structure to check the current blocks before merging.';
  if (mergeInProgress) return 'Finishing the merge…';
  if (authoringForms.some(form => form.dataset.saving === 'true')) return 'Finish saving before merging.';
  if (authoringForms.some(form => authoringBaselines.get(form) !== authoringValue(form))) {
    return 'Save or revert unsaved edits before merging.';
  }
  const following = document.getElementById('block-' + button.dataset.nextBlockId);
  if (following?.hidden) return 'The next block is hidden by this filter. Show All before merging.';
  return '';
}
function updateMergeControls() {
  for (const button of document.querySelectorAll('[data-action="merge"]')) {
    // A running older server can serve new JavaScript before it is relaunched.
    // Keep its disabled controls and require the updated saved-state metadata.
    if (!button.hasAttribute('data-merge-reason')) {
      let help = document.getElementById(button.getAttribute('aria-describedby'));
      button.dataset.mergeReason = button.disabled && help?.textContent.trim()
        || 'Relaunch PDF to Web to use the updated merge controls.';
      if (!help) {
        help = document.createElement('small'); help.className = 'merge-help';
        help.id = 'merge-help-' + button.dataset.blockId;
        button.setAttribute('aria-describedby', help.id);
        button.closest('.block-actions')?.append(help);
      }
    }
    const reason = mergeDisabledReason(button);
    button.disabled = Boolean(reason);
    const help = document.getElementById(button.getAttribute('aria-describedby'));
    if (help) {
      help.textContent = reason; help.hidden = !reason;
      // A live save/draft/stale-state blocker keeps the original status size.
      help.classList.toggle('helper-text', reason === button.dataset.mergeReason);
    }
  }
}
for (const eventName of ['input', 'change']) document.addEventListener(eventName, event => {
  if (event.target.closest('.block-form, .complex-visual-form')) updateMergeControls();
});
const quitForms = [...document.querySelectorAll('form')].filter(form => form.id !== 'source-page-controls');
const quitValue = form => JSON.stringify([...form.querySelectorAll('input:not([readonly]):not([type="hidden"]), textarea:not([readonly]), select')].map(field => [field.name, field.type === 'file' ? [...field.files].map(f => [f.name, f.size, f.lastModified]) : field.type === 'checkbox' || field.type === 'radio' ? field.checked : field.value]));
const quitBaselines = new WeakMap(quitForms.map(form => [form, quitValue(form)]));
const resetQuitForm = form => { if (form) quitBaselines.set(form, quitValue(form)); };
let appRequestsActive = 0;
let quitRequested = false;

const bulkReview = document.querySelector('#bulk-review[data-review-token]');
if (bulkReview) {
  const filter = document.getElementById('bulk-review-filter');
  const visibility = document.getElementById('bulk-review-visibility');
  const reviewScope = () => visibility?.value || 'all';
  const viewLabel = () => visibility ? visibility.options[visibility.selectedIndex].text : 'All records';
  const all = document.getElementById('bulk-review-select-all');
  const state = document.getElementById('bulk-review-state');
  const apply = document.getElementById('bulk-review-apply');
  const confirm = document.getElementById('bulk-review-confirm');
  const confirmation = document.getElementById('bulk-review-confirmation');
  const message = document.getElementById('bulk-review-message');
  const selectors = [...bulkReview.querySelectorAll('.bulk-review-select')];
  const visible = () => selectors.filter(box => !box.closest('.bulk-review-row').hidden && !box.closest('.bulk-review-group').hidden);
  const selected = () => visible().filter(box => box.checked);
  let pendingBatch = null;
  const labels = {approved: 'Approved — block or accessibility decision', needs_review: 'Needs review — blocks', excluded: 'Excluded', reviewed: 'Reviewed — descriptions', reclassified: 'Awaiting review — descriptions', not_applicable: 'Not applicable', unresolved: 'Unresolved — accessibility decisions'};
  function selectionChanged() {
    pendingBatch = null; confirm.hidden = true; confirmation.hidden = true;
    const choices = selected();
    const kinds = new Set(choices.map(box => box.dataset.kind));
    const prior = state.value;
    state.replaceChildren();
    if (choices.length && kinds.size === 1) {
      for (const value of JSON.parse(choices[0].dataset.states)) {
        const option = document.createElement('option'); option.value = value; option.textContent = labels[value]; state.append(option);
      }
      if ([...state.options].some(option => option.value === prior)) state.value = prior;
    } else {
      const option = document.createElement('option'); option.value = ''; option.textContent = choices.length ? 'Select one record type' : 'Select records first'; state.append(option);
    }
    state.disabled = !choices.length || kinds.size !== 1;
    apply.disabled = state.disabled;
    const descriptions = choices.reduce((count, box) => count + Number(box.dataset.descriptionCount || 0), 0);
    document.getElementById('bulk-review-selection').textContent = `${choices.length} selected${descriptions ? `; image approval also reviews ${descriptions} associated descriptions shown below` : ''}${kinds.size > 1 ? '. Select one record type to choose a review state.' : ''}`;
    all.checked = visible().length > 0 && choices.length === visible().length;
    all.indeterminate = choices.length > 0 && choices.length < visible().length;
  }
  selectors.forEach(box => box.addEventListener('change', selectionChanged));
  all.addEventListener('change', () => { for (const box of visible()) box.checked = all.checked; selectionChanged(); });
  function filterRecords(changed = false) {
    for (const box of selectors) box.checked = false;
    for (const row of bulkReview.querySelectorAll('.bulk-review-row')) {
      row.hidden = Boolean(filter.value && row.dataset.classification !== filter.value)
        || reviewScope() !== 'all' && (row.dataset.pending === 'true') !== (reviewScope() === 'pending');
    }
    for (const group of bulkReview.querySelectorAll('.bulk-review-group')) group.hidden = !group.querySelector('.bulk-review-row:not([hidden])');
    const count = document.getElementById('bulk-review-visible-count');
    if (count) count.textContent = `${visible().length} of ${selectors.length} saved records shown · ${viewLabel()}${filter.value ? ` · ${filter.value}` : ''}`;
    const empty = document.getElementById('bulk-review-empty');
    if (empty) {
      empty.hidden = visible().length !== 0;
      empty.textContent = reviewScope() === 'pending'
        ? 'No pending saved records in this view. Completed records remain available in Show records.' : 'No saved records match this view.';
    }
    if (changed) message.textContent = 'Review view changed. Selection cleared.';
    selectionChanged();
  }
  filter.addEventListener('change', () => filterRecords(true));
  visibility?.addEventListener('change', () => filterRecords(true));
  filterRecords();
  state.addEventListener('change', () => { pendingBatch = null; confirm.hidden = true; confirmation.hidden = true; });
  apply.addEventListener('click', () => {
    const choices = selected();
    if (!choices.length || state.disabled) return;
    pendingBatch = {project_id: bulkReview.dataset.projectId, expected_review_token: bulkReview.dataset.reviewToken, classification: filter.value, review_scope: reviewScope(), visible_ids: visible().map(box => box.value), selected_ids: choices.map(box => box.value), status: state.value};
    confirmation.textContent = `Apply ${labels[state.value]} to ${choices.length} selected ${choices[0].dataset.kind} records in ${viewLabel()} · ${filter.value || 'All classifications'}? ${document.getElementById('bulk-review-selection').textContent}. The entire batch must pass validation before saving.`;
    confirmation.hidden = false; confirm.hidden = false; confirm.focus();
  });
  confirm.addEventListener('click', async () => {
    if (!pendingBatch) return;
    confirm.disabled = true; apply.disabled = true;
    try {
      const result = await api('/api/accessibility/bulk-review', {method: 'POST', headers: csrfHeaders(), body: JSON.stringify(pendingBatch)});
      announce(`${result.applied} selected review records saved. One Undo restores this batch.`);
      location.hash = 'bulk-review-heading'; window.location.reload();
    } catch (error) { message.textContent = error.message; announce(error.message); }
    finally { confirm.disabled = false; apply.disabled = state.disabled; }
  });
  document.getElementById('bulk-review-undo').addEventListener('click', async () => {
    try { await api('/api/review/undo', {method: 'POST', headers: csrfHeaders(), body: '{}'}); location.hash = 'bulk-review-heading'; window.location.reload(); }
    catch (error) { message.textContent = error.message; announce(error.message); }
  });
}
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

// A write can finish while its response stalls. Bound the wait, preserve fields
// and require reload through the uncertain-save guard; never retry the write.
const reviewSaveSignal = () => AbortSignal.timeout(30000);
const reviewRefreshRecovery = message => message.startsWith('Saved,') ? message : 'Saved, but the review display could not be refreshed. Your fields remain here. Reload Structure before making another change.';

async function api(url, options = {}) {
  const lifecycleRequest = ['/api/lifecycle', '/api/quit'].includes(url);
  if (quitRequested && !lifecycleRequest) throw new Error('PDF to Web is quitting. New work is unavailable.');
  if (!lifecycleRequest) appRequestsActive += 1;
  try {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok || data.status === 'error') {
      const error = new Error(data.error || data.detail || 'Request failed');
      error.status = response.status;
      error.confirmedRejection = response.status < 500;
      throw error;
    }
    return data;
  } catch (error) {
    // Browser abort exceptions have read-only messages. Normalize them so save
    // handlers can provide actionable uncertain-write recovery instructions.
    if (error.name === 'AbortError' || error.name === 'TimeoutError') throw new Error('Request result could not be confirmed.');
    throw error;
  } finally { if (!lifecycleRequest) appRequestsActive -= 1; }
}

const quitDialog = document.getElementById('quit-dialog');
const quitOpen = document.getElementById('quit-open');
const quitConfirm = document.getElementById('quit-confirm');
const quitStatus = document.getElementById('quit-status');
const quitCancel = document.getElementById('quit-cancel');
function unsavedQuitForms() {
  return quitForms.filter(form => authoringBaselines.has(form)
    ? authoringBaselines.get(form) !== authoringValue(form)
    : quitBaselines.get(form) !== quitValue(form));
}
quitOpen?.addEventListener('click', async () => {
  quitConfirm.disabled = true;
  quitStatus.textContent = 'Checking this app’s running work…';
  const dirty = unsavedQuitForms().length;
  document.getElementById('quit-edits').textContent = dirty ? 'This tab has unsaved edits or choices. Keep working to save them, or explicitly quit without saving.' : 'No unsaved edits detected in this tab. Check other open tabs before quitting.';
  quitConfirm.textContent = dirty ? 'Quit without saving' : 'Quit PDF to Web';
  quitDialog.showModal(); quitCancel.focus();
  try {
    const state = await api('/api/lifecycle');
    quitStatus.textContent = !state.available ? 'Quit is unavailable for this externally managed server. Stop its own launcher instead.'
      : state.state === 'stopping' ? 'Quit has already been requested. Waiting for this app to stop…'
      : state.error || (state.active_work || appRequestsActive ? 'Work is still in progress. Keep working until it finishes, then try Quit again.' : 'This app is ready to quit.');
    quitConfirm.disabled = !state.available || state.active_work > 0 || appRequestsActive > 0 || state.state === 'stopping';
  } catch { quitStatus.textContent = 'Could not check the app. Keep working and retry Quit when the connection is available.'; }
});
quitCancel?.addEventListener('click', () => quitDialog.close());
quitDialog?.addEventListener('close', () => { if (!quitRequested) quitOpen.focus({preventScroll: true}); });
quitDialog?.addEventListener('cancel', event => { if (quitRequested) event.preventDefault(); });
async function confirmQuitStopped(error) {
  // An accepted Quit followed by repeated loss of the local server supports
  // completion. HTTP errors, offline browsers and timeouts remain uncertain.
  if (!(error instanceof TypeError) || navigator.onLine === false) {
    throw new Error('Could not confirm that PDF to Web stopped. Check the connection, then retry Quit or stop its own launcher.');
  }
  for (let attempt = 0; attempt < 2; attempt += 1) {
    await new Promise(resolve => setTimeout(resolve, 250));
    if (navigator.onLine === false) throw new Error('Could not confirm that PDF to Web stopped while the browser is offline. Check the connection, then retry Quit or stop its own launcher.');
    try {
      await fetch('/api/health', {cache: 'no-store', signal: AbortSignal.timeout(1500)});
      return false; // Any HTTP response means the server is still responding.
    } catch (probeError) {
      if (!(probeError instanceof TypeError) || navigator.onLine === false) {
        throw new Error('Could not confirm that PDF to Web stopped. Check the connection, then retry Quit or stop its own launcher.');
      }
    }
  }
  return true;
}
function showQuitStopped() {
  const message = 'PDF to Web has stopped. It’s safe to close this browser tab or window.';
  quitDialog.dataset.state = 'stopped';
  const heading = document.getElementById('quit-heading');
  heading.textContent = 'PDF to Web has stopped'; heading.tabIndex = -1;
  for (const id of ['quit-warning', 'quit-edits', 'quit-launcher-note']) document.getElementById(id).hidden = true;
  document.getElementById('quit-actions').remove();
  quitOpen.disabled = true;
  quitDialog.setAttribute('aria-describedby', 'quit-status');
  quitStatus.textContent = message;
  heading.focus({preventScroll: true});
  announce(message);
}
quitConfirm?.addEventListener('click', async () => {
  if (appRequestsActive) { quitStatus.textContent = 'A request is still in progress. Wait for it to finish before quitting.'; return; }
  quitConfirm.disabled = true; quitCancel.disabled = true;
  quitStatus.textContent = 'Requesting Quit…';
  try {
    await api('/api/quit', {method: 'POST', headers: csrfHeaders(), body: JSON.stringify({confirm: true})});
    quitRequested = true;
    quitStatus.textContent = 'Waiting for this app’s server to stop…';
    for (let attempt = 0; attempt < 10; attempt += 1) {
      await new Promise(resolve => setTimeout(resolve, 250));
      let state;
      try { state = await api('/api/lifecycle'); }
      catch (error) {
        if (await confirmQuitStopped(error)) { showQuitStopped(); return; }
        continue;
      }
      if (state.error || state.state !== 'stopping') throw new Error(state.error || 'The server did not stop. Keep working and retry Quit.');
    }
    throw new Error('The server is still responding. Keep working and retry Quit or stop its own launcher.');
  } catch (error) {
    quitRequested = false; quitConfirm.disabled = false; quitCancel.disabled = false;
    quitStatus.textContent = error.message; announce(error.message);
  }
});

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
function revealSourceRegions(pane, highlights) {
  // Scroll the source panel itself, preserving the reviewer's editor/card focus.
  if (!pane || !highlights?.children.length || getComputedStyle(pane).overflowY !== 'auto') return;
  const bounds = pane.getBoundingClientRect();
  const top = bounds.top + pane.clientTop;
  const bottom = top + pane.clientHeight;
  const regions = Array.from(highlights.children, region => region.getBoundingClientRect());
  const first = Math.min(...regions.map(region => region.top));
  const last = Math.max(...regions.map(region => region.bottom));
  if (first < top + 8) pane.scrollTop += first - top - 8;
  else if (last > bottom - 8) {
    pane.scrollTop += last - first > pane.clientHeight - 16 ? first - top - 8 : last - bottom + 8;
  }
}
window.addEventListener('resize', () => requestAnimationFrame(() =>
  revealSourceRegions(document.querySelector('.source-pane'), document.getElementById('source-highlights'))));
async function loadSourcePageImage(url) {
  const image = document.getElementById('source-image');
  if (sourceImageRequest?.url !== url) sourceImageRequest?.controller.abort();
  if (image.dataset.loadedSourceUrl === url && image.complete && image.naturalWidth) return;
  if (sourceImageRequest?.url === url && !sourceImageRequest.controller.signal.aborted) return sourceImageRequest.promise;
  sourceImageRequest?.controller.abort();
  const request = {url, controller: new AbortController()};
  sourceImageRequest = request;
  const work = (async () => {
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
  let abortListener;
  const aborted = new Promise((resolve, reject) => {
    abortListener = () => reject(request.controller.signal.reason || new DOMException('Source page changed', 'AbortError'));
    request.controller.signal.addEventListener('abort', abortListener, {once: true});
  });
  const deadline = setTimeout(() => request.controller.abort(new DOMException('Source page response timed out. Retry or open the source PDF.', 'TimeoutError')), 30000);
  request.promise = Promise.race([work, aborted]);
  try { await request.promise; }
  finally {
    clearTimeout(deadline);
    request.controller.signal.removeEventListener('abort', abortListener);
    if (sourceImageRequest === request) sourceImageRequest = null;
  }
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
  const sourceUrl = `/source-page/${requestedPage}.png?v=${sourceKey}`;
  const sameRenderedPage = sourceImage.dataset.loadedSourceUrl === sourceUrl && sourceImage.complete && sourceImage.naturalWidth && !sourceImage.hidden;
  const previousSourceHeight = sourceImage.parentElement.getBoundingClientRect().height;
  sourceImage.parentElement.style.minHeight = previousSourceHeight > 2 ? `${previousSourceHeight}px` : '';
  sourceImage.alt = `Rendered source PDF page ${requestedPage}`;
  if (!sameRenderedPage) sourceImage.hidden = true;
  const sourceLink = document.getElementById('open-source-page');
  sourceLink.href = `/source.pdf?v=${sourceKey}#page=${requestedPage}`;
  sourceLink.textContent = `Open source PDF page ${requestedPage}`;
  document.getElementById('source-page-number').value = requestedPage;
  updateManualReconstruction(requestedPage);
  updateSourcePageReview(requestedPage);
  document.getElementById('source-page-previous').disabled = requestedPage === 1;
  document.getElementById('source-page-next').disabled = requestedPage === pageCount;
  const label = document.getElementById('source-page-label');
  const regionStatus = document.getElementById('source-region-status');
  const selectedOnPage = card && Number(card.dataset.page) === requestedPage;
  const blockType = selectedOnPage && card.dataset.filterType !== 'other' ? card.dataset.filterType : card?.dataset.sourceType;
  const blockLabel = selectedOnPage ? `Block ${card.dataset.blockIndex} · ${String(blockType || 'block').replace(/^./, char => char.toUpperCase())} · Page ${requestedPage}` : `Page ${requestedPage}`;
  const coverage = selectedOnPage && card.dataset.sourceCoverage ? ` ${card.dataset.sourceCoverage}` : '';
  label.textContent = blockLabel + coverage;
  regionStatus.textContent = selectedOnPage ? 'Checking its source region…' : 'Select a block to outline its source region.';
  const highlights = document.getElementById('source-highlights');
  const status = document.getElementById('source-page-render-status');
  const retry = document.getElementById('source-page-retry');
  const stage = document.querySelector('.source-image-stage');
  const retryFocused = document.activeElement === retry;
  highlights.replaceChildren();
  status.hidden = sameRenderedPage;
  status.textContent = `Loading source page ${requestedPage}…`;
  retry.hidden = !retryFocused;
  retry.disabled = true;
  stage.setAttribute('aria-busy', 'true');
  try {
    await loadSourcePageImage(sourceUrl);
    if (selection !== sourceSelection) return;
    sourceImage.hidden = false;
    stage.style.minHeight = '';
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
    regionStatus.textContent = 'Its source region is not outlined.';
    return;
  }
  if (!card || Number(card.dataset.page) !== requestedPage) {
    regionStatus.textContent = card
      ? `The selected block is on page ${card.dataset.page}; no region is outlined.`
      : 'Select a block to outline its source region.';
    return;
  }
  if (!card.dataset.bboxes) { regionStatus.textContent = 'No reliable source region is available for this block.'; return; }
  try {
    const regions = JSON.parse(card.dataset.bboxes);
    if (!regions.length) { regionStatus.textContent = 'No reliable source region is available for this block.'; return; }
    const dimensions = await api(`/api/source-page/${requestedPage}`, {signal: AbortSignal.timeout(10000)});
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
    regionStatus.textContent = regions.length === 1 ? 'Approximate outline' : `Approximate outlines (${regions.length})`;
    revealSourceRegions(pane, highlights);
  } catch (error) {
    if (selection === sourceSelection) regionStatus.textContent = 'Its source region could not be outlined.';
  }
}

async function selectSourceBlock(card) {
  const page = card.dataset.page;
  selectedSourceCard = card;
  sessionStorage.setItem(blockSelectionKey, card.id);
  updateBlockNavigation();
  if (!page || page === 'Unknown') return;
  await showSourcePage(page, card);
  // On narrow screens the source image grows above Reading order after loading.
  // Resettle only the still-focused card; never move a reviewer to an old selection.
  if (selectedSourceCard === card && document.activeElement === card && !card.hidden) {
    requestAnimationFrame(() => {
      if (selectedSourceCard === card && document.activeElement === card && !card.hidden) card.scrollIntoView({block: 'start'});
    });
  }
}

function blockCards() {
  return Array.from(document.querySelectorAll('.block-card')).filter(card => !card.hidden);
}

const blockFilter = document.getElementById('block-review-filter');
const blockTypeFilter = document.getElementById('block-type-filter');
const blockFilterKey = `pdf-to-web-block-filter:${document.body.dataset.projectRoot || document.querySelector('.current-document')?.textContent || ''}`;
const blockTypeFilterKey = `${blockFilterKey}:type`;
const blockSelectionKey = `${blockFilterKey}:selected`;
let selectedBlockFilter = 'all';
let selectedBlockType = 'all';
function matchesReviewFilter(card, filter) {
  return filter === 'all' || (filter === 'pending' ? ['unreviewed', 'needs_review'].includes(card.dataset.reviewStatus) : card.dataset.reviewStatus === filter);
}
function matchesTypeFilter(card, filter) {
  return filter === 'all' || card.dataset.filterType === filter;
}
function applyBlockFilter() {
  if (!blockFilter) return;
  const cards = Array.from(document.querySelectorAll('.block-card'));
  const counts = { all: 0, approved: 0, pending: 0, excluded: 0 };
  for (const card of cards) {
    const status = card.dataset.reviewStatus;
    if (matchesTypeFilter(card, selectedBlockType)) {
      counts.all += 1;
      if (['unreviewed', 'needs_review'].includes(status)) counts.pending += 1;
      else if (status in counts) counts[status] += 1;
    }
    card.hidden = !matchesReviewFilter(card, selectedBlockFilter) || !matchesTypeFilter(card, selectedBlockType);
  }
  blockFilter.querySelectorAll('[data-filter]').forEach(link => {
    link.querySelector('[data-filter-count]').textContent = `(${counts[link.dataset.filter]})`;
    if (link.dataset.filter === selectedBlockFilter) link.setAttribute('aria-current', 'true');
    else link.removeAttribute('aria-current');
  });
  blockTypeFilter?.querySelectorAll('[data-type-filter]').forEach(link => {
    const filter = link.dataset.typeFilter;
    link.querySelector('[data-filter-count]').textContent = `(${cards.filter(card => matchesReviewFilter(card, selectedBlockFilter) && matchesTypeFilter(card, filter)).length})`;
    if (filter === selectedBlockType) link.setAttribute('aria-current', 'true');
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
  sessionStorage.setItem(blockTypeFilterKey, selectedBlockType);
  updateBlockNavigation();
  updateMergeControls();
}
const blockFilterDialog = document.getElementById('block-filter-dialog');
let requestedBlockFilters = null;
function setBlockFilters(review, type, notice = '', selectFirst = false) {
  selectedBlockFilter = review; selectedBlockType = type;
  applyBlockFilter();
  const feedback = document.getElementById('block-filter-notice');
  if (feedback) { feedback.textContent = notice; feedback.hidden = !notice; }
  if (selectFirst) focusFirstFilterResult();
}
function focusFirstFilterResult() {
  updateStickyHeaderOffset();
  const cards = blockCards();
  if (cards.length) {
    selectDescription(null);
    focusBlock(cards[0]);
    announce(`Showing ${cards.length} matching block${cards.length === 1 ? '' : 's'}. First matching block ${cards[0].dataset.blockIndex} selected.`);
  } else {
    selectedSourceCard = null;
    updateBlockNavigation();
    if (!focusEmptyBlockFilter()) {
      const heading = document.getElementById('blocks-heading');
      if (heading) { heading.tabIndex = -1; heading.focus({preventScroll: true}); }
    }
    announce(document.getElementById('block-filter-empty-message')?.textContent || 'No blocks are available.');
  }
}
function requestBlockFilters(review, type, trigger) {
  const hiddenDirty = authoringForms.filter(form => {
    const card = form.closest('.block-card');
    return card && authoringBaselines.get(form) !== authoringValue(form)
      && (!matchesReviewFilter(card, review) || !matchesTypeFilter(card, type));
  });
  if (hiddenDirty.length && blockFilterDialog) {
    requestedBlockFilters = {review, type, trigger, scrollX: window.scrollX, scrollY: window.scrollY};
    blockFilterDialog.showModal();
    document.getElementById('block-filter-cancel').focus({preventScroll: true});
    return;
  }
  setBlockFilters(review, type, '', true);
}
function closeBlockFilterDialog(restoreScroll = true) {
  const previous = requestedBlockFilters;
  requestedBlockFilters = null;
  blockFilterDialog.close();
  previous?.trigger?.focus({preventScroll: true});
  if (restoreScroll && previous) window.scrollTo({left: previous.scrollX, top: previous.scrollY, behavior: 'instant'});
}
document.getElementById('block-filter-cancel')?.addEventListener('click', () => closeBlockFilterDialog());
blockFilterDialog?.addEventListener('cancel', event => { event.preventDefault(); closeBlockFilterDialog(); });
document.getElementById('block-filter-confirm')?.addEventListener('click', () => {
  const requested = requestedBlockFilters;
  closeBlockFilterDialog(false);
  if (requested) setBlockFilters(requested.review, requested.type,
    'Edited blocks are hidden. Your unsaved edits remain in this tab; reset filters to show them again.', true);
});
if (blockFilter) {
  const saved = sessionStorage.getItem(blockFilterKey);
  if (['all', 'approved', 'pending', 'excluded'].includes(saved)) selectedBlockFilter = saved;
  const savedType = sessionStorage.getItem(blockTypeFilterKey);
  if (['all', 'heading', 'paragraph', 'list', 'image', 'table', 'other'].includes(savedType)) selectedBlockType = savedType;
  applyBlockFilter();
  blockFilter.querySelectorAll('[data-filter]').forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    requestBlockFilters(link.dataset.filter, selectedBlockType, link);
  }));
  blockTypeFilter?.querySelectorAll('[data-type-filter]').forEach(link => link.addEventListener('click', event => {
    event.preventDefault(); requestBlockFilters(selectedBlockFilter, link.dataset.typeFilter, link);
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
  if (page) page.textContent = index >= 0 ? `Page ${cards[index].dataset.page}` : cards.length ? 'No block selected' : 'No blocks shown';
  if (position) position.textContent = index >= 0 ? `Block ${cards[index].dataset.blockIndex} · ${index + 1} of ${cards.length} shown`
    : cards.length ? 'No block selected. Use Next block to begin.'
      : document.querySelector('.block-card') ? '0 blocks shown' : 'No blocks are available.';
  const empty = document.getElementById('block-filter-empty');
  const emptyFilter = cards.length === 0 && !!document.querySelector('.block-card') && (selectedBlockFilter !== 'all' || selectedBlockType !== 'all');
  if (empty) {
    empty.hidden = !emptyFilter;
    document.getElementById('block-filter-empty-message').textContent = emptyFilter
      ? selectedBlockFilter === 'pending' ? 'No items left to review with these filters.' : 'No blocks match these filters.'
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
  setBlockFilters('all', 'all', '', true);
});

function focusEmptyBlockFilter() {
  const recovery = document.getElementById('show-all-blocks');
  if (blockCards().length || !recovery || recovery.closest('[hidden]')) return false;
  recovery.focus({preventScroll: true});
  recovery.scrollIntoView({block: 'center'});
  return true;
}

function revealLinkedBlock(card) {
  if (card.hidden && blockFilter) {
    setBlockFilters(matchesReviewFilter(card, selectedBlockFilter) ? selectedBlockFilter : 'all',
      matchesTypeFilter(card, selectedBlockType) ? selectedBlockType : 'all',
      'Filters changed to show the linked block. Your saved content and review decisions are unchanged.');
  }
}
function focusBlock(card) {
  if (!card) return;
  if (card.hidden) return;
  card.focus({ preventScroll: true });
  card.scrollIntoView({ block: 'start', behavior: 'instant' });
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
  card.addEventListener('focusin', event => {
    selectSourceBlock(card);
    if (event.target.matches('.image-block-form :is(input, textarea, select, button)')) {
      // Browser focus scrolling does not account for the sticky review controls.
      requestAnimationFrame(() => {
        if (document.activeElement !== event.target) return;
        updateStickyHeaderOffset();
        const offset = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--structure-scroll-offset'));
        const rect = event.target.getBoundingClientRect();
        if (rect.top < offset || rect.top >= innerHeight) event.target.scrollIntoView({block: 'start'});
      });
    }
  });
});

function selectDescription(card) {
  document.querySelectorAll('.complex-visual').forEach(visual => {
    const selected = visual === card;
    visual.classList.toggle('description-selected', selected);
    const notice = visual.querySelector('.description-selection-notice');
    if (notice) notice.hidden = !selected;
  });
  const page = Number(card?.dataset.sourcePage);
  if (page && page !== Number(document.getElementById('source-page-number')?.value)) navigateSourcePage(page);
}
document.querySelectorAll('.complex-visual').forEach(card => {
  card.addEventListener('focusin', () => selectDescription(card));
  card.addEventListener('click', () => selectDescription(card));
});
function focusLinkedBlock() {
  if (location.hash === '#bulk-review-heading') {
    const tools = document.getElementById('bulk-review-tools');
    const heading = document.getElementById('bulk-review-heading');
    if (tools && heading) {
      tools.open = true;
      heading.focus({preventScroll: true});
      heading.scrollIntoView({block: 'start'});
    }
    return;
  }
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
    if (pendingReviewFocus) return;
    revealLinkedBlock(card);
    selectDescription(null);
    focusBlock(card);
  }
  else if (card?.classList.contains('image-description-record')) {
    const owner = card.closest('.block-card');
    if (owner) {
      if (pendingReviewFocus) return;
      revealLinkedBlock(owner);
      selectSourceBlock(owner);
      selectDescription(null);
      card.focus({preventScroll: true});
      card.scrollIntoView({block: 'start'});
    }
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
const draftingTools = document.getElementById('image-description-tools');
if (draftingTools) {
  const projectId = document.getElementById('image-draft-toolbar').dataset.documentId;
  const preferenceKey = `pdf-to-web-drafting-tools-${projectId}`;
  const preferenceStores = () => {
    const stores = [];
    try { stores.push(localStorage); } catch {}
    try { stores.push(sessionStorage); } catch {}
    return stores;
  };
  for (const storage of preferenceStores()) {
    try {
      const preferred = storage.getItem(preferenceKey);
      if (preferred === 'open' || preferred === 'closed') { draftingTools.open = preferred === 'open'; break; }
    } catch { /* Fall back to this tab, then to the saved-request default. */ }
  }
  draftingTools.querySelector(':scope > summary').addEventListener('click', () => {
    // Only a user's summary action persists. A direct help/hash link may reveal
    // tools for this visit without replacing their preferred default.
    for (const storage of preferenceStores()) {
      try { storage.setItem(preferenceKey, draftingTools.open ? 'closed' : 'open'); } catch {}
    }
  });
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
let pendingReviewFocus = null;
try { pendingReviewFocus = JSON.parse(sessionStorage.getItem(reviewAdvanceKey)); } catch { /* Ignore a superseded selection format. */ }
const restoringReviewPosition = Boolean(pendingReviewFocus);
window.addEventListener('load', () => {
  if (restoringReviewPosition || accessibilityParams.has('source_page')) return;
  if (!pendingReviewFocus && focusEmptyBlockFilter()) return;
  if (pendingReviewFocus || location.hash.startsWith('#block-') || location.hash.startsWith('#visual-') || location.hash === '#image-description-tools') return;
  const card = document.getElementById(sessionStorage.getItem(blockSelectionKey));
  if (!card?.classList.contains('block-card')) return;
  selectedSourceCard = card;
  applyBlockFilter();
  if (selectedSourceCard) focusBlock(selectedSourceCard);
}, {once: true});
if (pendingReviewFocus) {
  sessionStorage.removeItem(reviewAdvanceKey);
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  // Restore the review destination before the next paint, rather than showing
  // the page top while images load and then jumping after a delayed load event.
  (() => {
    try {
    updateStickyHeaderOffset();
    if (location.hash === '#image-description-tools') return;
    // A reviewer who has entered provider setup keeps focus there.
    if (document.activeElement?.closest('#image-draft-toolbar')) return;
    if (focusEmptyBlockFilter()) return;
    const complete = document.getElementById('structure-review-complete');
    if (pendingReviewFocus.advance && complete) { complete.focus({preventScroll: true}); complete.scrollIntoView({block: 'center', behavior: 'instant'}); announce('Block saved and approved. Structure review complete.'); return; }
    const remembered = document.getElementById(pendingReviewFocus.blockId);
    const cards = Array.from(document.querySelectorAll('.block-card'));
    const index = cards.indexOf(remembered);
    const following = [...cards.slice(index + 1), ...cards.slice(0, Math.max(0, index))].filter(card => !card.hidden);
    const pendingCard = !pendingReviewFocus.advance && remembered && !remembered.hidden ? remembered
      : following.find(card => ['unreviewed', 'needs_review'].includes(card.dataset.reviewStatus)) || following[0]
        || (remembered && !remembered.hidden ? remembered : blockCards()[0]);
    if (!pendingCard) return;
    focusBlock(pendingCard);
    announce(pendingReviewFocus.advance ? `Block saved and approved. Block ${pendingCard.dataset.blockIndex} selected for review.` : 'Saved review position restored.');
    } finally { pendingReviewFocus = null; }
  })();
}

function updateManualReconstruction(page) {
  const control = document.getElementById('manual-reconstruction-control');
  if (!control) return;
  control.dataset.sourcePage = String(page);
  const entry = JSON.parse(control.dataset.pages)[String(page)];
  const toggle = document.getElementById('manual-reconstruction-toggle');
  toggle.checked = Boolean(entry);
  toggle.defaultChecked = Boolean(entry);
  toggle.setAttribute('aria-label', `Needs manual reconstruction for source page ${page}`);
  const status = document.getElementById('manual-reconstruction-status');
  status.textContent = entry ? `Source page ${page} needs manual reconstruction. ${Object.keys(entry.blocks).length} blocks held; ${entry.shared_block_ids.length} shared blocks retained. Export is blocked.` : '';
  status.hidden = !entry;
}
const manualPageToggle = document.getElementById('manual-reconstruction-toggle');
const manualHelpLine = document.querySelector('.manual-reconstruction-line');
const manualHelpButton = document.getElementById('manual-reconstruction-help-button');
const manualHelpTip = document.getElementById('manual-reconstruction-help');
if (manualHelpButton && manualHelpTip) {
  let pinned = false;
  const open = () => !manualHelpTip.hidden && (!manualHelpTip.showPopover || manualHelpTip.matches(':popover-open'));
  const hide = () => {
    if (manualHelpTip.showPopover && manualHelpTip.matches(':popover-open')) manualHelpTip.hidePopover();
    manualHelpTip.hidden = true; pinned = false;
    manualHelpButton.setAttribute('aria-expanded', 'false');
  };
  const place = () => {
    if (!open()) return;
    const viewport = window.visualViewport;
    const left = viewport?.offsetLeft || 0, top = viewport?.offsetTop || 0;
    const width = viewport?.width || innerWidth, height = viewport?.height || innerHeight;
    manualHelpTip.style.maxWidth = `min(24rem, ${Math.max(1, width - 16)}px)`;
    manualHelpTip.style.maxHeight = `${Math.max(1, height - 16)}px`;
    manualHelpTip.style.overflowY = 'auto';
    const anchor = manualHelpButton.getBoundingClientRect(), bounds = manualHelpTip.getBoundingClientRect();
    manualHelpTip.style.left = `${Math.max(left + 8, Math.min(anchor.left, left + width - bounds.width - 8))}px`;
    manualHelpTip.style.top = `${Math.max(top + 8, Math.min(top + height - bounds.height - 8, anchor.bottom + bounds.height + 8 > top + height ? anchor.top - bounds.height - 8 : anchor.bottom + 8))}px`;
  };
  const show = () => {
    manualHelpTip.hidden = false;
    if (manualHelpTip.showPopover && !manualHelpTip.matches(':popover-open')) manualHelpTip.showPopover();
    manualHelpButton.setAttribute('aria-expanded', 'true'); place();
  };
  const leave = () => {
    if (!pinned && !manualHelpLine.contains(document.activeElement) && !manualHelpTip.matches(':hover')) hide();
  };
  manualHelpLine.addEventListener('pointerenter', e => { if (e.pointerType === 'mouse') show(); });
  manualHelpLine.addEventListener('pointerleave', leave);
  manualHelpTip.addEventListener('pointerleave', leave);
  manualHelpLine.addEventListener('focusin', show);
  manualHelpLine.addEventListener('focusout', () => requestAnimationFrame(leave));
  manualHelpButton.addEventListener('click', () => { if (pinned && open()) hide(); else { pinned = true; show(); } });
  manualHelpTip.addEventListener('toggle', e => { if (e.newState === 'closed') { pinned = false; manualHelpButton.setAttribute('aria-expanded', 'false'); } });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && open()) { e.preventDefault(); hide(); } });
  document.addEventListener('click', e => { if (open() && !manualHelpLine.contains(e.target) && !manualHelpTip.contains(e.target)) hide(); });
  window.addEventListener('resize', place);
  window.addEventListener('scroll', place, true);
  window.visualViewport?.addEventListener('resize', place);
  window.visualViewport?.addEventListener('scroll', place);
}
function displayedReconstructionPage() {
  return Number(document.getElementById('manual-reconstruction-control')?.dataset.sourcePage || document.getElementById('source-page-number')?.value || 1);
}
window.addEventListener('pageshow', () => {
  if (!manualPageToggle) return;
  // Native form restoration can happen after initial scripts. Use the page
  // actually displayed by source navigation, not a restored checkbox value.
  const page = displayedReconstructionPage();
  document.getElementById('source-page-number').value = page;
  updateManualReconstruction(page);
  updateSourcePageReview(page);
});
manualPageToggle?.addEventListener('change', async () => {
  const page = displayedReconstructionPage();
  const enabled = manualPageToggle.checked;
  let sent = false;
  try {
    if (reviewWriteBusy || reviewReloadRequired) throw new Error('Finish or confirm the current review save before changing the reconstruction hold.');
    if (authoringForms.some(form => authoringBaselines.get(form) !== authoringValue(form))) {
      throw new Error('Save or revert unsaved authoring edits before changing the reconstruction hold.');
    }
    manualPageToggle.disabled = true;
    sent = true;
    const result = await api('/api/source-pages/manual-reconstruction', {method: 'POST', headers: csrfHeaders(), body: JSON.stringify({page, enabled, expected_review_token: document.getElementById('manual-reconstruction-control').dataset.reviewToken})});
    if (result.source_page_reviews) document.querySelector('.source-pane').dataset.pageReviews = JSON.stringify(result.source_page_reviews);
    updateSourcePageReview(displayedReconstructionPage());
    sessionStorage.removeItem(reviewAdvanceKey);
    history.replaceState(null, '', `/structure?source_page=${displayedReconstructionPage()}`);
    location.reload();
  } catch (error) {
    if (sent && !error.confirmedRejection) reviewReloadRequired = true;
    updateSourcePageReview(displayedReconstructionPage());
    updateManualReconstruction(displayedReconstructionPage());
    document.getElementById('manual-reconstruction-status').textContent = `Source page ${page}: ${error.message}`;
    document.getElementById('manual-reconstruction-status').hidden = false;
    announce(error.message);
  } finally {manualPageToggle.disabled = false;}
});
const requestedSourcePage = new URLSearchParams(location.search).get('source_page');
if (manualPageToggle && requestedSourcePage && /^\d+$/.test(requestedSourcePage)) {
  requestAnimationFrame(() => {
    navigateSourcePage(Number(requestedSourcePage));
    if (location.hash.startsWith('#visual-') || location.hash.startsWith('#block-')) return;
    manualPageToggle.focus({preventScroll: true});
    document.getElementById('source-heading').scrollIntoView({block: 'start', behavior: 'instant'});
  });
}

function rememberReviewResult(card, advance = false) {
  if (!card) return;
  sessionStorage.setItem(reviewAdvanceKey, JSON.stringify({blockId: card.id, advance}));
  sessionStorage.setItem(blockSelectionKey, card.id);
  // An old hash can point to the now-hidden approved card and reveal All blocks
  // before reload restores the pending selection. Keep the active filter instead.
  const destination = new URL(location.href);
  destination.searchParams.delete('source_page');
  history.replaceState(null, '', destination.pathname + destination.search);
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
}
function rememberReviewAdvance(card) { rememberReviewResult(card, true); }

// Patch only review fragments. Matching controls keep their listeners and drafts;
// the source pane, document and history are never replaced after a saved review.
function reviewNodeKey(node) {
  if (node.nodeType !== Node.ELEMENT_NODE) return '';
  return node.id || (node.getAttribute('name') ? `${node.tagName}:${node.getAttribute('name')}` : '')
    || (node.dataset.action ? `${node.tagName}:${node.dataset.action}` : '')
    || (node.dataset.filter ? `filter:${node.dataset.filter}` : '')
    || (node.dataset.typeFilter ? `type-filter:${node.dataset.typeFilter}` : '');
}
function morphReviewNode(current, fresh, preservedForms) {
  if (preservedForms.has(current)) return;
  if (current.nodeType !== Node.ELEMENT_NODE) { current.nodeValue = fresh.nodeValue; return; }
  const open = current.tagName === 'DETAILS' ? current.open : null;
  for (const attribute of [...current.attributes]) if (!fresh.hasAttribute(attribute.name)) current.removeAttribute(attribute.name);
  for (const attribute of fresh.attributes) current.setAttribute(attribute.name, attribute.value);
  const oldChildren = [...current.childNodes], used = new Set();
  let cursor = current.firstChild;
  for (const child of [...fresh.childNodes]) {
    const key = reviewNodeKey(child);
    let match = oldChildren.find(node => !used.has(node) && node.nodeType === child.nodeType && node.nodeName === child.nodeName && (key ? reviewNodeKey(node) === key : !reviewNodeKey(node)));
    if (match) { used.add(match); morphReviewNode(match, child, preservedForms); }
    else match = child.cloneNode(true);
    if (match !== cursor) current.insertBefore(match, cursor);
    cursor = match.nextSibling;
  }
  for (const child of oldChildren) if (!used.has(child) && child.parentNode === current) child.remove();
  if (current.matches('input, textarea, select')) {
    current.value = fresh.value;
    if (current.type === 'checkbox') current.checked = fresh.checked;
  }
  if (open !== null) current.open = open;
}
function reviewFragment(markup) {
  const template = document.createElement('template');
  template.innerHTML = markup;
  return template.content;
}
function advanceAfterReview(ownerId, advance, message) {
  const owner = document.getElementById(ownerId);
  sessionStorage.removeItem(reviewAdvanceKey);
  const destination = new URL(location.href); destination.hash = ''; destination.searchParams.delete('source_page');
  history.replaceState(null, '', destination.pathname + destination.search);
  if (advance && document.getElementById('structure-review-complete')) {
    const complete = document.getElementById('structure-review-complete');
    complete.focus({preventScroll: true}); complete.scrollIntoView({block: 'center', behavior: 'instant'});
    announce(`${message} Structure review complete.`); return;
  }
  if (focusEmptyBlockFilter()) { announce(message); return; }
  const cards = [...document.querySelectorAll('.block-card')], index = cards.indexOf(owner);
  const following = [...cards.slice(index + 1), ...cards.slice(0, Math.max(0, index))].filter(card => !card.hidden);
  const target = !advance && owner && !owner.hidden ? owner : following.find(card => ['unreviewed', 'needs_review'].includes(card.dataset.reviewStatus)) || following[0] || (owner && !owner.hidden ? owner : blockCards()[0]);
  if (target) { focusBlock(target); sessionStorage.setItem(blockSelectionKey, target.id); }
  announce(`${message}${target ? ` Block ${target.dataset.blockIndex} selected.` : ''}`);
}
function applyReviewPatch(data, ownerId, advance, message, submittedForm = null) {
  if (!data.review_patch) throw new Error(data.refresh_error || 'Saved, but this running app cannot refresh review in place. Reload after relaunching PTW before making another change.');
  const patch = data.review_patch;
  const sourcePane = document.querySelector('.source-pane');
  if (sourcePane && patch.source_page_reviews) sourcePane.dataset.pageReviews = JSON.stringify(patch.source_page_reviews);
  receiveSourcePageVisualReviews(patch.source_page_visual_reviews);
  updateSourcePageReview();
  const submitted = new Set(Array.isArray(submittedForm) ? submittedForm : [submittedForm]);
  const preserved = new Set(authoringForms.filter(form => !submitted.has(form) && authoringBaselines.get(form) !== authoringValue(form)));
  for (const markup of patch.cards) {
    const fresh = reviewFragment(markup).firstElementChild, current = document.getElementById(fresh.id);
    if (!current) throw new Error('Saved content changed the review structure. Reload before making another change.');
    morphReviewNode(current, fresh, preserved);
  }
  const ids = new Set(patch.block_ids.map(id => `block-${id}`));
  document.querySelectorAll('.block-card').forEach(card => { if (!ids.has(card.id)) card.remove(); });
  for (const [selector, markup] of [['#review-summary', patch.summary], ['#structure-completion-region', `<div id="structure-completion-region">${patch.completion}</div>`]]) {
    const current = document.querySelector(selector); if (current) morphReviewNode(current, reviewFragment(markup).firstElementChild, preserved);
  }
  const filters = reviewFragment(patch.filters);
  for (const id of ['block-review-filter', 'block-type-filter']) morphReviewNode(document.getElementById(id), filters.querySelector(`#${id}`), preserved);
  document.querySelectorAll('#undo-action, #reading-order-undo').forEach(button => { button.disabled = !patch.can_undo; });
  if (patch.can_undo) document.querySelector('.undo-empty')?.remove();
  const overall = document.querySelector('.review-overall-status'); if (overall) overall.hidden = patch.complete;
  const control = document.getElementById('manual-reconstruction-control');
  if (control) { control.dataset.reviewToken = patch.review_token; control.dataset.pages = JSON.stringify(patch.manual_pages); updateManualReconstruction(displayedReconstructionPage()); }
  authoringForms.splice(0, authoringForms.length, ...document.querySelectorAll('.block-form, .complex-visual-form'));
  for (const form of authoringForms) if (!preserved.has(form)) {
    const token = form.elements.namedItem('expected_review_token'); if (token) token.value = patch.review_token;
    authoringBaselines.set(form, authoringValue(form));
    if (form.matches('.block-form')) initializeBlockForm(form);
  }
  document.querySelectorAll('.block-content-modes').forEach(initializeBlockContentModes);
  updateAuthoringFeedback();
  document.querySelectorAll('[data-merge-token]').forEach(button => { button.dataset.mergeToken = patch.review_token; });
  mergeSnapshotStale = false;
  applyBlockFilter();
  if (preserved.size) { announce(`${message} Other unsaved edits remain in this tab.`); return; }
  advanceAfterReview(ownerId, advance, message);
}
document.addEventListener('click', event => {
  if (!event.target.closest('[data-save-and-approve], .block-action[data-action="approve"]')) return;
  if (reviewWriteBusy || performance.now() < reviewClickLockUntil || event.detail > 1) { event.preventDefault(); event.stopImmediatePropagation(); }
}, true);

function showBlockActionMessage(card, text) {
  if (!card) { announce(text); return; }
  let message = card.querySelector('.block-action-message');
  if (!message) {
    message = document.createElement('p');
    message.className = 'block-action-message';
    message.setAttribute('role', 'status');
    message.setAttribute('aria-live', 'polite');
  }
  // Earlier open pages put this feedback in the distant lower footer.
  const actions = card.querySelector('.block-review-actions');
  if (actions && actions.nextElementSibling !== message) actions.after(message);
  message.textContent = text;
  message.hidden = false;
  message.scrollIntoView({block: 'nearest', behavior: 'instant'});
  announce(text);
}
function blockFormValues(form) {
  const values = Object.fromEntries(new FormData(form));
  if (form.classList.contains('image-block-form')) {
    values.description_edits = [...form.querySelectorAll('.image-description-record')].map(record => ({id: record.dataset.visualId, ...Object.fromEntries([...record.querySelectorAll('[data-description-field]')].map(field => [field.dataset.descriptionField, field.value]))}));
    values.displayed_description_ids = values.description_edits.map(record => record.id);
    for (const key of Object.keys(values)) if (/^description_\d+_/.test(key)) delete values[key];
  }
  const decorative = form.querySelector('input[name="decorative"]');
  if (decorative) values.decorative = decorative.checked;
  ['table_header_row', 'table_header_column', 'table_reviewed'].forEach((name) => {
    const checkbox = form.querySelector(`input[name="${name}"]`);
    if (checkbox) values[name] = checkbox.checked;
  });
  if (values.type === 'heading') values.level = Number(values.level);
  else delete values.level;
  return values;
}
function initializeBlockForm(form) {
  if (boundBlockForms.has(form)) return;
  boundBlockForms.add(form);
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (event.submitter?.hasAttribute('data-save-and-approve')) {
      announce('Save your edits, then relaunch PTW and reload Structure to use the updated top approval action.'); return;
    }
    saveBlockAuthoring(form, event.submitter);
  });
}
async function saveBlockAuthoring(form, submitter, saveAndApprove = false, submittedForms = [form]) {
  if (reviewWriteBusy || performance.now() < reviewClickLockUntil || form.dataset.saving === 'true') return;
  if (reviewReloadRequired) { showBlockActionMessage(form.closest('.block-card'), 'The previous save needs confirmation. Your edits remain here. Preserve them before reloading to inspect the saved result.'); return; }
  if (form.dataset.saveUncertain === 'true') { showBlockActionMessage(form.closest('.block-card'), 'This save could not be confirmed. Your edits remain here. Preserve them before reloading; do not submit the same approval again.'); return; }
  if (saveAndApprove && submitter?.dataset.saveEditors !== 'true') {
    const text = 'Save your edits, then relaunch PTW and reload Structure to use Save & Approve. This running server has the earlier editor.';
    showBlockActionMessage(form.closest('.block-card'), text); return;
  }
  let values = blockFormValues(form);
  if (saveAndApprove) {
    if (submittedForms.some(editor => {
      if (editor.checkValidity()) return false;
      showBlockActionMessage(form.closest('.block-card'), 'An edited field is invalid. Check the highlighted field; your changes have not been saved.');
      editor.closest('.block-content-modes')?.querySelector('[role=tab][aria-controls^=content-edit-]')?.click();
      editor.reportValidity(); return true;
    })) return;
    values = {expected_review_token: form.elements.namedItem('expected_review_token')?.value,
      form_edits: submittedForms.map(editor => {
        const edits = blockFormValues(editor);
        delete edits.expected_review_token; delete edits.displayed_description_ids;
        return edits;
      })};
    const image = form.closest('.block-card').querySelector('.image-block-form');
    if (image) values.displayed_description_ids = [...image.querySelectorAll('.image-description-record')].map(record => record.dataset.visualId);
  }
  const ownerId = form.closest('.block-card').id;
  const submitterText = submitter?.textContent;
  let sent = false, confirmed = false;
  const disabled = new Map([...submittedForms.flatMap(editor => [...editor.querySelectorAll('input, textarea, select, button')]), ...(submitter ? [submitter] : [])].map(field => [field, field.disabled]));
  try {
    const otherDirty = authoringForms.find(other => !submittedForms.includes(other) && authoringBaselines.get(other) !== authoringValue(other));
    if (otherDirty) throw new Error(`Block ${otherDirty.closest('.block-card')?.dataset.blockIndex || 'in another editor'} also has unsaved changes. Save or revert those edits first; your changes in this block remain here.`);
    if (saveAndApprove) {
      delete values.review_status;
    }
    form.dataset.saving = 'true';
    reviewWriteBusy = true;
    values.review_refresh = true;
    disabled.forEach((state, field) => { field.disabled = true; });
    if (submitter) { submitter.dataset.saving = 'true'; submitter.textContent = 'Saving…'; }
    announce('Saving…');
    updateMergeControls();
    sent = true;
    const saved = await api(`/api/blocks/${encodeURIComponent(form.dataset.blockId)}${saveAndApprove ? '/save-and-approve' : ''}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values), signal: reviewSaveSignal() });
    confirmed = true;
    if (returnToAccessibility(form.closest('.block-card'))) return;
    applyReviewPatch(saved, ownerId, Boolean(saveAndApprove), saveAndApprove ? 'Block saved and approved.' : saved.block_status === 'needs_review' ? 'Changes saved. Review the saved content, then approve it.' : 'Block saved.', submittedForms);
    reviewClickLockUntil = performance.now() + 250;
  } catch (error) {
    if (saveAndApprove && [404, 405].includes(error.status)) error.message = 'Save & Approve is unavailable in this running server. Your edits remain here. Preserve them, then relaunch PTW and reload Structure.';
    if (sent && (confirmed || !error.confirmedRejection)) {
      form.dataset.saveUncertain = 'true';
      reviewReloadRequired = true;
      if (!confirmed) error.message = 'The save result could not be confirmed. Your fields remain here. Reload before retrying; do not submit the same approval again.';
      else error.message = reviewRefreshRecovery(error.message);
    }
    showBlockActionMessage(form.closest('.block-card'), error.message);
  } finally {
    delete form.dataset.saving;
    reviewWriteBusy = false;
    disabled.forEach((state, field) => { if (field.isConnected) field.disabled = state; });
    if (submitter?.isConnected) { delete submitter.dataset.saving; if (submitterText) submitter.textContent = submitterText; }
    updateAuthoringFeedback();
    updateMergeControls();
  }
}
document.querySelectorAll('.block-form').forEach(initializeBlockForm);

document.addEventListener('change', event => {
  const checkbox = event.target;
  if (!checkbox.matches('.image-block-form input[name="decorative"]')) return;
  const alt = checkbox.closest('form').querySelector('textarea[name="alt"]');
  alt.disabled = checkbox.checked;
  if (checkbox.checked) alt.value = '';
});

document.addEventListener('change', event => {
  const select = event.target;
  if (!select.matches('.block-form select[name="type"]')) return;
  const level = select.closest('form').querySelector('.heading-level');
  level.hidden = select.value !== 'heading';
  level.querySelector('select').disabled = select.value !== 'heading';
});

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
    receiveSourcePageReviews(data.source_page_reviews);
    receiveSourcePageVisualReviews(data.source_page_visual_reviews);
    if (data.reload_required) { location.hash = 'visual-' + encodeURIComponent(form.dataset.visualId); window.location.reload(); return; }
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
    form.elements.namedItem('expected_review_token').value = data.review_token;
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
      const record = [...imageForm.querySelectorAll('.image-description-record')].find(record => record.dataset.visualId === form.dataset.visualId);
      if (record && wasClean) {
        for (const field of record.querySelectorAll('[data-description-field]')) { field.value = values[field.dataset.descriptionField]; field.defaultValue = field.value; }
        record.querySelector('.image-description-state').textContent = data.visual.label;
        record.querySelector('.image-description-reason').textContent = data.visual.reason;
        record.querySelector('.image-description-decision').textContent = data.visual.status;
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
    for (const editor of authoringForms) if (authoringBaselines.get(editor) === authoringValue(editor)) {
      const token = editor.elements.namedItem('expected_review_token');
      if (token) token.value = data.review_token;
    }
  } catch (error) { message.textContent = error.message; announce(error.message); }
  finally {
    button.disabled = false;
    if (restoreFocus && document.activeElement === document.body) button.focus({preventScroll: true});
    updateMergeControls();
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
  if (reviewWriteBusy || reviewReloadRequired || button.dataset.saveUncertain === 'true') { showBlockActionMessage(button.closest('.block-card'), 'Finish or confirm the current save before another review action. Your edited fields remain here.'); return; }
  let action = button.dataset.action;
  const blockId = button.dataset.blockId;
  if (action === 'approve') {
    const edited = [...button.closest('.block-card').querySelectorAll('.block-form')].filter(form => authoringBaselines.get(form) !== authoringValue(form));
    if (edited.length) { await saveBlockAuthoring(edited[0], button, true, edited); return; }
  }
  const body = {};
  if (action === 'toggle-excluded') action = button.dataset.currentStatus === 'excluded' ? 'include' : 'exclude';
  if (action === 'merge') {
    const reason = mergeDisabledReason(button);
    if (reason) {
      updateMergeControls(); announce(reason);
      const message = button.closest('.block-card')?.querySelector('.block-action-message');
      if (message) { message.textContent = reason; message.hidden = false; }
      return;
    }
    body.expected_review_token = button.dataset.mergeToken;
    body.expected_next_block_id = button.dataset.nextBlockId;
    mergeInProgress = true;
    updateMergeControls();
  }
  if (action === 'split') {
    const textarea = button.closest('.block-card').querySelector('textarea');
    body.offset = textarea?.selectionStart || 0;
    if (!body.offset) { announce('Place the text cursor where the block should split.'); textarea?.focus(); return; }
  }
  const refresh = ['approve', 'flag', 'exclude', 'include'].includes(action);
  const originalText = button.textContent;
  const originalDisabled = button.disabled;
  let sent = false, confirmed = false;
  try {
    if (action !== 'merge') {
      const dirty = authoringForms.find(form => authoringBaselines.get(form) !== authoringValue(form));
      if (dirty) {
        dirty.closest('.block-card')?.querySelector('.block-review-actions [data-action=approve]')?.focus();
        throw new Error(action === 'approve' ? 'There are unsaved edits. Use Save & Approve in the edited block, or revert those edits before approving saved content.' : 'There are unsaved edits. Save or revert them before changing the saved blocks.');
      }
    }
    if (refresh) {
      body.review_refresh = true;
      body.expected_review_token = button.closest('.block-card').querySelector('[name="expected_review_token"]')?.value || button.closest('.block-card').querySelector('[data-merge-token]')?.dataset.mergeToken;
      if (action === 'approve' && button.closest('.block-card').querySelector('.image-block-form')) {
        body.displayed_description_ids = [...button.closest('.block-card').querySelectorAll('.image-description-record')].map(record => record.dataset.visualId);
      }
      reviewWriteBusy = true;
      button.disabled = true;
      button.textContent = 'Saving…';
      announce('Saving review…');
    }
    sent = true;
    const saved = await api(`/api/blocks/${encodeURIComponent(blockId)}/${action}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(body), ...(refresh ? {signal: reviewSaveSignal()} : {}) });
    confirmed = true;
    if (!refresh) receiveSourcePageReviews(saved.source_page_reviews);
    if (returnToAccessibility(button.closest('.block-card'))) return;
    if (refresh) {
      applyReviewPatch(saved, button.closest('.block-card').id, true, action === 'approve' ? 'Block approved.' : 'Review action saved.');
      reviewClickLockUntil = performance.now() + 250;
      return;
    }
    rememberReviewResult(button.closest('.block-card'));
    announce('Review action saved.');
    window.location.reload();
  } catch (error) {
    if (refresh && sent && (confirmed || !error.confirmedRejection)) {
      button.dataset.saveUncertain = 'true';
      reviewReloadRequired = true;
      if (!confirmed) error.message = 'The review save result could not be confirmed. Reload before retrying; no automatic retry was made.';
      else error.message = reviewRefreshRecovery(error.message);
    }
    showBlockActionMessage(button.closest('.block-card'), error.message);
    if (action === 'merge' && /^(The document changed|The next block changed)\./.test(error.message)) mergeSnapshotStale = true;
  } finally {
    if (refresh) {
      reviewWriteBusy = false;
      if (button.isConnected) button.textContent = originalText;
      const card = button.closest('.block-card');
      // A saved image may still have pending descriptions. Keep the server's
      // refreshed disabled state after success; restore the old state on rejection.
      if (card) button.disabled = button.dataset.saveUncertain === 'true' || (confirmed ? button.disabled : originalDisabled);
    }
    if (action === 'merge') { mergeInProgress = false; updateMergeControls(); }
    updateAuthoringFeedback();
  }
}));

let undoInProgress = false;
document.querySelectorAll('#undo-action, #reading-order-undo').forEach(button => button.addEventListener('click', async () => {
  if (reviewWriteBusy || reviewReloadRequired) { announce('Finish or confirm the current save before Undo. Reload if its result is uncertain.'); return; }
  if (undoInProgress) return;
  undoInProgress = true;
  const controls = Array.from(document.querySelectorAll('#undo-action, #reading-order-undo'));
  const disabledStates = controls.map(control => control.disabled);
  controls.forEach(control => { control.disabled = true; });
  let sent = false;
  try {
    const dirty = authoringForms.find(form => authoringBaselines.get(form) !== authoringValue(form));
    if (dirty) {
      dirty.closest('.block-card')?.querySelector('button[type="submit"]')?.focus();
      throw new Error('Save or revert unsaved edits before Undo so they remain recoverable.');
    }
    sent = true;
    const result = await api('/api/review/undo', { method: 'POST', headers: csrfHeaders(), body: '{}' });
    receiveSourcePageReviews(result.source_page_reviews);
    if (manualPageToggle && new URLSearchParams(location.search).has('source_page')) {
      sessionStorage.removeItem(reviewAdvanceKey);
    } else rememberReviewResult(selectedSourceCard || document.getElementById(sessionStorage.getItem(blockSelectionKey)));
    announce('Last action undone.');
    window.location.reload();
  } catch (error) {
    if (sent && !error.confirmedRejection) { reviewReloadRequired = true; error.message = 'Undo result could not be confirmed. Reload before another review change.'; }
    updateSourcePageReview();
    undoInProgress = false;
    controls.forEach((control, index) => { control.disabled = disabledStates[index]; });
    announce(error.message); alert(error.message);
  }
}));

document.querySelectorAll('.preview-width').forEach((button) => button.addEventListener('click', () => {
  const shell = document.getElementById('preview-shell');
  shell.classList.toggle('narrow', button.dataset.width === 'mobile');
  document.querySelectorAll('.preview-width').forEach((item) => { item.classList.toggle('secondary', item !== button); item.setAttribute('aria-pressed', String(item === button)); });
  announce(`${button.textContent} preview selected.`);
}));

const previewFrame = document.querySelector('#preview-shell iframe');
const previewProfile = document.getElementById('preview-profile');
const previewPage = document.getElementById('preview-page');
const previewWorkspace = document.getElementById('preview-workspace');
let activePreviewMode = previewWorkspace?.dataset.mode || 'wordpress';
function updatePreviewPage() {
  if (!previewPage) return;
  const index = previewPage.selectedIndex, count = previewPage.options.length - 1;
  document.getElementById('preview-previous').disabled = index <= 1;
  document.getElementById('preview-next').disabled = index >= count || !count;
  document.getElementById('preview-page-status').textContent = index ? `Page ${index} of ${count}${previewPage.selectedOptions[0].dataset.state ? " · " + previewPage.selectedOptions[0].dataset.state : ""}` : `Whole document · ${count} output page${count === 1 ? '' : 's'}`;
  document.getElementById('preview-arrange').href = `/output-pages?${new URLSearchParams({page_id: previewPage.value, mode: activePreviewMode, profile: previewProfile.value})}`;
  const params = new URLSearchParams({page_id: previewPage.value, mode: activePreviewMode, profile: previewProfile.value});
  history.replaceState(null, '', `/preview?${params}`);
  document.querySelectorAll('[data-preview-export]').forEach(link => { link.href = `/export?${params}`; });
}
let previewExportPending = false;
let previewExportRecoveryTimer = null;
const previewExportStatus = document.getElementById('preview-export-status');
function previewExportFeedback(message, pending) {
  previewExportPending = pending;
  previewExportStatus.hidden = false;
  previewExportStatus.textContent = message;
  previewPage.disabled = pending;
  previewProfile.disabled = pending;
  document.querySelectorAll('.preview-mode, #preview-previous, #preview-next').forEach(control => { control.disabled = pending; });
  if (!pending) updatePreviewPage();
  document.querySelectorAll('[data-preview-export]').forEach(link => {
    link.setAttribute('aria-disabled', String(pending));
    link.setAttribute('aria-busy', String(pending));
  });
}
document.querySelectorAll('[data-preview-export]').forEach(link => link.addEventListener('click', async event => {
  if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  if (previewExportPending) return;
  clearTimeout(previewExportRecoveryTimer);
  const destination = link.href;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  previewExportFeedback('Opening Export… This does not generate files.', true);
  try {
    const response = await fetch(destination, {signal: controller.signal, cache: 'no-store'});
    if (!response.ok) throw new Error(`Export screen returned HTTP ${response.status}.`);
    window.location.assign(destination);
    // A cancelled or failed browser navigation must not leave a permanently busy link.
    previewExportRecoveryTimer = setTimeout(() => previewExportFeedback('Export has not opened. Try Continue to Export again, or Restore preview to use the main navigation. No files were generated by this action.', false), 10000);
  } catch (error) {
    previewExportFeedback(`Could not open Export. ${error.name === 'AbortError' ? 'The request timed out.' : error.message} Try again, or Restore preview to use the main navigation. Your selected page remains here.`, false);
  } finally { clearTimeout(timeout); }
}));
window.addEventListener('pageshow', () => {
  if (previewExportStatus) {
    clearTimeout(previewExportRecoveryTimer);
    previewExportFeedback('', false);
    document.querySelectorAll('[data-preview-export]').forEach(link => { link.setAttribute('aria-disabled', 'false'); link.setAttribute('aria-busy', 'false'); });
    previewExportStatus.hidden = true;
  }
});
previewPage?.addEventListener('change', () => selectPreviewMode(activePreviewMode));
for (const [id, direction] of [['preview-previous', -1], ['preview-next', 1]]) {
  document.getElementById(id)?.addEventListener('click', () => {
    previewPage.selectedIndex += direction;
    selectPreviewMode(activePreviewMode);
    // At a boundary the activated button becomes disabled; retain a usable focus target.
    if (document.getElementById(id).disabled) previewPage.focus();
  });
}
document.getElementById('preview-expand')?.addEventListener('click', event => {
  const expanded = previewWorkspace.classList.toggle('expanded');
  event.currentTarget.setAttribute('aria-expanded', String(expanded));
  event.currentTarget.textContent = expanded ? 'Restore preview' : 'Expand preview';
  // Keep keyboard focus within the visible viewport without creating another dialog.
  for (const element of [...document.querySelector('main').children, ...document.body.children]) {
    if (element === previewWorkspace || element.contains(previewWorkspace) || element.tagName === 'SCRIPT') continue;
    if (expanded) { element.dataset.previewWasInert = String(element.inert); element.inert = true; }
    else if (element.dataset.previewWasInert !== undefined) { element.inert = element.dataset.previewWasInert === 'true'; delete element.dataset.previewWasInert; }
  }
});
function exitExpandedPreview(event) {
  if (event.key === 'Escape' && previewWorkspace.classList.contains('expanded')) {
    document.getElementById('preview-expand').click();
    document.getElementById('preview-expand').focus();
  }
}
previewWorkspace?.addEventListener('keydown', exitExpandedPreview);
previewFrame?.addEventListener('load', () => {
  try { previewFrame.contentDocument?.addEventListener('keydown', exitExpandedPreview); } catch (_) { /* Confined preview may be unavailable. */ }
});
function selectPreviewMode(mode) {
  if (!previewFrame) return;
  activePreviewMode = mode;
  const wordpress = mode === 'wordpress';
  document.querySelectorAll('.preview-mode').forEach((button) => {
    const selected = button.dataset.mode === mode;
    button.classList.toggle('secondary', !selected);
    button.setAttribute('aria-pressed', String(selected));
  });
  previewProfile?.closest('label').toggleAttribute('hidden', !wordpress);
  previewFrame.title = wordpress ? 'WordPress Gutenberg preview' : 'Semantic HTML preview';
  const option = previewPage?.selectedOptions[0];
  if (option?.value) previewFrame.title += ` — ${option.textContent}`;
  previewFrame.src = option?.value
    ? `/output-preview/${encodeURIComponent(option.dataset.slug)}.html?mode=${mode}&profile=${encodeURIComponent(previewProfile.value)}`
    : wordpress
    ? `/api/preview/wordpress?profile=${encodeURIComponent(previewProfile?.value || 'generic')}`
    : '/api/preview/html';
  const description = document.getElementById('preview-description');
  if (description) description.textContent = wordpress
    ? 'Approximate content and structure preview using local minimal CSS. Production WSU theme and plugins determine the final design.'
    : 'Semantic Preview shows the reviewed document independently of WordPress.';
  updatePreviewPage();
  announce(`${wordpress ? 'WordPress' : 'Semantic HTML'} preview selected.`);
}
document.querySelectorAll('.preview-mode').forEach((button) => button.addEventListener('click', () => selectPreviewMode(button.dataset.mode)));
previewProfile?.addEventListener('change', () => selectPreviewMode('wordpress'));
if (previewWorkspace) {
  previewProfile.value = previewWorkspace.dataset.profile;
  selectPreviewMode(activePreviewMode);
}

const exportForm = document.getElementById('export-form');
let exportMutationPending = false;
let contentExportPending = false;
function updateExportAvailability() {
  if (!exportForm) return;
  const prefix = document.querySelector('#media-export-form [name="image_prefix"]');
  const prefixChanged = prefix && prefix.value !== prefix.defaultValue;
  const stale = exportForm.dataset.reviewStale === 'true';
  const reviewRequired = exportForm.dataset.publicationReady !== 'true';
  exportForm.querySelector('button[type="submit"]').disabled = exportMutationPending || contentExportPending || reviewRequired || prefixChanged;
  const message = document.getElementById('export-availability-message');
  if (message) message.textContent = contentExportPending ? 'Exporting the reviewed document…'
    : exportMutationPending ? 'Finishing the media change before export…'
    : stale ? 'Reload Export to check the current reviews and generate fresh content.'
    : reviewRequired ? 'Export is unavailable until the required content reviews are resolved.'
    : prefixChanged ? 'Prepare the images ZIP and mapping CSV to save the new image prefix before exporting.' : 'Ready to export.';
  const link = document.getElementById('export-readiness-link');
  if (link) link.hidden = false;
  for (const button of document.querySelectorAll('#media-wxr-form button, #media-mapping-form button, #media-export-form button, #media-review-recovery-preview, #media-review-recovery-selection button')) {
    button.disabled = exportMutationPending || contentExportPending || exportForm.dataset.conversionBlocked === 'true';
  }
  if (prefix) prefix.disabled = exportMutationPending || contentExportPending;
}
exportForm?.querySelector('[name="target"]')?.addEventListener('change', updateExportAvailability);
updateExportAvailability();

function setExportMutationPending(pending) {
  exportMutationPending = pending;
  updateExportAvailability();
}
function applyExportReviewState(state) {
  document.getElementById('export-review-state').innerHTML = state.html;
  document.getElementById('unmapped-media').innerHTML = state.unmapped_html;
  exportForm.dataset.publicationReady = String(state.publication_ready);
  exportForm.dataset.reviewStale = 'false';
  updateExportAvailability();
}

function focusExportReadiness() {
  const target = document.getElementById('readiness-heading');
  if (target) {
    target.tabIndex = -1;
    target.focus({preventScroll: true});
    target.scrollIntoView({block: 'start'});
  }
}
function focusExportAfterMapping(data = {}) {
  const feedback = document.getElementById('readiness-mapping-feedback');
  if (feedback) {
    feedback.hidden = document.getElementById('media-mapping-result').hidden;
    feedback.replaceChildren();
    if (data.refresh_required) {
      feedback.className = 'media-mapping-feedback has-unmatched';
      feedback.append(document.createTextNode(`${data.refresh_required} existing attachment IDs were not refreshed. Choose the XML first, then confirm unchanged images in step 2 and match again before generating fresh content. `));
    } else {
      feedback.className = '';
      feedback.append(document.createTextNode(`${data.mapped || 0} mappings updated${data.unchanged ? `; ${data.unchanged} already current` : ''}. `));
    }
    const link = document.createElement('a'); link.href = '#media-mapping-result';
    link.textContent = 'View media matching results'; feedback.append(link);
    if (data.unmatched || data.ambiguous || (data.retained_images || []).length) {
      const manual = document.createElement('a'); manual.href = '#manual-media-tools';
      manual.dataset.manualMediaLink = ''; manual.textContent = 'Use manual CSV mapping';
      feedback.append(document.createTextNode(' · '), manual);
    }
  }
  focusExportReadiness();
}
document.getElementById('export-readiness-link')?.addEventListener('click', event => {
  event.preventDefault();
  focusExportReadiness();
});
document.getElementById('export-review-state')?.addEventListener('click', event => {
  if (!event.target.closest('a[href="#content-export-heading"]')) return;
  event.preventDefault();
  const heading = document.getElementById('content-export-heading');
  heading.tabIndex = -1; heading.focus({preventScroll: true}); heading.scrollIntoView({block: 'start'});
});

let recordedApprovalPlan = null;
document.getElementById('export-review-state')?.addEventListener('click', async event => {
  const button = event.target.closest('button');
  if (!button || !['media-review-recovery-preview', 'media-review-recovery-confirm', 'media-review-recovery-cancel'].includes(button.id)) return;
  if (contentExportPending || exportMutationPending) return;
  const selection = document.getElementById('media-review-recovery-selection');
  const message = document.getElementById('media-review-recovery-result');
  if (button.id === 'media-review-recovery-cancel') {
    selection.hidden = true; selection.replaceChildren(); recordedApprovalPlan = null;
    document.getElementById('media-review-recovery-preview')?.focus();
    return;
  }
  setExportMutationPending(true);
  try {
    if (button.id === 'media-review-recovery-confirm') {
      if (!recordedApprovalPlan) throw new Error('Preview recorded approvals again.');
      const data = await api('/api/media-review-recovery', {method: 'POST', headers: csrfHeaders(), body: JSON.stringify({
        token: recordedApprovalPlan.token, project_id: recordedApprovalPlan.project_id,
        block_ids: recordedApprovalPlan.rows.map(row => row.block_id)
      })});
      recordedApprovalPlan = null;
      applyExportReviewState(data.export_state);
      invalidateContentExport();
      document.getElementById('media-review-recovery-result').textContent = `${data.restored} recorded image approvals restored with their original dates. Current media mappings and newer decisions were kept. Undo last change restores the pending states.`;
      focusExportReadiness();
      announce(`${data.restored} recorded approvals restored. ${data.export_state.announcement}`);
    } else {
      recordedApprovalPlan = null;
      selection.replaceChildren(); selection.hidden = true;
      const plan = await api('/api/media-review-recovery');
      message.textContent = plan.notice;
      if (!plan.rows.length) return;
      recordedApprovalPlan = plan;
      const heading = document.createElement('h3');
      heading.textContent = `${plan.rows.length} recorded image approvals`; heading.tabIndex = -1;
      const list = document.createElement('ul');
      for (const row of plan.rows) {
        const item = document.createElement('li');
        item.textContent = `Source page ${row.source_page || 'unknown'} · ${row.block_id}: ${row.alt || row.caption || 'Decorative image'} · Originally approved ${row.approved_at}`;
        list.append(item);
      }
      const actions = document.createElement('div'); actions.className = 'button-row';
      const undoNotice = document.createElement('p'); undoNotice.id = 'media-review-recovery-undo-notice';
      undoNotice.textContent = 'Undo returns these images to pending review and removes a saved history snapshot. Restoring them again may be unavailable, requiring manual review before export.';
      const confirm = document.createElement('button'); confirm.type = 'button'; confirm.id = 'media-review-recovery-confirm';
      confirm.className = 'review-approve'; confirm.textContent = `Confirm restore ${plan.rows.length} recorded approvals`;
      confirm.setAttribute('aria-describedby', undoNotice.id);
      const cancel = document.createElement('button'); cancel.type = 'button'; cancel.id = 'media-review-recovery-cancel';
      cancel.className = 'neutral-action'; cancel.textContent = 'Cancel';
      actions.append(confirm, cancel); selection.append(heading, list, undoNotice, actions); selection.hidden = false;
      heading.focus({preventScroll: true}); heading.scrollIntoView({block: 'start'});
    }
  } catch (error) {
    recordedApprovalPlan = null; selection.hidden = true; selection.replaceChildren();
    const currentMessage = document.getElementById('media-review-recovery-result');
    currentMessage.textContent = error.message; announce(error.message); focusExportReadiness();
  } finally { setExportMutationPending(false); }
});

async function copyText(content) {
  try {
    await navigator.clipboard.writeText(content);
  } catch (error) {
    const focused = document.activeElement;
    const field = document.createElement('textarea');
    field.value = content;
    field.className = 'visually-hidden';
    field.setAttribute('readonly', '');
    document.body.append(field);
    try {
      field.select();
      if (!document.execCommand('copy')) throw error;
    } finally {
      field.remove();
      if (focused?.isConnected) focused.focus({preventScroll: true});
    }
  }
}
document.getElementById('draft-copy-instructions')?.addEventListener('click', async event => {
  const button = event.currentTarget;
  const text = document.getElementById('draft-copy-instructions-text');
  const message = document.getElementById('draft-copy-instructions-status');
  button.disabled = true; text.hidden = true; message.textContent = '';
  try {
    await copyText(text.value);
    message.textContent = 'Instructions copied. Attach the exported ZIP, then paste them in Codex or ChatGPT.';
  } catch {
    message.textContent = 'Copy failed. Select the instructions below and copy them manually.';
    text.hidden = false; text.focus({preventScroll: true}); text.select();
    text.scrollIntoView({block: 'center'});
  } finally {
    button.disabled = false;
    if (text.hidden) button.focus({preventScroll: true});
  }
});
async function copyExportHtml(file) {
  if (exportForm?.dataset.publicationReady !== 'true') {
    focusExportReadiness();
    throw new Error('Resolve the required content reviews before copying.');
  }
  const response = await fetch(file.url, {cache: 'no-store'});
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    if (response.status === 409) markExportReviewStale();
    throw new Error(error.detail || 'Could not read the exported HTML file.');
  }
  await copyText(await response.text());
}

function savedOutputControls(data) {
  const region = document.createElement('div'); region.className = 'saved-output-controls';
  const path = document.createElement('code'); path.textContent = data.output_root;
  const location = document.createElement('p'); location.append('Saved in this project: ', path);
  const open = document.createElement('button'); open.type = 'button'; open.className = 'review-approve';
  open.textContent = 'Open output folder';
  const status = document.createElement('p'); status.setAttribute('role', 'status');
  open.addEventListener('click', async () => {
    open.disabled = true;
    try {
      await api('/api/output-folder/open', {method: 'POST', headers: csrfHeaders(), body: JSON.stringify({project_root: data.project_root})});
      status.textContent = 'Output folder opened. Use the saved files here.';
    } catch (error) { status.textContent = error.message; }
    finally { open.disabled = false; announce(status.textContent); }
  });
  region.append(location, open, status);
  return region;
}

function browserCopy(file, label) {
  const details = document.createElement('details'); details.className = 'browser-copy-option';
  const summary = document.createElement('summary'); summary.textContent = 'Optional browser copy';
  const note = document.createElement('p'); note.className = 'helper-text'; note.textContent = 'This makes an extra copy wherever your browser saves downloads. The project file is already saved.';
  const link = document.createElement('a'); link.href = file.url; link.download = file.filename || '';
  link.textContent = label || `Save browser copy of ${file.path.split('/').pop()}`;
  details.append(summary, note, link);
  return details;
}
document.querySelectorAll('[data-open-project-output]').forEach(button => button.addEventListener('click', async () => {
  button.disabled = true;
  try {
    await api('/api/output-folder/open', {method: 'POST', headers: csrfHeaders(), body: JSON.stringify({project_root: document.body.dataset.projectRoot})});
    announce('Output folder opened. The mapping CSV is in wordpress/reports.');
  } catch (error) {
    document.getElementById('manual-media-notice').textContent = error.message;
    announce(error.message);
  } finally { button.disabled = false; }
}));
function markExportReviewStale() {
  const region = document.getElementById('export-review-state');
  const heading = document.createElement('h2'); heading.id = 'readiness-heading'; heading.tabIndex = -1;
  heading.textContent = 'Export readiness';
  const notice = document.createElement('p'); notice.setAttribute('role', 'status');
  notice.textContent = 'This page is out of date. Reload Export to check current reviews and generate fresh content before copying.';
  const reload = document.createElement('a'); reload.href = '/export'; reload.textContent = 'Reload Export';
  region.replaceChildren(heading, notice, reload);
  exportForm.dataset.publicationReady = 'false'; exportForm.dataset.reviewStale = 'true';
  recordedApprovalPlan = null;
  invalidateContentExport(); updateExportAvailability(); focusExportReadiness();
}
document.getElementById('copy-page-title')?.addEventListener('click', async () => {
  const message = document.getElementById('copy-page-title-status');
  message.textContent = '';
  try { await copyText(document.getElementById('export-page-title').value); message.textContent = 'Copied'; announce('Page title copied.'); }
  catch (error) { message.textContent = 'Copy failed'; announce(error.message); }
});
exportForm?.querySelectorAll('[name="title_in_template"], [name="heading_style"], [name="target"], [name="profile"], [name="post_type"], [name="wrap_in_section"]').forEach(field => field.addEventListener('change', invalidateContentExport));

exportForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (contentExportPending || exportMutationPending) return;
  if (exportForm.dataset.publicationReady !== 'true') {
    focusExportReadiness();
    announce('Resolve the required content reviews before exporting.');
    return;
  }
  const output = document.getElementById('export-result');
  contentExportPending = true;
  updateExportAvailability();
  const controls = [...exportForm.querySelectorAll('select, input[type="checkbox"]')];
  let focusResult = true;
  try {
    const prefixField = document.querySelector('#media-export-form [name="image_prefix"]');
    if (prefixField && prefixField.value !== prefixField.defaultValue) throw new Error('Prepare the images ZIP and mapping CSV to save the new image prefix before exporting content.');
    const values = Object.fromEntries(new FormData(event.currentTarget));
    values.title_in_template = event.currentTarget.elements.title_in_template.checked;
    controls.forEach(control => { control.disabled = true; });
    output.textContent = 'Exporting the reviewed document…';
    output.setAttribute('aria-busy', 'true');
    const data = await api('/api/export', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values) });
    resetQuitForm(exportForm);
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
      const actions = document.createElement('span');
      actions.className = 'export-file-actions';
      actions.append(browserCopy(file));
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
      path.textContent = `${data.project_root}/${file.path}`;
      item.append(actions, document.createElement('br'), path);
      files.append(item);
    });
    output.replaceChildren(heading, savedOutputControls(data), ...(data.media ? [media] : []), files);
    announce('Export complete.');
  } catch (error) {
    if (error.message.startsWith('Publication requires current review:')) {
      markExportReviewStale(); focusResult = false;
    }
    output.textContent = `Export failed: ${error.message} Correct the issue and try again.`; announce(error.message);
  }
  finally {
    controls.forEach(control => { control.disabled = false; });
    output.setAttribute('aria-busy', 'false');
    contentExportPending = false;
    updateExportAvailability();
    if (focusResult) { output.tabIndex = -1; output.focus({preventScroll: true}); output.scrollIntoView({block: 'start'}); }
  }
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
function revealManualMedia({focus = false, reason = ''} = {}) {
  const tools = document.getElementById('manual-media-tools');
  if (!tools) return;
  tools.open = true;
  if (reason) document.getElementById('manual-media-notice').textContent = reason;
  if (focus) {
    const heading = document.getElementById('manual-media-heading');
    heading.focus({preventScroll: true}); heading.scrollIntoView({block: 'start'});
  }
}
document.getElementById('open-manual-media')?.addEventListener('click', () => revealManualMedia({focus: true}));
document.addEventListener('click', event => {
  if (!event.target.closest('[data-manual-media-link]')) return;
  event.preventDefault(); revealManualMedia({focus: true});
});
function showMappingFeedback(message, data = {}, focus = true) {
  const output = document.getElementById('media-mapping-result');
  output.hidden = false;
  const missing = [...(data.unmatched_images || []), ...(data.ambiguous_images || []), ...(data.retained_images || []), ...(data.refreshable_images || [])];
  output.className = `media-mapping-feedback${missing.length ? ' has-unmatched' : ''}`;
  document.getElementById('media-mapping-announcement').textContent = message;
  const detail = document.getElementById('media-mapping-details');
  detail.replaceChildren();
  const add = (parent, tag, text) => { const element = document.createElement(tag); element.textContent = text; parent.append(element); return element; };
  if (data.matched !== undefined) {
    const table = document.createElement('table'); table.className = 'result-table';
    add(table, 'caption', 'Media matching summary');
    const body = document.createElement('tbody');
    for (const [key, label] of [['mapped', 'Mappings updated'], ['refresh_required', 'IDs not refreshed — confirmation required'], ['unchanged', 'Already current — no change needed'], ['matched', 'Filename matches'], ['unmatched', 'Unmatched filenames'], ['ambiguous', 'Ambiguous filenames'], ['existing_kept', 'Existing mappings kept']]) {
      if (data[key] === undefined) continue;
      const row = document.createElement('tr'); add(row, 'th', label).scope = 'row';
      add(row, 'td', String(data[key])).className = 'result-count'; body.append(row);
    }
    table.append(body); detail.append(table);
  }
  if (missing.length) {
    const wrap = document.createElement('div'); wrap.className = 'result-table-wrap';
    const table = document.createElement('table');
    add(table, 'caption', 'Mappings needing attention');
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
    if (data.refresh_required) add(detail, 'p', 'For IDs awaiting refresh: choose the XML first, confirm that the uploads are the same reviewed images using the checkbox in step 2, then match again. Filename matches alone do not update saved IDs.');
    if ((data.unmatched_images || []).length || (data.ambiguous_images || []).length || (data.retained_images || []).length) add(detail, 'p', 'Enter the correct WordPress URLs for these images in the mapping CSV, then import it under “Map images manually with a CSV”.');
    if (document.getElementById('manual-media-download')?.hidden === false) {
      add(detail, 'code', `${document.body.dataset.projectRoot}/output/wordpress/reports/media-mapping.csv`);
      detail.append(browserCopy({path: 'output/wordpress/reports/media-mapping.csv', url: '/download/output/wordpress/reports/media-mapping.csv'}));
    }
  }
  if (focus) { output.focus({preventScroll: true}); output.scrollIntoView({block: 'start'}); }
  if (data.unmatched || data.ambiguous || (data.retained_images || []).length) {
    revealManualMedia();
    const link = add(detail, 'a', 'Use manual CSV mapping for these images');
    link.href = '#manual-media-tools'; link.dataset.manualMediaLink = '';
  }
  announce(message);
}
const mediaExportForm = document.getElementById('media-export-form');
mediaExportForm?.querySelector('[name="image_prefix"]').addEventListener('input', () => {
  document.getElementById('media-export-result').replaceChildren();
  invalidateContentExport();
  updateExportAvailability();
});
mediaExportForm?.addEventListener('submit', async event => {
  event.preventDefault();
  if (contentExportPending || exportMutationPending) return;
  const form = event.currentTarget;
  const output = document.getElementById('media-export-result');
  const button = form.querySelector('button[type="submit"]');
  const values = Object.fromEntries(new FormData(form));
  button.disabled = true;
  setExportMutationPending(true);
  try {
    const data = await api('/api/media-export', {method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values)});
    const field = form.querySelector('[name="image_prefix"]');
    field.value = field.defaultValue = data.image_prefix;
    resetQuitForm(form);
    output.replaceChildren(document.createTextNode(`${data.media.copied_assets} images packaged. Unzip and upload them to WordPress, then map their URLs in step 2. `));
    output.append(savedOutputControls(data));
    for (const file of data.downloads) {
      const path = document.createElement('code'); path.textContent = `${data.project_root}/${file.path}`;
      output.append(document.createElement('br'), path, browserCopy(file));
    }
    showMappingStatus(data.media.unresolved);
    document.getElementById('manual-media-download').hidden = false;
    announce('Images ZIP and mapping CSV are ready.');
  } catch (error) { output.textContent = error.message; announce(error.message); }
  finally { setExportMutationPending(false); }
});
document.getElementById('media-export-undo')?.addEventListener('click', async () => {
  if (contentExportPending || exportMutationPending) return;
  setExportMutationPending(true);
  try {
    const data = await api('/api/media-export/undo', {method: 'POST', headers: csrfHeaders(), body: '{}'});
    applyExportReviewState(data.export_state);
    const prefix = mediaExportForm.querySelector('[name="image_prefix"]');
    prefix.value = prefix.defaultValue = data.image_prefix;
    exportForm.elements.title_in_template.checked = data.publication.title_in_template ?? true;
    exportForm.elements.heading_style.value = data.publication.heading_style || 'nested';
    resetQuitForm(mediaExportForm); resetQuitForm(exportForm);
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
  if (contentExportPending || exportMutationPending) return;
  const output = document.getElementById('media-mapping-result');
  const form = event.currentTarget;
  const file = new FormData(form).get('mapping');
  setExportMutationPending(true);
  try {
    if (!(file instanceof File)) throw new Error('Choose a media mapping CSV.');
    const data = await api('/api/media-mapping', {
      method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ csv: await file.text() })
    });
    applyExportReviewState(data.export_state);
    resetQuitForm(form);
    showMappingFeedback(`${data.mapped} image mapping${data.mapped === 1 ? '' : 's'} imported; ${data.remaining} images still need URLs. ${data.export_state.announcement}`, data, false);
    showMappingStatus(data.remaining);
    focusExportAfterMapping(data);
  } catch (error) { showMappingFeedback(error.message); }
  finally { setExportMutationPending(false); }
});

document.querySelector('#media-wxr-form [name="media_wxr"]')?.addEventListener('change', () => {
  const refresh = document.getElementById('refresh-existing-media');
  const notice = document.getElementById('media-refresh-selection-notice');
  const cleared = !!refresh?.checked;
  if (refresh) refresh.checked = false;
  if (notice) {
    notice.hidden = !cleared;
    notice.textContent = cleared ? 'Refresh confirmation cleared because the XML selection changed. Check it again after choosing the file if these are the same reviewed images.' : '';
  }
  if (cleared) announce('Refresh confirmation cleared because the XML selection changed. Check it again if these are the same reviewed images.');
});
document.getElementById('refresh-existing-media')?.addEventListener('change', () => {
  const notice = document.getElementById('media-refresh-selection-notice');
  if (notice) { notice.hidden = true; notice.textContent = ''; }
});
document.getElementById('media-wxr-form')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (contentExportPending || exportMutationPending) return;
  const output = document.getElementById('media-mapping-result');
  const form = event.currentTarget;
  const formData = new FormData(form);
  const file = formData.get('media_wxr');
  const refreshExisting = formData.has('refresh_existing');
  setExportMutationPending(true);
  try {
    if (!(file instanceof File)) throw new Error('Choose a WordPress media XML file.');
    const data = await api('/api/media-mapping-wxr', {
      method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ xml: await file.text(), refresh_existing: refreshExisting })
    });
    applyExportReviewState(data.export_state);
    resetQuitForm(form);
    const outcome = data.refresh_required
      ? `${data.refresh_required} existing attachment IDs were not refreshed because confirmation was not selected. ${data.mapped} mappings updated; ${data.unchanged} already current. Choose the XML first, then confirm unchanged images in step 2 and match again before generating fresh content.`
      : `${data.mapped} mappings updated; ${data.unchanged || 0} already current (no change needed).`;
    showMappingFeedback(`${outcome} ${data.matched} filename matches in ${data.attachments_found} media attachments; ${data.unmatched} unmatched and ${data.ambiguous} ambiguous. ${data.existing_kept || 0} existing mappings kept.`, data, false);
    showMappingStatus(data.remaining);
    focusExportAfterMapping(data);
  } catch (error) {
    showMappingFeedback(error.message);
    revealManualMedia({reason: 'XML matching failed. Prepare or download the mapping CSV, enter the correct WordPress URLs, then import it here. Keep block IDs unchanged.'});
    const link = document.createElement('a'); link.href = '#manual-media-tools';
    link.dataset.manualMediaLink = ''; link.textContent = 'Use manual CSV mapping';
    document.getElementById('media-mapping-details').append(link);
  }
  finally { setExportMutationPending(false); }
});

document.documentElement.dataset.appReady = 'true';

const pageEditor = document.getElementById('page-editor');
const pageMessage = document.getElementById('output-page-message');
const selectedPageId = () => pageEditor?.dataset.pageId;
const pageMetadata = document.getElementById('output-page-metadata');
const pageMetadataValue = () => pageMetadata ? JSON.stringify([...new FormData(pageMetadata)]) : '';
const initialPageMetadata = pageMetadataValue();
const pageApprovalForm = document.getElementById('output-page-approval');
const pageApprovalValue = () => pageApprovalForm ? JSON.stringify([...new FormData(pageApprovalForm)]) : '';
const initialPageApproval = pageApprovalValue();
function outputPreviewLink() {
  const requested = new URLSearchParams(location.search);
  const mode = document.getElementById('output-page-preview') ? (document.getElementById('output-page-preview').getAttribute('aria-pressed') === 'true' ? 'semantic' : 'wordpress') : (requested.get('mode') === 'semantic' ? 'semantic' : 'wordpress');
  return `/preview?${new URLSearchParams({page_id: selectedPageId() || '', mode, profile: document.getElementById('output-page-profile')?.value || (requested.get('profile') === 'wsuwp' ? 'wsuwp' : 'generic')})}`;
}
if (pageEditor) {
  document.querySelectorAll('a[href="/preview"]').forEach(link => link.href = outputPreviewLink());
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link || link.target === '_blank' || link.origin !== location.origin) return;
    try {
      requireSavedPageMetadata();
      if (pageActionPending) throw new Error('Wait for the page save to finish.');
      if (link.pathname === '/preview') link.href = outputPreviewLink();
    } catch (error) { event.preventDefault(); pageMessage.textContent = error.message; pageMessage.scrollIntoView({block: 'nearest'}); }
  });
  window.addEventListener('beforeunload', event => {
    if (!pageActionPending && (pageMetadataValue() !== initialPageMetadata || pageApprovalValue() !== initialPageApproval)) {
      event.preventDefault(); event.returnValue = '';
    }
  });
}

let pageActionPending = false;
let pageReloadRequired = false;
function lockPageMetadata() {
  const fields = [...(pageEditor?.querySelectorAll('input, select, textarea, button') || [])];
  const states = fields.map(e => e.disabled);
  fields.forEach(e => {e.disabled = true;});
  return () => fields.forEach((e, i) => {e.disabled = states[i];});
}
function requireSavedPageMetadata(allowApprovalDraft = false) {
  if (pageReloadRequired) throw new Error('The last save could not be confirmed. Reload before changing this arrangement.');
  if (pageMetadataValue() !== initialPageMetadata) throw new Error('Save or revert the unsaved page title, slug and metadata before changing the arrangement. Your draft remains here.');
  if (!allowApprovalDraft && pageApprovalValue() !== initialPageApproval) throw new Error('Save or revert the unsaved page reviewer note before changing the arrangement. Your draft remains here.');
}
async function pageAction(action, values = {}) {
  if (pageActionPending) return;
  let sent = false;
  let unlockMetadata = () => {};
  try {
    if (action !== 'metadata') requireSavedPageMetadata(action === 'approve');
    else if (pageApprovalValue() !== initialPageApproval) throw new Error('Save or revert the unsaved page reviewer note first. Your drafts remain here.');
    if (pageReloadRequired) throw new Error('Reload before another arrangement save.');
    pageActionPending = true;
    unlockMetadata = lockPageMetadata();
    sent = true;
    const result = await api(`/api/output-pages/${action}`, { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ page_id: selectedPageId(), ...values }) });
    sessionStorage.setItem('output-page-announcement', 'Changes saved.');
    const destination = `/output-pages?page_id=${encodeURIComponent(result.page_id || '')}`;
    if (location.pathname + location.search === destination) {
      location.hash = 'page-editor';
      location.reload();
    } else window.location.assign(destination + '#page-editor');
  } catch (error) {
    if (sent && !error.confirmedRejection) { pageReloadRequired = true; error.message = 'Save result could not be confirmed. Your draft remains here. Reload before another arrangement change.'; }
    pageMessage.textContent = error.message;
  } finally { unlockMetadata(); pageActionPending = false; }
}
function automaticPageSlug(title, used = []) {
  let base = String(title).normalize('NFKD').replace(/[^\x00-\x7f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'page';
  base = base.slice(0, 100).replace(/-+$/g, '');
  let slug = base, suffix = 2;
  while (used.includes(slug) || ['contents', 'publications'].includes(slug)) {
    const ending = `-${suffix++}`;
    slug = base.slice(0, 100 - ending.length).replace(/-+$/g, '') + ending;
  }
  return slug;
}
function syncAutomaticPageSlug() {
  if (!pageMetadata || pageMetadata.elements.slug_mode.value !== 'auto') return;
  pageMetadata.elements.slug.value = automaticPageSlug(pageMetadata.elements.title.value, JSON.parse(pageMetadata.dataset.otherSlugs || '[]'));
  document.getElementById('page-slug-status').textContent = 'Automatic from title';
}
pageMetadata?.elements.title.addEventListener('input', syncAutomaticPageSlug);
pageMetadata?.elements.slug.addEventListener('input', () => {
  pageMetadata.elements.slug_mode.value = 'custom';
  document.getElementById('page-slug-status').textContent = 'Custom slug — title edits keep this value';
});
document.getElementById('page-slug-auto')?.addEventListener('click', () => {
  pageMetadata.elements.slug_mode.value = 'auto'; syncAutomaticPageSlug();
});
document.getElementById('output-page-add-content')?.addEventListener('click', () => {
  const outline = document.getElementById('content-outline'); outline.open = true;
  const summary = outline.querySelector('summary'); summary.focus(); summary.scrollIntoView({block: 'center'});
});

const groupingRoot = document.getElementById('grouping-suggestions');
const groupingProposal = document.getElementById('grouping-proposal');
const groupingStatus = document.getElementById('grouping-status');
let groupingSnapshot = null;
let groupingRequest = 0;
let groupingBusy = false;
let groupingChoices = {};
function groupingValues() {
  return {method: groupingRoot.querySelector('[name=grouping_method]:checked').value,
    selected: [...groupingRoot.querySelectorAll('[name=suggestion]:checked')].map(e => Number(e.value)), choices: {...groupingChoices}};
}
function invalidateGrouping() {
  groupingSnapshot = null;
  groupingRequest++;
  document.getElementById('grouping-apply').disabled = true;
  if (!groupingProposal.hidden) groupingStatus.textContent = 'Selection changed. Preview this arrangement again before applying.';
}
function groupingText(parent, tag, value) {
  const node = document.createElement(tag); node.textContent = value; parent.append(node); return node;
}
function renderGroupingProposal(proposal) {
  groupingProposal.replaceChildren(); groupingProposal.hidden = false;
  groupingText(groupingProposal, 'h3', proposal.method === 'titles' ? `${proposal.pages.length} existing output pages — title refresh` : `${proposal.pages.length} proposed output pages`);
  groupingText(groupingProposal, 'p', proposal.method === 'titles' ? 'Apply updates only recognized generated titles and their automatic slugs. Content assignments, custom titles, manual slugs and reconstruction labels stay unchanged. Review the before-and-after fields below. This is one saved change with Undo; changed page metadata still requires normal review.' : 'This is a proposal. Apply saves one arrangement with Undo. Existing block content, review decisions and reconstruction holds are retained. Publication still requires complete assignments and review.');
  for (const note of proposal.notes || []) groupingText(groupingProposal, 'p', note);
  for (const error of proposal.errors || []) groupingText(groupingProposal, 'p', `Needs a decision: ${error}`);
  if (proposal.publication_findings?.length) {
    const findings = groupingText(groupingProposal, 'details', '');
    groupingText(findings, 'summary', `${proposal.publication_findings.length} arrangement requirements before publication`);
    const items = groupingText(findings, 'ul', '');
    for (const finding of proposal.publication_findings) groupingText(items, 'li', finding);
  }
  const list = groupingText(groupingProposal, 'ol', '');
  for (const item of proposal.pages) {
    const row = groupingText(list, 'li', '');
    groupingText(row, 'strong', item.title);
    groupingText(row, 'small', ` · ${item.block_ids.length} blocks${item.manual_reconstruction_source_page ? ' · Needs reconstruction' : item.block_ids.length === 0 ? ' · Needs content' : ''}`);
    const sourcePage = item.manual_reconstruction_source_page || item.source_page_group;
    if (sourcePage) {
      const link = groupingText(row, 'a', ` · Open source page ${sourcePage} in Structure`);
      link.href = `/structure?source_page=${sourcePage}`; link.target = '_blank'; link.rel = 'noopener';
    }
    const details = groupingText(row, 'details', ''); groupingText(details, 'summary', 'Content in Structure order');
    const blocks = groupingText(details, 'ul', '');
    for (const b of item.preview_blocks || []) groupingText(blocks, 'li', `Block ${b.number}: ${b.snippet}${b.excluded ? ' (excluded, retained)' : ''}`);
  }
  const effects = groupingText(groupingProposal, 'details', ''); groupingText(effects, 'summary', 'Existing pages and metadata');
  const effectList = groupingText(effects, 'ul', '');
  const effectNames = {source_order: 'Move to source-page order', reset_parent: 'Use no parent because the former parent is replaced', replace: 'Replace this page; Undo restores its metadata', assignments_changed: 'Move selected content; retain page metadata', refresh_title: 'Update generated title; keep content assignments'};
  for (const effect of proposal.effects || []) {
    const row = groupingText(effectList, 'li', `${effect.title}: ${effectNames[effect.action] || 'Update page'}`);
    const fields = groupingText(row, 'ul', '');
    for (const field of effect.display_fields || []) groupingText(fields, 'li', `${field.label}: ${field.before} → ${effect.action === 'replace' ? 'Replaced; recoverable with Undo' : field.after}`);
  }
  const moves = groupingText(groupingProposal, 'details', ''); groupingText(moves, 'summary', `${proposal.moves.length} selected block moves`);
  const moveList = groupingText(moves, 'ul', '');
  for (const move of proposal.moves) groupingText(moveList, 'li', `Block ${move.block_number || move.block_id}: ${move.from_title || 'Unassigned'} → ${move.to_title}`);
  for (const exception of proposal.exceptions || []) {
    if (exception.held_source_pages?.length) {
      groupingText(groupingProposal, 'p', `${exception.label}: restore the held source page before moving this semantic bundle.`);
      for (const number of exception.held_source_pages) {
        const link = groupingText(groupingProposal, 'a', `Open source page ${number} in Structure`);
        link.href = `/structure?source_page=${number}`; link.target = '_blank'; link.rel = 'noopener';
      }
      continue;
    }
    const label = groupingText(groupingProposal, 'label', `${exception.label || exception.reason}: choose its destination`);
    const select = groupingText(label, 'select', '');
    const empty = groupingText(select, 'option', 'Choose source page'); empty.value = '';
    for (const item of proposal.groups || []) {
      const number = item.source_pages?.length === 1 ? item.source_pages[0] : null;
      const page = proposal.pages.find(p => p.id === item.page_id);
      if (!number || page?.manual_reconstruction_source_page) continue;
      const option = groupingText(select, 'option', `Source page ${number}`); option.value = String(number);
    }
    select.value = String(groupingChoices[exception.key] || '');
    select.addEventListener('change', () => {if (select.value) groupingChoices[exception.key] = Number(select.value); else delete groupingChoices[exception.key]; invalidateGrouping();});
  }
  document.getElementById('grouping-apply-actions').hidden = false;
}
groupingRoot?.querySelectorAll('[name=grouping_method]').forEach(input => input.addEventListener('change', () => {
  const source = groupingValues().method === 'source';
  document.getElementById('source-grouping-options').hidden = !source;
  document.getElementById('heading-grouping-options').hidden = source;
  document.getElementById('grouping-preview').textContent = source ? 'Preview source-page arrangement' : 'Preview selected suggestions';
  document.getElementById('grouping-apply').textContent = source ? 'Apply source-page arrangement' : 'Apply selected suggestions';
  groupingChoices = {}; invalidateGrouping();
}));
groupingRoot?.querySelectorAll('[name=suggestion]').forEach(input => input.addEventListener('change', invalidateGrouping));
for (const [id, checked] of [['grouping-select-all', true], ['grouping-clear-all', false]]) document.getElementById(id)?.addEventListener('click', () => {
  groupingRoot.querySelectorAll('[name=suggestion]').forEach(input => {input.checked = checked;}); invalidateGrouping();
});
async function previewGrouping(method = null) {
  if (groupingBusy || pageActionPending) return;
  groupingBusy = true;
  const request = ++groupingRequest, values = groupingValues();
  if (method) values.method = method;
  groupingStatus.textContent = 'Preparing arrangement preview…';
  try {
    const result = await api('/api/page-grouping/preview', {method: 'POST', headers: csrfHeaders(), body: JSON.stringify(values)});
    if (request !== groupingRequest) return;
    renderGroupingProposal(result.proposal);
    groupingSnapshot = {values, expected_review_token: result.expected_review_token, proposal_digest: result.proposal_digest};
    document.getElementById('grouping-apply').disabled = !result.proposal.can_apply;
    document.getElementById('grouping-apply').textContent = values.method === 'titles' ? 'Apply generated page titles' : values.method === 'source' ? 'Apply source-page arrangement' : 'Apply selected suggestions';
    groupingStatus.textContent = result.proposal.can_apply ? 'Proposal ready. Review the pages and selected moves before Apply.' : result.proposal.errors.length ? 'Resolve the assignment questions, then preview again.' : values.method === 'titles' ? 'No recognized generated titles need updating. Custom titles and slugs remain unchanged.' : 'Select at least one heading suggestion, then preview again.';
    groupingProposal.focus();
  } catch (error) {groupingStatus.textContent = error.message;}
  finally {groupingBusy = false;}
}
document.getElementById('grouping-preview')?.addEventListener('click', () => previewGrouping());
document.getElementById('grouping-title-preview')?.addEventListener('click', () => previewGrouping('titles'));
document.getElementById('grouping-apply')?.addEventListener('click', async () => {
  if (!groupingSnapshot || groupingBusy || pageActionPending) return;
  let sent = false;
  let unlockMetadata = () => {};
  try {
    requireSavedPageMetadata();
    groupingBusy = true; pageActionPending = true;
    unlockMetadata = lockPageMetadata();
    document.getElementById('grouping-apply').disabled = true;
    sent = true;
    const {values, ...verification} = groupingSnapshot;
    const result = await api('/api/page-grouping/apply', {method: 'POST', headers: csrfHeaders(), body: JSON.stringify({...values, ...verification})});
    sessionStorage.setItem('output-page-announcement', 'Arrangement saved. Undo last action restores the previous pages and metadata.');
    window.location.assign(`/output-pages?page_id=${encodeURIComponent(result.page_id || '')}#page-editor`);
  } catch (error) {
    if (sent && !error.confirmedRejection) {pageReloadRequired = true; error.message = 'Apply result could not be confirmed. Your draft remains here. Reload before another arrangement change.';}
    invalidateGrouping();
    groupingStatus.textContent = error.message;
  } finally {unlockMetadata(); groupingBusy = false; pageActionPending = false;}
});
document.getElementById('grouping-cancel')?.addEventListener('click', () => {
  if (groupingBusy) return;
  invalidateGrouping(); groupingProposal.hidden = true;
  document.getElementById('grouping-apply-actions').hidden = true;
  groupingStatus.textContent = 'Proposal cancelled. Saved arrangement unchanged.';
  document.getElementById('grouping-preview').focus();
});
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
  const slug = pageEditor.dataset.pageSlug;
  const profile = document.getElementById('output-page-profile').value;
  const wordpress = mode === 'wordpress';
  const frame = document.getElementById('output-page-frame');
  frame.title = wordpress ? 'WordPress page preview' : 'Semantic HTML page preview';
  frame.src = `/output-preview/${encodeURIComponent(slug)}.html?mode=${mode}&profile=${encodeURIComponent(profile)}`;
  for (const [id, active] of [['output-page-preview', !wordpress], ['output-page-wordpress-preview', wordpress]]) {
    const button = document.getElementById(id);
    button.setAttribute('aria-pressed', String(active));
    button.classList.toggle('secondary', !active);
  }
}
document.getElementById('output-page-preview')?.addEventListener('click', () => previewOutputPage('semantic'));
document.getElementById('output-page-wordpress-preview')?.addEventListener('click', () => previewOutputPage('wordpress'));
if (document.getElementById('output-page-frame')) {
  const requested = new URLSearchParams(location.search);
  if (['generic', 'wsuwp'].includes(requested.get('profile'))) document.getElementById('output-page-profile').value = requested.get('profile');
  if (['semantic', 'wordpress'].includes(requested.get('mode'))) previewOutputPage(requested.get('mode'));
}
document.getElementById('output-page-profile')?.addEventListener('change', () => {
  if (document.getElementById('output-page-wordpress-preview').getAttribute('aria-pressed') === 'true') previewOutputPage('wordpress');
});
document.querySelectorAll('[data-page-export]').forEach(button => button.addEventListener('click', async () => {
  try {
    const result = await api('/api/output-pages/export', { method: 'POST', headers: csrfHeaders(), body: JSON.stringify({ page_id: button.dataset.pageExport === 'individual' ? selectedPageId() : null, profile: document.getElementById('output-page-profile').value }) });
    pageMessage.replaceChildren(document.createTextNode('Export complete. Review the manifest and manual import instructions. '));
    pageMessage.append(savedOutputControls(result));
    for (const file of result.downloads) {
      const path = document.createElement('code'); path.textContent = `${result.project_root}/${file.path}`;
      pageMessage.append(path, browserCopy(file), document.createElement('br'));
    }
  } catch (error) { pageMessage.textContent = error.message; }
}));

// Image drafts use the Structure editor and its existing Undo and focus behavior.
const draftToolbar = document.getElementById('image-draft-toolbar');
if (draftToolbar) {
  const message = document.getElementById('draft-message');
  const workflowStatus = document.getElementById('draft-workflow-status');
  const updateWorkflowStatus = entries => {
    const notes = [];
    for (const [status, label] of [['generating', 'generating'], ['failed', 'failed — retry or inspect the error'], ['stale', 'context changed — inspect drafting tools'], ['requested', 'awaiting response'], ['ready', 'drafts ready — review image blocks']]) {
      const count = entries.filter(entry => entry.status === status).length;
      if (count) notes.push(`${count} ${label}`);
    }
    if (workflowStatus) workflowStatus.textContent = notes.length ? `${notes.join('; ')}. Images still require review.` : 'Drafting is optional. Images still require review.';
    // Completion changes the next-visit default through saved request history.
    // Never collapse a live editor, replace a preference or move focus here.
  };
  const reportDraftError = error => { message.textContent = error.message; if (workflowStatus) workflowStatus.textContent = `Drafting needs attention: ${error.message}`; };
  const docId = draftToolbar.dataset.documentId;
  const postDraft = (action, data) => { if (['populate', 'associate', 'edit', 'apply', 'reject', 'cancel'].includes(action) || action === 'import' && data.commit) requireSavedAuthoring(); return api(`/api/image-drafts/${action}`, {method: 'POST', headers: csrfHeaders(), body: JSON.stringify({document_id: docId, ...data})}); };
  const panelFor = id => [...document.querySelectorAll('.image-draft-panel')].find(p => p.dataset.blockId === id);
  const reloadDraft = id => { requireSavedAuthoring(); if (id) sessionStorage.setItem(reviewAdvanceKey, `block-${id}`); location.reload(); };
  const providerSelect = document.getElementById('draft-provider');
  const providerMessage = document.getElementById('draft-provider-message');
  const updateProviderSetup = () => {
    document.getElementById('draft-manual-route').hidden = providerSelect.value !== 'manual';
    document.getElementById('draft-provider-route').hidden = providerSelect.value === 'manual';
    document.querySelectorAll('[data-draft-action="generate"], [data-draft-action="regenerate"]').forEach(button => { button.hidden = providerSelect.value === 'manual'; });
    document.querySelectorAll('[data-draft-action="export"], [data-draft-action="export-new"]').forEach(button => { button.hidden = providerSelect.value !== 'manual'; });
    document.getElementById('draft-model-label').hidden = providerSelect.value !== 'ollama-local';
    const help = document.getElementById('draft-provider-help');
    help.textContent = JSON.parse(help.dataset.providerHelp)[providerSelect.value];
    const generateButton = draftToolbar.querySelector('[data-draft-batch="generate"]');
    generateButton.textContent = providerSelect.value === 'manual' ? 'Export selected ZIP (manual provider)'
      : providerSelect.value === 'openai' ? 'Generate selected with OpenAI' : 'Generate selected with local Ollama';
  };
  providerSelect.addEventListener('change', () => {
    updateProviderSetup();
    providerMessage.textContent = 'Selection changed. Save provider settings to keep it when you reopen this project.';
  });
  document.getElementById('draft-provider-form').addEventListener('submit', async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector('button[type="submit"]');
    const keepFocus = document.activeElement === button;
    try {
      button.disabled = true;
      await postDraft('settings', {provider: providerSelect.value, model: document.getElementById('draft-model').value});
      resetQuitForm(form);
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
  const exportScope = document.getElementById('draft-export-scope');
  const exportIds = () => exportScope.value === 'selected' ? selectedIds() : pendingIds();
  const updateBatchControls = () => {
    const ids = selectedIds();
    const pending = pendingIds();
    document.getElementById('draft-selection-summary').textContent = `${ids.length} images selected · ${pending.length} pending images needing drafts.`;
    exportScope.options[0].textContent = `All pending images (${pending.length})`;
    exportScope.options[1].textContent = `Selected images (${ids.length})`;
    document.querySelectorAll('[data-draft-batch]').forEach(button => {
      const action = button.dataset.draftBatch;
      if (action === 'cancel') button.hidden = !ids.some(id => ['requested', 'generating'].includes(panelFor(id)?.dataset.requestStatus));
      else button.disabled = !(action === 'export' ? exportIds().length : ids.length);
    });
  };
  document.querySelectorAll('.draft-selection').forEach(input => input.addEventListener('change', updateBatchControls));
  exportScope.addEventListener('change', updateBatchControls);
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
    const responsePath = document.getElementById('draft-response-path');
    if (typeof result.manual_instructions === 'string' && result.response_delivery?.suggested_path) {
      document.getElementById('draft-copy-instructions-text').value = result.manual_instructions;
      if (responsePath) responsePath.textContent = result.response_delivery.suggested_path;
      document.getElementById('draft-copy-instructions-status').textContent = '';
    } else {
      document.getElementById('draft-copy-instructions-status').textContent = 'Save your work and relaunch the app to include the project response destination in the ZIP and copied instructions.';
    }
    const controls = savedOutputControls(result);
    const open = controls.querySelector('button');
    const saved = document.createElement('p'); saved.className = 'draft-saved-path';
    const location = document.createElement('code'); location.textContent = result.saved_path;
    saved.append('Saved in this project: ', location);
    document.getElementById('draft-downloads').replaceChildren(controls, saved, browserCopy(result, 'Save browser copy of image-draft ZIP'));
    document.getElementById('draft-export-message').textContent = 'Image-draft ZIP saved in this project. Open the output folder and attach the ZIP with the copied instructions. Imported descriptions still need review.';
    message.textContent = '';
    open.focus({preventScroll: true});
    open.scrollIntoView({block: 'start'});
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
    } catch (error) { reportDraftError(error); }
  });
  document.getElementById('draft-transmission-cancel').addEventListener('click', () => { cloudRequest = null; document.getElementById('draft-transmission').hidden = true; message.textContent = 'Cloud request cancelled.'; });
  document.querySelectorAll('[data-draft-batch]').forEach(button => button.addEventListener('click', async () => {
    const ids = button.dataset.draftBatch === 'export' ? exportIds() : selectedIds();
    const exporting = ['export', 'pending'].includes(button.dataset.draftBatch);
    const resultMessage = exporting ? document.getElementById('draft-export-message') : message;
    try {
      if (!ids.length) throw new Error('Select at least one image.');
      resultMessage.textContent = 'Preparing image requests…';
      if (exporting) showDownload(await postDraft('export', {block_ids: ids}));
      else if (button.dataset.draftBatch === 'generate') await generate(ids);
      else {
        const current = await api('/api/image-drafts');
        if (current.document_id !== docId) throw new Error('Project changed; reload this screen.');
        for (const entry of current.entries.filter(e => ids.includes(e.block_id) && ['requested', 'generating'].includes(e.status))) await postDraft('cancel', entry);
        reloadDraft(ids[0]);
      }
    } catch (error) {
      resultMessage.textContent = error.message;
      resultMessage.tabIndex = -1; resultMessage.focus(); resultMessage.scrollIntoView({block: 'nearest'});
    }
  }));
  document.querySelectorAll('.draft-association-form').forEach(form => form.addEventListener('submit', async event => {
    event.preventDefault();
    try { await postDraft('associate', {...Object.fromEntries(new FormData(form)), block_id: form.dataset.blockId}); reloadDraft(form.dataset.blockId); }
    catch (error) { reportDraftError(error); announce(error.message); }
  }));
  document.querySelectorAll('.draft-edit-form').forEach(form => form.addEventListener('submit', async event => {
    event.preventDefault();
    try { await postDraft('edit', {block_id: form.dataset.blockId, request_id: form.dataset.requestId, draft: draftValues(form)}); reloadDraft(form.dataset.blockId); }
    catch (error) { reportDraftError(error); announce(error.message); }
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
    } catch (error) { reportDraftError(error); announce(error.message); }
  }));
  document.getElementById('draft-import-preview').addEventListener('click', async () => {
    importPayload = null; document.getElementById('draft-import-confirm').disabled = true;
    try {
      const file = document.getElementById('draft-response-file').files[0];
      if (!file) throw new Error('Choose a response JSON file.');
      if (file.size > 4 * 1024 * 1024) throw new Error('Response exceeds 4 MiB.');
      const payload = JSON.parse(await file.text());
      const result = await postDraft('import', {response: payload});
      const findings = document.getElementById('draft-import-findings');
      const blankTemplate = !result.valid_count && payload.responses?.length && payload.responses.every(row => typeof row.alt === 'string' && !row.alt.trim())
        && result.findings.every(f => f.error.startsWith('Invalid alt:'));
      if (blankTemplate) {
        findings.textContent = `Unfilled response template: all ${payload.responses.length} alt-text fields are blank. Send the exported ZIP with the copied instructions to your drafting tool, then upload its completed response JSON. Nothing was imported.`;
      } else {
        const groups = new Map();
        for (const finding of result.findings) groups.set(finding.error, (groups.get(finding.error) || 0) + 1);
        findings.textContent = `${result.valid_count} valid drafts. ${[...groups].map(([error, count]) => `${count} ${count === 1 ? 'entry' : 'entries'}: ${error}`).join(' ')}`;
      }
      importPayload = payload; document.getElementById('draft-import-confirm').disabled = !result.valid_count;
    } catch (error) { document.getElementById('draft-import-findings').textContent = error.message; reportDraftError(error); }
  });
  document.getElementById('draft-import-confirm').addEventListener('click', async () => {
    try { requireSavedAuthoring(); const result = await postDraft('import', {response: importPayload, commit: true});
      if (!result.valid_count) throw new Error(result.findings.map(f => f.error).join(' '));
      reloadDraft();
    } catch (error) { document.getElementById('draft-import-findings').textContent = error.message; reportDraftError(error); }
  });
  document.getElementById('draft-populate').addEventListener('click', async () => {
    try { requireSavedAuthoring(); await postDraft('populate', {}); reloadDraft(); } catch (error) { reportDraftError(error); }
  });
  document.getElementById('draft-refresh').addEventListener('click', () => { try { reloadDraft(); } catch (error) { reportDraftError(error); announce(error.message); } });
  // Update status only; polling must not discard unsaved reviewer edits or move focus.
  const pollDrafts = async () => {
    try {
      const result = await api('/api/image-drafts');
      if (result.document_id !== docId) { message.textContent = 'Project changed; reload this screen.'; if (workflowStatus) workflowStatus.textContent = message.textContent; return; }
      updateWorkflowStatus(result.entries);
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
    } catch (error) { reportDraftError(error); if (workflowStatus) workflowStatus.textContent = `Draft status could not be refreshed: ${error.message}`; }
  };
  setInterval(pollDrafts, 2500);
}

// Page-order drafts are isolated from block authoring until one confirmed Apply.
window.addEventListener('reading-order-ready', () => {
  window.initializeReadingOrder({
    api, headers: csrfHeaders, announce,
    guard() {
      if (reviewWriteBusy) throw new Error('Wait for the current save before repairing reading order.');
      if (reviewReloadRequired) throw new Error('Reload to confirm the previous save before repairing reading order.');
      const dirty = authoringForms.find(form => authoringBaselines.get(form) !== authoringValue(form));
      const otherDraft = [...document.querySelectorAll('.draft-edit-form, .draft-association-form, #draft-provider-form')].find(form => [...form.elements].some(field =>
        !field.disabled && (field.tagName === 'TEXTAREA' || field.tagName === 'INPUT' && field.type !== 'hidden' || field.tagName === 'SELECT') &&
        (['checkbox', 'radio'].includes(field.type) ? field.checked !== field.defaultChecked : field.tagName === 'SELECT' ? field.value !== ([...field.options].find(option => option.defaultSelected) || field.options[0])?.value : field.value !== field.defaultValue)));
      if (dirty || otherDraft) throw new Error('Save or revert unsaved block or drafting edits before repairing reading order. Your fields remain here.');
    },
    busy(value) { reviewWriteBusy = value; },
    uncertain() { reviewReloadRequired = true; },
    saved(page, id, reviews) {
      receiveSourcePageReviews(reviews, page);
      const destination = new URL(location.href);
      destination.searchParams.set('source_page', String(page));
      destination.hash = id ? `block-${id}` : '';
      history.replaceState(null, '', destination.pathname + destination.search + destination.hash);
      location.reload();
    }
  });
}, {once: true});

document.addEventListener('click', event => {
  const link = event.target.closest('[data-review-actions-return]');
  if (!link) return;
  event.preventDefault();
  const approve = link.closest('.block-card').querySelector('.block-review-actions [data-action=approve]');
  approve.scrollIntoView({block: 'center', behavior: 'instant'});
  (approve.disabled ? approve.closest('.block-card') : approve).focus({preventScroll: true});
});
