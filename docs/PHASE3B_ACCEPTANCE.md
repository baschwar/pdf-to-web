# Phase 3B acceptance ledger

Version: 0.7.0. Updated: 2026-10-04.

Local implementation, external acceptance and publication are separate. The
public ledger records behavior and verification without source-document names,
private project identities, attachment IDs, revision histories or input hashes.
Detailed earlier reports are retained only in ignored local evidence. Sanitizing
this checkout does not remove material from previously published Git history.

## Latest authorized UI continuation — 2026-10-04

This continuation builds on `70d0a72` and retains the earlier edits. The user
requested a scoped branch push after final checks. No main merge, tag, release,
deployment, real-project migration or real app restart is included.

- Quit reaches an announced terminal stopped state after accepted shutdown and
  two unavailable local health probes. Confirmation controls disappear; offline,
  HTTP-error and timeout cases retain uncertainty and retry feedback.
- Drafting method controls show the selected manual/provider workflow. One manual
  ZIP export offers counted pending/selected scope before completed-response import.
  Blank templates receive an actionable summary; strict alt and identity checks
  remain. Imported drafts remain suggestions requiring human review.
- Successful image Save and approve follows solo Approve's visible reading order,
  preserves the exact filter and handles empty filters, final completion and Undo.
  A narrow-layout source-render race now resettles the focused next card only while
  it still owns focus; newer editor focus and typing are preserved.
- Link Save and approve atomically corrects the displayed nested link and approves
  its containing block's final content fingerprint in one revision. Ordinary Save
  still marks changed content pending. Other link findings remain unresolved;
  blank, stale and foreign-target attempts cannot partially save or approve.
- App exports stay in the chosen project's output subfolders. Exact paths and
  authenticated Open output folder replace prominent browser downloads; optional
  browser copies are collapsed and explicitly follow browser settings. Unique
  history snapshots preserve reusable previous outputs before replacement. Original
  source files and existing Downloads files are preserved. No-image documents skip
  image drafting and WordPress media mapping.
- Export readiness remains visible and receives focus/scroll after media matching,
  for blocked or stale export/copy actions. Ready exports focus completion and
  saved files; successful copying stays at its control. Continue to Export and
  copy content focuses that section. The earlier always-readiness behavior is
  superseded by this result-specific navigation.

Final runtime/test/tool/launcher candidate:
`07bc2930903225181e8fb0c5b82df08e2031444a1423e9b40b405aa1493afac6`
(139 files; documentation excluded). **477 tests passed in 30.910 seconds**.
The focused link-workflow suite passed **18 tests in 1.504 seconds**; output routes
also verify report, media, HTML, Gutenberg, WXR and arranged-package persistence,
prior-output recovery, authorization, confinement and no-image text review gates.
Earlier failed runs are retained locally, including outdated no-image layout
expectations corrected without weakening export review checks.

Read-only response inspection distinguished an unchanged blank template from a
completed valid response. Historical task snapshots demonstrate that importing
image suggestions did not invalidate existing approvals or create extra image
review tasks; linked descriptions are included in their image-owned tasks.
Historical counts are not treated as current while the user actively reviews.
The user confirmed successful image-containing and no-image document results; this does not establish
production WordPress, human VoiceOver or actual Windows acceptance.

Independent navigation verification passed 17 review-navigation groups and three
no-image export groups on the preceding candidate. A final five-group check on
this candidate reconfirmed narrow-card geometry, exact filter retention, no-image
export-result focus, valid generated HTML, no automatic download, exact optional
copy bytes and graceful owned-server exits. All 139 hashes matched before/after;
zero browser JavaScript errors were recorded. Native folder opening was mocked.
These browser groups overlap the full suite and are not added to its test count.

Independent output verification passed 15 desktop/narrow groups plus five
nested-link groups on the preceding runtime-identical candidate. Four final
manual-exchange groups verified empty-model save, immediate method visibility,
saved reload, keyboard ZIP export, actual copied instructions, read-only JSON
validation and explicit import. The request trace contained settings/export/import
and Quit only, with no provider/preflight calls. Final 139-file hashes matched
before/after, zero JavaScript errors were recorded and owned servers exited 0.
Native folder opening was mocked; native select keystrokes and arranged-package
browser coverage were not established in this check. Full package functional
coverage remains in the suite. An added no-Ollama regression passed within the
focused 15-route suite (1.449 seconds) and final 477-test suite. Detailed
private evidence stays ignored under `build/quit-stopped-feedback-20261004/`,
`build/image-navigation-independent-20261004/` and
`build/structure-zip-independent-20261004/`. External acceptance remains pending.

## Earlier local continuation — 2026-10-04

The published checkout at `70d0a72` remains the baseline. This continuation keeps
all existing edits. At this earlier checkpoint its changes were uncommitted;
no push, merge, tag, release, deployment or real-project processing occurred.

- Manual CSV mapping has a visible entry beside XML matching. Unmatched or
  ambiguous results and XML failures reveal the existing tools and recovery links.
  Existing identity validation, review decisions and Undo remain in use.
- Optional image-description tools precede Reading order and open when pending
  image review or draft requests/results make them useful. An explicit browser
  choice persists per project; direct links reveal tools for a visit without
  replacing that choice. Opening tools does not save or approve content.
- Quit is available throughout the app, confirms unsaved current-tab fields and
  warns about all tabs. It refuses during requests, streamed downloads and queued
  or running generation. It stops only the owned server; external servers refuse.
  Cancel/Escape preserve edits, callback failure supports retry, and another tab
  reports an already requested shutdown. An exact copied macOS launcher ended
  normally; actual Terminal window closing and Windows hardware remain unverified.

Earlier runtime/test/tool/launcher candidate:
`6697bf09f11b29adc5a76ab9538e11c2a80487253ae3a9114c58dddd7fdc4558`
(137 files; documentation excluded). **463 tests passed in 27.924 seconds**;
the focused lifecycle/discovery/layout checks passed **32 tests in 2.804 seconds**.
The first full run's two obsolete always-collapsed expectations were updated to
the useful-default behavior while retaining the other layout assertions. Both
failure and final passing logs are retained locally.

Independent checks include six functional Quit tests, earlier 16 discovery/media
and seven Quit browser groups, and separate final five- and four-group smoke
checks on matching runtime hashes. They verify CSV import/Undo, preferences,
keyboard and 390px layouts, unsaved Cancel, busy refusal, shutdown races,
failure/retry and actual owned-process exit. Final smoke reports record zero
JavaScript errors, unchanged saved fixture bytes and stopped owned servers.
These groups overlap the full suite and are not added to its test total.

A further independent check of the user's readiness-navigation request verified
successful XML matching, CSV import, Export and actual Copy HTML at both 1440px
and 390px. All eight actions focus the readiness heading below the sticky header;
clipboard contents exactly match generated HTML. Zero browser errors, unchanged
137-file candidate and normal owned-server exit are recorded in
`build/discoverability-quit-independent-20261004/readiness-actions/report.json`.
This behavior was already implemented; no duplicate runtime change was needed.

Installed Homebrew Poppler 26.08.0 was reverified without another installation.
The launcher paths resolve both rendering commands even with a minimal initial
PATH. Fresh uncached rendering of two pages from an approved real-PDF disposable
copy produced 1020 × 1320 PNGs; source bytes remained unchanged. Prior caches
support earlier successful rendering, but the later PATH failure's cause is
unknown. Existing diagnostic coverage passes in the full suite; its historical
54-task warning was one included block review, and the inspected current review
now records that diagnostic as resolved. Pillow was not installed. The live
app and actual project state were not changed or restarted.

Evidence: `build/held-items-sprint-20261004/`,
`build/discoverability-quit-independent-20261004/`, and
`build/safe-quit-independent-20261004/`. Earlier rendering and diagnostic evidence
is retained in `build/poppler-diagnostic-20261002/`. External acceptance below
remains pending.

## Current implementation and local verification

The Phase 3B page/article builder is implemented. Existing single-document
review, preview and export workflows remain available; arranging several output
pages is optional. See [workflow and schema](PHASE3B_OUTPUT_PAGES.md).

The accumulated stabilization work covers:

- Atomic Save and approve for editable blocks. Image approval validates the
  displayed image and linked descriptions together; ordinary saves and material
  edits still require manual review. Missing text, stale snapshots and conflicting
  associations reject approval without partial writes.
- One image-owned review task for linked descriptions, with a unified editable
  form, direct recovery links and consistent counts across Document, Structure,
  Accessibility and Export. Provided text awaiting review is distinguished from
  missing text. Standalone descriptions keep their own editor.
- Accessibility bulk review with exact visible scope, explicit confirmation,
  stale-scope rejection, normal save/reopen and Undo. Completed decisions remain
  editable history. Document findings, content approvals and automated HTML checks
  have distinct scopes; overlapping counts are not added together.
- Document diagnostics with a recorded cause, affected source/block context,
  publication impact and a recovery action. Historical resolved diagnostics stay
  separate from current manual review tasks. Missing targets have useful guidance
  without broken links.
- Media routing that preserves existing content approvals when only WordPress
  URLs or attachment IDs change. Source-image or authored-text changes still
  require fresh review; generated publications remain sensitive to mapping changes.
- Exact-filename media matching after unchanged-image re-upload. Changed IDs
  require explicit confirmation and the same saved URL; XML does not prove image
  bytes unchanged. Missing, ambiguous or different-URL entries keep current
  mappings and explain why. Choosing another XML clears confirmation visibly.
  Results distinguish updates, already-current mappings and confirmation required.
- Explicit preview/confirmation for restoring approvals lost to earlier routing-only
  changes. Retained history must prove the original decision, unchanged content,
  coherent project identity and exact current scope. Recovery preserves original
  approval dates, descriptions, mappings and newer decisions; uncertain histories
  require manual review. Undo consequences are disclosed before confirmation.
- Export readiness visible for both ready and blocked projects. Matching media,
  document export and Copy content move focus and scroll to readiness; links return
  to matching results or content controls. Stale-copy recovery preserves the
  clipboard, clears obsolete results and directs the user to reload Export.
- Contextual Help opening separately from authoring, concise action feedback,
  floating Back to top, saved block/filter focus and keyboard focus below sticky
  controls. WSUWP previews explicitly use approximate local CSS.
- Source rendering with actionable missing-Poppler/start/render failures and retry.
  Chosen project folders retain original inputs and partial processing output;
  global Recent projects failures do not invalidate saved projects.
- Manual image-drafting instructions beside ZIP controls. Copy uses the existing
  clipboard helper, restores focus, preserves unsaved edits and offers fully
  selected readonly text if both copy methods fail. The fallback scrolls into view
  on narrow screens. Imported suggestions require human review.
- Retained nested text regions included in source outlines, with partial-coverage
  explanations where needed. Text-bearing lists without children remain visible,
  block incomplete publication and support explicit recovery with Undo. Mixed-block
  list conversion and real-project reconstruction remain separate author actions.

Earlier published runtime/test/tool candidate:
`09f0816c993f51990609721e87d7798c6570e946aa0bde1b1b3538feaa3fb892`
(134 files; documentation excluded). At this candidate, **452 tests passed in
26.708 seconds**; focused image-draft checks passed **36 tests in 1.744 seconds**.
Publication checks below record the final checkout after documentation sanitization.

### Browser and artifact evidence

Isolated Chrome workflows verified review/edit/save/reopen/Undo, explicit approval,
bulk review, pending/complete counts, Help, media matching/recovery, ready/blocked
export feedback, downloaded artifacts and clipboard behavior. Synthetic regression
fixtures contain generated local images and example.test URLs; approved real-input
checks used disposable copies and kept detailed evidence local.

- Media-to-WSUWP draft Page journeys parsed downloaded PNG ZIPs, mapping reports and
  WXR content. Image URLs, attachment metadata, alternatives and linked descriptions
  agreed with the reviewed fixture. Repeating current XML made no new revision;
  Undo/rematching and rejection of genuine edits were checked.
- Manual drafting exported and downloaded a real ZIP from a synthetic project.
  INSTRUCTIONS.txt, request.json, response-template.json, review-sheet.csv and PNG
  bytes were inspected. Exchange-v1, all five identity fields and null optional
  response fields matched the copied prompt. Six primary browser groups and an
  independent UI review passed, including exact clipboard contents, real native
  fallback, total/throwing failure, retry and separately opened Help. Unsaved fields
  and saved revisions remained unchanged; the independent copy-only check sent no
  POST requests. The failure textarea was fully visible below the sticky header at
  390px. Zero JavaScript errors; screenshots were visually inspected.
- Source pages rendered freshly from an approved disposable real PDF copy using
  Homebrew Poppler 26.08.0. The two inspected PNGs were 1020 × 1320 pixels. Prior
  local caches confirm earlier rendering; the later missing-PATH cause is unknown.
  Pillow remains separately absent and was not installed by assumption.
- Existing arranged-package tests exercise assignments, navigation, internal links,
  page-local footnotes/backlinks, image descriptions and representative downloaded
  HTML/Gutenberg/WXR/ZIP output. These are local fixture checks, not production or
  human acceptance of representative multi-page publications.

Local ignored evidence directories:

| Area | Evidence |
| --- | --- |
| Latest candidate, clipboard and full suite | `build/image-draft-copy-instructions-20261004/` |
| Independent clipboard review | `build/manual-copy-instructions-independent-20261004/` |
| Media refresh and result semantics | `build/media-xml-rematch-20261004/` |
| Readiness, approval recovery and broader coverage | `build/export-readiness-scroll-20261004/` |
| Poppler setup and diagnostic clarity | `build/poppler-diagnostic-20261002/` |
| Publication privacy audit and final checks | `build/publication-20261004/` |

These evidence files are not part of the published source. Owned test servers were
stopped; actual project data and the live app were not rewritten or restarted.
No private source PDFs, caches, generated publications, credentials or screenshots
are added by this stabilization publication.

## Historical local milestones

These are recorded earlier results, not current test counts or external approval.
Detailed historical notes, source identities and private comparisons are withheld
from this public summary and retained in ignored local evidence.

| Milestone | Recorded local result |
| --- | --- |
| Poppler setup and Document diagnostic clarity, 2026-10-02 | 338 tests passed; fresh real-source rendering on disposable copies |
| Draft discovery, project-local ZIPs and merge feedback, 2026-10-02 | 347 tests passed; nine desktop/narrow Chrome groups |
| Source-backup verification, 2026-10-03 | 361 tests passed; syntax and diff checks |
| Media refresh and result semantics, 2026-10-04 | 450 tests passed; actual-XML disposable-copy and synthetic regression checks |
| Manual instructions clipboard, 2026-10-04 | 452 tests passed; primary and independent browser checks |

## External acceptance — still pending

| Required check | Status and reason |
| --- | --- |
| Production-authoritative WSU WordPress/plugin Gutenberg and WXR imports | Pending: local serializers, shims and fixture imports do not establish compatibility with the destination's actual versions. A reported successful import is not full editor/render acceptance. |
| Human VoiceOver review | Pending: a person must listen and interact with representative workflows and exported output on macOS. Browser assertions do not replace this. |
| Actual Windows hardware | Pending: no actual Windows run established. |
| Dedicated representative multi-page WordPress round trip | Pending: verify complete content, arrangement, images, navigation, footnotes and edit/save/reopen on the authoritative destination. Synthetic package checks do not fulfill it. |

A later Docker startup check confirmed the installed engine and cached WordPress
images, but the WordPress Importer dependency was unavailable for that new local
run. No additional dependency was installed. Earlier local importer evidence is
historical; no fresh local WordPress import/editor acceptance is claimed here.

Provider draft quality, OCR/extraction hardening and optional backlog items remain
outside this publication. [Future work](FUTURE_FEATURES.md) does not authorize its
implementation. Local browser/axe checks do not certify WCAG conformance.

## Publication status

Version remains **0.7.0**; stabilization changes are recorded under **Unreleased**
in CHANGELOG.md. The authorized destination is the existing public repository's
`codex/phase3b/output-page-builder` branch. Publication is a source handoff, not a
backup of private projects. No main merge, tag, deployment or release is included.
The completion report identifies the exact pushed commit and any CI outcome.

Final publication checkout: **452 tests passed in 26.531 seconds** after
documentation sanitization. Python/JavaScript syntax, corpus JSON parsing,
version consistency and `git diff --check` passed. Runtime hashes still match the
browser-tested candidate above, so existing affected-workflow browser evidence
applies. Detailed private reports are preserved under ignored local `build/`.
