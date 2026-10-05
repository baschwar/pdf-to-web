import copy
import html
import json
import math
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject, NumberObject, RectangleObject

from pdf_to_web.normalize import apply_source_title, recover_source_title_region, recover_source_supplemental_regions
from pdf_to_web.project import create_project, save_project
from pdf_to_web.source_pages import SourceTextRegion, display_source_box, matched_source_text_box, source_page_size, source_regions_for_blocks, source_text_regions


def geometry_project(root, *, size=(600, 1500), origin=(0, 8), rotation=0, crop=False, repeated=False, second_position=False):
    project = create_project(root, 'Geometry fixture')
    writer = PdfWriter()
    page = writer.add_blank_page(width=size[0], height=size[1])
    page.mediabox = RectangleObject([origin[0], origin[1], origin[0] + size[0], origin[1] + size[1]])
    if crop:
        page.cropbox = RectangleObject([origin[0] + 20, origin[1] + 30, origin[0] + size[0] - 20, origin[1] + size[1] - 30])
    if rotation:
        page.rotate(rotation)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica'), NameObject('/Encoding'): NameObject('/WinAnsiEncoding')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    top = origin[1] + size[1] - 34
    title = f'q .75 0 0 -.75 {origin[0] + 40} {top} cm BT /F1 52 Tf 1 0 0 -1 7 48 Tm (Fixture title) Tj ET Q\n'
    subtitle = f'q .75 0 0 -.75 {origin[0] + 20} {top - 60} cm BT /F1 24 Tf 1 0 0 -1 14 27 Tm (A fixture subtitle) Tj ET Q\n'
    content = title + (title if repeated else '') + subtitle
    if second_position:
        content += f'BT /F1 20 Tf 1 0 0 1 {origin[0] + 40} {origin[1] + 100} Tm (Fixture title) Tj ET\n'
    content += f'BT /F1 10 Tf 1 0 0 1 {origin[0] + 30} {origin[1] + 30} Tm (Reference text) Tj ET\n'
    stream = DecodedStreamObject(); stream.set_data(content.encode('ascii'))
    page[NameObject('/Contents')] = writer._add_object(stream)
    source = root / 'source' / 'geometry.pdf'
    with source.open('wb') as output:
        writer.write(output)
    project['source'].update(path='source/geometry.pdf', original_filename='geometry.pdf', page_count=1, classification='TEXT PDF')
    project['extraction']['status'] = 'complete'
    save_project(root, project)
    return source


def recovered(identity='recovered-document-title', text='Fixture title'):
    return {'id': identity, 'type': 'heading', 'level': 1 if identity.endswith('title') else 2, 'content': text,
            'provenance': {'source_type': 'recovered first-page header' if identity.endswith('title') else 'recovered first-page subtitle', 'source_page': 1, 'bounding_box': [7, 35, 550, 100]},
            'review': {'status': 'needs_review', 'updated_at': '2026-01-01T00:00:00+00:00'}}


class SourceGeometryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'project'
        self.source = geometry_project(self.root)

    def test_scaled_flipped_local_text_matrix_maps_title_to_real_top_of_tall_page(self):
        title, box = recover_source_title_region(self.root)
        self.assertEqual(title, 'Fixture title')
        self.assertGreater(box[1], 1400)
        self.assertAlmostEqual(box[0], 45.25)
        self.assertLess(box[2], 600)
        page = PdfReader(self.source).pages[0]
        _, regions = source_text_regions(page)
        self.assertLess(next(r.legacy_box[1] for r in regions if r.text == title), 100)
        overlay = source_regions_for_blocks(self.root, [recovered()])
        self.assertGreater(overlay['recovered-document-title']['regions'][0][1], 1400)
        self.assertEqual(overlay['recovered-document-title']['coverage'], '')

    def test_subtitle_text_selection_is_preserved_but_its_region_moves_out_of_footer(self):
        subtitle, box = recover_source_supplemental_regions(self.root)['subtitle']
        self.assertEqual(subtitle, 'A fixture subtitle')
        self.assertGreater(box[1], 1300)
        self.assertLess(box[3], 1450)
        block = recovered('recovered-document-subtitle', subtitle)
        before = copy.deepcopy(block)
        self.assertGreater(source_regions_for_blocks(self.root, [block])[block['id']]['regions'][0][1], 1300)
        self.assertEqual(block, before)

    def test_existing_nonempty_wrong_box_is_not_persistently_repaired(self):
        document = {'metadata': {'title': 'Fixture title'}, 'blocks': [recovered()]}
        before = copy.deepcopy(document)
        self.assertFalse(apply_source_title(document, self.root))
        self.assertEqual(document, before)
        self.assertNotEqual(source_regions_for_blocks(self.root, document['blocks'])['recovered-document-title']['regions'][0], before['blocks'][0]['provenance']['bounding_box'])

    def test_existing_authored_title_and_metadata_are_preserved_and_unmatched_outline_refused(self):
        document = {'metadata': {'title': 'Author selected metadata'}, 'blocks': [recovered(text='Authored changed title')]}
        before = copy.deepcopy(document)
        self.assertFalse(apply_source_title(document, self.root))
        self.assertEqual(document, before)
        result = source_regions_for_blocks(self.root, document['blocks'])['recovered-document-title']
        self.assertEqual(result['regions'], [])
        self.assertIn('could not be matched confidently', result['coverage'])
        self.assertIn('text remains in Reading order', result['coverage'])

    def test_missing_legacy_box_backfill_requires_source_text_to_still_match(self):
        for content, expected in [('Fixture title', True), ('Authored changed title', False)]:
            with self.subTest(content=content):
                block = recovered(text=content); del block['provenance']['bounding_box']
                document = {'metadata': {'title': content}, 'blocks': [block]}
                self.assertEqual(apply_source_title(document, self.root), expected)
                self.assertEqual(block['content'], content)
                if expected:
                    self.assertGreater(block['provenance']['bounding_box'][1], 1400)
                else:
                    self.assertNotIn('bounding_box', block['provenance'])

    def test_media_origin_rotation_and_crop_box_match_renderer_media_contract(self):
        for size in [(612, 792), (600, 1500), (420, 1000)]:
            for rotation in [0, 90, 180, 270]:
                with self.subTest(size=size, rotation=rotation):
                    root = Path(self.tmp.name) / f'page-{size[0]}-{rotation}'
                    source = geometry_project(root, size=size, origin=(100, 200), rotation=rotation, crop=True)
                    page = PdfReader(source).pages[0]; width, height = size
                    expected = {0: [10, 20, 60, 40], 90: [20, width - 60, 40, width - 10],
                                180: [width - 60, height - 40, width - 10, height - 20], 270: [height - 40, 10, height - 20, 60]}[rotation]
                    self.assertEqual(display_source_box(page, [110, 220, 160, 240]), expected)
                    self.assertEqual(source_page_size(root, 1), (height, width) if rotation in [90, 270] else (width, height))
                    block = {'id': 'ordinary', 'type': 'paragraph', 'content': 'Ordinary source', 'provenance': {'source_page': 1, 'bounding_box': [110, 220, 160, 240]}, 'review': {'status': 'approved'}}
                    before = copy.deepcopy(block)
                    self.assertEqual(source_regions_for_blocks(root, [block])['ordinary']['regions'], [expected])
                    self.assertEqual(block, before)

    def test_letter_and_nonletter_sizes_do_not_guess_page_origin_or_paper_format(self):
        for size in [(612, 792), (600, 1500), (420, 1000)]:
            root = Path(self.tmp.name) / f'title-{size[0]}'
            geometry_project(root, size=size, origin=(-10, 20))
            result = source_regions_for_blocks(root, [recovered()])['recovered-document-title']
            self.assertEqual(result['coverage'], '')
            self.assertGreater(result['regions'][0][1] / size[1], .8)
            self.assertLess(result['regions'][0][3], size[1])

    def test_coincident_overprint_has_one_outline_but_legitimate_repeated_locations_are_ambiguous(self):
        root = Path(self.tmp.name) / 'overprint'; geometry_project(root, repeated=True)
        self.assertEqual(len(source_regions_for_blocks(root, [recovered()])['recovered-document-title']['regions']), 1)
        root = Path(self.tmp.name) / 'different-locations'; geometry_project(root, repeated=True, second_position=True)
        result = source_regions_for_blocks(root, [recovered()])['recovered-document-title']
        self.assertEqual(result['regions'], [])
        self.assertIn('could not be matched confidently', result['coverage'])

    def test_unknown_glyph_metrics_do_not_use_a_guessed_five_hundred_unit_width(self):
        page = PdfReader(self.source).pages[0]
        with mock.patch('pdf_to_web.source_pages._font_text_width', return_value=None):
            _, regions = source_text_regions(page)
            self.assertIsNone(matched_source_text_box('Fixture title', regions))
            result = source_regions_for_blocks(self.root, [recovered()])['recovered-document-title']
        self.assertEqual(result['regions'], [])
        self.assertIn('Source outline unavailable', result['coverage'])

    def test_cid_font_widths_use_encoded_glyph_ids_rather_than_unicode_indices(self):
        from pdf_to_web.source_pages import _font_text_width
        cmap = DecodedStreamObject()
        cmap.set_data(b'1 begincodespacerange\n<0000> <FFFF>\nendcodespacerange\n3 beginbfchar\n<0001> <0041>\n<0002> <0042>\n<0003> <0020>\nendbfchar')
        descriptor = DictionaryObject({NameObject('/Type'): NameObject('/FontDescriptor'), NameObject('/FontName'): NameObject('/Fixture')})
        descendant = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/CIDFontType2'),
            NameObject('/BaseFont'): NameObject('/Fixture'), NameObject('/FontDescriptor'): descriptor,
            NameObject('/W'): ArrayObject([NumberObject(1), ArrayObject([NumberObject(700), NumberObject(250), NumberObject(300)])]),
            NameObject('/DW'): NumberObject(1000)})
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type0'),
            NameObject('/BaseFont'): NameObject('/Fixture'), NameObject('/Encoding'): NameObject('/Identity-H'),
            NameObject('/DescendantFonts'): ArrayObject([descendant]), NameObject('/ToUnicode'): cmap})
        self.assertAlmostEqual(_font_text_width(font, 'A B'), 1.25)
        self.assertIsNone(_font_text_width(font, 'C'))
        font[NameObject('/Encoding')] = NameObject('/Identity-V')
        self.assertIsNone(_font_text_width(font, 'AB'))

    def test_invalid_recovered_page_and_off_page_ordinary_box_show_actionable_coverage(self):
        title = recovered(); title['provenance']['source_page'] = 2
        outside = {'id': 'outside', 'type': 'paragraph', 'content': 'Saved text',
                   'provenance': {'source_page': 1, 'bounding_box': [1000, 100, 1100, 120]}}
        overlay = source_regions_for_blocks(self.root, [title, outside])
        for identity in ['recovered-document-title', 'outside']:
            self.assertEqual(overlay[identity]['regions'], [])
            self.assertIn('source PDF', overlay[identity]['coverage'])

    def test_multiline_match_and_invalid_or_missing_source_are_conservative(self):
        region = SourceTextRegion('First line', [10, 600, 90, 620], [0, 0, 10, 10], 20)
        second = SourceTextRegion('Second line', [10, 570, 100, 590], [0, 0, 10, 10], 20)
        self.assertEqual(matched_source_text_box('First line Second line', [region, second]), [10, 570, 100, 620])
        self.assertIsNone(matched_source_text_box('First line', [region, SourceTextRegion('First line', None, [0, 0, 10, 10], 20)]))
        self.source.unlink()
        result = source_regions_for_blocks(self.root, [recovered()])['recovered-document-title']
        self.assertEqual(result['regions'], [])
        self.assertIn('open the source PDF', result['coverage'])

    def test_nested_list_text_regions_preserve_missing_coverage_and_excluded_children(self):
        block = {'id': 'list', 'type': 'list', 'provenance': {'source_page': 1, 'bounding_box': [10, 100, 400, 700]}, 'children': [
            {'id': 'a', 'type': 'list_item', 'content': 'One', 'provenance': {'source_page': 1, 'bounding_box': [20, 600, 80, 620]}},
            {'id': 'b', 'type': 'list_item', 'content': 'Two', 'provenance': {'source_page': 1}},
            {'id': 'excluded', 'type': 'list_item', 'review': {'status': 'excluded'}, 'provenance': {'source_page': 1, 'bounding_box': [20, 500, 80, 520]}},
            {'id': 'image', 'type': 'image', 'provenance': {'source_page': 1, 'bounding_box': [20, 400, 80, 420]}},
        ]}
        overlay = source_regions_for_blocks(self.root, [block])['list']
        self.assertEqual(overlay['regions'], [[20, 592, 80, 612]])
        from pdf_to_web.web import _source_region_coverage
        self.assertIn('1 nested text element', _source_region_coverage(block, overlay))

    def test_source_box_clips_image_canvas_without_shifting_to_visible_icon(self):
        page = PdfReader(self.source).pages[0]
        self.assertEqual(display_source_box(page, [-50, 1000, 250, 1200]), [0, 992, 250, 1192])
        for box in ([0, 0, 0, 10], [1, 1, math.nan, 10], [1000, 100, 1100, 120], None):
            self.assertIsNone(display_source_box(page, box))

    def test_structure_get_reopen_preserves_authored_text_metadata_decisions_and_saved_files(self):
        from fastapi.testclient import TestClient
        from pdf_to_web.review_state import ensure_review_document, original_path, save_review_document, _set_status
        from pdf_to_web.web import WebAppConfig, create_app
        document = {'schema_version': 'pdf-to-web-normalized-v1', 'metadata': {'title': 'Fixture title', 'page_count': 1},
                    'review': {'status': 'needs_review', 'issues': [], 'complex_visuals': []}, 'blocks': [recovered(), recovered('recovered-document-subtitle', 'A fixture subtitle')]}
        original_path(self.root).write_text(json.dumps(document))
        document = ensure_review_document(self.root)
        document['blocks'][0]['content'] = 'Authored changed title'
        document['metadata']['title'] = 'Author selected metadata'
        _set_status(document['blocks'][0], 'approved')
        save_review_document(self.root, document)
        files = [self.root / 'project.json', self.root / 'review/current.json', *sorted((self.root / 'review/revisions').glob('*.json'))]
        before = {str(p): p.read_bytes() for p in files}
        for index in [1, 2]:
            config = WebAppConfig(project=self.root, recent_projects=(self.root,), projects_root=Path(self.tmp.name), recent_store=Path(self.tmp.name) / f'recent-{index}.json', port=54600 + index, bootstrap_token=f'bootstrap-{index}')
            client = TestClient(create_app(config), base_url=f'http://127.0.0.1:{54600 + index}')
            client.get(f'/bootstrap/bootstrap-{index}', follow_redirects=False)
            response = client.get('/structure')
            self.assertEqual(response.status_code, 200)
            card = re.search(r'<article[^>]*id="block-recovered-document-title".*?</article>', response.text, re.S).group()
            self.assertIn('Authored changed title', card)
            self.assertIn('data-bboxes=""', card)
            self.assertIn('could not be matched confidently', html.unescape(card))
            self.assertIn('status-approved', card)
            self.assertEqual({str(p): p.read_bytes() for p in files}, before)
            self.assertEqual(sorted((self.root / 'review/revisions').glob('*.json')), files[2:])
            client.close()


if __name__ == '__main__':
    unittest.main()
