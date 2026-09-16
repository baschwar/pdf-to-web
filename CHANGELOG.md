# Changelog

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
