"""Diagnostic counts explain review ownership without changing decisions."""
import copy
import re
import unittest

import test_image_draft_routes as routes
from pypdf import PdfWriter
from review_helpers import approve_publication_fixture
from pdf_to_web.accessibility import assess_document
from pdf_to_web.project import load_project, save_project
from pdf_to_web.publication import readiness_findings
from pdf_to_web.review_state import ensure_review_document, save_review_document, update_block, undo_last


class DiagnosticSummaryTests(unittest.TestCase):
    def setUp(self):
        routes.ImageDraftRouteTests.setUp(self)
        # Diagnostic recovery links need a real, available source, unlike the
        # image-drafting fixture from which the review setup is reused.
        source = self.root / 'source/diagnostic-fixture.pdf'
        writer = PdfWriter()
        for _ in range(12):
            writer.add_blank_page(width=612, height=792)
        writer.write(source)
        project = load_project(self.root)
        project['source'].update(path=str(source.relative_to(self.root)), page_count=12)
        save_project(self.root, project)

    def flagged_document(self):
        document = ensure_review_document(self.root)
        document['blocks'] = [
            {'id': f'block-{n}', 'type': 'heading' if n in (1, 53) else 'paragraph',
             'content': 'Example Course Certificate of Completion' if n == 53 else f'Synthetic content {n}',
             **({'level': 1 if n == 1 else 2} if n in (1, 53) else {}),
             'provenance': {'source_page': 12 if n == 53 else 1},
             'review': {'status': 'needs_review' if n == 53 else 'unreviewed',
                        'issues': [{'code': 'additional_h1_demoted', 'message': 'An additional H1 was changed to H2; verify the source heading hierarchy.'}] if n == 53 else []}}
            for n in range(1, 55)]
        document['review'].update(status='needs_review', complex_visuals=[], issues=[
            {'code': 'block_review_required', 'message': '1 block(s) require review before export.', 'block_ids': ['block-53']}])
        document['output_pages']['pages'][0]['block_ids'] = [b['id'] for b in document['blocks']]
        save_review_document(self.root, document)
        return ensure_review_document(self.root)

    def test_54_tasks_and_overlapping_diagnostic_share_one_summary_with_exact_cause(self):
        self.flagged_document()
        before = (self.root / 'review/current.json').read_bytes()
        screen = self.client.get('/document').text
        summary = re.search(r'<section class="document-review-progress".*?</section>', screen, re.S).group()
        self.assertIn('Pending 54 review tasks', summary)
        self.assertIn('54 block reviews · 0 description reviews', summary)
        self.assertIn('1 unresolved diagnostic issue.', summary)
        self.assertIn('1 affected block review is already included', summary)
        self.assertIn('An additional H1 was changed to H2', summary)
        self.assertIn('href="/structure#block-block-53"', summary)
        self.assertIn('Source page 12', summary.replace('source page', 'Source page'))
        self.assertNotIn('Pending 55', screen)
        self.assertNotIn('document-status-heading', screen)
        self.assertEqual((self.root / 'review/current.json').read_bytes(), before)

    def test_accessibility_diagnostic_shows_same_cause_impact_and_target_once(self):
        self.flagged_document()
        screen = self.client.get('/accessibility').text
        card = re.search(r'<article id="finding-diagnostic:block_review_required:document".*?</article>', screen, re.S).group()
        self.assertIn('An additional H1 was changed to H2', card)
        self.assertIn('does not add another block review', card)
        self.assertEqual(card.count('href="/structure#block-block-53"'), 1)
        self.assertNotIn('Review diagnostic in Accessibility', card)

    def test_fresh_manual_review_resolves_note_and_undo_restores_it(self):
        document = self.flagged_document()
        original_issues = copy.deepcopy(document['review']['issues'])
        self.assertTrue(any(i['block_id'] == 'block-53' for i in readiness_findings(document)))
        update_block(self.root, 'block-53', {'review_status': 'approved'})
        current = ensure_review_document(self.root)
        diagnostic = next(i for i in assess_document(current)['items'] if i['category'] == 'diagnostics')
        self.assertEqual(diagnostic['status'], 'resolved')
        self.assertNotIn('unresolved diagnostic issue', self.client.get('/document').text)
        self.assertIn('Resolved extraction note', self.client.get('/accessibility').text)
        self.assertEqual(current['review']['issues'], original_issues)
        undo_last(self.root)
        self.assertIn('1 unresolved diagnostic issue.', self.client.get('/document').text)

    def test_document_wide_warning_explains_scope_recovery_and_truthful_export_impact(self):
        document = self.flagged_document()
        document['review']['issues'] = [{'code': 'incomplete_text_recovery', 'message': 'Only 60% of embedded source text was recovered.'}]
        save_review_document(self.root, document)
        approve_publication_fixture(self.root)
        self.assertEqual(readiness_findings(ensure_review_document(self.root)), [])
        screen = self.client.get('/document').text
        self.assertIn('document-wide extraction check; no single block was identified', screen)
        self.assertIn('Some source text may be missing', screen)
        self.assertIn('does not independently block publication', screen)
        self.assertIn('href="/source.pdf"', screen)
        self.assertIn('href="/accessibility#finding-diagnostic%3Aincomplete_text_recovery%3Adocument"', screen)
        self.assertNotIn('pdftoppm', screen)
        self.assertNotIn('Pillow', screen)

    def test_page_specific_warning_links_to_real_pdf_page_without_inventing_block(self):
        document = self.flagged_document()
        document['review']['issues'] = [{'code': 'complex_visual_text_loss', 'page': 2, 'message': 'Only some source-page text was recovered.'}]
        save_review_document(self.root, document)
        screen = self.client.get('/document').text
        self.assertIn('source page 2, but no single block', screen)
        self.assertIn('href="/source.pdf#page=2"', screen)
        self.assertNotIn('href="/structure#block-block-53"', screen)

    def test_missing_source_has_recovery_guidance_without_a_broken_link(self):
        document = self.flagged_document()
        document['review']['issues'] = [{'code': 'incomplete_page_coverage', 'message': 'Some pages were not extracted.'}]
        save_review_document(self.root, document)
        (self.root / 'source/diagnostic-fixture.pdf').unlink()
        screen = self.client.get('/document').text
        self.assertNotIn('href="/source.pdf"', screen)
        self.assertIn('Source PDF is unavailable', screen)
        self.assertIn('restore the project’s source copy', screen)

    def test_stale_reference_does_not_invent_a_target(self):
        document = self.flagged_document()
        document['review']['issues'][0]['block_ids'] = ['not-present']
        save_review_document(self.root, document)
        screen = self.client.get('/document').text
        self.assertIn('referenced content is no longer available', screen)
        self.assertNotIn('/structure#block-not-present', screen)

    def test_blocked_conversion_keeps_recovery_and_publication_gate_visible(self):
        document = self.flagged_document()
        document['review'].update(status='conversion_blocked', issues=[{'code': 'invalid_text_characters', 'message': 'Extracted text contains replacement characters.'}])
        save_review_document(self.root, document)
        screen = self.client.get('/document').text
        self.assertIn('Conversion blocked', screen)
        self.assertIn('recover the extraction if conversion is blocked', screen)
        self.assertTrue(any(i['code'] == 'conversion_blocked' for i in readiness_findings(ensure_review_document(self.root))))

    def test_duplicate_notes_do_not_add_multiple_reviews_and_text_is_escaped(self):
        document = self.flagged_document()
        document['review']['issues'].append({'code': 'missing_heading_levels', 'message': '<script>alert(1)</script>', 'block_ids': ['block-53']})
        save_review_document(self.root, document)
        screen = self.client.get('/document').text
        self.assertIn('Pending 54 review tasks', screen)
        self.assertIn('2 unresolved diagnostic issues.', screen)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', screen)
        self.assertNotIn('<script>alert(1)</script>', screen)

    def test_nested_flag_targets_its_existing_review_owner(self):
        document = self.flagged_document()
        document['blocks'][1].update(type='list', children=[{'id': 'nested-child', 'type': 'list_item', 'content': 'Nested source', 'review': {'status': 'needs_review', 'issues': [{'message': 'Nested source requires inspection.'}]}}])
        document['review']['issues'][0]['block_ids'] = ['nested-child']
        save_review_document(self.root, document)
        screen = self.client.get('/document').text
        self.assertIn('href="/structure#block-block-2"', screen)
        self.assertIn('Nested source requires inspection.', screen)
        self.assertNotIn('href="/structure#block-nested-child"', screen)
        update_block(self.root, 'block-2', {'review_status': 'approved'})
        diagnostic = next(i for i in assess_document(ensure_review_document(self.root))['items'] if i['category'] == 'diagnostics')
        self.assertEqual(diagnostic['status'], 'resolved')
        undo_last(self.root)
        self.assertIn('1 unresolved diagnostic issue.', self.client.get('/document').text)

    def test_missing_reference_does_not_resolve_with_the_remaining_approved_block(self):
        document = self.flagged_document()
        document['review']['issues'][0]['block_ids'].append('missing-content')
        save_review_document(self.root, document)
        update_block(self.root, 'block-53', {'review_status': 'approved'})
        diagnostic = next(i for i in assess_document(ensure_review_document(self.root))['items'] if i['category'] == 'diagnostics')
        self.assertEqual(diagnostic['status'], 'unresolved')
        screen = self.client.get('/document').text
        self.assertIn('Some referenced content is no longer available', screen)
        self.assertIn('href="/structure#block-block-53"', screen)
        self.assertNotIn('href="/structure#block-missing-content"', screen)
