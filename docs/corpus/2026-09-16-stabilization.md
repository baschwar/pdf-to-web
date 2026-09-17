# PDF Corpus Stabilization Report

Date: 2026-09-16  
Version: 0.5.0  
Corpus run: `sample_runs/20260917T042813Z` (local ignored evidence)

## Coverage

Six real university PDFs were exercised in heuristic and structure-tree modes.

| Document | Categories covered |
| --- | --- |
| All-Policy-Vaccination-Admission-Policy.pdf | policy, title in header, nested lists, footnotes, repeated furniture, table, links |
| Forrest-Alisha-NURS-495-Practicum-deliverable-PDF1.pdf | multi-column designed publication, numbered references, lists |
| Instructions for CITI Training_20230608.pdf | image-heavy instructions, nested/numbered lists, links, page numbers |
| NURS-495-Practicum-Project-_Ayaka-Kawanishi.pdf | designed publication, complex visual, images, links |
| bacc-to-phd-4-year-sample-program.pdf | table-heavy program plan, multi-line title |
| bloodborne-pathogen-training.pdf | policy/training document, tables, captions, links, repeated furniture |

All ten requested categories are represented without adding duplicate source documents.

## Results

- Semantic HTML, Gutenberg, and WXR validation passed for every completed normalization.
- Titles were correctly recovered for the policy, CITI instructions, Heart Failure guide,
  program plan, and Bloodborne document. The poster title remains truncated at the source
  extraction boundary in metadata, while its longer existing H1 is retained.
- Completed heuristic documents contain exactly one H1. Additional H1s are demoted and
  upward level jumps are clamped with review diagnostics.
- All normalized block types with source geometry retained usable bounding boxes in the
  completed runs. Recovered titles, headings, paragraphs, lists, list items, images,
  captions, and tables therefore expose source regions. No unknown blocks occurred.
- No normalized list item retained a literal PDF bullet character. Ordered and nested
  list structures remained semantic in export.
- Four program-plan tables retained rows, columns, and spans. Exporters identify the first
  row as column headers. Complex or ambiguous tables still require review; no editor was added.
- The policy heuristic run identified two footnotes, moved both bodies to one final Footnotes
  section, and generated unique forward and return anchors. The structure-tree mode did not
  identify those footnotes.
- PDF link annotations are now retained even when an inline label cannot be reconstructed.
  CITI preserved seven of eight annotations as four unique inline links, Ayaka heuristic
  preserved six of six, and Bloodborne preserved three of three in both modes.

## Issues And Classification

1. **Extraction issue:** OpenDataLoader timed out on one policy structure-tree run. The
   timeout handler also masked mixed byte/text diagnostics; the handler is fixed and tested.
2. **Normalization issue:** page number `1` and early body text could be chosen as titles in
   designed PDFs. Prominent-text selection, multi-line joining, and repetition collapse fixed it.
3. **Normalization issue:** link matching selected empty parent list blocks instead of nested
   list items. Matching now prefers intersecting blocks containing the visible URL.
4. **Normalization issue:** unrelated source H1s could prevent insertion of the actual title,
   while additional H1s and H1-to-H3 jumps remained. Title matching and hierarchy correction
   now produce one H1 without skipped levels.
5. **Extraction issue:** Ayaka structure-tree mode recovers too little text and no reference
   geometry, leaving six link annotations unmatched. Heuristic mode preserves all six.
6. **Extraction issue:** the policy's two links use prose labels rather than visible target URLs;
   annotations are retained but no label is guessed. One CITI annotation is similarly unmatched.
7. **Unsupported source complexity:** the Heart Failure visual is preserved with 19 images and
   a complex-visual warning. The surrounding document still exports.
8. **Extraction issue:** the program plan reports incomplete text recovery and remains reviewable.

## WordPress

The user previously pasted and saved the representative policy Gutenberg export in the WSU
WordPress editor without invalid blocks; headings, lists, and the table rendered accurately.
WSU Section wrapping remains absent by default. Automated Gutenberg preview and WXR round-trip
tests pass. The isolated Docker WordPress editor test could not be rerun because Docker Desktop
was not running. The newer Custom HTML footnote forward/backlink behavior therefore still needs
one live WordPress paste/edit/save/reopen confirmation.

## Known Limits

- OpenDataLoader does not consistently expose link labels or annotation relationships.
- URLs printed as text without PDF link annotations are not auto-linked.
- Designed posters can have mode-dependent text order and recovery.
- Footnote detection remains mode-dependent for the policy fixture.
- AI alt text, OCR expansion, direct publishing, DOCX/PPTX import, table editing, and WYSIWYG
  editing were intentionally not added.
