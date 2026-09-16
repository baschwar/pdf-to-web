import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pdf_to_web.project import create_project
from pdf_to_web.recent_projects import (
    RECENT_PROJECTS_SCHEMA,
    load_recent_projects,
    remember_project,
    remove_recent_project,
)


class RecentProjectsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / "config" / "recent-projects.json"

    def project(self, name: str, title: str | None = None) -> Path:
        path = self.root / name
        create_project(path, title or name)
        return path

    def test_add_order_deduplicate_and_remove(self):
        first = self.project("first", "First")
        second = self.project("second", "Second")
        records = remember_project(self.config, first, opened_at="2026-01-01T00:00:00+00:00")
        records = remember_project(self.config, second, records, opened_at="2026-01-02T00:00:00+00:00")
        records = remember_project(self.config, first, records, opened_at="2026-01-03T00:00:00+00:00")
        self.assertEqual([record.title for record in records], ["First", "Second"])
        self.assertEqual(records[0].last_opened, "2026-01-03T00:00:00+00:00")

        records = remove_recent_project(self.config, first, records)
        self.assertEqual([record.title for record in records], ["Second"])
        self.assertEqual([record.title for record in load_recent_projects(self.config)], ["Second"])

    def test_reopen_filters_missing_projects_and_corrupt_config(self):
        project = self.project("available", "Available")
        remember_project(self.config, project)
        data = json.loads(self.config.read_text(encoding="utf-8"))
        data["projects"].append(
            {"title": "Missing", "path": str(self.root / "missing"), "last_opened": "2026-01-01T00:00:00+00:00"}
        )
        self.config.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual([record.title for record in load_recent_projects(self.config)], ["Available"])

        self.config.write_text("not json", encoding="utf-8")
        self.assertEqual(load_recent_projects(self.config), [])

    def test_canonical_paths_suppress_symlink_duplicates(self):
        project = self.project("canonical")
        alias = self.root / "alias"
        try:
            alias.symlink_to(project, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Symlinks unavailable: {exc}")
        records = remember_project(self.config, project)
        records = remember_project(self.config, alias, records)
        self.assertEqual(len(records), 1)
        self.assertEqual(Path(records[0].path), project.resolve())

    def test_load_does_not_scan_for_projects(self):
        declared = self.project("declared")
        self.project("undisclosed")
        self.config.parent.mkdir(parents=True)
        self.config.write_text(
            json.dumps(
                {
                    "schema_version": RECENT_PROJECTS_SCHEMA,
                    "projects": [
                        {"title": "Declared", "path": str(declared), "last_opened": "2026-01-01T00:00:00+00:00"}
                    ],
                }
            ),
            encoding="utf-8",
        )
        with mock.patch.object(Path, "rglob", side_effect=AssertionError("filesystem scan")):
            records = load_recent_projects(self.config)
        self.assertEqual([record.title for record in records], ["Declared"])


if __name__ == "__main__":
    unittest.main()
