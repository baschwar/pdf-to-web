import copy
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from pdf_to_web import output_pages as op
from pdf_to_web.errors import PdfToWebError
from pdf_to_web.output_page_export import export_pages
from pdf_to_web.project import create_project
from pdf_to_web.review_state import (ensure_review_document, original_path, review_path, save_review_document,
                                    update_output_pages, split_block, merge_with_next, move_block, undo_last, update_block)
from pdf_to_web.exporters import html, gutenberg, wxr


def fixture():
    def block(i, kind, content, page, **more):
        return {'id': i, 'type': kind, 'content': content, 'provenance': {'source_page': page}, 'review': {'status': 'approved'}, **more}
    return {'schema_version': 'pdf-to-web-normalized-v1', 'metadata': {'title': 'Handbook'},
            'review': {'status': 'needs_review', 'issues': [], 'complex_visuals': []},
            'accessibility_review': {'decisions': {'diagnostic:example:document': {'status': 'approved', 'note': 'Preserved'}}},
            'blocks': [block('h1', 'heading', 'Handbook', 1, level=1),
                       block('p1', 'paragraph', 'Welcome 1', 1, footnote_references=[{'id': 'ref1', 'footnote_id': 'note1', 'marker': '1', 'start': 8, 'end': 9}]),
                       block('p2', 'paragraph', 'More text', 3),
                       block('h2', 'heading', 'Policy', 4, level=2),
                       block('p3', 'paragraph', 'Policy 1', 4, footnote_references=[{'id': 'ref2', 'footnote_id': 'note1', 'marker': '1', 'start': 7, 'end': 8}]),
                       block('p4', 'paragraph', 'Go', 5, runs=[{'type': 'link', 'text': 'Welcome', 'url': '#p1'}])],
            'footnotes': [{'id': 'note1', 'marker': '1', 'text': 'Shared note', 'references': [{'id': 'ref1'}, {'id': 'ref2'}]}]}


class OutputPagesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'project'
        create_project(self.root, 'Handbook')
        original_path(self.root).write_text(json.dumps(fixture()))
        self.document = ensure_review_document(self.root)
        self.first = op.pages(self.document)[0]['id']

    def group(self):
        update_output_pages(self.root, 'apply_suggestions', {})
        d = ensure_review_document(self.root)
        return d, op.pages(d)

    def test_legacy_migration_is_persisted_preserves_content_and_decisions(self):
        d = ensure_review_document(self.root)
        self.assertEqual(d['blocks'], self.document['blocks'])
        self.assertEqual(d['accessibility_review'], fixture()['accessibility_review'])
        self.assertEqual(op.pages(d)[0]['block_ids'], [b['id'] for b in d['blocks']])
        self.assertNotIn('output_pages', json.loads(original_path(self.root).read_text()))
        self.assertEqual(op.pages(d), json.loads(review_path(self.root).read_text())['output_pages']['pages'])

    def test_suggestions_do_not_replace_and_ranges_are_discontinuous(self):
        proposed = op.suggest(self.document)
        self.assertEqual(proposed[0]['source_ranges'], [[1, 1], [3, 3]])
        self.assertEqual(len(op.pages(self.document)), 1)
        self.assertEqual(proposed, op.suggest(self.document))

    def test_group_reopen_metadata_stable_identity_and_navigation(self):
        d, group = self.group()
        update_output_pages(self.root, 'metadata', {'page_id': group[1]['id'], 'title': 'Changed', 'slug': 'changed', 'parent': group[0]['id'], 'navigation_order': 9})
        reopened = ensure_review_document(self.root)
        self.assertEqual(op.pages(reopened)[1]['id'], group[1]['id'])
        self.assertEqual(op.pages(reopened)[1]['navigation_order'], 9)
        self.assertEqual(op.pages(reopened)[1]['block_ids'], ['h2', 'p3', 'p4'])
        self.assertEqual(op.validate(reopened), [])

    def test_page_split_merge_reassign_reorder_undo_preserves_content(self):
        d, group = self.group()
        new = update_output_pages(self.root, 'split', {'page_id': group[0]['id'], 'block_id': 'p2'})
        update_output_pages(self.root, 'assign', {'page_id': new, 'block_id': 'p1'})
        update_output_pages(self.root, 'merge', {'page_id': group[0]['id'], 'other_id': new})
        update_output_pages(self.root, 'reorder', {'page_id': group[0]['id'], 'direction': 'down'})
        undo_last(self.root)
        now = ensure_review_document(self.root)
        self.assertEqual(op.pages(now)[0]['id'], group[0]['id'])
        self.assertEqual(op.validate(now), [])
        self.assertEqual(now['blocks'], self.document['blocks'])
        self.assertEqual(now['accessibility_review'], fixture()['accessibility_review'])

    def test_structure_split_merge_exclude_restore_move(self):
        d, group = self.group()
        split_block(self.root, 'p2', 4)
        d = ensure_review_document(self.root)
        self.assertIn('p2-split-1', op.pages(d)[0]['block_ids'])
        merge_with_next(self.root, 'p2')
        d = ensure_review_document(self.root)
        self.assertNotIn('p2-split-1', op.pages(d)[0]['block_ids'])
        update_block(self.root, 'p2', {'review_status': 'excluded'})
        self.assertNotIn('p2', [b['id'] for b in op.page_document(ensure_review_document(self.root), group[0]['id'])['blocks']])
        update_block(self.root, 'p2', {'review_status': 'approved'})
        move_block(self.root, 'p2', 'start')
        d = ensure_review_document(self.root)
        self.assertEqual(op.pages(d)[0]['block_ids'][0], 'p2')
        self.assertEqual(op.validate(d), [])

    def test_invalid_arrangements_are_reported(self):
        for case in ['empty', 'unassigned', 'duplicate', 'missing', 'unsafe', 'collision', 'parent', 'cycle', 'article', 'reserved']:
            with self.subTest(case=case):
                d = copy.deepcopy(self.document)
                a = op.pages(d)[0]
                b = op.new_page('Second', ['p2'])
                a['block_ids'].remove('p2')
                op.pages(d).append(b)
                if case == 'empty': b['block_ids'] = []
                if case == 'unassigned': a['block_ids'].remove('p1')
                if case == 'duplicate': b['block_ids'].append('p1')
                if case == 'missing': b['block_ids'].append('gone')
                if case == 'unsafe': b['slug'] = '../../escape'
                if case == 'collision': b['slug'] = a['slug']
                if case == 'parent': b['parent'] = 'missing'
                if case == 'cycle': a['parent'], b['parent'] = b['id'], a['id']
                if case == 'article': b['type'], b['parent'] = 'post', a['id']
                if case == 'reserved': b['slug'] = 'contents'
                self.assertTrue(op.validate(d))

    def test_invalid_split_is_atomic(self):
        before = review_path(self.root).read_bytes()
        with self.assertRaises(ValueError):
            update_output_pages(self.root, 'split', {'page_id': self.first, 'block_id': 'h1'})
        self.assertEqual(before, review_path(self.root).read_bytes())

    def test_approval_invalidation_preserves_unaffected_page_and_content_decisions(self):
        d, group = self.group()
        for p in group:
            update_output_pages(self.root, 'approve', {'page_id': p['id'], 'note': 'Human review'})
        update_block(self.root, 'p1', {'content': 'Revised welcome'})
        d = ensure_review_document(self.root)
        self.assertEqual(op.pages(d)[0]['approval']['status'], 'needs_review')
        self.assertEqual(op.pages(d)[1]['approval']['status'], 'reviewed')
        self.assertEqual(d['accessibility_review'], fixture()['accessibility_review'])

    def test_slug_changes_resolve_links_and_invalidate_linking_page(self):
        d, group = self.group()
        update_output_pages(self.root, 'approve', {'page_id': group[1]['id']})
        update_output_pages(self.root, 'metadata', {'page_id': group[0]['id'], 'slug': 'new-name'})
        d = ensure_review_document(self.root)
        projected = op.page_document(d, group[1]['id'])
        self.assertEqual(projected['output_link_mappings'][0]['url'], 'new-name.html#p1')
        self.assertEqual(op.pages(d)[1]['approval']['status'], 'needs_review')

    def test_shared_footnotes_are_local_with_backlinks(self):
        d, group = self.group()
        all_ids = []
        for p in group:
            projected = op.page_document(d, p['id'])
            note = projected['footnotes'][0]
            self.assertEqual(len(note['references']), 1)
            all_ids.append(note['id'])
            rendered = html.render_document(projected)
            self.assertIn('href="#' + note['id'] + '"', rendered)
            self.assertIn('href="#' + note['references'][0]['id'] + '"', rendered)
        self.assertEqual(len(set(all_ids)), 2)

    def test_exports_manifest_xml_metadata_and_single_page(self):
        d, group = self.group()
        update_output_pages(self.root, 'metadata', {'page_id': group[1]['id'], 'title': 'Policy <& "', 'parent': group[0]['id'], 'navigation_order': 3})
        paths = export_pages(self.root)
        manifest = json.loads((self.root / 'output/pages/manifest.json').read_text())
        self.assertEqual(len(manifest['pages']), 2)
        self.assertTrue(manifest['complete_package'])
        xml = ET.parse(self.root / 'output/pages/publications.xml')
        items = xml.findall('./channel/item')
        self.assertEqual(items[1].findtext('{'+wxr.WP_NS+'}post_parent'), '1')
        self.assertEqual(items[1].findtext('{'+wxr.WP_NS+'}menu_order'), '3')
        self.assertEqual(items[1].findtext('title'), 'Policy <& "')
        self.assertEqual(items[1].findtext('{'+wxr.CONTENT_NS+'}encoded'), (self.root / 'output/pages/policy.gutenberg.html').read_text())
        self.assertIn('Policy &lt;&amp;', (self.root / 'output/pages/policy.html').read_text())
        self.assertEqual({i for p in manifest['pages'] for i in p['block_ids']}, {b['id'] for b in d['blocks']})
        for p in manifest['pages']:
            for file in p['files'].values(): self.assertTrue((self.root / 'output/pages' / file).is_file())
        export_pages(self.root, group[1]['id'], 'wsuwp')
        individual = json.loads((self.root / 'output/page-2/manifest.json').read_text())
        self.assertEqual(individual['pages'][0]['manual_parent_assignment'], group[0]['id'])
        self.assertFalse(individual['complete_package'])

    def test_unresolved_findings_not_converted_to_approved(self):
        d, group = self.group()
        update_output_pages(self.root, 'approve', {'page_id': group[0]['id']})
        update_block(self.root, 'p1', {'review_status': 'needs_review'})
        export_pages(self.root)
        manifest = json.loads((self.root / 'output/pages/manifest.json').read_text())
        self.assertGreater(manifest['pages'][0]['review']['accessibility']['summary']['unresolved'], 0)

    def test_incomplete_export_and_failure_preserve_state_and_previous_package(self):
        export_pages(self.root)
        before = (self.root / 'output/pages/manifest.json').read_bytes()
        state = review_path(self.root).read_bytes()
        with patch('pdf_to_web.output_page_export.gutenberg.render_document', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError): export_pages(self.root)
        self.assertEqual(before, (self.root / 'output/pages/manifest.json').read_bytes())
        self.assertEqual(state, review_path(self.root).read_bytes())
        update_output_pages(self.root, 'create', {'title': 'Empty'})
        with self.assertRaisesRegex(PdfToWebError, 'empty page'): export_pages(self.root)

    def test_deleted_blocks_visible_new_blocks_unassigned(self):
        d = ensure_review_document(self.root)
        d['blocks'] = d['blocks'][1:]
        d['blocks'].append({'id': 'new', 'type': 'paragraph', 'content': 'New'})
        save_review_document(self.root, d)
        errors = op.validate(ensure_review_document(self.root))
        self.assertTrue(any('missing block h1' in e for e in errors))
        self.assertTrue(any('Unassigned content: new' in e for e in errors))

    def test_image_caption_indivisible_and_table_semantics(self):
        d = ensure_review_document(self.root)
        d['blocks'] += [{'id': 'image', 'type': 'image', 'caption_block_id': 'caption', 'caption': 'Figure caption', 'alt': 'Meaningful figure', 'src': 'images/figure.png', 'provenance': {'source_page': 5}}, {'id': 'caption', 'type': 'caption', 'content': 'Figure caption', 'export_as_part_of_image': True}, {'id': 'table', 'type': 'table', 'rows': [['Header'], ['Value']], 'caption': 'Table caption', 'table_accessibility': {'header_row': True, 'reviewed': True}}]
        save_review_document(self.root, d)
        update_output_pages(self.root, 'assign', {'page_id': self.first, 'block_id': 'image'})
        update_output_pages(self.root, 'assign', {'page_id': self.first, 'block_id': 'table'})
        with self.assertRaisesRegex(ValueError, 'caption'):
            update_output_pages(self.root, 'split', {'page_id': self.first, 'block_id': 'caption'})
        projected = op.page_document(ensure_review_document(self.root), self.first)
        for rendered in [html.render_document(projected), gutenberg.render_document(projected)]:
            self.assertIn('scope="col"', rendered)
            self.assertIn('Meaningful figure', rendered)
        export_pages(self.root)
        manifest = json.loads((self.root / 'output/pages/manifest.json').read_text())
        self.assertEqual(manifest['manual_media_actions'][0]['block_id'], 'image')

    def test_nested_targets_and_unresolved_links(self):
        d = self.document
        d['blocks'][1]['runs'] = [{'type': 'link', 'text': 'Missing', 'url': '#absent'}]
        projected = op.page_document(d, self.first)
        self.assertEqual(projected['output_unresolved_targets'][0]['target'], 'absent')

    def test_nested_anchors_have_real_targets_in_both_serializers(self):
        d = self.document
        d['blocks'][1] = {'id': 'p1', 'type': 'list', 'children': [{'id': 'nested', 'type': 'list_item', 'content': 'Nested target'}]}
        d['blocks'][-1]['runs'][0]['url'] = '#nested'
        projected = op.page_document(d, self.first)
        from pdf_to_web.validation import validate_internal_links
        for markup in [html.render_document(projected), gutenberg.render_document(projected)]:
            self.assertIn('id="nested"', markup)
            self.assertTrue(validate_internal_links(markup)['valid'])

    def test_missing_footnote_body_blocks_export_without_corruption(self):
        d = ensure_review_document(self.root)
        d['footnotes'] = []
        save_review_document(self.root, d)
        before = review_path(self.root).read_bytes()
        with self.assertRaisesRegex(PdfToWebError, 'missing footnote'):
            export_pages(self.root)
        self.assertEqual(before, review_path(self.root).read_bytes())

    def test_excluded_footnote_reference_has_no_dangling_backlink(self):
        d, group = self.group()
        update_block(self.root, 'p1', {'review_status': 'excluded'})
        projected = op.page_document(ensure_review_document(self.root), group[0]['id'])
        self.assertEqual(projected['footnotes'], [])
        from pdf_to_web.validation import validate_internal_links
        self.assertTrue(validate_internal_links(html.render_document(projected))['valid'])

    def test_cross_page_structure_merge_retains_provenance_and_invalidates_both(self):
        d, group = self.group()
        update_output_pages(self.root, 'assign', {'page_id': group[1]['id'], 'block_id': 'p2'})
        for p in group:
            update_output_pages(self.root, 'approve', {'page_id': p['id']})
        # Bring adjacent paragraphs together in Structure while retaining distinct page assignments.
        move_block(self.root, 'p3', 'up')
        merge_with_next(self.root, 'p2')
        d = ensure_review_document(self.root)
        self.assertNotIn('p3', [i for p in op.pages(d) for i in p['block_ids']])
        p2 = next(b for b in d['blocks'] if b['id'] == 'p2')
        self.assertIn('Policy', p2['content'])
        self.assertEqual(op.source_ranges([p2]), [[3, 4]])
        self.assertEqual(op.pages(d)[1]['approval']['status'], 'needs_review')
        undo_last(self.root)
        self.assertIn('p3', [i for p in op.pages(ensure_review_document(self.root)) for i in p['block_ids']])

    def test_complex_visual_descriptions_export_and_moves_keep_images_together(self):
        d = ensure_review_document(self.root)
        d['blocks'].extend([{'id': 'im1', 'type': 'image', 'alt': 'Chart one', 'provenance': {'source_page': 6}}, {'id': 'im2', 'type': 'image', 'alt': 'Chart two', 'provenance': {'source_page': 6}}])
        d['review']['complex_visuals'] = [{'id': 'visual', 'source_page': 6, 'status': 'reclassified', 'accessibility': {'short_alt': 'Chart', 'long_description': 'The result rises from ten to twenty.'}}]
        save_review_document(self.root, d)
        second = update_output_pages(self.root, 'create', {'title': 'Results'})
        update_output_pages(self.root, 'assign', {'page_id': second, 'block_id': 'im1'})
        d = ensure_review_document(self.root)
        self.assertEqual(op.pages(d)[1]['block_ids'], ['im1', 'im2'])
        with self.assertRaisesRegex(ValueError, 'complex visual'):
            update_output_pages(self.root, 'split', {'page_id': second, 'block_id': 'im2'})
        projected = op.page_document(d, second)
        for markup in [html.render_document(projected), gutenberg.render_document(projected)]:
            self.assertIn('The result rises from ten to twenty.', markup)

    def test_page_hierarchy_changes_invalidate_descendant_approval(self):
        d, group = self.group()
        update_output_pages(self.root, 'metadata', {'page_id': group[1]['id'], 'parent': group[0]['id']})
        update_output_pages(self.root, 'approve', {'page_id': group[1]['id']})
        update_output_pages(self.root, 'metadata', {'page_id': group[0]['id'], 'title': 'New parent title'})
        self.assertEqual(op.pages(ensure_review_document(self.root))[1]['approval']['status'], 'needs_review')

    def test_xml_control_characters_fail_with_actionable_error(self):
        update_output_pages(self.root, 'metadata', {'page_id': self.first, 'title': 'Bad\x00title'})
        before = review_path(self.root).read_bytes()
        with self.assertRaisesRegex(PdfToWebError, 'control characters'):
            export_pages(self.root)
        self.assertEqual(before, review_path(self.root).read_bytes())

    def test_zip_failure_keeps_previous_complete_package(self):
        export_pages(self.root)
        previous = (self.root / 'output/pages/manifest.json').read_bytes()
        previous_zip = (self.root / 'output/pages.zip').read_bytes()
        with patch('pdf_to_web.output_page_export.zipfile.ZipFile', side_effect=OSError('Cannot write ZIP')):
            with self.assertRaisesRegex(OSError, 'Cannot write ZIP'):
                export_pages(self.root)
        self.assertEqual(previous, (self.root / 'output/pages/manifest.json').read_bytes())
        self.assertEqual(previous_zip, (self.root / 'output/pages.zip').read_bytes())

    def test_wsuwp_hero_retains_source_title_link_anchor(self):
        from pdf_to_web.project import load_project, save_project
        from pdf_to_web.wordpress_preview import render_gutenberg_preview
        d, group = self.group()
        d['blocks'][-1]['runs'][0]['url'] = '#h1'
        save_review_document(self.root, d)
        project = load_project(self.root)
        project['export']['hero']['enabled'] = True
        project['export']['wrap_in_section'] = True
        save_project(self.root, project)
        export_pages(self.root, profile='wsuwp')
        markup = (self.root / 'output/pages/handbook.gutenberg.html').read_text()
        self.assertIn('wp:wsuwp/hero', markup)
        self.assertIn('wp:wsuwp/section', markup)
        self.assertIn('id="h1"', markup)
        preview = render_gutenberg_preview(markup)
        self.assertFalse(preview.unsupported_blocks)
        self.assertIn('id="h1"', preview.html)


if __name__ == '__main__':
    unittest.main()
