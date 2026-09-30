import copy
import csv
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from pdf_to_web import image_drafts as d
from pdf_to_web.project import create_project
from pdf_to_web.review_state import original_path, ensure_review_document, update_block, undo_last, save_review_document
from pdf_to_web.exporters import html, gutenberg, wxr
from pdf_to_web.export import _local_image_path


class ImageDraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'project'
        create_project(self.root, 'Draft fixture')
        self.document = {'schema_version': 'pdf-to-web-normalized-v1', 'metadata': {'title': 'Guide'}, 'review': {'status': 'review_ready', 'issues': [], 'complex_visuals': [{'id': 'chart', 'source_page': 1, 'accessibility': {'long_description': 'Accepted long description'}}]}, 'blocks': [
            {'id': 'h', 'type': 'heading', 'level': 1, 'content': 'Guide'},
            {'id': 'p', 'type': 'paragraph', 'content': 'Verified context'},
            {'id': 'photo', 'type': 'image', 'src': 'images/photo.png', 'alt': 'Accepted ALT', 'caption': 'Accepted CAPTION', 'review': {'status': 'approved'}, 'provenance': {'source_page': 1}},
            {'id': 'ambiguous', 'type': 'image', 'src': None, 'alt': '', 'provenance': {'source_page': 1}},
            {'id': 'decoration', 'type': 'image', 'src': 'images/photo.png', 'decorative': True, 'caption': 'Legitimate caption'},
        ]}
        original_path(self.root).write_text(json.dumps(self.document))
        (self.root / 'extraction/raw/images/photo.png').write_bytes(b'fixture image bytes')
        for name in ('one.png', 'two.png'):
            (self.root / 'extraction/assets/images' / name).write_bytes(name.encode())
        (self.root / 'extraction/assets/manifest.json').write_text(json.dumps({'assets': [{'filename': name, 'source_page': 1} for name in ('one.png', 'two.png')]}))

    def read(self):
        return ensure_review_document(self.root)

    def entry(self, **kwargs):
        return d.prepare(self.root, ['photo'], **kwargs)[0]

    def response(self, entry, **changes):
        item = {k: entry[k] for k in d.IDENTITY} | {'alt': 'DRAFT ALT', 'caption': 'DRAFT CAPTION', 'long_description': 'DRAFT LONG', 'warnings': []}
        item.update(changes)
        return {'schema_version': d.EXCHANGE, 'responses': [item]}

    def imported(self):
        entry = self.entry()
        d.import_response(self.root, self.response(entry), commit=True)
        return entry

    def test_legacy_migration_is_empty_and_original_untouched(self):
        self.assertEqual(d.state(self.read())['requests'], {})
        self.assertNotIn('image_description_drafts', json.loads(original_path(self.root).read_text()))
        doc = self.read(); doc['image_description_drafts']['schema_version'] = 'future'
        with self.assertRaises(ValueError): d.ensure_state(doc)

    def test_draft_import_preserves_existing_text_and_null_fields(self):
        before = copy.deepcopy(self.read()['blocks'])
        entry = self.entry()
        preview = d.import_response(self.root, self.response(entry, long_description=None))
        self.assertEqual(len(preview['valid']), 1)
        self.assertIsNone(d.state(self.read())['requests'][entry['request_id']]['draft'])
        d.import_response(self.root, self.response(entry, long_description=None), commit=True)
        self.assertEqual(self.read()['blocks'], before)

    def test_apply_individual_field_persistence_and_undo(self):
        entry = self.imported()
        d.mutate(self.root, 'apply', {'block_id': 'photo', 'request_id': entry['request_id'], 'fields': ['alt']})
        block = d.image(self.read(), 'photo')
        self.assertEqual(block['alt'], 'DRAFT ALT')
        self.assertEqual(block['caption'], 'Accepted CAPTION')
        self.assertEqual(block['review']['status'], 'needs_review')
        d.mutate(self.root, 'apply', {'block_id': 'photo', 'request_id': entry['request_id'], 'fields': ['caption']})
        self.assertEqual(d.image(self.read(), 'photo')['caption'], 'DRAFT CAPTION')
        undo_last(self.root)
        self.assertEqual(d.image(self.read(), 'photo')['caption'], 'Accepted CAPTION')
        undo_last(self.root)
        self.assertEqual(d.image(self.read(), 'photo')['alt'], 'Accepted ALT')

    def test_needs_review_is_not_approved_by_application(self):
        update_block(self.root, 'photo', {'review_status': 'needs_review'})
        entry = self.imported()
        d.mutate(self.root, 'apply', {'block_id': 'photo', 'request_id': entry['request_id'], 'fields': ['alt']})
        self.assertEqual(d.image(self.read(), 'photo')['review']['status'], 'needs_review')

    def test_ambiguous_page_association_and_exported_asset(self):
        with self.assertRaisesRegex(ValueError, 'association'): d.prepare(self.root, ['ambiguous'])
        d.mutate(self.root, 'associate', {'block_id': 'ambiguous', 'asset_path': 'extraction/assets/images/two.png', 'purpose': 'Explain a chart', 'visual_id': 'chart'})
        entry = d.prepare(self.root, ['ambiguous'])[0]
        self.assertEqual(entry['asset_path'], 'extraction/assets/images/two.png')
        self.assertEqual(_local_image_path(self.root, d.image(self.read(), 'ambiguous')['src']).name, 'two.png')
        package = d.exchange_package(self.root, [entry])
        with zipfile.ZipFile(package) as archive:
            manifest = json.loads(archive.read('request.json'))
            self.assertEqual(archive.read(manifest['requests'][0]['image_file']), b'two.png')
            self.assertEqual(json.loads(archive.read('response-template.json'))['schema_version'], d.EXCHANGE)
            rows = list(csv.DictReader(io.StringIO(archive.read('review-sheet.csv').decode('utf-8-sig'))))
            self.assertEqual(rows[0]['image_file'], manifest['requests'][0]['image_file'])
            self.assertEqual(rows[0]['source_image_name'], 'two.png')
            self.assertEqual(rows[0]['block_id'], 'ambiguous')
            self.assertEqual(rows[0]['draft_alt'], '')
            self.assertEqual(rows[0]['draft_caption'], '')
            self.assertEqual(rows[0]['request_id'], entry['request_id'])

    def test_long_description_creates_image_specific_association(self):
        entry = self.imported()
        visual = d.visual_for(self.read(), d.image(self.read(), 'photo'))
        self.assertEqual(visual['source_block_id'], 'photo')
        self.assertEqual(visual['accessibility']['long_description'], 'DRAFT LONG')
        d.mutate(self.root, 'associate', {'block_id': 'photo', 'asset_path': 'extraction/raw/images/photo.png', 'visual_id': 'chart'})
        entry = self.entry(regenerate=True)
        d.import_response(self.root, self.response(entry), commit=True)
        d.mutate(self.root, 'apply', {'block_id': 'photo', 'request_id': entry['request_id'], 'fields': ['long_description']})
        self.assertEqual(self.read()['review']['complex_visuals'][0]['accessibility']['long_description'], 'DRAFT LONG')

    def test_errors_invalid_types_and_omitted_caption(self):
        entry = self.entry()
        for changes in ({'error': 'provider failed'}, {'alt': 'ERROR: provider failed'}, {'alt': 23}, {'alt': ''}, {'caption': {}}, {'warnings': 'uncertain'}, {'decorative': 'yes'}):
            self.assertEqual(len(d.import_response(self.root, self.response(entry, **changes))['findings']), 1)
        payload = self.response(entry, caption=None, long_description=None)
        d.import_response(self.root, payload, commit=True)
        with self.assertRaisesRegex(ValueError, 'omitted'):
            d.mutate(self.root, 'apply', {'block_id': 'photo', 'request_id': entry['request_id'], 'fields': ['caption']})
        self.assertEqual(d.image(self.read(), 'photo')['caption'], 'Accepted CAPTION')

    def test_duplicate_unknown_stale_and_cross_project_responses(self):
        entry = self.entry()
        payload = self.response(entry)
        payload['responses'] *= 2
        self.assertEqual(len(d.import_response(self.root, payload)['findings']), 2)
        for changes in ({'document_id': 'other'}, {'block_id': 'other'}, {'asset_hash': 'other'}, {'context_hash': 'other'}, {'request_id': 'other'}):
            self.assertTrue(d.import_response(self.root, self.response(entry, **changes))['findings'])
        update_block(self.root, 'p', {'content': 'Changed context'})
        self.assertTrue(d.import_response(self.root, self.response(entry))['findings'])
        newer = self.entry(regenerate=True)
        self.assertNotEqual(entry['cache_key'], newer['cache_key'])

    def test_preserve_manual_edits_rejections_and_success_on_rerun(self):
        entry = self.imported()
        edited = {'alt': 'Reviewer edited', 'caption': None, 'long_description': None}
        d.mutate(self.root, 'edit', {'block_id': 'photo', 'request_id': entry['request_id'], 'draft': edited})
        self.assertTrue(d.import_response(self.root, self.response(entry), commit=True)['findings'])
        self.assertEqual(self.entry()['draft']['alt'], 'Reviewer edited')
        self.assertEqual(self.entry(provider='different', model='different')['draft']['alt'], 'Reviewer edited')
        d.mutate(self.root, 'reject', {'block_id': 'photo', 'request_id': entry['request_id']})
        self.assertEqual(self.entry()['status'], 'rejected')
        self.assertNotEqual(self.entry(regenerate=True)['request_id'], entry['request_id'])

    def test_failure_retry_cancellation_and_late_response(self):
        entry = self.entry(provider='mock', model='vision')
        self.assertTrue(d.begin(self.root, entry))
        d.complete(self.root, entry, error=True)
        self.assertEqual(d.state(self.read())['requests'][entry['request_id']]['status'], 'failed')
        retried = self.entry(provider='mock', model='vision')
        self.assertNotEqual(retried['request_id'], entry['request_id'])
        d.begin(self.root, retried)
        d.mutate(self.root, 'cancel', {'block_id': 'photo', 'request_id': retried['request_id']})
        self.assertFalse(d.complete(self.root, retried, value=self.response(retried)['responses'][0]))
        self.assertEqual(d.state(self.read())['requests'][retried['request_id']]['status'], 'cancelled')

    def test_context_or_image_replacement_exclusion_and_deletion_during_generation(self):
        for change in ('context', 'asset', 'exclude', 'delete'):
            entry = self.entry(provider='mock', model='vision', regenerate=True)
            d.begin(self.root, entry)
            if change == 'context': update_block(self.root, 'p', {'content': 'New context'})
            elif change == 'asset': (self.root / 'extraction/raw/images/photo.png').write_bytes(b'replaced')
            elif change == 'exclude': update_block(self.root, 'photo', {'review_status': 'excluded'})
            else:
                doc = self.read(); doc['blocks'] = [b for b in doc['blocks'] if b['id'] != 'photo']; save_review_document(self.root, doc)
            d.complete(self.root, entry, value=self.response(entry)['responses'][0])
            self.assertIsNone(d.state(self.read())['requests'][entry['request_id']]['draft'])

    def test_default_selection_excludes_decorative_and_approved_and_excluded(self):
        self.assertEqual(d.selected(self.read()), ['ambiguous'])
        update_block(self.root, 'ambiguous', {'review_status': 'excluded'})
        self.assertEqual(d.selected(self.read()), [])

    def test_public_exports_only_accepted_fields(self):
        self.imported()
        doc = self.read()
        for output in (html.render_document(doc), gutenberg.render_document(doc), wxr.render_wxr([{'title': 'Guide', 'content': gutenberg.render_document(doc)}])):
            self.assertNotIn('DRAFT ALT', output)
            self.assertNotIn('DRAFT CAPTION', output)
            self.assertIn('Accepted ALT', output)
            self.assertNotIn('image_description_drafts', output)

    def test_mock_provider_success_and_invalid_identity(self):
        entry = self.entry(provider='mock', model='vision')
        d.begin(self.root, entry)
        d.complete(self.root, entry, value=self.response(entry, block_id='other')['responses'][0])
        self.assertEqual(d.state(self.read())['requests'][entry['request_id']]['status'], 'failed')
        retried = self.entry(provider='mock', model='vision')
        d.begin(self.root, retried)
        d.complete(self.root, retried, value=self.response(retried)['responses'][0])
        self.assertEqual(d.state(self.read())['requests'][retried['request_id']]['status'], 'ready')

    def test_empty_fields_populate_on_import_reopen_export_and_undo(self):
        update_block(self.root, 'photo', {'alt': '', 'caption': '', 'review_status': 'needs_review'})
        entry = self.entry()
        d.import_response(self.root, self.response(entry), commit=True)
        doc = self.read(); block = d.image(doc, 'photo')
        self.assertEqual((block['alt'], block['caption']), ('DRAFT ALT', 'DRAFT CAPTION'))
        self.assertEqual(block['review']['status'], 'needs_review')
        stored = d.state(doc)['requests'][entry['request_id']]
        self.assertFalse(d.stale(self.root, doc, stored))
        for output in (html.render_document(doc), gutenberg.render_document(doc), wxr.render_wxr([{'title': 'Guide', 'content': gutenberg.render_document(doc)}])):
            self.assertIn('DRAFT ALT', output)
            self.assertIn('DRAFT CAPTION', output)
            self.assertEqual(output.count('DRAFT LONG'), 1)
        update_block(self.root, 'photo', {'long_description': 'Reviewer description'})
        self.assertEqual(d.visual_for(self.read(), d.image(self.read(), 'photo'))['accessibility']['long_description'], 'Reviewer description')
        undo_last(self.root); undo_last(self.root)
        block = d.image(self.read(), 'photo')
        self.assertEqual(block['alt'], '')
        self.assertNotIn('complex_visual_id', block)
        self.assertIsNone(d.state(self.read())['requests'][entry['request_id']]['draft'])

    def test_reject_removes_untouched_population_and_preserves_author_edits(self):
        update_block(self.root, 'photo', {'alt': '', 'caption': ''})
        entry = self.imported()
        update_block(self.root, 'photo', {'caption': 'Reviewer caption'})
        d.mutate(self.root, 'reject', {'block_id': 'photo', 'request_id': entry['request_id']})
        block = d.image(self.read(), 'photo')
        self.assertEqual(block['alt'], '')
        self.assertEqual(block['caption'], 'Reviewer caption')
        self.assertEqual(d.visual_for(self.read(), block)['accessibility']['long_description'], '')
        undo_last(self.root)
        self.assertEqual(d.image(self.read(), 'photo')['alt'], 'DRAFT ALT')

    def test_generated_drafts_populate_empty_fields(self):
        update_block(self.root, 'photo', {'alt': '', 'caption': ''})
        entry = self.entry(provider='mock', model='vision')
        d.begin(self.root, entry)
        d.complete(self.root, entry, value=self.response(entry)['responses'][0])
        self.assertEqual(d.image(self.read(), 'photo')['alt'], 'DRAFT ALT')
        self.assertEqual(d.image(self.read(), 'photo')['review']['status'], 'needs_review')

    def test_existing_imports_can_fill_empty_fields_without_reimport(self):
        entry = self.entry()
        doc = self.read(); block = d.image(doc, 'photo'); block['alt'] = ''; block['caption'] = ''
        stored = d.state(doc)['requests'][entry['request_id']]
        stored.update(status='ready', draft=self.response(entry)['responses'][0])
        stored['current_context_hash'] = d.current_identity(self.root, doc, 'photo')[0]['context_hash']
        save_review_document(self.root, doc)
        d.mutate(self.root, 'populate', {})
        self.assertEqual(d.image(self.read(), 'photo')['caption'], 'DRAFT CAPTION')
        undo_last(self.root)
        self.assertEqual(d.image(self.read(), 'photo')['caption'], '')

    def test_description_stays_with_image_across_output_pages(self):
        from pdf_to_web import output_pages as op
        self.imported(); doc = self.read()
        doc['output_pages']['pages'] = [op.new_page('Photo', ['photo']), op.new_page('Other', ['h', 'p', 'ambiguous', 'decoration'])]
        photo = op.page_document(doc, doc['output_pages']['pages'][0]['id'])
        other = op.page_document(doc, doc['output_pages']['pages'][1]['id'])
        self.assertEqual(html.render_document(photo).count('DRAFT LONG'), 1)
        self.assertNotIn('DRAFT LONG', html.render_document(other))

    def test_asset_transmission_checks_hash_at_read_time(self):
        entry = self.entry()
        path = self.root / entry['asset_path']
        path.write_bytes(b'replaced before send')
        with self.assertRaisesRegex(ValueError, 'changed'):
            d.image_bytes(entry, path)

    def test_ready_draft_stales_after_context_edit_and_apply_is_blocked(self):
        entry = self.imported()
        update_block(self.root, 'p', {'content': 'Context changed'})
        self.assertTrue(d.stale(self.root, self.read(), d.state(self.read())['requests'][entry['request_id']]))
        with self.assertRaisesRegex(ValueError, 'Context changed'):
            d.mutate(self.root, 'apply', {'block_id': 'photo', 'request_id': entry['request_id'], 'fields': ['alt']})

    def test_path_escape_and_whole_selection_validation_leave_no_requests(self):
        with self.assertRaisesRegex(ValueError, 'association'):
            d.prepare(self.root, ['photo', 'ambiguous'])
        self.assertEqual(d.state(self.read())['requests'], {})
        (self.root / 'extraction/raw/images/link.png').symlink_to(self.root / 'project.json')
        with self.assertRaises(ValueError):
            d.confined(self.root, '../outside.png')

    def test_review_csv_preserves_text_without_spreadsheet_formulas(self):
        update_block(self.root, 'photo', {'caption': '=HYPERLINK("https://example.invalid", "source text")', 'alt': 'Text with, comma and "quotes"\nsecond line'})
        entry = self.entry()
        with zipfile.ZipFile(d.exchange_package(self.root, [entry])) as archive:
            rows = list(csv.DictReader(io.StringIO(archive.read('review-sheet.csv').decode('utf-8-sig'))))
            self.assertTrue(rows[0]['current_caption'].startswith("'="))
            self.assertEqual(rows[0]['current_alt'], 'Text with, comma and "quotes"\nsecond line')
            self.assertEqual(rows[0]['draft_alt'], '')
