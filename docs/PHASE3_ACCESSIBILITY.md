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
- ambiguous or empty link text;
- unknown content; and
- extraction diagnostics retained from normalization.

Every finding has a stable identifier and a current status:

- `unresolved`;
- `approved`; or
- `not_applicable`.

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

The browser generates:

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

- The tool does not generate descriptions with AI.
- It does not determine whether a human-authored alternative is factually or
  contextually sufficient.
- It does not provide a spreadsheet-like table editor.
- It does not replace testing of the published WordPress page with assistive
  technology.
- OCR remediation and output-page/article building remain later phases.
