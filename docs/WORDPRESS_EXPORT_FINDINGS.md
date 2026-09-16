# WordPress Document Export Findings

Source reviewed: `sample_files/collegeofnursing.WordPress.2026-09-16.xml`

## Export shape

- 203 total items.
- Every item uses the custom post type `document`.
- Statuses: 141 published, 59 private, and 3 trash.
- The WordPress content field usually contains a numeric attachment ID rather
  than Gutenberg markup or the document URL.
- The public PDF URL is stored in each item's `<link>` value.
- The item GUID commonly identifies the uploads directory, not the individual
  PDF.
- No item in this export uses a post MIME type. These are document-library
  records that refer to media, not WXR attachment records themselves.
- Common metadata includes `_edit_last`; some records also include featured
  image, old slug/date, desired slug, or WSU Spine page settings.

## Architecture consequences

- `document` must be treated as a configurable WordPress destination/source
  post type, never as a normalized-document block type.
- A future migration workflow needs an explicit mapping among the custom
  document record, its numeric media attachment ID, and its public PDF URL.
- Numeric attachment IDs from the source site must not be reused for newly
  generated image blocks unless the destination site confirms the same media
  records exist.
- Converting a library item to an accessible Page or Post should preserve the
  original item title, slug, visibility, publication date, author, and PDF URL
  as source metadata while defaulting the new import to Draft.
- Phase 1's WXR serializer accepts arbitrary post-type strings. The destination
  must register `document` before importing that post type; otherwise the
  fixture proof should use Page or Post.

## Phase 1B local round trip

Validated on 2026-09-16 with WordPress 7.1 and WordPress Importer 0.9.6 in the
isolated Docker stack under `tools/wordpress-roundtrip/`.

- Imported a single Page, a single Post with category and tag, parent and child
  Pages, a four-item WXR file, and a WSU-profile Page.
- All imported publications remained Draft.
- Page/Post types, slugs, parent resolution, and menu order survived import.
- The editor parsed headings, paragraphs, lists and list items, images, quotes,
  and tables as their corresponding `core/*` blocks.
- The WSU fixture parsed as `wsuwp/hero` and `wsuwp/section` with nested core
  blocks when the validation shim registered those block contracts.
- Every imported item completed an edit/save/restore/reopen cycle with no
  invalid blocks, no editor error notices, no browser console errors, and exact
  content restoration.

The WSU result proves the exporter contract against the fixture registration,
not against every production WSUWP release. The exact destination plugin must
still be included in release-candidate validation.

The XML is reference input only. PDF to Web does not modify or re-export it.
