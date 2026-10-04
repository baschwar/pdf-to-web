# Export Validation Gate 0.5.1

This gate validates the same reviewed document state used by the application.
It calls the production exporters and does not reimplement serialization.

## Layers

1. `pdf-to-web validate-exports --project PROJECT_PATH` validates generated
   Semantic HTML, generic Gutenberg, WSUWP Gutenberg, WXR, and cross-export
   semantic equivalence without a WordPress installation.
2. The local `wp-block-to-html` adapter validates rendered generic and WSUWP
   previews when its Node dependencies are installed.
3. `WORDPRESS_ACCEPTANCE_0.5.1.md` records the small set of tests that require a
   real WordPress editor or WSUWP installation. Pending tests remain pending.

Source-document names and project/export identifiers are withheld from this public
report; descriptive labels retain the recorded coverage and findings. Detailed
evidence remains local and ignored.

## Corpus Feature Matrix

| Document | Text | Lists | Tables | Links | Footnotes | Images | Furniture | Title | Columns | Complex visual |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Policy document | Yes | Yes | No | Yes | Yes | Logo | Yes | Yes | No | No |
| Multi-column poster | Yes | Yes | No | Yes | No | Yes | Yes | Yes | Yes | Yes |
| Screenshot-heavy instructions | Yes | Yes | No | Yes | No | Yes | Yes | Yes | No | No |
| Designed infographic | Yes | Yes | No | Yes | No | Yes | Yes | Yes | Yes | Yes |
| Table-heavy program plan | Yes | No | Yes | No | No | No | Yes | Yes | No | No |
| Training guide | Yes | Yes | No | Yes | No | Yes | Yes | Yes | No | No |

The machine-generated reports are authoritative for individual run results.
This matrix documents why the corpus is representative and should only change
when source coverage changes.

## Result Rules

- `review_ready` and `needs_review` projects generate all supported outputs.
  Needs-review findings remain explicit warnings.
- `conversion_blocked` projects generate diagnostic Semantic HTML only;
  Gutenberg and WXR must fail closed.
- Missing reviewed content, broken anchors, malformed block comments, invalid
  WXR, or changed link targets fail the gate.
- External network availability is never part of the result.
