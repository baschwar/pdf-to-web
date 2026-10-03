import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pdf_to_web.project import create_project, save_project
from pdf_to_web.source_pages import render_source_page
from pdf_to_web.errors import PdfToWebError


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

    @mock.patch("pdf_to_web.source_pages.shutil.which", return_value=None)
    def test_missing_renderer_is_actionable_and_does_not_create_cache(self, _which):
        source = self.project / 'source/original.pdf'
        before = source.read_bytes()
        (self.project / 'review/source-pages').rmdir()  # Legacy project without a render-cache folder.
        with self.assertRaisesRegex(PdfToWebError, 'Install Poppler PDF utilities, then restart'):
            render_source_page(self.project, 1)
        self.assertFalse((self.project / 'review/source-pages').exists())
        self.assertEqual(source.read_bytes(), before)

    @mock.patch("pdf_to_web.source_pages.shutil.which", return_value=None)
    def test_existing_cached_page_is_available_without_renderer(self, which):
        page = self.project / 'review/source-pages/page-0001.png'
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_bytes(b'cached image')
        self.assertEqual(render_source_page(self.project, 1), page.resolve())
        which.assert_not_called()

    @mock.patch("pdf_to_web.source_pages.shutil.which", return_value="/usr/bin/pdftoppm")
    @mock.patch("pdf_to_web.source_pages.subprocess.run", side_effect=OSError('renderer cannot start'))
    def test_renderer_start_failure_has_setup_guidance(self, _run, _which):
        with self.assertRaisesRegex(PdfToWebError, 'Check the Poppler installation'):
            render_source_page(self.project, 1)

    @mock.patch("pdf_to_web.source_pages.shutil.which", return_value="/usr/bin/pdftoppm")
    @mock.patch("pdf_to_web.source_pages.subprocess.run")
    def test_renderer_failure_retains_detail_and_source(self, run, _which):
        source = self.project / 'source/original.pdf'
        before = source.read_bytes()
        run.return_value = mock.Mock(returncode=1, stderr='Synthetic invalid source')
        with self.assertRaisesRegex(PdfToWebError, 'Synthetic invalid source'):
            render_source_page(self.project, 1)
        self.assertEqual(source.read_bytes(), before)
        self.assertFalse((self.project / 'review/source-pages/page-0001.png').exists())

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
