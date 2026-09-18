# Third-party notices

PDF to Web is an independent MIT-licensed project. It uses the following
principal third-party software.

## Extraction engine

- [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf),
  version 2.x, is used as the PDF extraction engine and is licensed under the
  Apache License 2.0. Copyright 2025-2026 Hancom, Inc. Its upstream
  [NOTICE](https://github.com/opendataloader-project/opendataloader-pdf/blob/main/NOTICE)
  and complete dependency notices remain authoritative.

PDF to Web does not copy or modify OpenDataLoader source code. The
`opendataloader-pdf` Python distribution is installed as a runtime dependency
and supplies its own Java extraction engine. PDF to Web invokes that engine in
deterministic local mode and normalizes the resulting data into its own model.

## Python runtime dependencies

- [FastAPI](https://github.com/fastapi/fastapi) - MIT
- [Uvicorn](https://github.com/encode/uvicorn) - BSD-3-Clause
- [pypdf](https://github.com/py-pdf/pypdf) - BSD-3-Clause

Exact installed versions are constrained in `pyproject.toml` and resolved by
the user's Python package installer. Each distribution includes its applicable
license and notices.

## JavaScript dependencies

- [sanitize-html](https://github.com/apostrophecms/sanitize-html) - MIT
- [wp-block-to-html](https://github.com/aaronbushnell/wp-block-to-html) - MIT

These packages support the optional local WordPress Preview. Exact resolved
versions and transitive dependency licenses are recorded in `package-lock.json`.

## Bundled user interface dependency

- [Pico CSS](https://picocss.com/), version 2.1.1 - MIT

The minified Pico CSS file retains its upstream copyright and license header.

## System tools

Java, Python, Node.js, npm, and Poppler are installed separately by the user.
They are not redistributed by this repository and retain their respective
licenses.
