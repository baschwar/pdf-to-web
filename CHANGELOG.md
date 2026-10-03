# Changelog

## [Unreleased]

### Stabilization

- Include recorded nested paragraph/text regions in list source outlines,
  deduplicate boxes and explain partial coverage when regions are unavailable.
  Unoutlined text is not treated as missing content.
- Keep text-bearing lists without items visible in editors and semantic,
  Gutenberg/WXR and Markdown previews. Reject blank saves and approval/export
  until their structure is recovered. Unchanged-text conversion or explicit
  recovery preserves the text as one item with links, formatting, footnotes,
  source provenance, fresh review and Undo; no existing project is auto-repaired.
- Prepare an isolated, reviewable CITI step 11 nesting reconstruction. Preserve
  original IDs and text, output-page assignment and Undo; leave actual project
  changes and approval to the author. General mixed-type list conversion,
  insertion, source-region drawing and OCR remain separate proposed work.

- Make Image description drafts a distinct Structure section with collapsible
  tools and direct, keyboard-focused links beside image alternatives and findings.
  Keep imported/generated drafts separate from manual approval.
- Show the project-local saved path for AI drafting ZIPs, with descriptive unique
  filenames, atomic creation, output path confinement and preserved earlier
  packages. Retain browser downloads and the existing identity/context schema.
- Explain Merge next limits beside disabled unsupported controls and show failed
  actions inline. Protect lists, rich/nested and excluded content from unsupported
  merges; retain footnote IDs, positions and backlinks in supported text merges.
  Mixed-block list conversion remains a separate design decision.

- Explain Document diagnostics within the review-task summary, with recorded
  causes, affected source/block links, publication impact and recovery guidance.
  Count affected reviews once; preserve manual decisions, resolved history and
  Undo. Identify missing source copies or targets without broken recovery links.
- Document Poppler as a separate system dependency, with Homebrew setup,
  verification and restart/PATH troubleshooting. Include standard Homebrew
  executable paths in the macOS launcher. Verified fresh CITI source-page
  rendering with Homebrew Poppler 26.08.0 on an isolated PDF copy; Pillow remains
  a separate supplemental-extraction dependency.

- Let new projects use an explicitly chosen destination folder as their exact
  root. Show full working paths, preserve original PDFs and loose files, reject
  conflicting working directories, and retain/report partial conversion files
  without switching away from the previous project. Defaults remain explicit.
  Report global Recent projects write failures without blocking saved projects.

- Show actionable source-page rendering failures in Structure, with original PDF
  access and Retry. Outline source regions only after the page image loads, and
  prevent older page requests from replacing the current selection. Missing
  Poppler is reported without creating an empty render-cache directory.

- Refresh Export counts, exact review links and its enabled state immediately
  after XML/CSV media mapping and Undo. Keep manual approval invalidation for
  changed media, preserve authored fields, and retain state after failed imports.

- Group Export's image preparation/Undo and title Copy/content Export buttons
  into rows, and align media file chooser/action controls horizontally. Rows wrap
  at narrow widths; forward actions are green and Undo/Copy are gray.
- Explain empty reading-order filters beside disabled navigation, with a visible
  Show all blocks recovery link in the sticky toolbar. Keep the active filter
  after its last approval and preserve unsaved edits when recovering to All.
- Show aggregate pending block/description review tasks without changing block
  totals. Description links visibly select the exact editor and expose truthful
  reasons, affected fields after actual Reviewed edits, and manual next actions.
- Remove repeated status/guidance and duplicate Export readiness targets across
  the review UI; consistently bold field labels while keeping values/help normal.
  Retain useful preview handoffs and title-export help.
- Use the same manual description-review readiness in Document, Structure,
  Accessibility and Export. Filled Reclassified descriptions remain pending;
  Export findings link to exact items with readable source context.
- Recover existing legacy list approvals only from matching retained local
  history, recording versioned evidence without new approval decisions. Lists
  with uncertain history remain actionable and explain why review is needed.
- Restore reading-order selection after reload; recover an adjacent matching
  block after filter changes and explain empty
  filters. Explain fresh approval after a previously approved block changes,
  retaining that reason through reopen and Undo without an edit log.
- Require current source approval before HTML, Markdown, Gutenberg, WXR and page
  package generation. Reject pending or stale publication downloads and copying;
  retain previews, reports and image/draft preparation during review.
- Invalidate approval after content edits; require a fresh decision for edited
  Reviewed descriptions. Protect unsaved authoring forms during draft refresh and
  import, and preserve current alternatives/captions when mapping a media CSV.
- Retain Undo snapshots and roll back current state after failed persistence.
- Preserve retained list item identities and destinations on insertion/reordering,
  preserve list starts after reorder/reopen, retain trailing formatting during
  resource-link edits, and default new exports to nested heading hierarchy.
- Keep edited footnote source bodies and exported note text consistent through
  save, fresh approval and Undo. Use the existing Reviewed page decision for page
  publication eligibility and apply download gates to canonical resolved paths.

### Added

- Floating Back to top on every app screen after scrolling, with keyboard focus
  returned to the application header and no changes to authoring state.

- Save and approve beside primary block-editor save controls. The explicit action
  saves edits or retained-list recovery and approves valid final content in one
  Undo step. Validation failures leave saved state and entered fields intact;
  unsaved edits prevent ordinary approval from discarding authoring work.

- Compact gray Undo last saved change button in Structure's sticky Reading order
  toolbar, using existing persisted snapshots, disabled when history is empty,
  and retaining the selected block after Undo.

- View tested rules dialog for Automated HTML checks, showing the current scan's
  passed, detected, human-review and not-applicable rule results with descriptions,
  rule IDs, element counts, WCAG criteria and guidance. Opens to passed rules and
  supports keyboard closing and a compact scrolling layout.

- Document filename above every workflow screen and in browser tab titles;
  reading-order filters for approved, pending and excluded blocks.
- Explicit Reviewed and Not applicable visual-description choices, current
  readiness feedback, optional-field guidance, and linked pending items on Export.
- WordPress template-title export with a separate copyable HTML body and page
  title; H2 section or orderly nested heading options, saved with Undo.
- Editable link labels that preserve destinations and formatting, with inline
  Accessibility findings for URLs used as visible link text.

- Separate image ZIP preparation before content export, with a saved document-based
  or custom filename prefix, Undo, ZIP/CSV download links and visible media-mapping
  progress. WordPress media XML matching and optional manual CSV import precede
  final HTML/Gutenberg/WXR export and copying.

- Free bundled axe-core 4.13.0 checks run automatically in Accessibility against
  local semantic HTML using WCAG 2.2 A/AA rules. Detected issues and checks needing
  human review show rule guidance, affected HTML and Structure links. Scan failures
  remain visible; existing review decisions and export behavior are preserved.

- Structure completion message when all blocks are approved or excluded, with a
  keyboard-accessible Continue to Accessibility link and focus after final approval.
  Pending review decisions, blocked conversion, and empty documents suppress it;
  Undo or returning a block to review removes it.

- Context-aware image-description drafts in Structure, kept separate from accepted
  alt text, captions and complex-visual descriptions, with individual application,
  editing, rejection, explicit regeneration/retry, cancellation and Undo.
- Manual image/request ZIP and validated versioned JSON response exchange using
  document, block, asset, context and request identities.
- Optional existing local Ollama vision generation and a dedicated-key OpenAI
  adapter with explicit per-selection cloud consent; no automatic model downloads.
- Confirmed image-asset associations, stale-draft detection, bounded generation,
  incremental persistence and protection against late or switched-project results.

### Changed

- Accessibility findings show the Reading order block number after the source
  page; Open block controls align right, including related extraction findings.

- Right-align final workflow actions consistently, including Structure's green
  Continue to Accessibility, the Accessibility handoff, and page/document exports.

- Saving block content, link text or review state stays at the saved block below
  Structure's sticky toolbar, including nested links and All/Approved filters.
  If its status leaves the filter, All opens to retain the saved block in view.

- Reading order filters include current counts in parentheses; the compact
  visible/total block count sits on the same line when space permits.

- Structure filters are small text links with an emphasized active choice.
  Longer image descriptions has direct review guidance and collapsed extraction
  help. Arrange Pages separates Continue to Preview from its four page actions;
  Preview aligns both Continue to Export buttons right and spaces its mode buttons.

- Accessibility block corrections return to the issue list with a fresh scan.
  Open block uses a compact button; Save decision has a compact width. Resolved
  extraction notes move into history with explicit no-action guidance. A green
  Arrange Pages handoff appears only after document and current HTML checks clear.
- Arrange Pages Undo is gray; Preview has green Export buttons at top and bottom.
  Export omits passing readiness checks and empty diagnostic warnings, identifies
  unmapped images, and confirms Copied beside Copy page title.
- Document review progress and Review structure move above metadata, with one
  count summary, larger bold metadata labels, and Structure's green Accessibility
  handoff when review is complete. Empty diagnostic counts no longer warn.
- Structure collapses description tools and saved Undo history to emphasize Source
  and Reading order. Description links expand the relevant panel; pending counts
  remain visible. Manual response steps are ordered, and approved blocks have a
  disabled gray Approve button, including after a linked description saves.

- Output Pages is named Arrange Pages, with its optional purpose explained at the
  top, green Preview contents and Continue to Preview controls. Button groups
  have space between actions. The WCAG notice appears once in the screen footer.
- Automated Accessibility results use tables with prominent counts. Media XML
  matching brings a visible, focused result into view and lists each unmatched
  or ambiguous image by filename, description, source page and Structure link.
- Publication outputs keep one H1 title and repair heading skips; WordPress
  content omits that H1 when the template provides it. Source blocks stay intact.
- Completed extraction block-review notes are labeled resolved and collapsed;
  unchanged visual saves preserve image approval, and incomplete equivalents
  suppress Structure's green completion message.

- Output Pages is explicitly optional for splitting documents; long documents can
  use Preview and Export directly. Its arrangement outline is collapsed, and
  unassigned content can be included in the selected page or all content kept on
  one page, with Undo. Invalid arrangements disable export with a visible reason.
- Exported image names include the document or chosen prefix and remain stable
  across reading-order edits. The images ZIP includes all included local images.
  Semantic HTML uses copied named assets or mapped WordPress URLs. Media mapping
  changes clear stale content export controls until regeneration.
- Accessibility shows current results immediately without a generation or download
  step. Extraction diagnostics link to affected blocks with current status and
  source location. Structure shows reviewed, pending and excluded counts.

- Imported and generated image drafts fill empty alt, caption and long-description
  fields directly, retaining existing text and requiring human review. Previously
  imported drafts can populate empty fields in one batch, with Undo.
- Image long descriptions are editable beside the image, use explicit block-bound
  associations when needed, and appear in HTML, Gutenberg, WXR and page exports.
- Rejecting drafts removes untouched auto-filled values while preserving edits.

### Fixed

- Arranged semantic previews load retained local images even for WordPress-mapped
  content. Whole-list edits and unchanged saves retain links and item state;
  nested link-label edits synchronize the parent text editor. PDF link annotations
  preserve destinations when extraction damages only the visible URL's hyphens.
- WordPress Media XML matching preserves newer reviewed alt text and captions,
  skips subsequently excluded images, and supports Undo of attachment mappings.
- Initial output-page assignments retain excluded block references so restoring
  content cannot leave it accidentally unassigned in newly initialized projects.
- Imported image-description cards now resolve retained image paths correctly,
  show the image short alt, and keep it synchronized when either editor saves.
- Visual review saves confirm beside the button, preserve focus, and retain
  changes through reload and Undo.
- Structure review actions appear above the block header and source details:
  Needs review (yellow), Exclude (red), Approve (green), in that order.

- Image-draft exports now show selection/pending counts, offer a pending-image
  ZIP without manual selection, and focus the download link. Cancel controls
  appear only for active requests.

- Provider selections can now be saved per project without reloading or moving
  focus to block review. ChatGPT / other tool explicitly selects manual exchange.
- Ollama model input is hidden for other providers; provider setup and manual
  import accordion headings are bold, bordered and easier to identify.
- Provider help now describes only the selected provider, including after save
  and reopening, so ChatGPT manual exchange shows no Ollama or API setup text.
- Delayed block-focus restoration yields to active provider setup interaction.
- Manual request ZIPs now include a CSV review sheet with image names, context
  and draft alt/caption fields; the import panel explains how to export a batch
  for manual writing or processing with ChatGPT, Codex or another tool.

### Acceptance boundary

- Provider calls were mocked during development; live generation remains untested.
  Production WSUWP, human VoiceOver, Windows, extraction-abort investigation and
  historical WordPress acceptance remain pending. No WordPress operation or release.

## [0.7.0] - 2026-09-30

### Added

- Output Pages workspace with persistent block-reference arrangements, explicit
  grouping suggestions, Page/Article metadata, parent hierarchy, contents order,
  reassignment, split/merge and Undo.
- Independent semantic/WordPress previews and page/complete-package exports with
  HTML, Gutenberg, WXR, media, contents and a versioned review/import manifest.
- Page-local footnotes/backlinks, cross-page block links recomputed after slug
  changes, assignment/metadata validation and affected-page review invalidation.
- CLI `export pages` and repeatable synthetic browser workflow checks.

### Fixed

- Output-page refresh and focus after Undo, split, merge and metadata saves.
- Navigation wraps at narrower widths with the additional workspace.
- Accessibility link-purpose review recognizes existing normalized `url` runs.

### Acceptance boundary

- Production WSUWP, human VoiceOver, Windows, five-PDF OpenDataLoader abort
  investigation and historical WordPress retests remain pending in
  `docs/PHASE3B_ACCEPTANCE.md`. No publishing or release is implied.

## [0.6.1] - 2026-09-25

### Changed

- Project paths displayed in the browser now begin at the relevant project
  root instead of exposing the machine's full filesystem path.
- The application footer now shows the abbreviated Git commit after the
  version number.

## [0.6.0] - 2026-09-25

### Added

- A dedicated Accessibility workspace for reviewing document structure,
  images, complex visuals, tables, headings, links, unresolved content, and
  extraction diagnostics.
- Persistent human decisions with approved, unresolved, and not-applicable
  states plus reviewer notes.
- Short alt text, long-description, and adjacent-text-equivalent fields for
  complex visuals.
- Table caption, column-header, row-header, and structural-review controls.
- Downloadable human-readable HTML and machine-readable JSON accessibility
  review reports through the browser or `pdf-to-web export accessibility`.
- Regression coverage for assessment categories, decisions, reports, table
  semantics, HTTP persistence, and report downloads.

### Changed

- Reviewed table-header decisions now control semantic `th` and `scope`
  output in HTML and Gutenberg exports.
- Phase 2 is closed as the stable structural review foundation. Production
  WSUWP plugin compatibility and human VoiceOver listening remain documented
  external acceptance checks rather than automated conformance claims.

## [0.5.20] - 2026-09-18

### Added

- A silent end-to-end browser walkthrough using the synthetic Accessible Event
  Planning Guide sample.
- A public-safe Structure review screenshot in the GitHub README.
- Finder and Windows desktop launchers for an already configured checkout.
- Third-party dependency and OpenDataLoader attribution documentation.
- Platform-specific setup and Windows support-status documentation.

### Changed

- The project license changed from MIT to Apache License 2.0 beginning with
  this release. Previously published revisions remain available under MIT.
- The optional WordPress Preview now reports its effective Node.js 20.19
  minimum consistently with the locked dependency tree.

### Fixed

- WordPress Preview preserves ordered-list `start` and `type` attributes, so
  split or interrupted lists continue at their source numbers instead of
  restarting at 1.

## [0.5.19] - 2026-09-18

### Fixed

- Decimal ordered-list fragments and continuations now recover their actual
  starting number from the first source list item's original marker.

## [0.5.18] - 2026-09-18

### Changed

- Nested lists in Structure now display their full hierarchy instead of a
  misleading direct-item-only textarea. Whole-list text editing is disabled
  for these blocks so saving cannot discard nested items.

## [0.5.17] - 2026-09-18

### Fixed

- A following indented list is now associated with its preceding parent list
  item when their page geometry shows a clear nested relationship.

## [0.5.16] - 2026-09-18

### Fixed

- Lists interrupted by a screenshot are split into correctly ordered list,
  image, and continued-list blocks while preserving the continued item number.
- Empty text wrappers that duplicate an image region are removed.
- Selecting a list now outlines nested list items as well as top-level items.

## [0.5.15] - 2026-09-18

### Added

- Image blocks in Structure now provide an extracted-image preview, alt text,
  caption, and decorative-image controls.
- Image approval now requires either meaningful alt text or an explicit
  decorative designation. Previously approved images without either decision
  return to Needs review when reopened.

## [0.5.14] - 2026-09-18

### Changed

- Structure block navigation now aligns the selected block directly below the
  sticky Reading Order controls, using their measured height as the scroll
  offset.

## [0.5.13] - 2026-09-18

### Fixed

- Source highlighting for lists now outlines each list item's actual region
  instead of drawing one large rectangle across intervening screenshots or
  unrelated page content.

## [0.5.12] - 2026-09-18

### Changed

- Disabled buttons now use an opaque dark-text-on-light-gray treatment with
  enhanced text, border, and adjacent-background contrast.

## [0.5.11] - 2026-09-18

### Changed

- Structure's sticky source and reading-order headings now remain below the
  application header at different browser sizes and zoom levels.
- The selected block navigator now shows the source page above the block
  position; repeated page labels were removed from individual block headers.

## [0.5.10] - 2026-09-18

### Fixed

- Source-page previews and source-PDF links now carry a project-specific cache
  key, preventing screenshots from a previously opened project from persisting
  behind the current project's block highlights.
- Source PDF and rendered-page responses opt out of browser caching as an
  additional cross-project safeguard.

## [0.5.9] - 2026-09-18

### Changed

- Reading-order block headers now emphasize review status with text-labeled
  green, yellow, or red pills beside the source page number.

## [0.5.8] - 2026-09-18

### Added

- HTML export results now include a **Copy HTML** action beside the download
  link, with clipboard fallback and accessible success or failure feedback.

## [0.5.7] - 2026-09-17

### Added

- WordPress Media WXR/XML imports can populate generated media mappings by
  matching attachment filenames to exported PDF assets.
- Matched attachment URLs and IDs are saved both to `media-mapping.csv` and the
  reviewed document, while unmatched or ambiguous filenames remain unresolved.

## [0.5.6] - 2026-09-17

### Added

- WordPress media exports include a single `media-upload.zip` and editable
  `media-mapping.csv`, correlated by stable document block ID.
- The Export screen imports a completed mapping CSV, validates WordPress URLs
  and attachment IDs, and saves media mappings into the reviewed document.
- Regenerated Gutenberg and WXR exports use mapped URLs, attachment IDs, alt
  text, and captions in proper WordPress Image blocks.
- `docs/FUTURE_FEATURES.md` records authenticated REST media upload and direct
  draft publishing as deferred work.

### Security

- Manual media mapping remains entirely local and requires no WordPress
  credentials or predicted upload paths.

## [0.5.5] - 2026-09-17

### Fixed

- PDF title recovery now reads effective font scale from the text matrix, so a
  smaller multi-line subtitle is preserved as H2 instead of merged into H1.
- Meaningful sample-plan notes and revision dates omitted by extraction are
  recovered once from the first-page footer and retained at the document end.

## [0.5.4] - 2026-09-17

### Fixed

- Ordered-list Gutenberg attributes now use the same HTML marker values as the
  serialized list (`a`, `A`, `i`, or `I`), preventing WordPress from marking
  alphabetic, Roman, and decimal lists as invalid blocks.
- Empty normalized paragraphs are omitted from Gutenberg output instead of
  appearing as blank editor insertion points between lists and images.

## [0.5.3] - 2026-09-16

### Added

- Normalization records raw source order separately from high-confidence visual
  reading order and exposes inferred heading/table associations in Structure.
- Ambiguous heading/table and inconsistent page-region patterns are flagged for
  reading-order review instead of being silently rearranged.

### Fixed

- Visually stacked heading/table groups are restored when PDF object order puts
  copied tables after their labels, including the four-year program-plan case.
- Manual block moves persist as an explicit override and are never replaced by
  automatic visual reconciliation on reload.

## [0.5.2] - 2026-09-16

### Added

- WordPress exports copy extracted local images into
  `output/wordpress/assets/` and generate JSON and Markdown media manifests.
- Export results report unresolved image counts and provide downloads for
  extracted assets and media manifests.
- Normalized ordered lists retain decimal, alphabetic, and Roman marker style.

### Fixed

- Literal ordered-list prefixes are removed when source list semantics and
  marker evidence agree, preventing duplicate markers in WordPress.
- Gutenberg and WXR no longer emit local image paths as publishable URLs;
  unresolved meaningful images use an editor-visible replacement placeholder.
- Local Semantic and WordPress previews continue to render extracted images
  without requiring WordPress media mappings.

## [0.5.1] - 2026-09-16

### Added

- `validate-exports` generates Semantic HTML, generic and WSUWP Gutenberg,
  local Gutenberg previews, and WXR validation from the reviewed document.
- Machine-readable and Markdown export-validation reports include structural,
  internal-anchor, hyperlink, and cross-export semantic-equivalence results.
- WXR validation now inspects each embedded `content:encoded` Gutenberg payload
  instead of accepting XML well-formedness alone.
- A documented real-PDF feature matrix and manual WordPress acceptance
  checklist define the release boundary before Phase 3.

### Changed

- Export validators detect broken or malformed internal links, duplicate or
  empty IDs, literal list bullets, unbalanced Gutenberg blocks, and content
  missing from any supported publication output.

## [0.5.0] - 2026-09-16

### Added

- PDF link annotations are retained in normalized documents and become inline
  links when their visible URL can be matched without guessing.
- Corpus reports now include titles, content-type counts, footnotes, links,
  unknown blocks, export status, and classified findings.

### Fixed

- Title recovery ignores page numbers, favors prominent text, joins short
  multi-line titles, and collapses repeated text from designed PDFs.
- Recovered titles are represented by the matching H1 even when another source
  heading was labeled H1; later H1s and skipped heading levels are corrected
  and flagged for review.
- Link annotations can match nested list items instead of stopping at an empty
  parent list.
- Mixed byte and text output from an extraction timeout no longer masks the
  actionable timeout error.

## [0.4.1] - 2026-09-16

### Added

- Completed exports provide browser download links while retaining their
  project-relative output paths.

### Security

- Export downloads are confined to files inside the active document project's
  `output` directory.

## [0.4.0] - 2026-09-16

### Added

- First-page PDF header title recovery as reviewed document metadata and an H1
  block.
- Optional WSU Section wrapping on the Export screen.

### Fixed

- Hard bullet glyphs and confidently identified flattened sub-bullets are
  normalized into semantic list structure.
- Gutenberg footnotes use a trusted Custom HTML block so anchor IDs survive
  WordPress paste and save round trips.
- Recovered first-page titles retain their measured PDF source region for
  highlighting in Structure, including existing reviewed projects.

## [0.3.5] - 2026-09-16

### Changed

- Export artifact filenames use the hyphenated original PDF filename.
- Export results identify the absolute document-project folder containing the
  displayed relative output paths.

## [0.3.4] - 2026-09-16

### Fixed

- Saving a non-heading block no longer submits the hidden heading-level field.

## [0.3.3] - 2026-09-16

### Changed

- Previous and Next block controls remain visible while reviewing the reading
  order, and block controls use a more compact layout.
- Changing the source page selects and focuses the first reading-order block on
  that page.

## [0.3.2] - 2026-09-16

### Added

- Previous block and Next block controls above Reading order, synchronized with
  source-page selection and keyboard focus.

### Fixed

- Completing the final unresolved block keeps that block focused instead of
  returning to the top of the Structure page.

## [0.3.1] - 2026-09-16

### Added

- Move to start and Move to end review actions, with unavailable boundary moves
  disabled.

### Fixed

- Ordered footnote lists with matching same-page references are promoted to
  document-level endnotes, including existing review documents.

## [0.3.0] - 2026-09-16

### Added

- Browser-first project creation, PDF import, and persistent recent-project
  management with Open and Remove actions.
- Automatic advancement to the next unresolved review block after review-state
  actions.
- First-class default-browser startup and desktop-browser testing workflow.
- Explicit Previous, Next, and direct page controls for the rendered source
  preview, with page-aware source highlighting.

### Changed

- Imported PDFs retain their original filenames.
- Filename collisions use readable numeric suffixes without overwriting an
  existing project source file.
- Source PDFs are served inline with their original filenames.

## [0.2.0] - 2026-09-16

### Added

- Document-level footnote normalization and end-of-document export for HTML,
  Gutenberg, and WXR output.
- Web review app footer displaying the current PDF to Web version.

## [0.1.0] - 2026-09-16

### Added

- Initial local-first PDF extraction, normalized document model, review app, and
  semantic HTML/Gutenberg/WXR export foundation.
