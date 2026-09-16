import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

from pdf_to_web.project import create_project, load_project
from pdf_to_web.review_state import original_path
from pdf_to_web.web import (
    CSRF_HEADER,
    WebAppConfig,
    create_app,
    is_allowed_host,
    is_allowed_origin,
    open_browser_when_ready,
    safe_project_file,
    static_path,
)
from pdf_to_web.wordpress_preview import WordPressPreview


@unittest.skipIf(TestClient is None, "FastAPI test dependencies are not installed")
class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "project"
        state = create_project(self.project, "Web fixture")
        (self.project / "source" / "original.pdf").write_bytes(b"%PDF-1.4\n%%EOF")
        state["source"].update({"path": "source/original.pdf", "original_filename": "fixture.pdf", "page_count": 2, "classification": "TEXT PDF"})
        state["extraction"].update({"status": "complete", "use_struct_tree": False})
        from pdf_to_web.project import save_project
        save_project(self.project, state)
        document = {
            "schema_version": "pdf-to-web-normalized-v1",
            "metadata": {"title": "Web fixture", "page_count": 2},
            "review": {"status": "review_ready", "issues": [], "complex_visuals": []},
            "blocks": [
                {"id": "h", "type": "heading", "level": 1, "content": "Web fixture", "provenance": {"source_page": 1}},
                {"id": "p1", "type": "paragraph", "content": "Original one", "provenance": {"source_page": 1}},
                {"id": "p2", "type": "paragraph", "content": "Original two", "provenance": {"source_page": 2}},
            ],
        }
        path = original_path(self.project)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document), encoding="utf-8")
        self.config = WebAppConfig(project=self.project, recent_projects=(self.project,), port=54321, bootstrap_token="bootstrap", session_token="session", csrf_token="csrf")
        self.client = TestClient(create_app(self.config), base_url="http://127.0.0.1:54321")

    def bootstrap(self):
        response = self.client.get("/bootstrap/bootstrap", follow_redirects=False)
        self.assertEqual(response.status_code, 303)

    def headers(self):
        return {"origin": "http://127.0.0.1:54321", CSRF_HEADER: "csrf"}

    def test_startup_bootstrap_and_pages(self):
        self.assertEqual(self.client.get("/api/health").status_code, 200)
        self.assertEqual(self.client.get("/").status_code, 401)
        self.bootstrap()
        self.assertEqual(self.client.get("/bootstrap/bootstrap").status_code, 403)
        for route, heading in (("/", "Projects"), ("/document", "Document"), ("/structure", "Structure"), ("/preview", "Preview"), ("/export", "Export")):
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertIn(f"<h1>{heading}</h1>", response.text)
        placeholder = self.client.get("/api/preview/MEDIA_URL_REQUIRED")
        self.assertEqual(placeholder.status_code, 200)
        self.assertEqual(placeholder.headers["content-type"], "image/svg+xml")

    @mock.patch("pdf_to_web.web.source_page_size", return_value=(612.0, 792.0))
    def test_structure_exposes_source_region_and_page_dimensions(self, page_size):
        self.bootstrap()
        document = json.loads(original_path(self.project).read_text())
        document["blocks"][0]["provenance"]["bounding_box"] = [36, 700, 300, 730]
        original_path(self.project).write_text(json.dumps(document))
        response = self.client.get("/structure")
        self.assertIn('data-bbox="[36, 700, 300, 730]"', response.text)
        self.assertIn('id="source-highlight"', response.text)
        metadata = self.client.get("/api/source-page/1")
        self.assertEqual(metadata.json(), {"page": 1, "width": 612.0, "height": 792.0})
        page_size.assert_called_once_with(self.project.resolve(), 1)

    def test_project_loading_requires_server_issued_selection(self):
        self.bootstrap()
        bad = self.client.post("/api/projects/open", headers=self.headers(), json={"path": str(self.project)})
        self.assertEqual(bad.status_code, 400)
        with mock.patch("pdf_to_web.web.choose_project_folder", return_value=self.project):
            picked = self.client.post("/api/picker/project", headers=self.headers(), json={})
        self.assertNotIn(str(self.project.parent), json.dumps(picked.json()))
        opened = self.client.post("/api/projects/open", headers=self.headers(), json={"selection_token": picked.json()["selection"]["token"]})
        self.assertEqual(opened.status_code, 200)

    def test_edit_persistence_type_level_exclusion_and_reorder(self):
        self.bootstrap()
        edited = self.client.post("/api/blocks/p1", headers=self.headers(), json={"type": "heading", "level": 3, "content": "Reviewed", "review_status": "approved"})
        self.assertEqual(edited.status_code, 200, edited.text)
        excluded = self.client.post("/api/blocks/p2/exclude", headers=self.headers(), json={})
        self.assertEqual(excluded.status_code, 200)
        moved = self.client.post("/api/blocks/p1/up", headers=self.headers(), json={})
        self.assertEqual(moved.status_code, 200)
        reopened = self.client.get("/api/document").json()["document"]
        self.assertEqual(reopened["blocks"][0]["id"], "p1")
        self.assertEqual(reopened["blocks"][0]["level"], 3)
        self.assertEqual(reopened["blocks"][2]["review"]["status"], "excluded")

    def test_merge_split_and_review_states(self):
        self.bootstrap()
        self.assertEqual(self.client.post("/api/blocks/p1/merge", headers=self.headers(), json={}).status_code, 200)
        content = self.client.get("/api/document").json()["document"]["blocks"][1]["content"]
        self.assertIn("Original two", content)
        split = self.client.post("/api/blocks/p1/split", headers=self.headers(), json={"offset": len("Original one")})
        self.assertEqual(split.status_code, 200, split.text)
        flagged = self.client.post("/api/blocks/p1/flag", headers=self.headers(), json={})
        self.assertEqual(flagged.status_code, 200)

    def test_preview_and_exports_use_reviewed_state(self):
        self.bootstrap()
        self.client.post("/api/blocks/p1", headers=self.headers(), json={"content": "Reviewed export text", "review_status": "approved"})
        preview = self.client.get("/api/preview/html")
        self.assertIn("Reviewed export text", preview.text)
        for target in ("html", "gutenberg", "wordpress-xml"):
            with self.subTest(target=target):
                result = self.client.post("/api/export", headers=self.headers(), json={"target": target, "profile": "generic", "post_type": "page"})
                self.assertEqual(result.status_code, 200, result.text)
                output = self.project / result.json()["files"][0]
                self.assertIn("Reviewed export text", output.read_text())

    def test_wordpress_preview_consumes_actual_gutenberg_output(self):
        self.bootstrap()
        self.client.post("/api/blocks/p1", headers=self.headers(), json={"content": "Reviewed Gutenberg preview text"})
        with mock.patch(
            "pdf_to_web.web.render_gutenberg_preview",
            return_value=WordPressPreview(
                '<p>Reviewed Gutenberg preview text</p>',
                ("core/paragraph",),
                ("wsuwp/example",),
            ),
        ) as render:
            response = self.client.get("/api/preview/wordpress?profile=wsuwp")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Reviewed Gutenberg preview text", render.call_args.args[0])
        self.assertIn("<!-- wp:wsuwp/section", render.call_args.args[0])
        self.assertIn("Unsupported preview blocks", response.text)
        self.assertIn("default-src 'none'", response.headers["content-security-policy"])

    def test_preview_page_has_distinct_sandboxed_modes(self):
        self.bootstrap()
        response = self.client.get("/preview")
        self.assertIn("Semantic HTML", response.text)
        self.assertIn("WordPress Preview", response.text)
        self.assertIn('sandbox="allow-same-origin"', response.text)

    def test_blocked_document_cannot_export_gutenberg_or_wxr(self):
        data = json.loads(original_path(self.project).read_text())
        data["review"]["status"] = "conversion_blocked"
        original_path(self.project).write_text(json.dumps(data))
        self.bootstrap()
        result = self.client.post("/api/export", headers=self.headers(), json={"target": "wordpress-xml", "profile": "generic", "post_type": "page"})
        self.assertEqual(result.status_code, 400)
        self.assertIn("blocked", result.json()["error"].lower())
        html_result = self.client.post("/api/export", headers=self.headers(), json={"target": "html", "profile": "generic", "post_type": "page"})
        self.assertEqual(html_result.status_code, 200)
        preview_result = self.client.get("/api/preview/wordpress")
        self.assertEqual(preview_result.status_code, 200)
        self.assertIn("Gutenberg export is blocked", preview_result.text)
        edit_result = self.client.post("/api/blocks/p1/approve", headers=self.headers(), json={})
        self.assertEqual(edit_result.status_code, 409)

    def test_state_changes_require_origin_and_csrf(self):
        self.bootstrap()
        missing = self.client.post("/api/blocks/p1/approve", headers={CSRF_HEADER: "csrf"}, json={})
        wrong = self.client.post("/api/blocks/p1/approve", headers={"origin": "http://127.0.0.1:54321", CSRF_HEADER: "wrong"}, json={})
        self.assertEqual((missing.status_code, wrong.status_code), (403, 403))

    def test_safe_path_and_loopback_helpers(self):
        self.assertTrue(is_allowed_host("127.0.0.1:54321", 54321))
        self.assertFalse(is_allowed_host("example.com:54321", 54321))
        self.assertTrue(is_allowed_origin("http://localhost:54321", 54321))
        self.assertTrue(static_path("pico.min.css").is_file())
        with self.assertRaises(ValueError):
            safe_project_file(self.project, "../outside.pdf")

    @mock.patch("pdf_to_web.web.webbrowser.open")
    @mock.patch("pdf_to_web.web.socket.create_connection")
    def test_browser_opens_only_after_server_is_ready(self, connect, browser_open):
        connection = mock.MagicMock()
        connect.side_effect = [ConnectionRefusedError, connection]

        with mock.patch("pdf_to_web.web.time.sleep"):
            open_browser_when_ready(
                "http://127.0.0.1:54321/bootstrap/token",
                "127.0.0.1",
                54321,
            )

        self.assertEqual(connect.call_count, 2)
        browser_open.assert_called_once_with("http://127.0.0.1:54321/bootstrap/token")


if __name__ == "__main__":
    unittest.main()
