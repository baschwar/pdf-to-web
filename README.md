# PDF to Web

PDF to Web is a local-first conversion tool that turns PDF publications into a
reviewable normalized document, semantic HTML, Gutenberg block markup, and
WordPress WXR/XML. [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf)
is the Apache-2.0-licensed extraction engine on which this project builds. PDF
to Web adds its own normalized document model, review workflow, source-aware
editing, validation, and web and WordPress exporters; it is not a fork of
OpenDataLoader. The normalized document remains independent of the extraction
engine and every export format. See [Third-party notices](THIRD_PARTY_NOTICES.md)
for the principal runtime and bundled dependencies.

Extraction uses deterministic local processing and never enables OpenDataLoader
hybrid or external AI processing. Phase 2 adds a local FastAPI/PicoCSS review
application over the same normalized document model and exporters used by the
CLI.

## Development setup

macOS or Linux:

```sh
cd pdf-to-web
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
npm install
pdf-to-web doctor
```

Windows PowerShell:

```powershell
cd pdf-to-web
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
npm install
pdf-to-web doctor
```

OpenDataLoader requires Python 3.10 or newer and Java 11 or newer. The doctor
command checks both and looks for common Homebrew Java installations when the
default `java` command is too old.

Poppler's `pdfinfo` and `pdftoppm` commands are also required for source-page
rendering. Node.js 20.19 or newer and `npm install` are required only for the
WordPress Preview; Semantic Preview and the other Python workflows do not need
Node.js.

### Desktop launchers

After completing development setup once, macOS users can double-click
`Launch PDF to Web.command` in Finder. If macOS blocks the first launch,
Control-click the file, choose **Open**, and approve it. Windows users can
double-click `Launch PDF to Web.bat` after setup. Both launchers use the local
`.venv` and run the same `pdf-to-web serve` command documented below.

The launchers intentionally report missing setup rather than installing
software or changing the computer automatically.

### Platform support

The application is developed and manually tested on macOS. Its Python paths,
local configuration, browser startup, and native file chooser have Windows and
Linux implementations, and OpenDataLoader supports Windows when Java is on
`PATH`. Windows also requires Python 3.10+, Java 11+, and Poppler utilities on
`PATH`; Node.js is optional as described above.

Windows should currently be treated as **supported but not yet validated**:
the automated suite has not been run on a Windows host and there is not yet a
Windows CI job. Please report platform-specific installation or file-picker
issues in GitHub Issues.

## Extraction spike workflow

```sh
pdf-to-web project create /path/to/my-report
pdf-to-web import /path/to/report.pdf --project /path/to/my-report
pdf-to-web extract --project /path/to/my-report
pdf-to-web normalize --project /path/to/my-report
pdf-to-web export all --project /path/to/my-report
pdf-to-web validate-exports --project /path/to/my-report
pdf-to-web validate-export-corpus /path/to/projects --output /path/to/reports
```

Use `--profile wsuwp` with the Gutenberg or all export command to exercise the
WSUWP profile. Project-level profile, hero, section, and WordPress publication
defaults live in `project.json`.

`validate-exports` generates the complete publication set through the existing
exporters and writes `output/reports/export-validation.json` plus
`output/reports/export-validation.md`. The gate checks HTML structure, internal
anchors, Gutenberg block balance, local Gutenberg preview conversion, WXR
metadata and embedded content, and semantic content preservation across the
reviewed model and each output. External URLs are preserved syntactically; core
validation never depends on network access.
`validate-export-corpus` runs that gate for each immediate document-project
folder and generates a corpus-level JSON and Markdown result matrix.

WordPress exports distinguish local extracted assets from publishable media.
Configured HTTP(S) URLs generate normal image blocks, with attachment IDs only
when explicitly supplied. Unresolved meaningful images generate visible
replacement placeholders instead of broken URLs. Their extracted files and
metadata are written to `output/wordpress/assets/` and
`output/wordpress/reports/media-manifest.{json,md}` for later Media Library
mapping. Direct upload is intentionally outside the current scope.

For a credential-free Media Library workflow, export Gutenberg or WXR and use
the generated `output/wordpress/media-upload.zip` plus
`output/wordpress/reports/media-mapping.csv`. Upload the ZIP contents through
WordPress, enter each resulting attachment ID and full media URL in the CSV,
and import that CSV on PDF to Web's Export screen. The stable `block_id` column
correlates each WordPress attachment with its source figure even when WordPress
renames the uploaded file. Regenerate Gutenberg or WXR after import to replace
the upload placeholders with proper Image blocks. Rows without a URL are left
unresolved; decorative images are excluded from the upload package.

Instead of entering every URL and attachment ID manually, use WordPress Tools >
Export to download a Media WXR/XML file after uploading the images, then choose
**Match WordPress media** on PDF to Web's Export screen. Exact filenames are
matched into `media-mapping.csv`; unmatched or duplicate filenames are left for
manual review rather than guessed.

Authenticated WordPress media upload and direct draft publishing are deferred
in `docs/FUTURE_FEATURES.md`.

## Local review application

Launch the local review interface:

```sh
pdf-to-web serve
```

The Projects screen can create a project, import its source PDF, run extraction
and normalization, open an existing project, and reopen recent projects. New
projects are stored under `~/Documents/PDF to Web Projects`. The command prints
and opens a one-use bootstrap URL, binds only to `127.0.0.1`, and keeps all
project data local. Use `--project /path/to/my-report` to open a known project at
startup or `--no-browser` to print the URL without opening it automatically.
Docker is not required to run, review, preview, or export a project.

Chrome, Safari, Firefox, and Edge are supported for the localhost review app.
Normal startup opens the one-use `/bootstrap/...` URL in the system default
browser, sets the local session cookie, and redirects to `http://127.0.0.1:8765/`.
With `--no-browser`, open the clearly printed bootstrap URL in the browser you
want to test.

Recent-project configuration contains only project title, canonical local path,
and last-opened timestamp. On macOS it is stored at
`~/Library/Application Support/PDF to Web/recent-projects.json`; Windows uses
`%LOCALAPPDATA%/PDF to Web/recent-projects.json`, and Linux uses
`$XDG_CONFIG_HOME/pdf-to-web/recent-projects.json` (falling back to
`~/.config/pdf-to-web`). Set `PDF_TO_WEB_CONFIG_DIR` to override the directory.
The app does not scan the filesystem for projects.

The Semantic HTML preview uses only Python dependencies. The optional WordPress
Preview additionally requires Node.js 20.19 or newer and the local packages
installed by `npm install`; it never requires WordPress, PHP, MySQL, Docker, or
an external service. See `docs/GUTENBERG_PREVIEW.md` for its compatibility and
security boundaries.

Reviewed content is stored in `review/current.json`; immutable normalized input
remains in `extraction/normalized/document.json`, and revision snapshots are
kept under `review/revisions/`. Files under `extraction/raw/` are never changed
by review operations. See `docs/PHASE2_REVIEW_APP.md` for the architecture,
security model, and current limits.

Run tests without third-party test tooling:

```sh
python -m unittest discover -s tests -v
```

Run the extraction spike corpus through both deterministic modes:

```sh
pdf-to-web spike sample_files --output sample_runs
```

The corpus report assigns one readiness state to every normalized result:

- `review_ready`: structurally exportable, with only advisory issues.
- `needs_review`: exportable, but a human must resolve material extraction or
  complex-visual issues.
- `conversion_blocked`: semantic HTML remains available for diagnosis, while
  Gutenberg and WXR generation are withheld.

Generate the repeatable local WordPress fixture set with:

```sh
pdf-to-web wordpress-fixtures --output build/wordpress-fixtures
```

The Docker and block-editor procedure is documented in
`tools/wordpress-roundtrip/README.md`.

The source PDFs remain unchanged. Each timestamped run contains separate
self-contained projects for heuristic and structure-tree extraction, plus JSON
and CSV comparison summaries. `sample_files/` and `sample_runs/` are ignored by
Git because source publications may contain internal or copyrighted material.

## Current boundary

The Phase 2 review interface does not include OCR remediation, AI, a full table
editor, media sideloading, direct publishing, or a claim of automated WCAG
conformance. The Phase 1B fixtures have been imported, edited, saved, and
reopened in an isolated local WordPress instance. Production WSUWP compatibility
still requires the exact deployed WSU block versions.

## License

PDF to Web is released under the [Apache License 2.0](LICENSE). See
[NOTICE](NOTICE) and [Third-party notices](THIRD_PARTY_NOTICES.md) for
attribution information.
