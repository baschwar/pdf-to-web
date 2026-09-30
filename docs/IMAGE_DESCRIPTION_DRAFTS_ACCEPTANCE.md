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
  equivalent of altTagger's OpenAI `gpt-4.1-nano` integration, with a dedicated
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
or validator was accessed. altTagger files remained unchanged; no code was copied
because the supplied project contained no license file.

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
