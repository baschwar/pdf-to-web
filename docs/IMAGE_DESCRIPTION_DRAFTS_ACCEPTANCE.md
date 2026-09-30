# Image description drafts — acceptance record

Date: 2026-09-30. Base version: 0.7.0; feature is Unreleased. Implemented on
`codex/phase3b/output-page-builder` from baseline `668d2e4`. The pre-existing
untracked `AGENTS.md` was preserved. No push, merge, tag, publication or release.

## Implemented locally

- Existing Structure image editor extended with optional drafting selection,
  image/context inspection, explicit ambiguous asset/complex-visual associations,
  accepted-versus-draft fields, editable drafts, individual application,
  rejection, cancellation, explicit retry/regeneration and Undo.
- Separate persistent draft state and additive older-project migration using
  reviewed-document persistence; stable document/block/asset/context/request
  identities, provider/model/settings provenance, contextual cache keys and
  incremental completion saves.
- Manual ZIP/image/request/template exchange and previewed JSON import validation.
- Optional existing-local-model Ollama adapter and independently implemented
  OpenAI `gpt-4.1-nano` integration, with a dedicated
  environment key and scoped explicit cloud request review/consent.
- Bounded concurrency, cancellation/late-response safeguards, project identity
  checks, stale-state protection and accepted-only export behavior.

## Verified evidence

- Baseline: **152 tests passed** before editing.
- Final full documented suite: **179 tests passed**; 27 new tests. Evidence:
  `build/image-drafts/tests.txt`. Covers persistence/Undo, migration, selected
  fields, errors/types/omissions, accepted metadata and approval preservation,
  context-dependent identity, ambiguous associations, public export isolation,
  edits/rejection/cache/retry, cancellation, changed assets/context, exclusion,
  deletion, project reopening/switching, both Undo routes and late responses,
  max-two concurrency and mocked provider HTTP payloads/key handling.
- Chrome **154.0.8037.59**: **13 workflow checks passed**, no page errors.
  `build/image-drafts/browser-report.json` and desktop/narrow/Output Pages
  screenshots record the result. Browser exercised selection defaults,
  cloud preflight/cancel with a dummy key, ambiguous association by keyboard,
  request download, response validation/confirmation, editing, individual
  application and focus, Undo, rejection, complex-visual description, mocked
  failure/retry, cancellation, save/reopen, retained approved/decorative metadata,
  semantic/WordPress page previews, complete package and narrow layout.
- Disposable final project: `build/image-drafts/project-5/`. Contains a NASA
  portrait photograph, multiple images on one source page, an approved image,
  a decorative image with caption, an ambiguous asset and a synthetic chart.
  Photograph obtained from NASA's
  [official portrait page](https://www.nasa.gov/image-article/official-portrait-of-neil-armstrong/)
  for local fixture inspection only; it is not committed or sent to a provider.
- `build/image-drafts/export-inspection.json` passed: one page/one parsed WXR
  item, declared media present, accepted alt and caption and long description
  present, unaccepted mock text/private draft state/provenance absent across
  generated publication files. Complete package:
  `build/image-drafts/project-5/output/pages.zip`.
- Paired sample exchange: `build/image-drafts/sample-request.zip` and
  `build/image-drafts/sample-response.json`. These are fixture-specific identity
  examples, not reusable responses for other projects. The browser imported
  them at the matching request state before subsequent review edits.
- `git diff --check` passed. Generated PDFs, photographs, request ZIPs,
  responses, exports, screenshots, config and logs remain ignored under `build/`.

Both provider integrations were tested with mocked generation/transport.
**No live generation, API spending or real document-image transmission occurred.**
An existing local Ollama `llava` model manifest was found, but the running service,
model suitability and live draft quality were not tested. No model/dependency
was installed. No WordPress site, media library, cookies, credentials, updater
or validator was accessed. No unrelated project files or credentials were modified or reused.

## Limitations and external acceptance

- Live provider availability, performance, accuracy and billing require separate
  authorized testing. Manual exchange is usable independently of either provider.
- Cancellation discards late results; already transmitted HTTP requests can run
  until timeout and may incur charges. Server restart/Undo does not restart them.
- Draft results require human factual/contextual review. No automated WCAG claim.
- Production-authoritative WSU Gutenberg/WXR/plugin compatibility, human VoiceOver,
  Windows hardware, five-PDF OpenDataLoader abort investigation and historical
  WordPress retests remain pending as recorded in `PHASE3B_ACCEPTANCE.md`.

Local implementation and verification are complete. External acceptance and
release are separate and remain pending. Restart the local review app to use the
updated Structure controls. See `IMAGE_DESCRIPTION_DRAFTS.md` for configuration,
exchange schema and reproduction commands.

## Provider setup and manual-exchange follow-up — 2026-09-30

Provider/model preferences now persist per project through the existing review
state and Undo. Save works in place without navigation or scrolling and retains
keyboard focus. OpenAI API and ChatGPT/other-tool manual exchange are distinct
choices; only Local Ollama displays its model input. Provider setup and manual
import use bold bordered accordion headings. Delayed block advancement yields
to a reviewer already using the provider toolbar.

Manual ZIPs now include `review-sheet.csv`: exported/original image filenames,
stable identities, source page, accepted alt/caption, purpose, surrounding context,
and blank draft alt/caption/long-description fields. The CSV is a spreadsheet
review companion; final responses use the authoritative JSON template for import.
The import accordion now explains the batch export and return steps and includes
an export button. Extracted strings are quoted safely as text in the CSV.

- Full suite: **181 tests passed**; `build/image-drafts/provider-tests.txt`.
- **Seven targeted Chrome checks passed**, no page errors:
  `build/image-drafts/provider-browser-report.json`. Checked keyboard save,
  no navigation/scroll/focus change, reload/reopen persistence, conditional model
  visibility, bold accordion headings, manual generation choosing ZIP export,
  CSV in the downloaded ZIP, and a slow-source-load/pending-block focus race.
- Screenshot: `build/image-drafts/provider-settings.png`; sample ZIP:
  `build/image-drafts/manual-review-sample.zip`.
- No live provider or WordPress call was made. External acceptance remains pending.

### Provider-specific help correction

Provider help now follows the current selection immediately and after save/reopen.
ChatGPT manual exchange displays only its ZIP/CSV/JSON workflow; Local Ollama and
OpenAI API each display their own setup. Unrelated project references were removed
from current UI, workflow documentation and code commentary.

Full suite: **181 passed** (`build/image-drafts/provider-help-tests.txt`). Updated
targeted Chrome run: **nine checks passed**, no page errors, including help on
selection change and after reopening. No live provider or WordPress call.

### Pending-image export and request controls

The toolbar displays selected/pending counts, exports pending images independently
of checkboxes, disables selected export for an empty selection, and focuses the
ZIP link or export error. Cancel controls are hidden without an awaiting-response
or generating request; batch cancellation filters to those states. Pending means
an image needing descriptions without a ready/rejected draft or running generation.
Unconfirmed image associations still require reviewer confirmation before export.

Full suite: 181 passed (`build/image-drafts/pending-tests.txt`). Targeted Chrome
check (`tools/pending-images-browser-check.js`) passed empty-selection controls,
pending export, focused download feedback, successful ZIP with CSV, and cancellation
visibility after request creation, with no page errors. No live provider calls.
Existing external WordPress, human VoiceOver and Windows acceptance remain pending.

### Direct image-field population — 2026-09-30

The user's follow-up supersedes the original apply-each-field workflow for empty
fields. Valid manual imports and generated responses populate empty image alt,
caption and long-description fields directly. Existing nonempty text is retained;
null values do not clear it. Changed images require review. Earlier imports have
a single batch population action. Descriptions use the existing complex-visual
model, creating an exact image-bound record when necessary. Structure exposes
an editable long-description field. Reject clears untouched populated values,
retains author edits, and remains undoable.

- Baseline: 181 tests passed. Final suite: 186 tests passed.
- Eight Chrome checks passed with no page errors: actual file validation/import,
  all three fields visible without Apply, review required, existing text retained,
  reload persistence, description editing/save, Undo edit and Undo import.
  Evidence: `build/image-drafts/direct-fields-browser-report.json`; reproduction:
  `tools/direct-image-fields-browser-check.js BOOTSTRAP_URL DISPOSABLE_PROJECT`.
- Export tests inspect HTML and Gutenberg and verify a description appears once
  and stays with its image across independently arranged Output Pages. WXR uses
  the same Gutenberg serialization. Null handling, generation, stale identities,
  Undo, legacy-import population and rejection preserve existing regression gates.
- Only disposable synthetic fixtures were used. No user project was changed,
  no provider/WordPress call was made, and nothing was pushed or released.
- Production WSUWP, human VoiceOver and Windows hardware acceptance remain pending.

Restart the app to load the updated code, then use **Fill empty fields from
existing drafts** once for earlier imports. Caption/long-description nulls in a
response mean that no text was supplied; population does not invent missing text.
