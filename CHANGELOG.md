# Changelog

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
