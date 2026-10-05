# Phase 3B acceptance ledger

Version: 0.7.1. Updated: 2026-10-05.

Local implementation, external acceptance and publication are separate. The
public ledger records behavior and verification without source-document names,
private project identities, attachment IDs, revision histories or input hashes.
Detailed earlier reports are retained only in ignored local evidence. Sanitizing
this checkout does not remove material from previously published Git history.

## Version 0.7.1 branch handoff — 2026-10-05

The authorized handoff reconciles the changes since `07d9311` on
`codex/phase3b/output-page-builder`. Version 0.7.1 is a patch for existing review,
source-preview, manual-response and export behavior; stored schemas are unchanged.
Bulk PDF importing was not started. General bold/italic preservation and automatic
small-running-header title selection remain backlog/limitations. The saved-title
preservation correction and manual arranged-title repair are verified below;
no actual project repair, re-extraction or approval was performed.

Final runtime/test/tool/launcher candidate:
`a24f4a3acb88ff98f42000c7fa5839e416d610699399734b38da4b93b84fb716`
(144 files, documentation excluded). **515 tests passed in 35.193 seconds** with
`TMPDIR=/private/tmp .venv/bin/python -m unittest discover -s tests -v`.
Separate previously authored functional and artifact drivers were rerun against
this exact candidate: **32 filter/merge browser groups**, **four manual-response
browser groups**, **11 source/export/readiness/Copy browser groups**, and **five
saved-artifact groups**. These are overlapping coverage, not extra unit tests or
a new independent human review. The source-header repair additionally passed six
disposable browser groups, inspected saved artifacts and exact Undo.

Final coverage includes every review/type intersection, first-result focus below
sticky controls, empty/reset behavior, dirty cancellation with exact selection/
scroll/text preservation, delayed source rendering, keyboard/narrow/reduced-motion
behavior, stale saves/merges, Save/approval/Undo/reopen, source pixel alignment,
manual ZIP/clipboard destination agreement, preserved earlier responses, clipboard
fallback, partial/complete media-to-readiness, saved-export focus, exact Copy,
stale Copy recovery and owned Quit. Actual HTML/Gutenberg/WXR/Markdown and arranged
package inspections retain authored standalone equivalents once, all 19 fixture
images with exact alternatives/local bytes, and WXR's exact Gutenberg content.
Acceptance stamps on the disposable artifact fixture are test instrumentation,
not editorial approval. Providers were forbidden and native folder opening mocked.
An initial copied artifact fixture required renewed page review after changed
export settings; the gate correctly blocked it, and the instrumented rerun passed.

Private evidence is retained under `build/release-0.7.1-20261005/`. The final
before/after checks matched all 144 candidate hashes and all 314 files across four
original projects. Six final screenshots were visually inspected, and all owned
test servers exited 0. Public source
and documentation scans found only synthetic test attachment IDs, with no actual
source names, project paths or private attachment metadata. No private PDF,
source screenshot, generated project export or evidence file is included in Git.
The existing public origin is `https://github.com/baschwar/pdf-to-web.git`; its
branch matched `07d9311` before publication. GitHub reports zero configured Actions
workflows. The final completion report supplies the pushed commit, verified remote
SHA and any check results. No main merge, tag, GitHub release or deployment is
included. Human VoiceOver, production WSUWP/plugin imports, Windows hardware and
the representative multi-page WordPress round trip remain pending.

## Small running-header title recovery — 2026-10-05

The author reported good content results apart from a missing document H1 in a
four-page sample. Read-only inspection confirmed that its small repeated header
is present in source pixels and PDF text on every page, but absent from raw JSON,
normalized blocks and saved exports. It has no block ID and was not removed by
review exclusion. Both the committed baseline and current largest-font selector
choose a larger body section instead; automatic title detection remains limited.

A disposable repair probe exposed a separate preservation defect: after demoting
that section, reopening added it again as a recovered title. Source-title
initialization now refuses to add a title once a review revision has been saved,
while fresh normalization and existing matching-title box backfill retain their
behavior. One new regression test covers the saved demotion. **49 normalization
and source-geometry tests passed in 0.571 seconds**, and **28 arrangement tests
passed in 0.720 seconds** before the preservation fix.

The final disposable browser repair passed **six groups**: section H1-to-H2 change,
explicit arranged title, exactly one semantic H1 with both tables retained,
save/reopen at 390px, actual saved HTML/Gutenberg/WXR exports and exact Undo of
block and arrangement records. Source text, IDs, provenance, links, tables and
other block decisions stayed intact. The WordPress template-title option was
honored: WXR carries the correct page title while body Gutenberg omits H1.
Zero JavaScript errors or horizontal overflow; desktop/narrow screenshots were
visually inspected. The owned server exited 0. An initial probe exposed the real
recovery defect; a subsequent driver synchronization race was corrected and its
log retained. No blanket initial-pass claim is made.

Existing projects need an explicit author repair through Structure and Arrange
Pages after relaunch; automatic re-extraction, source-header insertion or review
approval was not performed. README describes the arranged export route and
WordPress title-field distinction. Private source text, IDs, screenshots, saved
artifacts and recovery instructions remain under
`build/bloodborne-title-readonly-20261005/`. Final candidate-wide verification and
publication status are recorded separately.

## Inline formatting feasibility — 2026-10-05

This low-priority read-only follow-up inspected the requested table-heavy sample,
identified by the newest Recent projects record and matching project/source
metadata. The authenticated live session was not separately queried or navigated.
Both cached source-page images and PDF font dictionaries were inspected. The
sample has clear regular, bold, italic and combined font metadata, but some raw
elements coalesce differently styled PDF spans under one font label.

Of 51 normalized table cells, 27 retain multiple raw font names in provenance;
39 contain raw bold/italic text. No cell has normalized formatting runs. General
normalization does not translate font names into runs; table normalization joins
descendant text, and HTML/Gutenberg table rendering escapes plain cell content.
The actual saved WordPress export matches its manifest hash and the current
serializer byte-for-byte: four tables, no strong elements, and one emphasis
element for the recovered source note. This confirms partial support, not a
regression in an already-supported formatting path. Markdown also currently
ignores typed formatting runs.

Thirteen existing focused tests passed in 0.198 seconds, covering Gutenberg,
recovered-note emphasis, unchanged list saves and rich list editing with Undo.
Synthetic artifact probes confirm existing paragraph strong/emphasis runs survive
HTML, Gutenberg and WXR, while table-cell output and Markdown remain plain.
The 514-test full-suite result in the first-matching-block entry below applies to
the runtime unchanged by this follow-up's documentation-only edits. README and
Future Features
record a bounded proposal that separates reliable source presentation from
author-confirmed semantic emphasis and retains links, footnotes, IDs, table spans,
review fingerprints and explicit existing-project recovery. No formatting feature,
re-extraction, migration, dependency installation or live-app restart was performed.
All 44 original project files retained their before/after hashes, and all 144
runtime candidate hashes remained unchanged. Diff whitespace checks passed.
Private evidence is retained in `build/inline-style-readonly-20261005/`.

## First matching block after filtering — 2026-10-05

Explicit changes to either Structure filter, including Reset filters, select the
first matching block in saved reading order and reveal it below the sticky
controls with its source context selected. Both filter values remain active.
Empty intersections focus and announce Reset filters without selecting a hidden
block. Save, approval, Undo, reopening and finding-link navigation retain their
existing behavior; they do not use the new first-result action.

The existing unsaved-editor guard runs before a filter change. Cancel and Escape
preserve both filters, selection, exact scroll position and entered fields.
Confirmation closes the dialog before focusing the first permitted result.
Delayed source rendering resettles the selected block only while it still owns
focus. Narrow-layout and reduced-motion checks passed without forced animation.

The 144-file runtime/test/tool/launcher candidate is
`21d2fe216770714635ddc55a6c379e8a5d4a2152065d06edc9cdaa9790f39a51`
(documentation excluded). **514 tests passed in 35.227 seconds** using
`TMPDIR=/private/tmp .venv/bin/python -m unittest discover -s tests -v`.
Synthetic browser verification passed **32 groups** at 1440px and 390px, including
all 28 review/type intersections at each width, first-result focus, an already
matching later selection, empty results, dirty cancel/confirm, delayed source
rendering, keyboard navigation, reduced motion and retained Save/approval/Undo/
reload behavior. Zero JavaScript errors or horizontal overflow. Both representative
screenshots were visually inspected. JavaScript syntax and diff whitespace checks
passed. All 144 candidate hashes matched after testing; all 84 files in the
original project's before/after inventory retained their hashes. The owned fixture
server exited 0; the real app was not restarted or navigated.

A dense infographic remains an explicit regression case: its author's assessment
of the preview did not pass automatic grouping/layout acceptance. Retained assets
are useful, but manual semantic reconstruction may be necessary. Local filter,
source-outline and export tests do not establish acceptable automatic content
grouping. No real-project reconstruction, re-extraction or migration was performed.
This limitation is recorded in README and ignored local evidence.

Private evidence is retained in `build/filter-first-result-20261005/`, including
the browser report, full-suite log, before/after inventory and infographic
regression record. README and changelog describe first-result navigation. Work
remains uncommitted on `codex/phase3b/output-page-builder` at base `07d9311`;
nothing was pushed, merged, tagged or released. Human VoiceOver, production
WSUWP/plugin imports and actual Windows acceptance remain pending.

## Structure filters and Merge next safeguards — 2026-10-05

Structure now combines Review state and Block type in two compact rows. Their
intersection drives visible cards, contextual counts and Previous/Next. Linked
image descriptions affect their owner's state without adding block rows. Choices
remain separate per canonical project folder in browser-tab storage, including
projects with identical source filenames. Save, approval, classification changes,
Undo and reopening preserve both filters; empty views retain them and focus Reset
filters. Explicit finding links reveal their target with an explanation of the
necessary filter changes. Hiding dirty editors requires confirmation and keeps
their fields in the tab. Other saves, structural actions and Undo cannot discard
those fields; snapshot checks reject stale saves without overwriting newer work.

Merge next retains the shared server eligibility for adjacent matching text
blocks and same-level headings. List, mixed-type, rich/nested, excluded and final
block boundaries remain disabled with accessible reasons. Unsaved edits, saving
and hidden actual neighbors disable merging; filters never change its candidate.
Snapshot and target validation reject stale merges. Older server markup remains
disabled until relaunch rather than being enabled by newer JavaScript. Supported
merges retain their existing fresh-review and Undo behavior. Existing projects
are not re-extracted, migrated, merged or approved by these changes.

The final 144-file runtime/test/tool/launcher candidate is
`4bde04fb2c2fd621a6ab5b7dfa55711bf32b7daa9d7a1c23a4a7be1d9bdb1492`
(documentation excluded). **514 tests passed in 34.524 seconds** with the
documented macOS command `TMPDIR=/private/tmp .venv/bin/python -m unittest discover
-s tests -v`. The first default-temporary-directory run exposed seven existing
`/var` versus `/private/var` path-sensitive failures; its log is retained. No
unrelated path implementation or dependency changes were made.

Eight merge tests, five new filter tests and 16 existing layout tests passed.
Synthetic browser verification passed **23 groups** at 1440px and 390px, including
all 28 review/type combinations at each width, keyboard navigation, contextual
counts, dirty confirmation and Escape, classification save/Undo, finding links,
last matching Save and approve, stale save/merge rejection, supported merge/Undo,
older markup and project isolation. Zero JavaScript errors or horizontal overflow.
Both representative filter screenshots were visually inspected. All 144 candidate
hashes matched after testing; all 58 original project files retained their hashes.
Owned fixture servers were stopped; the real app was not restarted or navigated.

README and changelog explain the workflow and relaunch step. Work remains
uncommitted on `codex/phase3b/output-page-builder` at base commit `07d9311`;
nothing was pushed, merged, tagged or released. Private evidence is retained in
`build/merge-safeguards-20261005/`. Human VoiceOver, production WSUWP/plugin imports
and actual Windows acceptance remain pending.

## Manual response destination and infographic review — 2026-10-04

This local follow-up builds on published branch commit `07d9311`. New work is
uncommitted; no additional push, merge, tag, release or deployment is authorized.
Original projects and the live app remain untouched. Authorized source inspection,
editing, review and export checks use disposable copies or synthetic fixtures.

- Copied manual drafting instructions, ZIP instructions and request metadata name
  the selected project's absolute response destination and unique suggested JSON
  filename. Earlier files are preserved. Tools without authorized local access
  return an attachment/download instead of inventing a folder or claiming a save.
  Manual sharing discloses the local path. Exchange-v1 identities and explicit
  validate/import/review remain unchanged; responses may be selected elsewhere.
- Recovered title/subtitle outlines compose PDF text and graphics transforms and
  encoded glyph widths. Ordinary source boxes account for the actual MediaBox
  origin and rotation. A read-only display overlay preserves existing saved text,
  coordinates and decisions. Edited or ambiguous text receives an explanatory
  no-outline state. Tall rendered pages and highlights share the visible image
  dimensions; the desktop pane reveals selected regions within the available
  viewport and supports keyboard scrolling. Narrow layouts keep natural page
  scrolling; long response paths wrap.
- Authored standalone visual equivalents are included in document HTML,
  Gutenberg, WXR and Markdown. The shared arranged-page projection avoids
  duplication, preserves image associations and exclusions, and leaves original
  records unchanged. Pending reviews still prevent publication; unaccepted
  drafting suggestions are not included.

The independent source review accounts for all 44 saved blocks and all 19 image
assets in an approved source snapshot. It identifies repeated/shadow title text,
a truncated duplicate introduction, numbered-section placement and icon/group
reading-order decisions. These are explicit author-review findings, with private
block-level evidence retained locally. No deduplication, reclassification,
automatic ordering or medical/editorial approval is applied to real data.

Focused regressions pass: six manual-destination tests, 15 geometry tests, seven
standalone-description export tests and 28 existing arranged-page tests. Browser
review checks exercise description counts, image saves/approval, exact filters,
late rendering, Undo and reopening on a disposable source copy. Saved export
checks inspect HTML, Gutenberg, WXR, Markdown, image bytes and arranged output.
The final 142-file runtime/test/tool/launcher candidate is
`2e37a0575a4c03cdede736f1a6cdbea89d461022a27eb50303c1894514c48e5c`
(documentation excluded). **505 tests passed in 30.748 seconds**; all 142 hashes
matched afterward. JavaScript syntax and diff whitespace checks passed. The
source owner's actual copied-PDF browser probe passed 26 geometry/resize/late-load
assertions with zero JavaScript errors. Twelve actual Poppler rendering cases
cover three paper sizes, four rotations, nonzero MediaBox origins and a distinct
CropBox; all exited 0 and pixel alignment stayed within two pixels.

Before the final sticky-pane correction, the independent functional reviewer
passed **18 groups** on runtime candidate `bed0812a`:
four destination checks, five actual saved-export/package inspections and nine
browser source/navigation/review-gate groups. All 142 hashes matched before/after
and at cleanup; zero JavaScript errors were recorded. Original project inventories
remained byte-identical across all 41 files. The owned server exited 0 through
Quit. Earlier eight review groups cover counts, ordinary Save, Save and approve,
advance, exact filters, late rendering, newer editor focus, Undo and reopen.
Native folder opening was mocked; native macOS select keystrokes and external
acceptance were not established.

On the final candidate, independent visual review passed **88 selections** across
all 44 blocks at desktop/390px, all 44 desktop selected-region visibility checks,
resize alignment, keyboard pane scrolling and editor-focus preservation. Ten
representative screenshots were visually inspected; title and References outlines
are correct and visible. All 142 candidate hashes matched before/after; all 41
original files retained their hashes, sizes and mtimes. Zero JavaScript errors or
horizontal overflow; the owned visual QA server exited 0. The source owner also
passed ten integrated pane/keyboard/resize/late-load groups.

The final independent functional smoke passed **11 groups** on `2e37a057`,
covering desktop footer visibility, preserved review focus, keyboard pane
scrolling, natural narrow layout, source-title alignment, pending review gates,
partial/complete media matching to readiness, Continue to controls, saved-export
results, exact Copy bytes/focus, no-image export and stale-copy recovery. All
142 hashes matched before/after and cleanup; original 41 files remained unchanged.
Zero JavaScript errors; the owned functional QA server exited 0 through Quit.

Private evidence: `build/response-destination-highlight-20261004/`,
`build/infographic-source-review-20261004/` and
`build/infographic-functional-independent-20261005/`. Local browser/fixture
approval does not establish human VoiceOver, production WSUWP or Windows
acceptance; those remain pending.

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

Version **0.7.1** records stabilization in CHANGELOG.md. The patch version reflects
corrections to existing workflows with unchanged stored schemas. The authorized
destination is the existing public repository's
`codex/phase3b/output-page-builder` branch. Publication is a source handoff, not a
backup of private projects. No main merge, tag, deployment or release is included.
The completion report identifies the exact pushed commit and any CI outcome.

Earlier branch publication at `07d9311`: **452 tests passed in 26.531 seconds** after
documentation sanitization. Python/JavaScript syntax, corpus JSON parsing,
version consistency and `git diff --check` passed. Runtime hashes still match the
browser-tested candidate above, so existing affected-workflow browser evidence
applies. Detailed private reports are preserved under ignored local `build/`.
