from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .doctor import run_checks
from .corpus import run_corpus
from .errors import PdfToWebError
from .export import export_project
from .export_validation import validate_export_corpus, validate_project_exports
from .extraction import run_extraction
from .normalize import normalize_project
from .project import create_project, import_pdf
from .wordpress_fixtures import write_wordpress_fixtures
from .web import run_server


def _project_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-to-web", description="Convert PDF publications into accessible web content"
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="Check local extraction requirements")
    doctor.add_argument("--project", type=_project_path)
    doctor.add_argument("--json", action="store_true", dest="as_json")

    project = commands.add_parser("project", help="Manage project folders")
    project_commands = project.add_subparsers(dest="project_command", required=True)
    create = project_commands.add_parser("create", help="Create a self-contained project")
    create.add_argument("path", type=_project_path)
    create.add_argument("--title")

    intake = commands.add_parser("import", help="Copy and analyze a PDF source")
    intake.add_argument("pdf", type=_project_path)
    intake.add_argument("--project", required=True, type=_project_path)

    extract = commands.add_parser("extract", help="Run deterministic OpenDataLoader extraction")
    extract.add_argument("--project", required=True, type=_project_path)
    extract.add_argument("--use-struct-tree", action="store_true")

    normalize = commands.add_parser("normalize", help="Build the normalized document model")
    normalize.add_argument("--project", required=True, type=_project_path)

    spike = commands.add_parser("spike", help="Run both deterministic modes over a PDF corpus")
    spike.add_argument("sample_dir", type=_project_path)
    spike.add_argument("--output", required=True, type=_project_path)

    export = commands.add_parser("export", help="Export normalized content")
    export.add_argument(
        "target", choices=("markdown", "html", "gutenberg", "wordpress-xml", "all")
    )
    export.add_argument("--project", required=True, type=_project_path)
    export.add_argument("--profile", choices=("generic", "wsuwp"))

    validate_exports = commands.add_parser(
        "validate-exports", help="Generate and validate every supported publication output"
    )
    validate_exports.add_argument("--project", required=True, type=_project_path)

    validate_corpus = commands.add_parser(
        "validate-export-corpus", help="Validate immediate document projects and generate a corpus matrix"
    )
    validate_corpus.add_argument("project_root", type=_project_path)
    validate_corpus.add_argument("--output", type=_project_path)

    fixtures = commands.add_parser(
        "wordpress-fixtures", help="Generate repeatable WXR round-trip fixtures"
    )
    fixtures.add_argument("--output", required=True, type=_project_path)

    serve = commands.add_parser("serve", help="Start the local review application")
    serve.add_argument("--project", type=_project_path)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--no-browser", action="store_true")
    return parser


def _print_doctor(args: argparse.Namespace) -> int:
    checks = run_checks(args.project)
    if args.as_json:
        print(json.dumps([check.__dict__ for check in checks], indent=2))
    else:
        for check in checks:
            print(f"{check.status:6} {check.name}: {check.detail}")
            if check.action:
                print(f"       Suggested action: {check.action}")
    return 1 if any(check.status == "FAIL" for check in checks) else 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            return _print_doctor(args)
        if args.command == "project" and args.project_command == "create":
            create_project(args.path, args.title)
            print(f"Created project: {args.path}")
        elif args.command == "import":
            analysis = import_pdf(args.project, args.pdf)
            print(f"Imported: {args.pdf.name}")
            print(f"Classification: {analysis['classification']}")
            print(f"Pages: {analysis['page_count']}")
            if analysis["ocr_status"] == "OCR REQUIRED":
                print("Review status: OCR REQUIRED")
        elif args.command == "extract":
            outputs = run_extraction(args.project, args.use_struct_tree)
            print("OpenDataLoader extraction complete (local deterministic mode).")
            for path in outputs:
                print(path)
        elif args.command == "normalize":
            print(normalize_project(args.project))
        elif args.command == "spike":
            print(run_corpus(args.sample_dir, args.output))
        elif args.command == "export":
            for path in export_project(args.project, args.target, args.profile):
                print(path)
        elif args.command == "validate-exports":
            paths = validate_project_exports(args.project)
            for path in paths:
                print(path)
            report = json.loads(paths[0].read_text(encoding="utf-8"))
            return 0 if report["result"] == "PASS" else 1
        elif args.command == "validate-export-corpus":
            paths = validate_export_corpus(args.project_root, args.output)
            for path in paths:
                print(path)
            report = json.loads(paths[0].read_text(encoding="utf-8"))
            return 0 if report["result"] == "PASS" else 1
        elif args.command == "wordpress-fixtures":
            for path in write_wordpress_fixtures(args.output):
                print(path)
        elif args.command == "serve":
            run_server(args.project, args.host, args.port, open_browser=not args.no_browser)
        return 0
    except PdfToWebError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
