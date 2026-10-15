# Phase 3B: Output Pages and Article Builder

Date: 2026-09-30. Implementation version: 0.7.0.

## Specification and milestone

The approved Phase 3B scope is local authoring and manual import/export of one
reviewed document as multiple Pages or Articles. This document records the
implementation contract alongside the earlier normalized-model specification
in `EXTRACTION_SPIKE.md`, review architecture in `PHASE2_REVIEW_APP.md`, and
accessibility contract in `PHASE3_ACCESSIBILITY.md`.

| Milestone | Implementation status | External acceptance |
| --- | --- | --- |
| Phases 1 and 2 | Complete; existing workflows preserved | Historical WordPress retests pending |
| Phase 3A | Complete; inherited review decisions retained | Human listening pending |
| Phase 3B | Complete after local model, route, exporter and Chrome checks | See `PHASE3B_ACCEPTANCE.md`; pending items remain pending |
| Phase 3C | Deferred: extraction hardening and OCR decisions | OpenDataLoader abort investigation pending |
| Phase 4 | Deferred: connected publishing | No credentials, authenticated publishing or upload added |

## Using the builder

**Arrange Pages** (previously Output Pages) is optional. For one long web page, use **Preview** and **Export**
directly; PDF length does not require splitting. Use this builder for several
Pages or Articles. **Arrange content across pages (optional)** is collapsed until
needed. **Include unassigned content in this page** repairs omitted assignments;
**Keep everything on one page** replaces the arrangement while retaining the
selected page identity and metadata, all block content, decisions and exclusions.
Both support Undo. Invalid arrangements show the reason and disable export.

Open a reviewed project and select **Arrange Pages**. Older projects start with
one page containing every included top-level block; no heading grouping is
applied on load. Expand **Grouping suggestions** and choose a starting method:

- **PDF / source pages** uses the physical PDF page count and proposes one group
  per source page in numeric order. Preview identifies reconstruction holds,
  empty/excluded-only pages, metadata replacement effects and retained empty
  drafts. Exact assignment matches retain their page identity and metadata.
  Shared or missing source information requires an explicit destination choice;
  visual bundles remain intact. Existing empty drafts may make the final page
  count larger than the physical-page count, and are disclosed rather than lost.
- **Heading sections** uses H1/H2 and explicit `section_boundary` markers.
  Check the suggestions you want, or use **Select all / Clear all**. Preview
  shows the selected block moves; Apply moves only those sections and retains
  unselected assignments, page metadata and held fragments. Residual empty pages
  stay visible and unfinished. Conflicting semantic bundles require correction.

Both methods require **Preview** before **Apply**. Preview does not persist;
Apply recomputes the exact proposal, rejects stale review versions, saves once
and supports normal saved Undo. Unsaved page metadata blocks Apply while keeping
the draft visible. No grouping certifies review or publication readiness.

Generated titles follow the first included H1 or H2 encountered in reviewed
reading order within each page; excluded headings and descendants of excluded
blocks do not contribute. Paragraph text or retained merge provenance is not
treated as a heading. Without a usable heading, source groups use **Source page
N**, and heading groups use **Page N**. Reconstruction placeholders retain their
unfinished label. Duplicate heading text is allowed; automatic slugs remain unique.

For already generated defaults, choose **Preview generated page titles** and
inspect the title/slug before-and-after fields, then **Apply generated page
titles**. This changes no content assignments, identities, order or parent/type
metadata and supports saved Undo. Recognition uses tracked generated values or
the exact prior source-builder identity/default title; unrecognized or custom
titles remain untouched. Editing a title records a custom override. Automatic
slugs follow repaired titles; manual slugs remain unchanged. Changed page
metadata retains normal page-review invalidation while block approvals survive.

Select a page to edit its title, slug, Page/Article type, optional internal Page
parent and contents order. **Save page** persists locally. **Create page** creates
an empty group requiring content. **Add content to this page** opens the outline.
New slugs follow title edits, normalize Unicode accents and avoid collisions,
reserved package names and values longer than 100 characters. A manual slug
override survives later title edits; **Use title for slug** restores automatic
generation deliberately. Legacy saved slugs remain custom until explicitly changed.
**Move here** reassigns a complete block and saves immediately; page metadata
must first be saved or reverted.
**Split before** creates a page beginning at that block, and **Merge pages**
combines the selected second page into the current one. Page up/down updates
contents order. Structure continues to own content reading order. Parent/child
contents links are shown in **Preview contents**. An incomplete arrangement lists
every page once, including orphaned or cyclic pages, with links to edit invalid
slugs, assign content or restore a held source page. Valid individual pages remain
previewable. Package serializers and export validation keep their existing gates.

The page outline shows all document content and its assignment. Empty groups,
unassigned content, missing references, duplicate assignments, invalid slugs,
slug collisions, invalid parents and cycles remain visible and block all page
publication exports. Articles have no hierarchical parent. `contents` and
`publications` are reserved package filenames. Excluded content remains excluded.
A missing reference can be recovered with Undo or explicitly removed.
Initial references include excluded blocks so they remain assigned if restored.
Existing arrangements are preserved; their unassigned content requires the explicit
recovery action above.

**Preview page** and **WordPress Preview** use the existing HTML and Gutenberg
serializers over the same page projection as export. Choose Generic or WSUWP
for Gutenberg. **Export page** writes an individual package; **Export complete
package** writes `output/pages/` and `output/pages.zip`. Each package includes
semantic HTML, Gutenberg, per-page WXR, combined `publications.xml`, contents,
manifest, media files and `IMPORT.txt`. Existing Document Preview, Export and
`export all` retain their historical single-document behavior. CLI package export:

```sh
pdf-to-web export pages --project /path/to/project --profile generic
```

## Persistent model and migration

`review/current.json` retains its existing normalized/review schema and adds:

```json
{
  "output_pages": {
    "schema_version": "pdf-to-web-output-pages-v1",
    "project_id": "project-123",
    "pages": [{
      "id": "page-123",
      "title": "Introduction",
      "slug": "introduction",
      "type": "page",
      "parent": null,
      "navigation_order": 0,
      "block_ids": ["block-1", "block-2"],
      "approval": {"status": "needs_review", "note": ""}
    }]
  }
}
```

This is an additive, explicit migration: missing output state is initialized and
persisted, unknown output-state versions are rejected, and reviewed content,
accessibility decisions and immutable input are retained. IDs are generated
once and persisted; metadata edits do not replace them. Revision snapshots and
Undo include both arrangements and content. No content is copied into page state.

Source ranges are sorted inclusive integer pairs: `[[1,1],[3,4]]` means pages
1 and 3–4, never 1–4. They are computed from assigned included blocks and their
nested provenance, including merged source pages. PDF page boundaries do not
force output boundaries.

Structure splits place the new ID immediately after the source ID on the same
page. Structure merges keep the surviving block's page, remove the merged-away
reference everywhere and preserve both source-page provenances. Moves update
page reading order to match Structure. Exclusions retain assignments for restore;
excluded content is omitted from rendering. New content without a split origin
is unassigned and visible. Unexpected deleted references stay visible until
recovered or deliberately removed. Image/caption and complex-visual image bundles
travel together and cannot be split internally; tables are whole top-level units.

## Page review and rendering policy

Page structural and accessibility findings derive from current assigned content
plus applicable source-page and document-level findings. Content decisions are
retained independently of the page approval/note. Page approval records a human
workflow decision; it does not resolve mechanical findings. Material content,
assignment, metadata, hierarchy/ancestor or resolved-link changes invalidate
page approval. Unaffected content decisions and unaffected page approvals remain.
Document-level diagnostic/decision changes conservatively invalidate all pages.

The output title is a page H1. A matching first heading is rendered as H1 without
altering its reviewed block. Otherwise a projection-only title heading is added.
Additional source H1s and heading jumps remain visible review findings; the tool
does not silently certify or rewrite the rest of the hierarchy. Resolve those in
Structure and inspect again. Relevant complex-visual extended text equivalents
are projected with their source-page content and stay in both export formats.

Existing needs-review content remains exportable and explicitly reported. A
conversion-blocked document remains inspection-only and cannot generate page
publication packages. Missing footnote bodies and duplicate anchors block export;
unresolved link targets are displayed and recorded, never assigned guessed URLs.
Preview uses confined local media routes. Semantic packages copy local assets;
WordPress output uses existing explicit URL/attachment mappings or visible upload
placeholders. That deliberate media-preview substitution follows the existing app.
Prepare images on **Export** before copying publication markup: save a filename
prefix, download the ZIP, upload to WordPress, and import Media XML or a completed
mapping CSV. The optional `media_export.image_prefix` value lives in the same review
document and revision/Undo system; legacy files need no migration. Original image
files keep their names. Publication and semantic-package assets use the same prefix
and extraction-order numbering. Changing arrangements does not rename them.

## Links, footnotes and WordPress import

Links with `target_block_id`, or fragment URLs matching stable block IDs, resolve
to the owning output page and block anchor. References within a page use fragments;
cross-page references use relative `slug.html#block-id` paths. Slug changes
recompute links and invalidate affected approvals. Nested content anchors remain
addressable. Legacy fragments without a matching block identity are unresolved.
Each referenced note is copied into that output page's endnotes with page-prefixed
IDs and backlinks only to references present there. Notes with no live reference
remain with their body owner, or conservatively with the first page when legacy
provenance cannot identify that owner. Excluded note bodies are not restored by
export. Indivisible semantics are validated before packaging.

The complete local package resolves its relative paths. After WordPress import,
replace package `.html` links with actual permalinks. Existing production URLs
and external parent IDs are never invented. WXR package keys resolve internal
parents through the existing importer serializer. Individual WXR exports cannot
resolve absent parents: the manifest and instructions require manual assignment.
Individual exports also list sibling-page dependencies; use the complete package
for self-contained contents/navigation. Menu order matches `navigation_order`.
All items remain Draft. A manifest is not evidence of a successful import.

## Manifest contract

`manifest.json` uses `pdf-to-web-page-manifest-v1`. Required top-level fields are
`schema_version`, `app_version`, `project`, `export_settings`, `complete_package`,
`pages`, `media_files`, `manual_media_actions`, and `validation`.

`project` includes a stable persisted project identity, source metadata, normalized identity metadata and review
revision. Each page includes persistent page fields, assigned IDs, source ranges,
HTML/Gutenberg/WXR filenames, derived structural/accessibility findings and human
decisions, output approval, media block dependencies, resolved link mappings,
unresolved targets, missing sibling-package dependencies and manual parent work.
`validation` records existing semantic and Gutenberg validator results by page ID;
needs-review findings may remain, so consult individual results. Cross-package
anchors are additionally checked against rendered files before promotion.

A small generated example is `examples/page-manifest-v1.json`. Paths are package
relative. ZIPs include all declared media and manual-import files. Metadata cannot
supply directory paths: export requires unique bounded ASCII slugs and generates
all filenames. Titles/attributes/XML use established escaping. Package generation
stages files and ZIP before replacing the previous package; failed writes preserve
review state and prior output.

## Reproducing local checks

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/phase3b-fixture.py build/phase3b/my-fixture --serve
# In a second terminal, use the printed one-use bootstrap URL:
node tools/phase3b-browser-check.js BOOTSTRAP_URL build/phase3b/my-fixture
git diff --check
```

The fixture intentionally represents an older review file with saved edits and
an accessibility decision. It includes sections, a shared note, a cross-page link,
an image, a reviewed table and an extended visual description. It is synthetic,
not evidence of source extraction quality. Browser reports and screenshots are
local ignored artifacts under `build/phase3b/`. Real VoiceOver and WordPress
acceptance remain distinct from these checks.

### Preview output-page navigation

Preview offers **Previous**, **Next**, an **Output page** selector and **Page N
of M**. **Whole document** retains the single-document preview. Opening Preview
from Arrange Pages carries the selected saved page, Semantic HTML/WordPress mode
and Generic/WSUWP profile. **Arrange this page** returns to that page with the
same mode/profile. Empty pages and reconstruction placeholders stay visible as
incomplete; previewing does not approve or repair them.

**Expand preview** gives the content more viewport space without changing its
font or export styles. **Restore preview**, or Escape while focus is in the
preview controls, returns to the normal layout. Desktop/Narrow widths remain
available. The expansion is an in-page viewport, not a modal dialog.

Arrange Pages places Title/Slug above compact Type/Parent/Contents order fields,
uses one wrapping Assign/move and reorder row, and places Merge beside its
selector. Unsaved metadata and reviewer notes block in-app navigation and
arrangement changes; browser reload/back/close uses the browser's unsaved-edit
confirmation. Save or revert drafts before leaving.

Existing running processes need a deliberate relaunch to load changed Python
page markup. Save drafts in all tabs, quit normally, relaunch with the usual
launcher, reopen the project, and reload the browser. Code installation does
not apply any live arrangement or repair.

**Continue to Export** remains available in the expanded Preview toolbar. It
opens the Export screen without generating files. The current output page, mode
and profile are carried as return context; document export still covers the
whole document. **Return to Preview** restores that context. For individual
pages/packages, use Arrange Pages. Readiness findings remain visible on Export
and incomplete content still blocks generation.

A bounded navigation check shows Opening Export and prevents repeated clicks.
An HTTP failure or ten-second timeout restores the controls and shows retry
guidance beside Continue. **Restore preview** remains available. In an older
open tab where Continue is covered/inert, choose Restore preview (or Escape),
then Continue to Export; this does not require quitting the app.
