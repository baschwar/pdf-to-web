# Local Gutenberg Preview

Preview and the embedded Arrange Pages preview start in WordPress mode using
the project's saved profile. Semantic HTML remains an explicit mode. The selected
mode, iframe title and WordPress profile stay consistent during switching;
profile changes refresh an active WordPress preview without saving review state.

## Evaluation

`wp-block-to-html` 1.5.0 is MIT licensed, has no required runtime dependencies,
and performs conversion locally. It accepts parsed Gutenberg block objects or
WordPress rendered-content objects; it does not parse Gutenberg comment markup.
The package supports the required `core/paragraph`, `core/heading`, `core/list`,
`core/image`, `core/quote`, and `core/table` handlers, along with additional text,
media, layout, widget, dynamic, and selected theme blocks.

The integration uses Node.js 20.19 or newer. `sanitize-html` 2.17.7 is also MIT
licensed and is pinned to the first release that resolves the advisories found
during the integration spike. `npm audit --omit=dev` reports zero known
vulnerabilities for the locked dependency tree.

## Conversion path

```text
review/current.json
  -> existing Gutenberg exporter
  -> deterministic Gutenberg comment parser
  -> wp-block-to-html
  -> sanitize-html
  -> sandboxed browser iframe
```

The comment parser intentionally supports the serialization emitted by this
project rather than claiming to replace WordPress's full parser. It maps core
short names such as `wp:paragraph` to `core/paragraph`, retains attributes,
constructs nested blocks, and rejects mismatched or unclosed delimiters.

The package's rendered-mode table handler wrapped the export's complete
`<figure><table>...</table></figure>` in a second table during the spike. The
local worker overrides only `core/table` to preserve the valid exported table
markup. WordPress remains authoritative for final compatibility.

## WSU handlers

- `wsuwp/hero` renders `title`, validated `headingTag`, `caption`, `imageSrc`,
  `backgroundType`, and `className`. `imageId` is not required.
- `wsuwp/section` renders `id`, `className`, and recursively converted nested
  core or custom blocks.
- Other unsupported blocks render a visible placeholder and are returned in an
  unsupported-block diagnostic list. Gutenberg export remains unchanged.

Preview-specific styling lives in `static/wordpress-preview.css`. It is local,
minimal, and independent of conversion logic. No WSU production stylesheet is
downloaded. The WSUWP selector is labeled **WSUWP (approximate preview)**.
A single explanation beside the preview states that it shows content and
structure with local minimal CSS. It does not reproduce the production WSU
WordPress theme, plugin output or final visual design; validate those on the
production-authoritative versions.

## Security

- Converted HTML is passed through an explicit element and attribute allowlist.
- Scripts, inline event handlers, forms, embeds, and unsafe URL schemes are
  removed.
- The iframe has no script permission and uses a restrictive Content Security
  Policy.
- No arbitrary block JavaScript is loaded or executed.
- Existing HTTP(S) image behavior is retained; external scripts and styles are
  prohibited.
- Input is capped at 10 MB and Node conversion has a 15-second timeout.

## Supported preview boundary

The converter includes many core handlers, but this project validates only the
six core blocks and two WSU handlers listed above. Unsupported blocks are not a
preview error and never alter or suppress the Gutenberg export. Actual WordPress
imports remain required for regression and final compatibility testing.

## Recognized footnotes and native blocks

Preview sanitization preserves the exporters' existing `sup`, backlink
`aria-label`, and endnotes-section `aria-labelledby` markup. Styled-run marker
placement uses the shared inline renderer. These corrections do not change
paragraph/list block types or add a Custom HTML fallback. The existing recognized
footnote endnotes section is already a separate `core/html` block.

Saved literal line breaks, including blank lines, become HTML `br` elements in
the shared renderer and survive local WordPress preview conversion. Paragraphs
and list items retain their native wrappers and existing IDs; this does not add
a Custom HTML fallback or alter the simple-list editor's item-per-line convention.

New citation association and footnote ARIA authoring are deferred. The compact
Structure block preview shows saved semantic formatting, retains unsaved fields
in Edit, and makes destination links inactive while retaining local note links.
Neither preview creates associations for plain extracted citation numbers.
Actual WordPress open/save/reopen and human VoiceOver checks remain separate
acceptance steps.
