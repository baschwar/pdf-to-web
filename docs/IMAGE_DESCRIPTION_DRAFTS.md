# Image description drafts

This feature extends Structure's existing image authoring workflow. It does not
approve images, certify accessibility, upload media, or connect to WordPress.
Accepted fields continue to drive HTML, Gutenberg, WXR and Output Pages.

## Review workflow

1. Open Structure. Images needing descriptions are selected by default; approved,
   excluded and decorative images are not. Select individual images as needed.
2. Inspect the image, current alt/caption, nearby text and source page. Expand
   **Image and context** to confirm an asset when extraction supplied only page
   candidates. Even one page candidate needs confirmation. Add image purpose or
   verified identification. Associate a chart with the correct existing complex
   visual explicitly when one exists; page coincidence does not establish that
   relationship. A supplied long description without an association creates an
   image-specific record tied to its stable block ID.
3. Expand the bold **Provider setup** accordion, choose Local Ollama, OpenAI API
   or ChatGPT / other tool (manual exchange), and **Save provider settings**.
   Settings persist per project; saving keeps your position and focus. The Ollama
   model field appears only for Local Ollama; help text describes only the selected
   provider. ChatGPT manual exchange exports a
   request instead of calling an API. Choose **Generate drafts** or
   **Export drafting request**. Batch controls use
   the selected images. The toolbar shows selected and pending counts.
   **Export pending images ZIP** uses images needing descriptions that have no
   ready or rejected draft and are not currently generating, regardless of the
   checkboxes. Export displays and focuses a ZIP download link; click it to save.
   Cancel controls appear only for selected awaiting-response or generating requests.
   Local or cloud generation is optional.
4. Refresh results to review ready drafts beside the accepted fields. Polling
   updates status without overwriting unsaved edits or moving keyboard focus.
5. New imported or generated drafts fill empty alt, caption and long-description
   fields directly for review. Existing nonempty text is preserved; Apply can
   deliberately replace it. Long descriptions are editable in the image form.
   **Fill empty fields from existing drafts** handles earlier imports in one batch.
   Null fields leave content unchanged. Reject removes untouched auto-filled text
   while preserving subsequent author edits. Population never approves a block;
   use the existing review controls to approve. Decorative suggestions require
   the existing decorative control, which retains a legitimate caption.
6. Continue Structure/Accessibility and Output Pages review, then preview and
   export accepted content. Undo includes draft edits, imports, associations and
   field application. Save/reopen retains both drafts and accepted content.

**Regenerate / retry** explicitly requests a replacement through the selected
provider. **New manual request** explicitly creates a replacement exchange request.
Ordinary reruns preserve ready drafts, reviewer edits and rejected decisions even
if the selected provider changes. Stale drafts stay visible as **Context changed**
and cannot be applied. Request a replacement after inspecting the changed context.

## Manual exchange

No API key, model, network access or automatic external transmission is required.
The request ZIP contains selected image files, `review-sheet.csv`, `request.json`,
drafting instructions and `response-template.json`. The CSV identifies each exported
image alongside its original filename, block/page, accepted text, context and empty
draft alt/caption/long-description fields. Open it in a spreadsheet for manual
writing or send it with the image assets to ChatGPT, Codex or another tool. CSV
is a review companion; copy the final drafts into the identity-preserving JSON
template for import, or ask the tool to return that JSON directly. Manually attach the image files and
request manifest to ChatGPT or another tool. Opening that tool does not attach
files or send a request. A manual external submission is the user's action.

Return the completed response template as JSON. Open **Import manual responses**,
choose the file and **Validate responses**. Inspect the number of valid entries
and entry-specific findings, then **Import valid drafts**. Validation runs again
at import time. Importing fills empty editable fields and marks changed images as needing review.
Existing text is preserved. Populated fields drive previews and exports, so review
them before publication. Descriptions persist through save/reopen and Undo. Invalid entries are held out while valid entries may be imported.

The authoritative exchange version is `pdf-to-web-image-exchange-v1`. Request
entries contain `document_id`, `block_id`, `asset_hash`, `context_hash`,
`request_id`, `image_file`, and `context`. Response entries repeat all five
identity strings and contain:

```json
{
  "schema_version": "pdf-to-web-image-exchange-v1",
  "responses": [{
    "document_id": "copy-from-request",
    "block_id": "copy-from-request",
    "asset_hash": "copy-from-request",
    "context_hash": "copy-from-request",
    "request_id": "copy-from-request",
    "alt": "A concise, factual alternative in context.",
    "caption": null,
    "long_description": null,
    "warnings": ["Flag any uncertain identification or unreadable information."],
    "decorative": false
  }]
}
```

These illustrative identities are not importable; use the actual generated
response template. `alt` must be nonempty text. `caption` and `long_description`
are required keys but may explicitly be null. Warnings must be a string array;
`decorative` is an optional boolean suggestion. No caption is invented solely
because alt exists. Unsupported versions, malformed fields, duplicate requests,
unknown blocks/requests, cross-document identities, changed assets/context,
superseded requests, cancellations and protected existing drafts are rejected.
Matching never uses row order or filenames alone. Limits: 100 entries, 4 MiB
response JSON, 20 MiB per image; PNG/JPEG/GIF/WebP assets are supported.

## Optional providers and cost

Provider-independent service boundaries use a provider's name, model and
`generate(entry, image_path)` method. No provider SDK or large dependency is
required. Existing extraction remains deterministic and local.

- **Local Ollama:** run an already installed Ollama server at
  `http://127.0.0.1:11434` and enter an already installed vision model's name,
  for example `llava:latest`. The app never installs Ollama or downloads models.
  This adapter uses the local `/api/chat` JSON endpoint, disables proxies and
  redirects, and verifies the image hash before transmission. Local operation
  needs no cloud key; model suitability and draft accuracy require human review.
- **OpenAI:** optional cloud vision generation using `gpt-4.1-nano`. Set `PDF_TO_WEB_OPENAI_API_KEY` in the
  environment of the app's launch process. No key is entered into the browser,
  saved in project state, or reused from another tool. The
  fixed endpoint is `https://api.openai.com/v1/chat/completions`; images use
  base64 data URLs and responses are requested as JSON. The UI first displays
  the selected images' identities and context. **Send selected images to OpenAI**
  authorizes only that unchanged selection; changed context invalidates consent.
  API usage is paid; actual charges depend on input/output usage and current
  [OpenAI model pricing](https://developers.openai.com/api/docs/models/gpt-4.1-nano).
  See the [official vision request guide](https://developers.openai.com/api/docs/guides/images-vision).

The project works without either provider. During development all provider
transports and generation were mocked; no paid request or real document image
was sent externally. Live provider accuracy, account access, model availability
and performance are not established by those tests.

## State, identity and recovery

An additive migration creates empty `image_description_drafts` state in older
review documents, with version `pdf-to-web-image-drafts-v1`. Requests, active
block references, confirmed asset associations and purpose context live in the
existing `review/current.json` and revision snapshots. Immutable extraction is
unchanged. Confirmed associations retain original source provenance and resolve
the selected local asset consistently for previews and export.

Cache keys include persisted document identity, block ID, asset SHA-256,
canonical JSON context SHA-256, provider/model, prompt version and settings.
Context includes heading, surrounding text, current accepted fields, source page
and region, purpose, exclusions/decorative state and explicit complex-visual
metadata. Original provider results remain separate from editable drafts.
Provenance records request IDs, hashes, timestamps, provider/model/settings and
outcome, without credentials. Failed/cancelled attempts remain distinct and
retryable. Successful and rejected drafts are retained unless regeneration is
explicit. Historical request records remain recoverable in review JSON.

At most two provider calls run concurrently; batches contain up to 100 entries.
Each completion rechecks active request identity, edit revision, asset and context
before an atomic save through existing review persistence. Cancelled, replaced,
changed, deleted and switched-project requests cannot overwrite current content.
Cancellation prevents queued work and discards late responses; an already sent
HTTP request may continue until its 120-second timeout and may still incur cloud
charges. Server restart does not resume transmissions: interrupted provider work
is cancelled and can be retried explicitly. Manual requests persist independently.
Undo cancels live provider jobs before a late response can reapply an undone result.

Public serializers read image authoring fields, including populated drafts that
still need review. Explicitly associated long descriptions appear beside images
in HTML, Gutenberg, WXR and page exports without duplication. Provider errors,
request context and generation provenance never enter public output. Local
polling updates untouched image fields without overwriting unsaved typing.

## Verification

See `IMAGE_DESCRIPTION_DRAFTS_ACCEPTANCE.md` for actual results and limitations.
Developer fixture creation requires Pillow only for fixture images/PDF; it is
not an application dependency. Use an approved photograph when building it:

```sh
python tools/image-draft-fixture.py build/image-drafts/my-project --photo /path/to/approved-test-photo.jpg
PDF_TO_WEB_CONFIG_DIR="$PWD/build/image-drafts/test-config" PDF_TO_WEB_OPENAI_API_KEY=fixture-key .venv/bin/python tools/image-draft-fixture.py build/image-drafts/my-project --serve --mock-provider
node tools/image-draft-browser-check.js BOOTSTRAP_URL build/image-drafts/my-project
.venv/bin/python -m unittest discover -s tests -v
```

The mock fixture intentionally fails its first chart generation to exercise
retry. Use a fresh disposable directory for each browser run. Do not point these
fixture tools at a real reviewed project. Generated samples and evidence stay
ignored under `build/image-drafts/`.
