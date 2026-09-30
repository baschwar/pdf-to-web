# Phase 3B acceptance ledger

Date: 2026-09-30. Version: 0.7.0. Local implementation and external acceptance
are separate. No automated WCAG or production WSUWP claim is made.

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
