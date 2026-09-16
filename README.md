# PDF to Web

PDF to Web is a local-first conversion tool that turns PDF publications into a
reviewable normalized document, semantic HTML, Gutenberg block markup, and
WordPress WXR/XML. OpenDataLoader PDF is the extraction engine. The normalized
document remains independent of OpenDataLoader and every export format.

Extraction uses deterministic local processing and never enables OpenDataLoader
hybrid or external AI processing. Phase 2 adds a local FastAPI/PicoCSS review
application over the same normalized document model and exporters used by the
CLI.

## Development setup

```sh
cd /Users/bradschwartz/Documents/Codex/pdf-to-web
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
pdf-to-web doctor
```

OpenDataLoader requires Python 3.10 or newer and Java 11 or newer. The doctor
command checks both and looks for common Homebrew Java installations when the
default `java` command is too old.

## Extraction spike workflow

```sh
pdf-to-web project create /path/to/my-report
pdf-to-web import /path/to/report.pdf --project /path/to/my-report
pdf-to-web extract --project /path/to/my-report
pdf-to-web normalize --project /path/to/my-report
pdf-to-web export all --project /path/to/my-report
```

Use `--profile wsuwp` with the Gutenberg or all export command to exercise the
WSUWP profile. Project-level profile, hero, section, and WordPress publication
defaults live in `project.json`.

## Local review application

Launch the Phase 2 review interface for an existing project:

```sh
pdf-to-web serve --project /path/to/my-report
```

The command prints and opens a one-use bootstrap URL, binds only to
`127.0.0.1`, and keeps all project data local. Use `--no-browser` to print the
URL without opening it automatically. Docker is not required to run, review,
preview, or export a project.

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
