import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pdf_to_web.project import create_project, save_project
from pdf_to_web.source_pages import render_source_page


class SourcePageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "project"
        state = create_project(self.project)
        source = self.project / "source" / "original.pdf"
        source.write_bytes(b"%PDF-1.4\n%%EOF")
        state["source"].update({"path": "source/original.pdf", "page_count": 2})
        save_project(self.project, state)

    def test_rejects_out_of_range_page(self):
        with self.assertRaises(ValueError):
            render_source_page(self.project, 3)

    @mock.patch("pdf_to_web.source_pages.shutil.which", return_value="/usr/bin/pdftoppm")
    @mock.patch("pdf_to_web.source_pages.subprocess.run")
    def test_renders_to_confined_review_cache(self, run, _which):
        def create_output(command, **_kwargs):
            Path(command[-1] + ".png").write_bytes(b"png")
            return mock.Mock(returncode=0, stderr="")
        run.side_effect = create_output
        output = render_source_page(self.project, 2)
        self.assertEqual(output.relative_to(self.project.resolve()), Path("review/source-pages/page-0002.png"))
        self.assertEqual(run.call_args.args[0][1:5], ["-f", "2", "-l", "2"])


if __name__ == "__main__":
    unittest.main()
