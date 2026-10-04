# Phase 3B acceptance ledger

Version: 0.7.0. Updated: 2026-10-04.

Local implementation, external acceptance and publication are separate. The
public ledger records behavior and verification without source-document names,
private project identities, attachment IDs, revision histories or input hashes.
Detailed earlier reports are retained only in ignored local evidence. Sanitizing
this checkout does not remove material from previously published Git history.

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

Latest runtime/test/tool candidate:
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
