# Phase 2 Closeout

Date: 2026-09-25  
Release: 0.6.0

Phase 2 is complete as the stable structural-review foundation for PDF to Web.

## Completion evidence

- Project creation, opening, and persistent recent projects are available in
  the browser.
- Source-page navigation and project-specific rendered-page caching are
  implemented.
- Top-level reviewed blocks retain source page and bounding-box provenance.
- Text, type, heading level, review state, reading order, merge, split,
  include/exclude, and undo changes persist in `review/current.json`.
- Image alternatives and decorative decisions persist and block approval when
  incomplete.
- Semantic HTML, Gutenberg, WordPress Preview, and WXR consume reviewed state.
- Exported HTML is downloadable and copyable; WordPress media packages and
  mappings are available without credentials.
- The loopback bootstrap, session, Origin, CSRF, and confined-path controls are
  covered by integration tests.
- The current automated suite passes 125 tests.
- Chrome manual verification confirmed the 0.6.0 navigation, current project,
  Accessibility workspace, grouped findings, source links, and footer version.

## Candidate corpus

The 13 locally held candidate PDFs were run in heuristic and structure-tree
modes, producing 26 mode runs:

- 16 runs completed extraction and generated valid semantic HTML, Gutenberg,
  and WXR validation results;
- 13 completed runs were classified `needs_review`;
- 3 completed runs were classified `review_ready`; and
- 10 runs across five PDFs were classified `conversion_blocked` after
  OpenDataLoader exited with status `-6` in both modes.

The application failed closed for all extraction aborts. It did not present
partial content as a successful conversion. The source PDFs and generated
candidate runs remain untracked and are not part of the public repository.

The OpenDataLoader abort pattern is a future extraction-hardening investigation,
not a defect hidden by the Phase 2 review interface.

## External acceptance still required

- Production WSUWP block compatibility must be checked against the exact
  deployed plugin versions.
- A human VoiceOver listening pass should confirm rotor navigation and spoken
  verbosity on a long Structure and Accessibility screen.
- Windows remains supported by code paths and documentation but unvalidated on
  Windows hardware or CI.

These checks are not represented as passed and do not constitute an automated
WCAG claim.
