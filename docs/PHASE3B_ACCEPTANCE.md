# Phase 3B acceptance ledger

Date: 2026-09-30. Version: 0.7.0. Local implementation and external acceptance
are separate. No automated WCAG or production WSUWP claim is made.

## 2026-10-03 Save and approve

- Primary text, image, table and nested-list review forms now offer **Save and
  approve** alongside ordinary Save. The explicit action applies the editor's
  fields, performs retained-list recovery where needed, validates final content
  and stamps block approval through the existing persistence mechanism in one
  Undo snapshot. Plain saves still invalidate changed approval. Missing image
  alternatives or unrecovered list structure fail before persistence and show
  inline feedback without discarding entered text. Approval cannot reload over
  unsaved authoring fields; combined saves require other editors to be saved or
  reverted first. Repeated submissions issue one request. The saved block retains
  focus; separate description decisions and affected page review remain pending.
- Baseline: **361 tests passed** earlier in the same unchanged checkout, using
  canonical `TMPDIR=/private/tmp`. The default macOS temporary path reproduced
  the two already-recorded alias-related failures. Final documented suite:
  **370 passed in 19.854s**, including nine combined-action tests covering recovery,
  rich exported content, approval stamps, one-step Undo/reopen, validation failures,
  write rollback, image/table fields, page references/review invalidation, separate
  description decisions, CSRF and conversion-blocked inspection.
- Chrome **154.0.8037.95**, fresh disposable profile: **seven workflow groups
  passed**, zero page errors, at 1440px and 390px. Checks cover keyboard approval,
  saved status/counts, retained-list recovery, inline failures/retry, unsaved-field
  guards, image/table/nested-list edits, reload/Undo/focus and downloaded semantic
  HTML. Additional repeated-submit check passed with one request and one added
  Undo snapshot. Desktop and narrow controls screenshots were visually inspected.
  JavaScript syntax and `git diff --check` passed.
- Evidence is ignored under `build/save-and-approve-20261003/`: final-suite.log,
  browser-report.json, duplicate-submit.json, screenshots and QA-REPORT.md.
  The first browser attempt passed all UI groups but the download assertion used
  a relative URL unsupported by the test client; the harness was corrected and
  rerun on a fresh fixture. The separate description test fixture was corrected
  to use the required explicit block-to-description association. No production
  document or human decision was changed. The user's live app was not restarted;
  restart it to load these changes.
- Local implementation on `codex/phase3b/output-page-builder`; no push, merge,
  tag, release or deployment. Production-authoritative WSU Gutenberg/WXR, human
  VoiceOver and actual Windows hardware acceptance remain pending.

## 2026-10-02 Poppler setup and diagnostic clarity

- The authorized Homebrew installation is confirmed by the local receipt:
  Poppler **26.08.0**, installed on request at **17:48:52 UTC**, with linked
  `/usr/local/bin/pdftoppm` and `pdfinfo`. Doctor passes. The macOS launcher now
  includes both standard Homebrew bin paths; a disposable launcher harness with
  only the system PATH successfully located both commands. No reinstall,
  unrelated dependency installation or administrator prompt was needed during
  this verification. README, review-app setup and changelog document the actual
  dependency, installation, restart and PATH recovery.
- Fresh app-renderer calls on a disposable copy of the actual 12-page CITI PDF
  produced page 1 and page 12 PNGs at **1020 × 1320** (159,215 and 123,766 bytes).
  Both images were visually inspected and then displayed through the isolated
  browser app, including the page-12 heading outline. Their bytes exactly match
  the older CITI project's retained page 1/page 12 renders. That older project
  retains all 12 source-page images, and the September 30 doctor log records
  available Poppler. Prior rendering therefore has evidence; the reason Poppler
  subsequently became unavailable is unknown. The newer project caches remain
  empty because only disposable copies were rendered.
- Read-only Recent projects metadata now lists **CITI Validation** at the chosen
  `PDF to Web Validation` folder first; this folder now contains a project, its
  source copy and 21 extracted PNGs. **Validation** at the app-managed root is a
  separate project. No authenticated live-app selection is claimed and no live
  app was restarted or navigated. Both carry the same recorded diagnostic:
  `block_review_required`, targeting **odl-229 / Block 53 / source page 12**,
  “Example Course Certificate of Completion.” Its actual cause is
  `additional_h1_demoted`: an additional H1 became H2 and needs manual hierarchy
  review. This is separate from missing Poppler or Pillow.
- Document now shows one coherent summary: **54 pending block review tasks**,
  zero description tasks, and one unresolved extraction diagnostic whose block
  review is already included. Cause, impact, current block status and exact
  Structure/Accessibility links are visible. Page/document-only findings have
  source/recovery guidance; unavailable source copies and missing references do
  not create broken targets. Nested flags link to their review owner, and missing
  references prevent false automatic resolution. Manual approval/exclusion
  resolves historical block-review notes without changing the retained note;
  Undo restores the finding. No review decisions were made on real projects.
- Baseline with the unfinished diagnostic candidate: **336 tests, three failures**:
  the two existing source-link tests reused a fixture without a source PDF, and
  one older layout assertion expected the removed duplicate status banner.
  Corrected the fixture, added missing-source/missing-reference and nested-owner
  coverage, and updated the single-status assertion. Final full suite:
  **338 passed in 14.665s** with canonical `TMPDIR=/private/tmp`.
  Focused diagnostics: **11 passed**. Independent Chrome **154.0.8037.95**:
  **12 groups passed**, zero page errors, at 1440px and 390px; exact keyboard
  targeting, real renders/highlights, single counts, read-only screen integrity,
  save/reload/Undo, manual review/history, project reopen and original PDF download.
  Screenshots were inspected; JavaScript/launcher syntax and `git diff --check`
  passed. Browser harness navigation waits were corrected before the final pass.
- Evidence is local and ignored under `build/poppler-diagnostic-20261002/`:
  `real-render.json`, `launcher-verification.txt`, `full-suite.log`,
  `diagnostic-tests.log`, `browser-report.json`, screenshots and `QA-REPORT.md`.
  All real-project file hashes match the initial inventories. No actual project
  was migrated, regenerated or re-extracted. No process environment/credentials
  were read. Pillow is absent from the app virtualenv and remains a separate
  supplemental-extraction issue; it was not installed by assumption.
- Branch `codex/phase3b/output-page-builder`, HEAD `ca3326994d5a`, preserved
  uncommitted user work. No commit, push, merge, tag, release or deployment.
  Brad's remaining step is to stop/relaunch the live app and reopen the same
  project to load the code and Poppler PATH. Production-authoritative WSU
  Gutenberg/WXR, human VoiceOver and Windows hardware acceptance remain pending.

## 2026-10-01 local stabilization

### Manual acceptance follow-up: pending-save navigation and approval reasons

Brad's nested link-label save exposed lost selection after reload; editing the
sole Approved match left an empty filter with disabled navigation and no recovery
guidance. Explicit saves now keep their owning card, including nested links;
the concurrent save-focus fix reveals that card through All when necessary and
avoids jumping to the completion banner. Explicit filter changes recover a
matching neighbor or explain how to return to All. A URL with an explicit block
anchor continues to reveal its target on reload, following the existing direct
finding-link policy.

A single persisted review reason explains material changes after actual prior
approval in Structure and Accessibility. It survives pending saves/reopen,
clears after a fresh decision, and restores with Undo. Never-approved children
and unchanged manual flags do not receive a false prior-approval explanation.
No change log, provider request or live-project mutation was added.

The final live-layout code snapshot passed **271 tests in 10.781 seconds** and
five Chrome workflow groups; desktop and 390px screenshots were inspected.
Independent functional review passed **55/55 observations**, with **271 tests**
on the combined candidate. All **11 independent Chrome groups** passed across
the four filters, zero matches, adjacent navigation, keyboard, reload and Undo.
Exact fingerprints, independent filter/keyboard
evidence, code lineage and loading instructions are recorded in
`build/navigation-regression-20261001/QA-REPORT.md`. Existing document rendering,
WSU WordPress, VoiceOver and Windows limitations remain as recorded below.
No commit, push, merge, installation or release was performed.

The authorized local fix cycle adds source approval and artifact freshness gates
across whole-document, individual-page and complete-package publication paths.
Canonical resolved paths are checked before downloads; previews, accessibility
reports and media/draft preparation remain available while review is pending.
Page approval preserves the existing **Reviewed** model value. Changed source
content requires a fresh manual decision, including previously Reviewed visual
text; dirty authoring forms block destructive draft reloads, and completed media
CSVs preserve current alternatives and captions. Undo retains recovery snapshots
and restores current/project state when either persistence write fails.

List edits preserve retained identities, links, source evidence, descendants and
exclusions or reject ambiguous changes. Reordering retains list numbering starts;
compound resource-label edits preserve trailing emphasis. Source footnote edits
update the existing derived note text without changing IDs, markers or backlinks.
Fresh export settings default to nested headings and preserve explicit H2 sections.
The latest navigation filters, description panels, rules dialog and sticky Undo
remain part of the regression scope.

Local suite: **268 tests passed in 9.695 seconds** before the final independent
follow-up. The first frozen fix candidate exposed five additional concerns that
were corrected. The second independent pass confirmed those fixes and found one
safe-rejection edge for unmarked footnote prose, also corrected; its successful
core checks alone are not final acceptance.
Final independent functional/UI results, exact code fingerprints and remaining
items are recorded in `build/stabilization-20261001/QA-REPORT.md`. That local report
is the evidence for the final candidate. No actual project data, active app/browser,
provider, installation or Git release operation was changed by this cycle.

Production-authoritative WSU WordPress/plugins, human VoiceOver and actual Windows
acceptance remain pending. This execution runtime cannot render source pages
because `pdftoppm` is unavailable; no installation was attempted. Historical
Poppler availability below describes the earlier recorded environment.

## 2026-10-01 Reading order filter counts

- All, Approved, Needing review and Excluded each display their current count
  in parentheses. Counts cover all blocks regardless of the active filter and
  refresh with approval, exclusion, Undo and reload. Needing review combines
  unreviewed and needs-review blocks. The live visible/total summary omits
  "shown", shares the filter line when space permits, and wraps on narrow screens.
- Baseline and final full suite: **268 tests passed**, using
  `TMPDIR=/private/tmp .venv/bin/python -m unittest discover -s tests -v`.
  The default macOS temporary path exposed two existing `/var` versus `/private/var`
  alias failures in publication-integrity tests; canonical TMPDIR resolves both.
  JavaScript syntax and `git diff --check` passed. Chrome **154.0.8037.59** passed
  all six navigation browser groups, including keyboard filtering, live counts,
  zero results, approval/exclusion/Undo, reload, direct links and 390px layouts,
  with no page errors. Desktop and narrow filter screenshots were inspected.
- Evidence: ignored `build/reading-filter-counts/evidence/browser-report.json`
  and screenshots; disposable synthetic project only. Pre-existing changes are
  preserved. Work remains uncommitted on `codex/phase3b/output-page-builder`,
  HEAD `ca33269`; nothing pushed or released. Production WSU Gutenberg/WXR,
  human VoiceOver and actual Windows acceptance remain pending.

## 2026-10-01 Saved block focus

- Explicit block-form saves anchor to the owning Structure card rather than
  invoking approval advancement or focusing the completion banner. Link-text
  saves on nested list items use the parent list card. Saved blocks stay below
  the sticky toolbar with their source page selected; a saved block hidden by its
  new status opens All. Accessibility-origin corrections still return to their
  finding. Content, status invalidation, approval actions and Undo are preserved.
- Reproduced the defect in Chrome on a disposable synthetic nested-list project:
  Save review state focused `structure-review-complete` instead of the block.
  The repaired candidate passed **five browser groups** in Chrome
  **154.0.8037.59**, covering All/Approved unchanged saves with all blocks approved,
  nested link edits and review-state saves, status changes, Undo/reload/source
  selection, 390px layout and Accessibility return paths, with no page errors.
  Desktop and narrow saved-block screenshots were visually inspected; original
  normalized fixture bytes remained unchanged. Full suite: **271 tests passed**
  with canonical `TMPDIR=/private/tmp`; JavaScript syntax and `git diff --check`
  passed.
- Evidence: ignored `build/block-save-focus/evidence/browser-report.json` and
  screenshots; reproduce using `tools/block-save-focus-fixture.py` and
  `tools/block-save-focus-browser-check.js` with a new disposable project.
  No actual project content was changed. Work remains uncommitted on
  `codex/phase3b/output-page-builder`; existing changes were preserved. Nothing
  pushed or released. Production WSU Gutenberg/WXR, human VoiceOver and actual
  Windows acceptance remain pending.

## 2026-10-01 Final action alignment

- Final workflow actions share the existing right-aligned action-row layout:
  Document's Review structure and completion handoff, Structure's green Continue
  to Accessibility, Accessibility's Continue to Arrange Pages, the Arrange Pages
  and Preview handoffs, and final page/package/document export actions. Rows wrap
  at narrow widths while preserving labels, destinations and readiness gates.
- Baseline and final full suite: **271 tests passed**, using canonical
  `TMPDIR=/private/tmp`. `git diff --check` passed. Chrome **154.0.8037.59** passed
  **13 browser checks**: all six workflow screens at 1440px and 390px had
  right-aligned final actions and no overflow; keyboard handoffs reached each
  next screen and the final document export produced download links. No page
  errors. Desktop and narrow Structure screenshots were visually inspected.
- Evidence: ignored `build/final-action-alignment/evidence/browser-report.json`,
  screenshots and local browser script; synthetic fixture only. Actual review
  projects were untouched. Changes remain uncommitted on
  `codex/phase3b/output-page-builder`; existing work was preserved. Nothing
  pushed or released. Production WSU Gutenberg/WXR, human VoiceOver and actual
  Windows acceptance remain pending.

## 2026-10-01 Accessibility finding details

- Block findings display `Source page N · Block M`, using the current Structure
  reading-order position. Nested-link findings identify their owning list card;
  exclusions do not renumber subsequent blocks. Reordering and Undo update the
  number. Open block/description controls align right beside each finding, and
  related extraction block controls align right within their detail rows.
- Focused suite: **15 tests passed**. Full suite: **272 tests passed**, using
  canonical `TMPDIR=/private/tmp`; `git diff --check` passed. Chrome
  **154.0.8037.93** passed **four browser groups**: two edited/unapproved blocks
  identified correctly with right-aligned controls at 1440px and 390px and no
  overflow; keyboard Open block selected the correct block and source page,
  Save returned to its finding without approval; reorder/Undo updated the
  displayed number. No page errors. Desktop/narrow screenshots were visually
  inspected. Synthetic normalized fixture bytes remained unchanged.
- Evidence: ignored `build/accessibility-finding-details/evidence/browser-report.json`,
  screenshots and local browser script. Actual review projects were untouched.
  Work remains uncommitted on `codex/phase3b/output-page-builder`; existing
  changes were preserved. Nothing pushed or released. Production WSU
  Gutenberg/WXR, human VoiceOver and actual Windows acceptance remain pending.

## Environment

macOS; Python 3.12.2; Java 17.0.19; OpenDataLoader PDF 2.5.9; Node 24.19.0;
Poppler utilities available. Chrome 154.0.8037.59 with local Playwright.
`build/phase3b/doctor.txt` records the dependency check. No extraction engine
replacement, OCR or connected publishing was added.

## Required external tasks — still pending

| Task | Result on 2026-09-30 | Evidence and remaining work |
| --- | --- | --- |
| Production-authoritative WSU Gutenberg/WXR validation | blocked | No production site/plugin-version access supplied. Local serializer, XML and preview tests cannot establish production compatibility. |
| Human VoiceOver on long Structure, Accessibility and Output Pages | not tested | Chrome keyboard/control-name/focus checks are automated; no human listening session was performed. |
| Windows installation and launch on hardware or CI | not tested | This execution host is macOS; no Windows hardware or CI result available. |
| OpenDataLoader -6 aborts on five candidate PDFs | not tested | Existing `PHASE2_CLOSEOUT.md` records 10 failing mode runs. Current doctor detects 2.5.9, but dependency availability is not an abort investigation or corpus retest. Investigation remains Phase 3C. |
| Historical WordPress acceptance cases retested | blocked | Docker CLI exists, but `docker info` cannot connect to the local daemon outside the sandbox. Existing historical failures/NOT TESTED rows in `WORDPRESS_ACCEPTANCE_0.5.1.md` remain unchanged. |

## 2026-10-01 Structure filters and navigation spacing

- Structure uses compact text links for All blocks, Approved, Needing review and
  Excluded, with an emphasized accessible current choice. Session persistence,
  visible-block navigation and direct-link focus remain intact. Longer image
  descriptions explains the review action first; extraction details collapse
  under Why these images appear here. Description records and approvals remain.
- Arrange Pages keeps its first four actions in a separate group and aligns
  Continue to Preview to the right with space between. Preview aligns both Export
  handoffs right and separates Semantic HTML and WordPress Preview buttons.
  Framework group sizing was corrected after Chrome exposed desktop wrapping.
- Baseline and final full suite: **250 tests passed**. JavaScript syntax and
  `git diff --check` passed. Chrome **154.0.8037.59** passed **six browser groups**
  with no page errors: text-link filters/keyboard/counts/navigation/reload/deep
  links; approval and Undo while filtered; description guidance/help/deep links;
  arrangement grouping/right alignment/contents popup; both preview modes and
  Export handoffs; and 390px layouts/right alignment/bottom Export navigation.
  Desktop and narrow screenshots were visually inspected. The initial test
  expectations were corrected for existing direct-link and Undo focus behavior
  and the main container's narrow-screen padding.
- Reproduce with a new disposable fixture and its printed bootstrap URL:

  ```sh
  PDF_TO_WEB_CONFIG_DIR="$PWD/build/review-navigation/config" .venv/bin/python tools/document-structure-fixture.py build/review-navigation/new-project --serve --port 8783
  node tools/review-navigation-browser-check.js BOOTSTRAP_URL build/review-navigation/new-project build/review-navigation/new-evidence
  ```

- Ignored evidence: `build/review-navigation/evidence/browser-report.json` and
  desktop/narrow screenshots. Synthetic project only; private review files were
  untouched. Pre-existing tracked/untracked work was preserved. Changes remain
  uncommitted on `codex/phase3b/output-page-builder`, HEAD `ca33269`; nothing
  pushed, tagged, released or deployed. Production WSU Gutenberg/WXR, human
  VoiceOver and actual Windows verification remain pending.

## Local verification

- Baseline: 126 tests passed on clean `main` at `a508f1a`.
- Current full automated suite: 152 tests passed. Covers migration, persistence,
  assignments, structural split/merge/exclude/restore, independent orders,
  validation, stable IDs, Undo, accessibility preservation, approval invalidation,
  metadata escaping, hierarchy, local footnotes/backlinks, cross-page links,
  semantic/Gutenberg/WXR exports, media, manifests and failure recovery.
- Authenticated route tests cover page workspace, preview, export downloads,
  persistence, Undo, session and Origin/CSRF enforcement.
- Chrome walkthrough evidence: `build/phase3b/browser-report.json`, desktop/narrow
  screenshots and the disposable `build/phase3b/legacy-handbook-verified/` project.
  Final browser result: **passed**, 15 workflow/control/layout checks, no page errors; source inspection is not a
  substitute for that result. The walkthrough exercised saved legacy edits,
  suggestions, merge/split/Undo, create/reassign/Undo, metadata/Page/Article and
  parent rules, contents order, approval invalidation, reopening, keyboard/focus,
  individual previews, cross-page navigation, local WordPress preview and exports.
- The browser uncovered stale selection after Undo and a narrow navigation
  overflow. Both were fixed and the workflow rerun before handoff.
- A second WSUWP package with Hero and Section enabled was generated at
  `build/phase3b/legacy-handbook-wsuwp/output/pages/` and inspected through the
  local preview converter; `wsuwp-export-inspection.json` passed. This validates
  local contracts only.
- Generated package evidence lives in the fixture's `output/pages/` and
  `output/pages.zip`; individual artifacts in `output/page-2/`.
- Read-only `tools/phase3b-inspect-export.py` output is archived in
  `build/phase3b/export-inspection.json`; all checks passed.
- Export inspection includes XML parsing, manifest/file/content correspondence,
  semantic content equivalence, cross-page target anchors, footnote IDs/backlinks, table scopes, alt text,
  extended visual text and media files. Production permalink replacement and
  image uploads remain documented manual import actions.

Local implementation readiness does not close any of the five external tasks.

## Accessibility and Structure follow-up (2026-09-30)

- Full suite: 199 tests passed (baseline for this follow-up: 196).
- In-app browser synthetic fixture: immediate Accessibility results, diagnostic
  block link and focused Structure card, status counts, approval, Undo and reload
  verified. Private CITI review files inspected read-only: retained diagnostic
  points to block 53, source page 12, already approved.
- CLI HTML/JSON archival report behavior remains covered by existing report tests.
- Production WSUWP, human VoiceOver and Windows acceptance remain pending.

## Local axe-core follow-up (2026-09-30)

- Bundled unmodified axe-core 4.13.0 (MPL-2.0), WCAG 2.2 A/AA semantic-document
  scan. No account, external processing, project schema or review decision change.
- Browser: clean fixture scan (22 rules passed), deliberately empty link detected
  by `link-name`, affected HTML and Structure link verified. Exclude removes the
  finding; Undo restores it on reopening Accessibility.
- Three focused integration tests pass: automatic local assets, authenticated
  audit projection/CSP/no-store/state preservation, opt-in escaped annotations
  and exclusions. JavaScript syntax and diff whitespace checks pass.
- Final full checkout suite: 208 tests passed. An intermediate 202-test run had
  one media-filename expectation failure during concurrent media-naming work;
  after those tests were updated, the final full suite passed. Baseline: 199 passed.
- Browser results are transient and scoped to desktop semantic HTML. CLI archive
  reports, individual output pages and production WordPress are not axe-scanned.
  Human VoiceOver, Windows and production WSUWP acceptance remain pending.

## Output-page and media workflow follow-up (2026-09-30)

- Initial baseline: 199 tests passed. Final full checkout suite: **213 passed**,
  including concurrent accessibility-scan work. JavaScript syntax and
  `git diff --check` passed. Focused page, media, mapping and route tests cover
  assignment recovery, persistence, Undo, filename stability through ordering and
  exclusions, ZIP contents, safe prefix validation, media-only preparation,
  XML matching without overwriting newer reviewed text, and subsequent exclusions.
- Private CITI review inspected read-only: `odl-49` is an approved registration
  screenshot on source page 2, absent from its single-page assignment list.
  Both output-page exports correctly refused that incomplete arrangement. The
  document Preview uses the complete included content. Existing CITI review state
  was preserved; explicit recovery is now available in the UI after app restart.
- Chrome 154 synthetic 21-image walkthrough passed, with no JavaScript page errors:
  keyboard assignment recovery and focus, Undo, one-page arrangement, preview,
  individual/complete package export, prefix persistence/reload/Undo, ZIP and CSV
  downloads, exact-filename Media XML matching, mapped Gutenberg export and actual
  clipboard content, stale-output removal, and narrow layout. Evidence:
  `build/export-feedback/browser-report.json`, `export-desktop.png`,
  `export-narrow.png`; runner: `tools/export-feedback-browser-check.js`.
- Independent artifact inspection passed all seven checks in
  `build/export-feedback/export-inspection.json`: exact 21 prefixed ZIP members,
  unchanged synthetic image bytes, stable matching CSV block IDs/names, recovered
  image in the complete package, declared media paths present, WXR XML parse and
  all 21 mapped Gutenberg URLs. All fixture assets and generated output are local
  ignored evidence, separate from private PDFs.
- Existing arrangements remain unchanged until the user chooses an assignment
  recovery action. Output Pages is optional for a single long document. Naming
  and media mapping precede content export; direct upload remains manual.
- Production WSU Gutenberg/WXR, human VoiceOver and actual Windows acceptance
  remain pending. This establishes local implementation readiness only.

## 2026-10-01 Description task counts and seven-page cleanup

- Pending counts remaining block and description review tasks separately from
  block totals. The revision-249 disposable CITI clone shows 54 reviewed blocks,
  Total 54 blocks and Pending 5 review tasks (0 block, 5 description). The same
  summary appears on six document workflow pages and updates on Save/Undo.
- Description links expand/focus the exact editor, retain a visible selection,
  and distinguish same-page targets by context. Initial Reclassified text remains
  manual pending. Only actual edits invalidating Reviewed decisions show changed
  fields; timestamps alone do not prove prior approval. Reopen and Undo preserve
  reasons; fresh manual decisions clear them.
- Applied bounded cleanup across Projects, Document, Structure, Accessibility,
  Arrange Pages, Preview and Export: removed duplicate status/guidance and Export
  targets, shortened secondary copy, and consistently bolded field labels,
  including Classification, Review state and dynamic forms. Values/help remain
  ordinary weight; useful top/bottom Preview actions and accessible help remain.
- Final tested v2 fingerprint: `aaa3e1203d88f527de689bbe92103a3d4776c84670597bba9bdd02084651e6b7`,
  142 files, base HEAD `ca3326994d5a` plus uncommitted work. Root full suite:
  **299 passed in 11.354s**; independent suite: **299 passed in 10.706s**.
  Independent functional evidence: 47 v1 observations carried forward across a
  verified renderer-only delta plus 10 directly tested v2 controls, all passing.
  Browser evidence: 14 broad v1 groups plus 3 affected v2 groups, all passing,
  zero JavaScript errors. Broad checks include 40 exact-description entry cases
  and all seven pages at desktop/narrow widths; no fresh broad v2 rerun is claimed.
  Brad's original screenshot and final comparison/target screenshots were viewed.
  JavaScript syntax and `git diff --check` passed.
- Detailed handoff, version lineage, artifacts, limitations and manual retest:
  `build/description-task-followup-20261001/QA-REPORT.md`. This acceptance entry
  was added after the tested freeze; it changes documentation only.
- Actual CITI data remains unchanged from this task's baseline SHA256
  `53e26929cf75f596e6c42033b59d5a5243759a374a317ad0987ab7021f143e5f`.
  Five real manual description decisions remain pending. No live app/data,
  provider, installation, Git write, commit, push, release or deployment action.
  Relaunch the local app to load the corrections. Original PDF appearance,
  description factual quality, native pickers, human VoiceOver, actual Windows
  and production-authoritative WSU WordPress/plugin acceptance remain pending.

## 2026-10-01 Readiness consistency corrective review

- Document, Structure, Accessibility and Export now distinguish filled description
  text from the manual Reviewed/Not applicable decision. Reclassified descriptions
  remain pending. Excluded ancestors resolve nested image descriptions consistently.
  Export findings have readable exact block/description links with filter recovery,
  description expansion and focus.
- Legacy list approvals with pending nested items are preserved only when retained
  local history proves exact unchanged content, original approval timestamp,
  project/session, unique owner/descendant identities and consistent chronology.
  Versioned evidence records the snapshot SHA-256 without approving children or
  changing the original decision. Missing or uncertain proof stays actionable.
- Baseline **272 tests passed**; final root **289 passed in 8.729 seconds**;
  independent frozen-candidate **289 passed in 9.016 seconds**, with **48/48**
  functional observations and **5/5** all-history integration observations.
  All 50 retained CITI snapshots recovered exactly three existing approvals in a
  disposable clone, leaving five Reclassified descriptions for manual decisions.
  Save/reopen and Undo passed. Duplicate historical descendant IDs, contradictory
  history chronology and excluded-owner visual projections have regressions.
- Chrome 154.0.8037.93 independent focused QA passed **8 groups**, including all
  eight exact routes, four evidence controls yielding **5/8/6/6** pending targets,
  manual decisions and Undo; no JavaScript errors. All seven pages at desktop and
  390px, both preview modes and rules dialog were reviewed. No horizontal overflow
  in 14 page/viewport combinations. Broader UI changes remain recommendations.
- Frozen v4 source manifest (141 files):
  `9c18c66041b400a681c096a9ee7f98987171884f196366a6f763973e284ea120`.
  Full-layout review used v3 with identical renderer/JavaScript/CSS; v4 replay
  covered changed readiness behavior. This final acceptance entry is a later
  documentation-only addition. Ignored evidence and next review milestones:
  `build/readiness-correction-20261001/QA-REPORT.md` and
  `build/status-design-review-20261001/ui/REVIEW.md`.
- Actual CITI revision 249 current.json remained byte-identical; live app/browser
  untouched. QA clones omit original PDF/images; runtime source rasterizer is
  unavailable. Original PDF appearance, realistic media layout and native file
  pickers were not verified. No installation attempted.
- Work remains uncommitted on `codex/phase3b/output-page-builder`, HEAD
  `ca3326994d5a`; existing work preserved, zero staged. No Git write, push, merge,
  release or deployment. Ready for Brad's local relaunch/manual retest, which has
  not been performed. Production WSU WordPress/Gutenberg/WXR, human VoiceOver and
  actual Windows acceptance remain pending.

## 2026-10-01 Reading order Undo

- Structure's sticky Reading order toolbar includes a compact gray Undo last
  saved change button. It shares the existing saved project snapshots and endpoint
  with Saved review history, is disabled with empty history and absent during
  blocked conversion. Both controls update after an asynchronous description
  save. Pending Undo disables both controls and prevents duplicate requests;
  a failed request restores the controls without changing saved content.
- Undo clears pending review advancement and retains the selected block anchor.
  Manual scroll restoration prevents Chrome from hiding the restored block behind
  the sticky toolbar. It restores saved changes; unsaved typing is not a revision.
  No schema, persistence implementation or private project changes.
- Baseline **248 tests passed**; final full suite **250 passed**, including two
  focused route tests for persisted state restoration/empty history and blocked
  conversion. JavaScript syntax and `git diff --check` passed. Chrome
  **154.0.8037.59** passed all **seven browser groups**, with no page errors:
  saved text/reopen/keyboard Undo/focus/failure recovery; nested link labels,
  destinations and decisions; image alternatives/captions/mappings and table
  semantics; reading order and page identities; live description-save controls;
  390px toolbar/list Undo; and unchanged immutable source/restored semantic HTML.
  The browser caught and verified the scroll-restoration fix. Desktop and narrow
  screenshots were visually inspected. Ignored evidence:
  `build/reading-order-undo/evidence/browser-report.json` and
  `build/reading-order-undo/unit-tests.txt`.
- Reproduce with a new disposable fixture directory and printed bootstrap URL:

  ```sh
  PDF_TO_WEB_CONFIG_DIR="$PWD/build/reading-order-undo/config" .venv/bin/python tools/accessibility-export-fixture.py build/reading-order-undo/new-project --serve
  node tools/reading-order-undo-browser-check.js BOOTSTRAP_URL build/reading-order-undo/new-project build/reading-order-undo/new-evidence
  ```

- Existing tracked/untracked development work was preserved. Uncommitted on
  `codex/phase3b/output-page-builder`, HEAD `ca3326994d5a`; nothing pushed,
  tagged, released or deployed. Restart the app and reopen Structure to load the
  toolbar. Production WSU Gutenberg/WXR, human VoiceOver and actual Windows
  acceptance remain pending; these checks establish local readiness only.
- Work remains uncommitted on `codex/phase3b/output-page-builder`; pre-existing
  and concurrent changes were preserved. Nothing was pushed or released.

## 2026-10-01 UI and publication-heading feedback

- Document filenames appear above all seven workflow screens and in browser tab
  titles. Draft button rows have horizontal and vertical spacing. Reading-order
  filters show all, approved, pending or excluded blocks; direct finding links
  reveal hidden cards and preserve useful navigation and focus.
- Visual readiness reflects current alternatives. Reviewed explicitly approves
  the linked image; Not applicable retains the image. Long description and
  adjacent equivalent are alternatives, recovered text is optional, unchanged
  saves retain approval, and missing equivalents prevent green completion.
- Accessibility uses axe summary and finding tables with prominent numbers and
  linked affected blocks. The conformance notice appears once per app screen.
  Completed block-review extraction notes collapse as resolved without deleting
  original notes or saved decisions. CITI block 53 was verified read-only as an
  approved block associated with this historical diagnostic; its current page
  arrangement also validates without unassigned content.
- Arrange Pages explains its optional purpose at the top and provides green
  Preview contents and Continue to Preview controls. Internal routes and saved
  arrangements retain compatibility. Export lists linked pending blocks and
  visual descriptions. Media mapping uses ordered instructions, prominent
  totals, and a table identifying unmatched/ambiguous files and their blocks.
- Publication projections retain IDs, text, source provenance and review state,
  use one H1, and remove heading skips. Template mode omits the content title H1
  from Gutenberg/WXR and provides a copyable semantic HTML body without H1;
  standalone HTML retains H1. H2 sections default in the UI, with nested headings
  available. Settings save/reopen and Undo work. Source blocks are not rewritten.
- URL link-label warnings lead to editors that retain destinations and inline
  formatting. Label changes require review and support Undo. Blocks with footnote
  offsets require structural review before link-label editing; citation positions
  are never silently changed. Local semantic and axe previews use confined image
  routes, without changing stored assets or contacting remote media for the scan.
- Full suite: **226 tests passed** (213 before this task), plus JavaScript syntax
  checks and `git diff --check`. Chrome **154.0.8037.59** passed all nine browser
  check groups, including a real axe `link-name` finding, expanded block link,
  keyboard actions, save/reload/Undo, actual ZIP download and clipboard contents,
  18 matched/3 identified unmatched images, manual CSV recovery, both arrangement
  exports, and 390px layouts. No JavaScript page errors occurred. Evidence:
  `build/oct1-feedback/evidence/browser-report.json` and screenshots; runner:
  `tools/ui-feedback-browser-check.js`.
- Ten independent export inspections passed in
  `build/oct1-feedback/evidence/export-inspection.json`: exact 21 prefixed ZIP
  members, unchanged bytes, complete URLs, template/standalone heading behavior,
  H2 sections, preserved link destination, and matching parsed WXR/Gutenberg.
- Local implementation is verified. Production WSU WordPress/Gutenberg/WXR,
  human VoiceOver and actual Windows acceptance remain pending. Restart the
  local application to load the changes. Work is uncommitted on
  `codex/phase3b/output-page-builder` at HEAD `ca3326994d5a`; existing dirty work
  was preserved. No commit, push, tag, release or deployment was performed.

## 2026-10-01 Document and Structure layout follow-up

- Document moves progress and Review structure above metadata, retains one count
  summary, and counts only approved/excluded decisions in its progress bar.
  It reuses Structure's completion gate and green Accessibility handoff, including
  the description-readiness, empty-document and conversion-blocked guards.
  Genuine extraction diagnostics remain visible; zero diagnostic counts do not
  create warnings from unrelated Accessibility findings. Metadata labels are
  bold and larger than their values.
- Structure collapses description tools and saved review history. Description
  counts remain visible; direct links expand the panel and focus its card, including
  links from Document and Export. The UI explains the five-asset/image extraction
  heuristic and saved long-description records without deleting or reclassifying
  approved content. Manual import instructions use four ordered steps. Undo uses
  existing persisted snapshots and disables when none remain. Approved blocks'
  Approve buttons disable and turn gray, including after asynchronous visual saves.
- Baseline: **226 tests passed**. Final full suite: **234 passed** with eight new
  tests for completion guards, live progress, history, collapsed tools, ordered
  steps, preserved diagnostics and retained review state. JavaScript syntax and
  `git diff --check` passed.
- Chrome **154.0.8037.59** passed all **eight browser check groups**, with no page
  errors: desktop layout, keyboard ordered instructions, final approval and
  Document handoff, persisted history/Undo, visual deep-link focus and async
  status/buttons/counts, reload and Not applicable, semantic preview and actual
  HTML download, and collapsed/expanded 390px layouts. Desktop and narrow
  screenshots were visually inspected. Synthetic evidence is ignored under
  `build/document-structure-feedback/evidence/`; runner:
  `tools/document-structure-browser-check.js`.
- Reproduce with a new disposable fixture directory and the printed bootstrap URL:

  ```sh
  PDF_TO_WEB_CONFIG_DIR="$PWD/build/document-structure-feedback/config" .venv/bin/python tools/document-structure-fixture.py build/document-structure-feedback/new-project --serve
  node tools/document-structure-browser-check.js BOOTSTRAP_URL build/document-structure-feedback/new-project build/document-structure-feedback/new-evidence
  ```

- No private review project was edited. Existing tracked/untracked development
  work was preserved. Work remains uncommitted on
  `codex/phase3b/output-page-builder`, HEAD `ca3326994d5a`; nothing was pushed,
  tagged, released or deployed. Restart the local app to load the UI changes.
  Production WSU Gutenberg/WXR, human VoiceOver and actual Windows acceptance
  remain pending; these results establish local implementation readiness only.

## 2026-10-01 Accessibility return navigation and export follow-up

- Accessibility Open block buttons carry explicit return context. Successful
  block edits and decisions return to the issue list with a fresh scan; direct
  Structure edits retain their navigation. Link corrections still require review.
  Compact decision controls, visible focus below the sticky header, and resolved
  diagnostic history with no-action guidance were verified. The bottom green
  Arrange Pages handoff waits for resolved document findings and a successful
  current scan with neither violations nor incomplete checks.
- Arranged semantic previews use authenticated local assets even for mapped
  WordPress images. Arrange Pages Undo is gray. Preview has top/bottom green
  Export links. Export displays only outstanding readiness/diagnostic checks,
  lists unmapped meaningful images, explains Media XML/CSV mapping versus content
  WXR, and confirms Copied beside the title-copy button.
- Whole-list saves retain unchanged item state and rich formatting; label edits
  preserve link destinations, item IDs, provenance, nested content and exclusions.
  Nested link-label edits also update the parent editor. Hyphen-damaged visible
  URLs can use an otherwise matching, overlapping PDF annotation destination.
- CITI Resources: three links were explicitly recovered in the local review from
  immutable normalized input and retained PDF annotations. Edited labels, original
  bytes, block IDs, provenance, all image metadata and WordPress mappings were
  verified unchanged. One Undo snapshot contains the prior state; the two affected
  lists are marked needs review. Original export files were preserved. HTML and
  Gutenberg projections contain all three anchors. Three images on source pages
  10, 11 and 12 still lack WordPress URLs; those mappings were not guessed.
- Baseline **234 tests passed**; final full suite **248 passed**, including 14 new
  focused tests. JavaScript/Python syntax and `git diff --check` passed. Chrome
  **154.0.8037.59** passed all **seven browser groups**, with no page errors:
  compact controls/history, edit/approval return and fresh completion scan, all
  21 arranged-preview images loading, Preview/Export handoffs and title clipboard
  feedback, actual Gutenberg download/copy with 18 image sources and three
  placeholders plus three resource anchors, ordinary Structure/list edits with
  Undo, and four workflows at 390px. An initial clipboard assertion ran before
  copying completed; the runner now waits for Copied and passed on fresh fixtures.
  Screenshots were visually inspected. Ignored evidence:
  `build/accessibility-export-feedback/evidence/browser-report.json` and
  `build/accessibility-export-feedback/unit-tests.txt`.
- Reproduction uses a new disposable directory and the printed bootstrap URL:

  ```sh
  PDF_TO_WEB_CONFIG_DIR="$PWD/build/accessibility-export-feedback/config" .venv/bin/python tools/accessibility-export-fixture.py build/accessibility-export-feedback/new-project --serve
  node tools/accessibility-export-browser-check.js BOOTSTRAP_URL build/accessibility-export-feedback/new-project build/accessibility-export-feedback/new-evidence
  ```

- Existing tracked/untracked work was preserved. Work remains uncommitted on
  `codex/phase3b/output-page-builder`, HEAD `ca3326994d5a`. No push, tag, release,
  deployment, production import or publishing occurred. Restart the local app,
  review the recovered resource lists, complete the three missing media mappings,
  then regenerate the publication export. Production WSU Gutenberg/WXR, human
  VoiceOver and actual Windows acceptance remain pending.

## 2026-10-01 Automated HTML rule details

- View tested rules opens a compact native dialog using the same axe-core scan
  results as the summary. Initially shows passed rules; filters cover detected
  issues, human review, not applicable and all results. Names, descriptions, rule
  IDs, element counts, WCAG criterion tags and guidance explain what was checked.
  Not-applicable rules are distinct from passes, and a rule can have different
  results for different elements. No saved review state or schema changes.
- Baseline and final full suite: **248 tests passed**. JavaScript syntax and
  `git diff --check` passed. Chrome **154.0.8037.59** verified five browser groups:
  every displayed rule/count matched the actual engine results (22 passes and
  41 not applicable in the clean synthetic projection); keyboard focus containment,
  Close/Escape focus restoration and scrolling at 390px; reload with unchanged
  review bytes; actual detected and incomplete checks from a test-only preview
  response (one of each); and scan failure without misleading rule results.
  No page errors. Screenshots visually inspected. Ignored evidence:
  `build/axe-rule-details/evidence/browser-report.json` and
  `build/axe-rule-details/unit-tests.txt`.
- Reproduce using a new disposable directory and the printed bootstrap URL:

  ```sh
  PDF_TO_WEB_CONFIG_DIR="$PWD/build/axe-rule-details/config" .venv/bin/python tools/accessibility-export-fixture.py build/axe-rule-details/new-project --serve
  node tools/axe-rule-details-browser-check.js BOOTSTRAP_URL build/axe-rule-details/new-project build/axe-rule-details/new-evidence
  ```

- Existing tracked/untracked development work was preserved on
  `codex/phase3b/output-page-builder`, HEAD `ca3326994d5a`. Uncommitted; nothing
  pushed, tagged, released or deployed. Refresh Accessibility to load the dialog.
  Production WSU Gutenberg/WXR, human VoiceOver and actual Windows acceptance
  remain pending. This establishes local implementation readiness only.


## 2026-10-01 Empty-filter navigation recovery

- Added one neutral contextual empty-filter message and Show all blocks recovery
  beside disabled Previous/Next in the sticky Reading order toolbar. Empty
  Needing review says no items remain in that filter, without implying all
  description/Accessibility work is complete. Recovery restores All and meaningful
  block focus in place, retaining unsaved text and existing draft protections.
- Last approval/reload retain the chosen empty filter and focus recovery; Undo
  restores its matching item. Explicit incoming block links retain existing
  reveal behavior. This is UI mitigation, not a confirmed navigation regression.
- Baseline 299 tests passed; focused layout suite 11 passed; final full suite
  **300 passed in 11.450s**. Chrome **eight fresh desktop/narrow groups passed**,
  zero JavaScript errors. Tested initially empty filters, sticky/keyboard recovery,
  no overflow, unsaved text/disk preservation, remaining-description and fully
  completed last-approval cases, reload and Undo. Screenshots were viewed.
  JavaScript syntax and `git diff --check` passed.
- Frozen implementation fingerprint:
  `248407e19d89c18380f771ea1f493b6c1bdb1dc135a2bbc4c13e69c47ceb8e8d`,
  142 files, base HEAD `ca3326994d5a` plus uncommitted work. This final acceptance
  addition is documentation only. Detailed evidence/manual retest:
  `build/empty-filter-followup-20261002/QA-REPORT.md`.
- Real data/live app untouched; no install, provider, Git write, push or release.
  Relaunch to load the mitigation. Human VoiceOver, Windows hardware and
  production-authoritative WSU WordPress acceptance remain pending.


## 2026-10-01 Export button rows and colors

- Grouped Prepare/Undo in step 1, aligned each XML/CSV chooser with its submit
  button in step 2, and grouped Copy page title/Export in step 3. Compact rows
  wrap at narrow widths. Green marks forward actions; Undo/Copy and disabled
  Export use gray. Separate form submissions and existing review gates remain.
- Baseline 300 tests passed; final frozen implementation **301 passed in
  11.373s**. Seven Chrome desktop/narrow check groups passed with zero page
  errors, including actual synthetic Prepare/Undo, XML matching, CSV import,
  keyboard Copy, downloaded export inspection and pending-review gating.
  Six groups ran together; a targeted seventh probe verified disabled styling
  after its existing 0.2-second CSS transition. Screenshots were inspected.
- Frozen manifest: `6f4c6cafb9c03d1cf850d6ccaadf34d623136dbf0c5b9351d241cfc69046cdda`,
  142 files, base HEAD `ca3326994d5a` plus preserved uncommitted work. This
  acceptance addition is documentation only. Evidence and manual retest:
  `build/export-step-guidance-20261001/QA-REPORT.md`.
- Existing mapping behavior can require renewed source approval; the backend
  enforces it, while the client may show a stale enabled Export until reload.
  Recorded separately; this layout change does not alter approval behavior.
- Real data/live app untouched. No install, Git write, push, merge or release.
  Relaunch to load the change. Human VoiceOver, Windows hardware and
  production-authoritative WSU WordPress acceptance remain pending.


## 2026-10-01 Immediate Export readiness after media mapping

- Corrected stale readiness after successful XML/CSV media mapping and Undo.
  Mutation responses use the same authoritative readiness renderer as the initial
  page. Counts, exact source links/reasons and Export eligibility update in place,
  with truthful feedback and request-time gating. Undo restores saved prefix,
  title/heading controls, media links and eligibility without reload.
- Current approval fingerprint/manual decision policy is preserved. Changed media
  requires fresh source review; identical mappings retain approval. Authored
  fields remain unchanged, and failed imports retain saved state and prior gate.
- Baseline **301 passed in 12.547s**; focused suite **16 passed in 1.133s**;
  final frozen full suite **305 passed in 10.517s**. Fresh Chrome **14 groups
  passed** (seven desktop, seven narrow), zero page errors. Covered changed
  XML/CSV, pending export rejection, no-op imports, failures, Undo, keyboard/status,
  no reload, persisted approvals and actual inspected HTML downloads.
  JavaScript syntax and `git diff --check` passed; screenshots were viewed.
- Frozen manifest: `5aab69a81ca0eaf9ae574bd197c354349b74d0f8e33a9b4787c788666d0bb228`,
  142 files, base HEAD `ca3326994d5a` plus preserved uncommitted work. This final
  acceptance addition is documentation only. Detailed evidence/manual retest:
  `build/postmapping-readiness-20261001/QA-REPORT.md`.
- Resolves the stale-client gate finding recorded in the preceding Export-row
  acceptance entry; it does not exempt mapping changes from manual approval.
  Real CITI data/live app untouched. No install, provider, Git write, push, merge
  or release. Relaunch to load the fix. Human VoiceOver, Windows hardware and
  production-authoritative WSU WordPress acceptance remain pending.


## 2026-10-02 Source-page failure feedback and recovery

- Fixed silent source-render failure in Structure: actionable HTTP/render/decode
  feedback, original PDF access and keyboard Retry. Hide broken images, outline
  regions only after image success, coalesce in-flight same-page loads and reject
  stale image/metadata context. Missing Poppler no longer creates an empty cache;
  existing rendered pages remain usable and renderer-start errors have guidance.
- Baseline **305 passed in 11.127s**; focused renderer **6 passed in 0.020s**,
  web routes **25 passed in 1.316s**; frozen full suite **310 passed in 11.175s**.
  Fresh Chrome **12 desktop/narrow groups passed**, zero page errors, covering
  actual missing renderer, cached synthetic success, HTTP/decode/session errors,
  keyboard/status/focus, stale-request handling and retained review bytes.
- Frozen manifest: `a29307050125a3b90c158a19e31a358389ede89debdc262195c3121149aecdaf`,
  142 files, base HEAD `ca3326994d5a` with preserved dirty work. This final
  acceptance addition is documentation only. Evidence/diagnosis/recovery:
  `build/source-preview-recovery-20261002/QA-REPORT.md`.
- Reported source identity matches the newer Validation project, separate from
  CITI Validation; both retain the PDF and all 21 images. Isolated actual-PDF
  rendering fails for missing pdftoppm. The live authenticated image response and
  active-process PATH remain unverified; unauthenticated diagnostic GET is 401.
  Process-environment read was rejected by automatic approval review and not
  bypassed. Separate supplemental-asset errors identify missing Pillow.
- All private files and active app preserved. No install, actual-project
  regeneration, Git write, push or release. Positive image tests use synthetic
  cached PNGs; real Poppler rendering is not claimed. Source-comparison recovery
  needs live error confirmation and authorized dependency setup if missing.
  VoiceOver, Windows and production WSUWP acceptance remain pending.

## 2026-10-02 Explicit new-project destination

- New projects offer an explicit default or a native destination-folder choice.
  The chosen canonical folder is the exact root; the project name adds no child
  directory. Input PDFs are preserved and copied into source/; PDFs already
  there are used in place. Extraction, assets, review/revisions/source-page cache,
  previews and exports use the existing project-root mechanisms. Full working
  paths appear before creation, on workflow screens and in Recent projects.
- Preserve loose files and safe existing PDF-only source directories; reject
  existing projects, conflicting working entries and unsafe source links. Name
  collisions retain both files with suffixes. Cancellation creates no files.
  Later failure retains/reports partial files and preserves the previous active
  project. Partial reopening shows recovery guidance. Global Recent projects
  persistence failures warn without preventing create/open/startup.
- Baseline 310 tests; final frozen candidate **327 passed in 11.462s**, including
  17 destination tests. **12 Chrome desktop/narrow groups passed**, zero page
  errors: keyboard choice/cancel/busy states, exact Unicode paths, safe source
  copy, persisted review, reopen, actual HTML downloads, recents warning and
  partial-conversion recovery. Functional tests additionally exercised all
  publication formats, page packages, Undo/history/cache, collisions, path
  confinement, expired choices, permissions and failure recovery.
- Frozen 143-file manifest SHA-256:
  `c9ca51fafdfc0f6ead50f150080ea4163a90befcfbd9c8ca1c67bff53cf8d815`,
  base HEAD `ca3326994d5a`, branch `codex/phase3b/output-page-builder`, preserved
  dirty work. This acceptance addition and final changelog detail are docs only.
  Evidence and reproduction: `build/project-destination-20261002/QA-REPORT.md`.
- Native pickers and external Java extraction were substituted only in isolated
  QA. Real PDF analysis/copy, normalization, persistence and exports ran locally.
  Positive inline previews used synthetic cached PNGs; Poppler setup remains a
  separate unresolved dependency. No private project moved or regenerated.
  Validation, CITI Validation, older CITI and input-PDF inventories are unchanged.
  No installs, Git writes, push, merge or release. Human VoiceOver, actual Windows
  and production-authoritative WSU WordPress acceptance remain pending.

## 2026-10-02 Nested source outlines and retained list-text recovery

- Page 8 Block 29's nested paragraph was already retained, with a valid source
  box, but list highlighting omitted paragraph descendants. Include recorded
  same-page text regions, deduplicate valid boxes, omit excluded/other-page
  regions and explain partial coverage. No source region or text is invented.
- Text-bearing lists with no items remain visible in the editor and HTML,
  Gutenberg/WXR and Markdown serializers. Their approval/publication is blocked;
  blank saves reject without changing stored content. Explicit saving or an
  unchanged-text conversion creates one item, retaining rich runs, links,
  footnote IDs/positions/backlinks and source provenance, with fresh approval and
  Undo. Reopening cannot apply extraction marker heuristics to recovered text.
  There is no automatic repair/migration of existing projects.
- An exact guarded reconstruction of CITI source step 11 is available in a
  disposable review copy and `build/list-repair-20261002/STEP11-REVIEW.html`.
  It nests a/b choices with their i notes, retains all original block IDs and
  substantive words, preserves the output-page assignment, and leaves affected
  review/page approval pending. Original text/boxes remain recoverable; no precise
  combined-note box was fabricated. Save/reopen and Undo restore the previous
  blocks and arrangement. No actual project repair or approval was performed.
- Baseline **347 passed in 12.810s**; final **361 passed in 15.649s**, focused
  recovery/coverage **14 passed in 0.680s**. **10 Chrome desktop/narrow groups
  passed**, zero page errors or native error dialogs: retained text/guidance,
  blank-save/approval/export rejection, rich recovery and actual HTML download,
  unchanged conversion, Undo/reopen, real CITI page-8 outlines and the proposed
  nesting in semantic/WordPress previews. Screenshots were visually inspected.
  Details: `build/list-repair-20261002/QA-REPORT.md`.
- JavaScript syntax and `git diff --check` pass. Source/review hashes of the
  actual chosen-folder project match the initial read-only snapshot. All edited
  test projects, private copies, screenshots and previews remain ignored.
  Branch `codex/phase3b/output-page-builder`, HEAD `ca3326994d5a`; existing dirty
  work preserved, no commit/push/tag/release. Optional image-flow changes,
  insertion, region drawing, OCR and general mixed-type conversion were not added.
  Human VoiceOver, actual Windows and production-authoritative WSU WordPress
  Gutenberg/WXR acceptance remain pending.

## 2026-10-02 Poppler setup and Document diagnostic clarity

- Homebrew Poppler 26.08.0 is installed at `/usr/local/bin/pdftoppm` and
  `pdfinfo`; the receipt records installation on request at 17:48:52 UTC.
  The macOS launcher includes both standard Homebrew executable paths. A
  controlled launcher check found both commands from a minimal system PATH.
- Fresh source rendering on a disposable copy of the real CITI PDF produced
  page 1 and page 12 PNGs at 1020×1320, visually checked in an isolated browser.
  This supersedes the unresolved Poppler setup/real-rendering findings above.
  Older September 17–18 cached pages match these fresh renders; September 30
  doctor output also recorded Poppler available. The later missing-PATH cause
  cannot be established. Pillow remains separately absent and was not installed.
- The unexplained diagnostic was `block_review_required` for `odl-229`, Block
  53 on page 12: an additional H1 was demoted to H2 and needs manual hierarchy
  review. It overlaps one of the 54 pending review tasks. Document now explains
  cause, impact and recovery links without counting the review twice. Resolved
  notes remain in history; missing references cannot silently resolve; Undo
  restores the finding.
- Local verification: **338 tests passed in 14.665s**, focused diagnostics
  **11 passed**, **12 Chrome desktop/narrow groups passed**, zero page errors.
  Evidence: `build/poppler-diagnostic-20261002/QA-REPORT.md`. Real projects were
  inspected read-only; rendering and editable workflows used disposable copies.
  No Git writes or release. Live app relaunch remains a user action; no source
  regeneration is needed. External WSU WordPress, VoiceOver and Windows hardware
  acceptance remain pending.

## 2026-10-02 Draft discovery, project-local ZIPs and merge feedback

- Structure exposes a distinct Image description drafts section with collapsible
  tools. Image alternative fields and Accessibility findings link directly to
  the tools, opening them and focusing the heading by keyboard. Draft import
  continues to fill empty fields while preserving authored text and manual
  approval requirements; no provider or automatic generation was enabled.
- Draft request ZIPs remain inside the chosen project root's
  `output/image-drafts/`, with descriptive unique names and visible saved paths.
  Complete archives are published atomically without overwriting earlier ZIPs;
  output paths cannot escape the project. Browser downloads remain byte-identical
  copies. Existing request identities, context checks and import schema remain.
- Merge next now explains unsupported combinations beside disabled controls and
  reports failures inline. It supports adjacent matching text types, preserving
  valid footnote positions, IDs/backlinks, source provenance and Undo. It rejects
  lists, mixed types, excluded blocks and rich/nested content it cannot preserve.
  Combining mixed blocks into a list is a separate feature requiring agreed
  heading, item and nesting semantics; it was not added here.
- Baseline **338 passed in 14.196s**; final **347 passed in 13.069s**. Focused
  draft discovery/persistence **5 passed**, merge feedback **4 passed**, output
  pages **28 passed**. **9 Chrome desktop/narrow groups passed**, zero page errors
  or native error dialogs, including keyboard links, merge failure/success/Undo,
  repeated ZIP exports and actual downloads, response validation/import/Undo,
  and reopening the chosen-root test project. Evidence:
  `build/drafting-merge-feedback-20261002/QA-REPORT.md`.
- Only synthetic project state was edited in these checks. No live app restart
  or navigation, real project migration/re-extraction/merge, provider call,
  additional dependency installation, Git write, push, merge, tag or release.
  Changes remain on `codex/phase3b/output-page-builder`, HEAD `ca3326994d5a`,
  with the pre-existing dirty work preserved. Human VoiceOver, actual Windows
  and production-authoritative WSU WordPress acceptance remain pending.

## 2026-10-03 Authorized GitHub source backup verification

- Final source candidate: **361 tests passed in 13.629s**. Python, JavaScript,
  package JSON and macOS launcher syntax checks and `git diff --check` passed.
  Previous isolated browser evidence remains recorded in the entries above;
  this backup task does not claim a new browser or external acceptance run.
- Reviewed 73 explicit source/test/documentation/tooling paths. Bundled axe-core
  matches its pinned upstream files. Private PDFs, actual projects, caches,
  disposable review copies, generated exports and local evidence stay excluded.
  GitHub is a source backup, not a backup of those local project files.
- Target: existing `baschwar/pdf-to-web` repository, working branch
  `codex/phase3b/output-page-builder`; no main merge, tag, release or visibility
  change is authorized. No CI workflow is configured. Push outcome and exact
  remote commit are recorded in the completion report/local backup evidence.
- Version remains 0.7.0 with unreleased stabilization work. Production-authoritative
  WSU WordPress/plugin Gutenberg/WXR acceptance, human VoiceOver and actual
  Windows hardware verification remain pending. The actual step 11 proposal
  still requires author review; no real document or approval was changed.
