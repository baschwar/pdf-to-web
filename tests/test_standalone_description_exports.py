"""Standalone reviewed equivalents survive every publication projection."""
import copy
import unittest
import xml.etree.ElementTree as ET

import test_image_draft_routes as fixtures
from review_helpers import approve_publication_fixture
from pdf_to_web.errors import PdfToWebError
from pdf_to_web.export import export_project
from pdf_to_web.exporters import gutenberg, html, markdown, wxr
from pdf_to_web.exporters.common import blocks_with_image_descriptions
from pdf_to_web.output_pages import page_document, pages
from pdf_to_web.publication import require_ready
from pdf_to_web.review_state import ensure_review_document, save_review_document


class StandaloneDescriptionExportTests(unittest.TestCase):
    setUp = fixtures.ImageDraftRouteTests.setUp

    def document(self, field='long_description'):
        document = ensure_review_document(self.root)
        document['review']['complex_visuals'] = [{
            'id': 'standalone-synthetic', 'source_page': 1, 'status': 'reviewed',
            'accessibility': {'short_alt': 'Synthetic diagram purpose',
                              field: 'Standalone equivalent: first group; second group.'}}]
        save_review_document(self.root, document, snapshot=False)
        return approve_publication_fixture(self.root)

    def outputs(self, document):
        blocks = gutenberg.render_document(document)
        xml = ET.fromstring(wxr.render_wxr([{'content': blocks}]))
        return [html.render_document(document), blocks,
                xml.find('.//{' + wxr.CONTENT_NS + '}encoded').text,
                markdown.render_document(document)]

    def test_reviewed_standalone_text_present_once_without_mutating_saved_state(self):
        document = self.document()
        before = copy.deepcopy(document)
        saved = (self.root / 'review/current.json').read_bytes()
        require_ready(document)
        for output in self.outputs(document):
            self.assertEqual(output.count('Standalone equivalent: first group; second group.'), 1)
        self.assertEqual(document, before)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), saved)

    def test_adjacent_equivalent_and_output_page_projection_are_not_duplicated(self):
        document = self.document('adjacent_text')
        # The approval helper fills long_description; retain adjacent-only authored content.
        document['review']['complex_visuals'][0]['accessibility'].pop('long_description', None)
        for output in self.outputs(page_document(document, pages(document)[0]['id'])):
            self.assertEqual(output.count('Standalone equivalent: first group; second group.'), 1)

    def test_existing_image_association_never_creates_a_standalone_duplicate(self):
        document = self.document()
        visual = document['review']['complex_visuals'][0]
        image = next(b for b in document['blocks'] if b['type'] == 'image')
        image['complex_visual_id'] = visual['id']
        for source in (document, page_document(document, pages(document)[0]['id'])):
            for output in self.outputs(source):
                self.assertEqual(output.count('Standalone equivalent: first group; second group.'), 1)
        image['review']['status'] = 'excluded'
        for output in self.outputs(document):
            self.assertNotIn('Standalone equivalent:', output)

    def test_excluded_equivalent_and_unaccepted_draft_are_not_published(self):
        document = self.document()
        document['review']['complex_visuals'][0]['status'] = 'excluded'
        document['image_description_drafts']['requests']['unaccepted'] = {
            'draft': {'long_description': 'UNACCEPTED PRIVATE DRAFT'}}
        for output in self.outputs(document):
            self.assertNotIn('Standalone equivalent:', output)
            self.assertNotIn('UNACCEPTED PRIVATE DRAFT', output)

    def test_pending_standalone_review_blocks_real_export_before_writing(self):
        document = self.document()
        document['review']['complex_visuals'][0]['status'] = 'reclassified'
        save_review_document(self.root, document, snapshot=False)
        with self.assertRaisesRegex(PdfToWebError, 'needs review'):
            export_project(self.root, 'all')
        self.assertFalse(list((self.root / 'output/html').glob('*.html')))

    def test_real_publication_files_retain_the_reviewed_equivalent(self):
        self.document()
        exports = export_project(self.root, 'all')
        publication_files = [path for path in exports
                             if path.parent.name in {'html', 'markdown', 'blocks', 'wxr'}
                             and path.suffix in {'.html', '.md', '.xml'}]
        self.assertGreaterEqual(len(publication_files), 4)
        for path in publication_files:
            content = path.read_text()
            if path.suffix == '.xml':
                content = ET.fromstring(content).find('.//{' + wxr.CONTENT_NS + '}encoded').text
            self.assertEqual(content.count('Standalone equivalent: first group; second group.'), 1, path.name)

    def test_projection_avoids_colliding_content_ids_and_preserves_text(self):
        document = self.document()
        document['blocks'].append({'id': 'standalone-synthetic', 'type': 'paragraph',
                                   'content': 'Existing unrelated text'})
        blocks = blocks_with_image_descriptions(document)
        ids = [b['id'] for b in blocks]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(blocks[-1]['content'], 'Standalone equivalent: first group; second group.')


if __name__ == '__main__':
    unittest.main()
