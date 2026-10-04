"""Independent reviewed-content → media routing → draft Page XML journey."""
import csv
import hashlib
import io
import json
import re
import struct
import unittest
import xml.etree.ElementTree as ET
import zipfile
import zlib
from unittest.mock import patch

import test_image_draft_routes as routes
import test_unified_image_review as images
from pdf_to_web.exporters.wxr import CONTENT_NS, WP_NS
from pdf_to_web.media_mapping import apply_media_mapping
from pdf_to_web.publication import content_digest
from pdf_to_web.review_state import _set_status, ensure_review_document, review_progress, save_review_document, undo_last, update_block


class IndependentExportMediaJourneyTests(unittest.TestCase):
    setUp = routes.ImageDraftRouteTests.setUp
    image_model = images.UnifiedImageReviewTests.model

    def model(self, count=21):
        document = self.image_model(count)
        document['metadata']['title'] = 'Independent media journey'
        document['blocks'][0]['content'] = 'Independent media journey'
        for i, block in enumerate(document['blocks'][1:]):
            block['src'] = f'images/independent-{i}.png'
            block['caption'] = f'Caption {i}: Select Training & continue.'
            def chunk(kind, data):
                return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
            pixels = bytes([0, i * 11 % 256, i * 23 % 256, i * 37 % 256])
            png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
                   + chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b''))
            (self.root / 'extraction/raw' / block['src']).write_bytes(png)
        for visual in document['review']['complex_visuals']:
            visual['status'] = 'reviewed'
        document['blocks'].append({'id': 'table', 'type': 'table', 'rows': [['Training', 'Status'], ['CITI', 'Complete']],
            'caption': 'Training status', 'table_accessibility': {'header_row': True, 'header_column': False, 'reviewed': True},
            'review': {'status': 'approved'}})
        for block in document['blocks']:
            _set_status(block, 'approved')
        save_review_document(self.root, document)
        return ensure_review_document(self.root)

    def prepare(self):
        response = self.client.post('/api/media-export', headers=self.headers, json={'image_prefix': 'independent-journey-'})
        self.assertEqual(response.status_code, 200, response.text)
        return response

    def media_xml(self, omitted=()):
        rows = list(csv.DictReader(io.StringIO((self.root / 'output/wordpress/reports/media-mapping.csv').read_text())))
        xml = ET.Element('rss')
        channel = ET.SubElement(xml, 'channel')
        for i, row in enumerate(rows):
            if row['block_id'] in omitted:
                continue
            item = ET.SubElement(channel, 'item')
            ET.SubElement(item, f'{{{WP_NS}}}post_type').text = 'attachment'
            ET.SubElement(item, f'{{{WP_NS}}}post_id').text = str(900 + i)
            ET.SubElement(item, f'{{{WP_NS}}}attachment_url').text = 'https://example.test/uploads/' + row['asset_filename']
        return ET.tostring(xml, encoding='unicode')

    def match(self, omitted=()):
        return self.client.post('/api/media-mapping-wxr', headers=self.headers, json={'xml': self.media_xml(omitted)})

    def export(self):
        return self.client.post('/api/export', headers=self.headers,
            json={'target': 'wordpress-xml', 'profile': 'wsuwp', 'post_type': 'page', 'wrap_in_section': True})

    def xml_download(self, response):
        self.assertEqual(response.status_code, 200, response.text)
        download = next(d for d in response.json()['downloads'] if d['path'].endswith('.xml'))
        response = self.client.get(download['url'])
        self.assertEqual(response.status_code, 200, response.text)
        return ET.fromstring(response.content), download

    def test_full_21_image_media_match_keeps_reviews_and_exports_mapped_draft_wsuwp_page(self):
        self.model()
        prepared = self.prepare()
        download = next(d for d in prepared.json()['downloads'] if d['path'].endswith('.zip'))
        zipped = self.client.get(download['url'])
        self.assertEqual(zipped.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(zipped.content)) as archive:
            self.assertEqual(len(archive.namelist()), 21)
            self.assertIsNone(archive.testzip())
            rows = list(csv.DictReader(io.StringIO((self.root / 'output/wordpress/reports/media-mapping.csv').read_text())))
            blocks = {b['id']: b for b in ensure_review_document(self.root)['blocks']}
            for row in rows:
                data = archive.read(row['asset_filename'])
                self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))
                source = (self.root / 'extraction/raw' / blocks[row['block_id']]['src']).read_bytes()
                self.assertEqual(hashlib.sha256(data).digest(), hashlib.sha256(source).digest())
        before = ensure_review_document(self.root)
        matched = self.match()
        self.assertEqual(matched.status_code, 200, matched.text)
        self.assertEqual((matched.json()['matched'], matched.json()['remaining']), (21, 0))
        after = ensure_review_document(self.root)
        self.assertEqual(review_progress(after)['pending_tasks'], 0)
        self.assertEqual([b['review'] for b in after['blocks']], [b['review'] for b in before['blocks']])
        self.assertEqual(after['review']['complex_visuals'], before['review']['complex_visuals'])
        xml, _ = self.xml_download(self.export())
        item = xml.find('./channel/item')
        self.assertEqual(item.findtext(f'{{{WP_NS}}}post_type'), 'page')
        self.assertEqual(item.findtext(f'{{{WP_NS}}}status'), 'draft')
        self.assertEqual(item.findtext('title'), 'Independent media journey')
        body = item.findtext(f'{{{CONTENT_NS}}}encoded')
        self.assertIn('wp:wsuwp/section', body)
        self.assertNotIn('data-pdf-to-web-media="unresolved"', body)
        self.assertNotIn('src="images/', body)
        self.assertIn('<th scope="col">Training</th>', body)
        image_attributes = [json.loads(raw) for raw in re.findall(r'<!-- wp:image (\{.*?\}) -->', body)]
        self.assertEqual([attrs['id'] for attrs in image_attributes], list(range(900, 921)))
        for i, block in enumerate(after['blocks'][1:22]):
            self.assertIn(block['wordpress_url'], body)
            self.assertIn(f'wp-image-{900 + i}', body)
            self.assertIn(f'Image purpose {i}', body)
            self.assertIn(f'Caption {i}: Select Training &amp; continue.', body)
            self.assertIn(f'Complete description {i}', body)

    def test_mapping_changes_routing_digest_but_not_reviewed_content_digest(self):
        before = self.model(2)
        old_digest = content_digest(before['blocks'][1])
        apply_media_mapping(self.root, 'block_id,wordpress_url,wordpress_attachment_id\nimage-0,https://example.test/mapped.png,321\n')
        after = ensure_review_document(self.root)
        self.assertEqual(content_digest(after['blocks'][1]), old_digest)
        self.assertEqual(after['blocks'][1]['review'], before['blocks'][1]['review'])
        self.assertEqual(review_progress(after)['pending_tasks'], 0)

    def test_mapping_preserves_pending_decisions_and_never_approves_actual_content_edits(self):
        self.model(2)
        update_block(self.root, 'image-0', {'caption': 'A real authoring edit.'})
        before = ensure_review_document(self.root)
        self.prepare()
        self.assertEqual(self.match().status_code, 200)
        after = ensure_review_document(self.root)
        self.assertEqual(after['blocks'][1]['review'], before['blocks'][1]['review'])
        self.assertEqual(after['review']['complex_visuals'][0], before['review']['complex_visuals'][0])
        self.assertEqual(self.export().status_code, 400)

    def test_successful_export_then_mapping_change_rejects_stale_download_without_unreviewing(self):
        self.model(2)
        self.prepare()
        _, old = self.xml_download(self.export())
        self.assertEqual(self.match().status_code, 200)
        self.assertEqual(review_progress(ensure_review_document(self.root))['pending_tasks'], 0)
        self.assertEqual(self.client.get(old['url']).status_code, 409)
        xml, _ = self.xml_download(self.export())
        self.assertIn('https://example.test/uploads/', xml.findtext(f'./channel/item/{{{CONTENT_NS}}}encoded'))

    def test_mapping_undo_restores_routing_and_retains_manual_approvals(self):
        self.model(2)
        self.prepare()
        before = ensure_review_document(self.root)
        self.assertEqual(self.match().status_code, 200)
        undo_last(self.root)
        after = ensure_review_document(self.root)
        self.assertEqual(after['blocks'], before['blocks'])
        self.assertEqual(after['review']['complex_visuals'], before['review']['complex_visuals'])

    def test_failed_matching_writes_nothing_and_valid_retry_succeeds(self):
        self.model(2)
        self.prepare()
        before = (self.root / 'review/current.json').read_bytes()
        bad = self.client.post('/api/media-mapping-wxr', headers=self.headers, json={'xml': '<rss><broken>'})
        self.assertEqual(bad.status_code, 400)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)
        self.assertEqual(self.match().status_code, 200)
        self.xml_download(self.export())

    def test_export_failure_and_retry_do_not_change_authored_content_or_review(self):
        self.model(2)
        self.prepare()
        self.assertEqual(self.match().status_code, 200)
        before = ensure_review_document(self.root)
        with patch('pdf_to_web.web.export_project', side_effect=OSError('Independent export failure.')):
            self.assertEqual(self.export().status_code, 400)
        self.xml_download(self.export())
        after = ensure_review_document(self.root)
        self.assertEqual(after['blocks'], before['blocks'])
        self.assertEqual(after['review']['complex_visuals'], before['review']['complex_visuals'])

    def test_real_alt_edit_after_mapping_blocks_old_download_and_new_export(self):
        self.model(2)
        self.prepare()
        self.assertEqual(self.match().status_code, 200)
        _, download = self.xml_download(self.export())
        update_block(self.root, 'image-0', {'alt': 'A different purpose.'})
        self.assertEqual(self.client.get(download['url']).status_code, 409)
        self.assertEqual(self.export().status_code, 400)

    def test_already_invalidated_mapping_record_is_not_approved_on_reopen(self):
        from pdf_to_web import publication
        self.model(2)
        digest = publication.content_digest
        def old_mapping_inclusive_digest(block, **unused):
            return digest(block, include_media_mapping=True)
        with patch.object(publication, 'content_digest', old_mapping_inclusive_digest):
            apply_media_mapping(self.root, 'block_id,wordpress_url\nimage-0,https://example.test/legacy.png\n')
        before = (self.root / 'review/current.json').read_bytes()
        reopened = ensure_review_document(self.root)
        self.assertEqual(reopened['blocks'][1]['review']['status'], 'needs_review')
        self.assertEqual(reopened['review']['complex_visuals'][0]['status'], 'reviewed')
        self.assertEqual(review_progress(reopened)['pending_tasks'], 1)
        self.assertEqual(self.client.get('/export').status_code, 200)
        self.assertEqual(self.export().status_code, 400)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def legacy_approved_mapping(self):
        document = self.model(2)
        block = document['blocks'][1]
        block.update(wordpress_url='https://example.test/legacy-approved.png', wordpress_attachment_id=444,
                     wordpress_media={'url': 'https://example.test/legacy-approved.png', 'attachment_id': 444})
        block['review']['content_sha256'] = content_digest(block, include_media_mapping=True)
        save_review_document(self.root, document)
        return ensure_review_document(self.root)

    def test_existing_approved_mapping_legacy_hash_reads_without_rewrite(self):
        document = self.legacy_approved_mapping()
        self.assertNotEqual(document['blocks'][1]['review']['content_sha256'], content_digest(document['blocks'][1]))
        before = (self.root / 'review/current.json').read_bytes()
        for route in ('/document', '/structure', '/accessibility', '/export'):
            self.assertEqual(self.client.get(route).status_code, 200)
        reopened = ensure_review_document(self.root)
        self.assertEqual(reopened['blocks'][1]['review'], document['blocks'][1]['review'])
        self.assertEqual(review_progress(reopened)['pending_tasks'], 0)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_remap_legacy_approved_record_keeps_timestamp_and_normalizes_verified_hash(self):
        before = self.legacy_approved_mapping()
        old = before['blocks'][1]
        apply_media_mapping(self.root, 'block_id,wordpress_url,wordpress_attachment_id\nimage-0,https://example.test/remapped.png,555\n')
        after = ensure_review_document(self.root)
        block = after['blocks'][1]
        self.assertEqual(block['review']['status'], 'approved')
        self.assertEqual(block['review']['updated_at'], old['review']['updated_at'])
        self.assertEqual(block['review']['content_sha256'], content_digest(block))
        self.assertEqual((block['alt'], block['caption'], block['src']), (old['alt'], old['caption'], old['src']))
        self.assertEqual(after['review']['complex_visuals'], before['review']['complex_visuals'])
        self.assertEqual(review_progress(after)['pending_tasks'], 0)

    def test_media_undo_then_same_xml_rematches_21_despite_filled_report(self):
        self.model()
        self.prepare()
        xml = self.media_xml()
        first = self.client.post('/api/media-mapping-wxr', headers=self.headers, json={'xml': xml})
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json()['matched'], 21)
        before = ensure_review_document(self.root)
        undone = self.client.post('/api/media-export/undo', headers=self.headers, json={})
        self.assertEqual(undone.status_code, 200, undone.text)
        self.assertEqual(undone.json()['remaining'], 21)
        rows = list(csv.DictReader(io.StringIO((self.root / 'output/wordpress/reports/media-mapping.csv').read_text())))
        self.assertTrue(all(row['wordpress_url'] for row in rows))
        retry = self.client.post('/api/media-mapping-wxr', headers=self.headers, json={'xml': xml})
        self.assertEqual(retry.status_code, 200, retry.text)
        self.assertEqual((retry.json()['matched'], retry.json()['remaining']), (21, 0))
        after = ensure_review_document(self.root)
        self.assertEqual(review_progress(after)['pending_tasks'], 0)
        self.assertEqual([b['review'] for b in after['blocks']], [b['review'] for b in before['blocks']])
        self.assertEqual(after['review']['complex_visuals'], before['review']['complex_visuals'])
        artifact, _ = self.xml_download(self.export())
        body = artifact.findtext(f'./channel/item/{{{CONTENT_NS}}}encoded')
        self.assertEqual(artifact.findtext(f'./channel/item/{{{WP_NS}}}post_type'), 'page')
        self.assertEqual(artifact.findtext(f'./channel/item/{{{WP_NS}}}status'), 'draft')
        attrs = [json.loads(raw) for raw in re.findall(r'<!-- wp:image (\{.*?\}) -->', body)]
        self.assertEqual([a['id'] for a in attrs], list(range(900, 921)))
        self.assertNotIn('data-pdf-to-web-media="unresolved"', body)

    def test_reuploaded_same_url_media_refreshes_21_ids_and_exports_without_reapproval(self):
        self.model()
        self.prepare()
        self.assertEqual(self.match().status_code, 200)
        before = ensure_review_document(self.root)
        xml = ET.fromstring(self.media_xml())
        for node in xml.iter(f'{{{WP_NS}}}post_id'):
            node.text = str(int(node.text) + 1000)
        paths = [self.root / 'project.json', self.root / 'review/current.json',
                 *sorted((self.root / 'review/revisions').glob('*.json'))]
        saved = {p: p.read_bytes() for p in paths}
        preview = self.client.post('/api/media-mapping-wxr', headers=self.headers,
                                   json={'xml': ET.tostring(xml, encoding='unicode')})
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertEqual((preview.json()['matched'], preview.json()['mapped'], preview.json()['refresh_required']), (21, 0, 21))
        self.assertEqual(len(preview.json()['refreshable_images']), 21)
        self.assertEqual({p: p.read_bytes() for p in paths}, saved)
        response = self.client.post('/api/media-mapping-wxr', headers=self.headers,
                                    json={'xml': ET.tostring(xml, encoding='unicode'), 'refresh_existing': True})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual((response.json()['matched'], response.json()['mapped']), (21, 21))
        self.assertEqual((response.json()['unchanged'], response.json()['existing_kept']), (0, 0))
        after = ensure_review_document(self.root)
        self.assertEqual([b['review'] for b in after['blocks']], [b['review'] for b in before['blocks']])
        self.assertEqual(after['review']['complex_visuals'], before['review']['complex_visuals'])
        self.assertEqual(review_progress(after)['pending_tasks'], 0)
        images = [b for b in after['blocks'] if b['type'] == 'image']
        self.assertEqual([b['wordpress_attachment_id'] for b in images], list(range(1900, 1921)))
        self.assertEqual([b['wordpress_url'] for b in images], [b['wordpress_url'] for b in before['blocks'] if b['type'] == 'image'])
        artifact, _ = self.xml_download(self.export())
        body = artifact.findtext(f'./channel/item/{{{CONTENT_NS}}}encoded')
        attrs = [json.loads(raw) for raw in re.findall(r'<!-- wp:image (\{.*?\}) -->', body)]
        self.assertEqual([a['id'] for a in attrs], list(range(1900, 1921)))
        self.assertEqual(artifact.findtext(f'./channel/item/{{{WP_NS}}}status'), 'draft')
        self.assertEqual(artifact.findtext(f'./channel/item/{{{WP_NS}}}post_type'), 'page')
        rows = list(csv.DictReader(io.StringIO((self.root / 'output/wordpress/reports/media-mapping.csv').read_text())))
        self.assertEqual([int(r['wordpress_attachment_id']) for r in rows], list(range(1900, 1921)))
        undo_last(self.root)
        self.assertEqual(ensure_review_document(self.root)['blocks'], before['blocks'])

    def test_repeat_current_xml_confirms_matches_without_saving_another_revision(self):
        self.model(2)
        self.prepare()
        self.assertEqual(self.match().status_code, 200)
        paths = [self.root / 'project.json', self.root / 'review/current.json',
                 *sorted((self.root / 'review/revisions').glob('*.json'))]
        saved = {p: p.read_bytes() for p in paths}
        response = self.match()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual((response.json()['matched'], response.json()['mapped'], response.json()['unchanged']), (2, 0, 2))
        self.assertEqual({p: p.read_bytes() for p in paths}, saved)

    def test_current_mapping_is_authoritative_over_filled_report_and_different_xml(self):
        self.model(2)
        self.prepare()
        self.assertEqual(self.match().status_code, 200)
        before = ensure_review_document(self.root)
        mapping = self.root / 'output/wordpress/reports/media-mapping.csv'
        reader = csv.DictReader(io.StringIO(mapping.read_text()))
        fields, rows = reader.fieldnames, list(reader)
        for row in rows:
            row['wordpress_url'] = 'https://stale.example.test/report.png'
            row['wordpress_attachment_id'] = '99999'
            row['alt_text'], row['caption'] = 'Stale report alt', 'Stale report caption'
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        mapping.write_text(stream.getvalue())
        xml = self.media_xml().replace('https://example.test/uploads/', 'https://different.example.test/uploads/')
        response = self.client.post('/api/media-mapping-wxr', headers=self.headers, json={'xml': xml, 'refresh_existing': True})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual((response.json()['matched'], response.json()['remaining']), (0, 0))
        after = ensure_review_document(self.root)
        self.assertEqual(after['blocks'], before['blocks'])
        self.assertEqual(after['review']['complex_visuals'], before['review']['complex_visuals'])
        refreshed = list(csv.DictReader(io.StringIO(mapping.read_text())))
        images_by_id = {b['id']: b for b in before['blocks'] if b['type'] == 'image'}
        for row in refreshed:
            block = images_by_id[row['block_id']]
            self.assertEqual(row['wordpress_url'], block['wordpress_url'])
            self.assertEqual(int(row['wordpress_attachment_id']), block['wordpress_attachment_id'])
            self.assertEqual((row['alt_text'], row['caption']), (block['alt'], block['caption']))
