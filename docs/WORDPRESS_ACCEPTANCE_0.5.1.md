# WordPress Acceptance 0.5.1

Automated validation must pass before recording these manual results. Do not
mark a row passed without performing it in the named WordPress environment.

## Test Environment

- Test date: NOT TESTED
- Tester: NOT TESTED
- WordPress environment/site: NOT TESTED
- WordPress version: NOT TESTED
- Block editor/Gutenberg version: NOT TESTED
- WSUWP plugin/version context: NOT TESTED
- Acceptance bundle: `build/wordpress-acceptance-0.5.1/`

Do not record credentials, private URLs, or secrets in this document.

## Gutenberg Paste and Reopen

| Case | Source project / fixture | Export filename | Recognition and structure | Save/reopen | Frontend | Result / notes |
| --- | --- | --- | --- | --- | --- | --- |
| Text, nested lists, links | `instructions-for-citi-training-20230608--heuristic` | `gutenberg/01-generic-text-nested-list-links-citi.html` | NOT TESTED: headings, nested lists, separate explanatory paragraphs, links, no duplicate bullets, no invalid blocks | NOT TESTED | NOT TESTED | NOT TESTED |
| Table and nested content | `bacc-to-phd-4-year-sample-program--heuristic` | `gutenberg/02-generic-table-nested-content-program-plan.html` | NOT TESTED: recognized table, all rows/cells, nested table content, no duplication, no invalid blocks | NOT TESTED | NOT TESTED | NOT TESTED |
| Footnotes and anchors | `all-policy-vaccination-admission-policy--heuristic` | `gutenberg/03-generic-footnotes-vaccination-policy.html` | NOT TESTED: Custom HTML valid, reference links, backlinks, IDs, no duplicate IDs, footnotes at end | NOT TESTED | NOT TESTED | NOT TESTED |
| WSUWP profile | `wsu-block-contract` fixture | `gutenberg/04-wsuwp-hero-section-core-blocks.html` | NOT TESTED: `wsuwp/hero`, `wsuwp/section`, nested core blocks, no invalid blocks | NOT TESTED | NOT TESTED | NOT TESTED |

## WXR Import and Reopen

| Case | Export filename | Expected import | Block recognition / footnotes | Save/reopen | Frontend | Result / notes |
| --- | --- | --- | --- | --- | --- | --- |
| Page | `wxr/single-page.xml` | NOT TESTED: Page, `Round-trip Page`, slug `roundtrip-page`, Draft | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |
| Post | `wxr/single-post.xml` | NOT TESTED: Post, `Round-trip Post`, slug `roundtrip-post`, Draft, category Research, tag Accessibility | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |
| Parent and child Pages | `wxr/parent-child.xml` | NOT TESTED: two Pages, child assigned to parent, menu orders 3 and 4 | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |
| Mixed items and taxonomy | `wxr/multi-item.xml` | NOT TESTED: Page, Post, parent/child Pages, category Research, tag Accessibility | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED |

## Test Procedure

For Gutenberg files, create a new Page, open the code editor, paste the entire
file, return to the visual editor, inspect block recognition, save, reopen, and
inspect the frontend. Test the WSUWP file only in the production-authoritative
WSU WordPress environment.

For WXR files, use Tools > Import, inspect every expected item and its metadata,
open it in the editor, save, reopen, and inspect the frontend. Record any
serialization rewrite or warning verbatim without including private URLs.

## WSUWP Production Boundary

Local preview validates PDF to Web's serialization contract. It does not prove
compatibility with the exact WSUWP plugin versions deployed in production.
Record the WordPress URL, plugin/version context, tester, date, and observed
result here when production-authoritative testing is performed. The optional
`wxr/wsuwp-page.xml` fixture is included for diagnostics but is not a substitute
for the required direct Gutenberg paste test.
