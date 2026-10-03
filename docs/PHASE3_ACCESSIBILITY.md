# Phase 3A Accessibility Authoring

Phase 3A builds accessibility authoring and review on the stable Phase 2
reviewed-document model. It does not claim automated WCAG conformance.

## Workflow

The Accessibility screen evaluates the current reviewed document and groups
findings into:

- incomplete structural review;
- images missing alt-text or decorative decisions;
- complex visuals missing a short alternative and extended text equivalent;
- tables whose header relationships and caption have not been reviewed;
- heading hierarchy problems;
- ambiguous, empty or URL-only link text;
- unknown content; and
- extraction diagnostics retained from normalization.

Every finding has a stable identifier and a current status:

- `unresolved`;
- `approved`; or
- `not_applicable`;
- `resolved` for extraction block-review notes whose referenced blocks are now
  approved or excluded. Original notes and saved reviewer decisions are retained.

Visual text-equivalent readiness uses current short alt text and either a long
description or adjacent equivalent. Recovered text is optional. Explicit Reviewed
also approves a linked image; Not applicable records that an additional equivalent
is unnecessary without excluding the image. Unchanged saves preserve approval.
Incomplete descriptions prevent Structure from claiming completion.

The HTML-check summary and findings render as tables with emphasized rule and
element totals. App screens include one conformance notice in the footer. URL
link-label findings lead to Structure editors that retain destinations and rich
formatting, participate in Undo, and require review after label edits.

Open block is a compact button carrying an explicit return to Accessibility.
Saving edits or review actions on that block returns to the finding list and
reruns the local HTML scan. Direct Structure edits keep their normal navigation.
If a corrected finding disappears, focus returns to the Document review heading.
Resolved/approved extraction diagnostics are history with explicit no-action
guidance; their original notes and decisions remain recoverable.

Document lists unresolved extraction diagnostics within its single review-task
summary. Each explains the recorded cause, current publication impact and
affected review owner, including nested content owned by a list. A block or
description already counted as pending is not counted again for its diagnostic.
Page/document checks without a recorded block explain their scope and recovery;
missing targets do not produce invented links. Block-review notes resolve only
after current manual approvals or exclusions, and return after Undo. General
judgment-based notes still need a saved Accessibility decision; they do not
independently override the existing publication gates.

The bottom green Continue to Arrange Pages handoff requires a nonempty,
unblocked document with no unresolved document findings, plus a completed current
axe scan with no violations or incomplete checks. It stays hidden while scanning
or if the scan fails. This records local review progress and does not close the
external WordPress, human VoiceOver or Windows acceptance requirements.

Judgment-based decisions include an optional reviewer note and persist in
`review/current.json` under `accessibility_review`. They participate in the
existing revision snapshots and Undo workflow. Raw extraction and the immutable
normalized original remain unchanged.

Mechanical failures such as missing image alternatives, unresolved heading
hierarchy, unknown blocks, incomplete structure review, and unreviewed table
semantics cannot be approved as exceptions. They must be corrected in
Structure. Human approval and not-applicable decisions are reserved for
judgment-based findings such as link purpose and retained extraction
diagnostics.

## Automated HTML assessment

The browser automatically runs the bundled MPL-2.0 axe-core 4.13.0 engine against
an annotated semantic HTML projection. WCAG 2.0/2.1/2.2 A/AA tags are selected.
The engine executes inside an isolated local frame at 1024px width. Its CSP
blocks external images, connections and source-document scripts. Only the local
trusted engine is added; block identities are escaped and annotations are absent
from normal publication exports. Scanning does not change persisted review state.

Violations and incomplete checks appear in separate groups with impact, rule,
help link, affected element count, HTML and top-level Structure block links.
Document-level findings remain explicit when no block can be identified. A failed
scan reports unavailability and never claims success. Results reflect the document
when the screen opened; refresh or return after edits to rerun. CLI reports do not
include these transient browser results. Separate page projections, WordPress
preview/theme output, other widths and published-site checks remain future work.

View tested rules opens a native modal dialog populated directly from the same
scan results as the summary. Passed rules appear first; the result filter also
offers detected issues, needs human review, not applicable, and all results. Each
entry includes the rule name, description, ID, element count, associated WCAG
criterion tags and guidance link. The counts describe rule results, not WCAG
success criteria. One rule may pass for some elements and fail for others;
not-applicable rules found no matching content. Close and Escape restore focus
to the opening button. The dialog scrolls at narrow widths, changes no saved
state and is unavailable if scanning fails.

## Authoring controls

Structure continues to own content-specific editing:

- images: alt text, caption, or decorative status;
- complex visuals: short alt text, long description, adjacent text equivalent,
  classification, and recovered source text;
- tables: caption, column-header row, row-header column, and reviewed status;
- headings, links, and unknown content: correction through the existing block
  editor.

Reviewed table choices control semantic `th` and `scope` output in both HTML
and Gutenberg.

## Reports

The browser shows current findings and summary counts automatically, without a
generate button or report downloads. Extraction diagnostics retain affected
block links, source pages and current review statuses; their messages describe
the original extraction and do not undo later block approvals.

The CLI generates:

- `output/reports/accessibility-review.html` for human review; and
- `output/reports/accessibility-review.json` for automation and archival.

The same outputs are available from:

```sh
pdf-to-web export accessibility --project /path/to/project
```

The report includes source page, category, finding, decision, and reviewer
note. Its status is `review_complete` only when no current finding remains
unresolved. This means the recorded review workflow is complete, not that the
published page has been certified against WCAG.

## Boundaries

- Optional image-description drafting is now available in Structure. Drafts are
  unapproved suggestions; see `IMAGE_DESCRIPTION_DRAFTS.md`.
- It does not determine whether a human-authored alternative is factually or
  contextually sufficient.
- It does not provide a spreadsheet-like table editor.
- It does not replace testing of the published WordPress page with assistive
  technology.
- OCR remediation remains Phase 3C. Output-page/article building is implemented
  in Phase 3B; see `PHASE3B_OUTPUT_PAGES.md` for inherited and page-specific review.
