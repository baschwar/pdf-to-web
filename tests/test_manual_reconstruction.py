"""Page holds restore saved decisions exactly and never certify missing content."""
import copy
import unittest
import test_image_draft_routes as fixtures
from pdf_to_web import manual_reconstruction as mr, output_pages as op
from pdf_to_web.image_review import review_token
from pdf_to_web.review_state import ensure_review_document, update_block, undo_last, save_review_document
from pdf_to_web.project import load_project, save_project
from pdf_to_web.publication import readiness_findings
from pdf_to_web.accessibility import assess_document


class ManualReconstructionTests(unittest.TestCase):
    setUp = fixtures.ImageDraftRouteTests.setUp

    def read(self):
        return ensure_review_document(self.root)

    def toggle(self, enabled, page=1):
        return mr.toggle(self.root, page, enabled, review_token(self.read()))

    def prepare_pages(self):
        project = load_project(self.root)
        project['source']['page_count'] = 2
        save_project(self.root, project)
        document = self.read()
        for block in document['blocks']:
            block.setdefault('provenance', {})['source_page'] = 1
        document['blocks'].append({'id':'second', 'type':'paragraph', 'content':'Second page', 'provenance':{'source_page':2}, 'review':{'status':'needs_review'}})
        document['blocks'].append({'id':'shared', 'type':'paragraph', 'content':'Shared pages', 'provenance':{'source_page':1, 'merged_source_pages':[1,2]}, 'review':{'status':'needs_review'}})
        document['output_pages']['pages'] = [op.new_page('First', [str(b['id']) for b in document['blocks'] if b['id']!='second']), op.new_page('Second',['second'])]
        save_review_document(self.root, document)

    def test_restore_prior_approvals_exclusions_content_and_undo(self):
        self.prepare_pages()
        update_block(self.root,'ambiguous',{'review_status':'excluded'})
        before = copy.deepcopy(self.read()['blocks'])
        held = self.toggle(True)
        self.assertEqual(held['blocks'][2]['review']['status'],'excluded')
        self.assertTrue(mr.marked_pages(held))
        self.assertEqual(self.toggle(False)['blocks'],before)
        self.assertFalse(mr.marked_pages(self.read()))
        undo_last(self.root)
        self.assertTrue(mr.marked_pages(self.read()))
        undo_last(self.root)
        self.assertEqual(self.read()['blocks'],before)

    def test_shared_blocks_are_retained_and_separate_holds_reverse_independently(self):
        self.prepare_pages()
        before = copy.deepcopy(self.read()['blocks'])
        self.toggle(True)
        second = self.toggle(True,2)
        self.assertEqual(next(b for b in second['blocks'] if b['id']=='shared'),before[-1])
        self.assertIn('shared',mr.marked_pages(second)['1']['shared_block_ids'])
        self.toggle(False,1)
        self.assertIn('2',mr.marked_pages(self.read()))
        self.assertEqual(self.toggle(False,2)['blocks'],before)

    def test_repeat_toggle_is_idempotent_and_stale_toggle_changes_nothing(self):
        self.prepare_pages()
        stale = review_token(self.read())
        self.toggle(True)
        before = (self.root/'review/current.json').read_bytes()
        self.toggle(True)
        self.assertEqual((self.root/'review/current.json').read_bytes(),before)
        with self.assertRaisesRegex(ValueError,'project changed'):
            mr.toggle(self.root,1,False,stale)
        self.assertEqual((self.root/'review/current.json').read_bytes(),before)

    def test_managed_block_edits_rejected_and_conflicted_restore_is_atomic(self):
        self.prepare_pages();self.toggle(True)
        with self.assertRaisesRegex(ValueError,'held for manual'):
            update_block(self.root,'photo',{'alt':'Replacement'})
        document = self.read()
        next(b for b in document['blocks'] if b['id']=='photo')['alt']='External change'
        save_review_document(self.root,document)
        before=(self.root/'review/current.json').read_bytes()
        with self.assertRaisesRegex(ValueError,'no partial restoration'):
            self.toggle(False)
        self.assertEqual((self.root/'review/current.json').read_bytes(),before)

    def test_hold_remains_unresolved_in_publication_and_accessibility(self):
        self.prepare_pages();self.toggle(True)
        document=self.read()
        self.assertTrue(any(i['code']=='manual_reconstruction_pending' for i in readiness_findings(document)))
        item=next(i for i in assess_document(document)['items'] if i['id']=='manual-reconstruction:1')
        self.assertEqual(item['status'],'unresolved');self.assertFalse(item['decision_allowed'])
        self.assertNotIn('id="structure-review-complete"',self.client.get('/structure').text)
        from pdf_to_web.export import export_project
        from pdf_to_web.errors import PdfToWebError
        with self.assertRaisesRegex(PdfToWebError, 'manual reconstruction'):
            export_project(self.root, 'html')

    def test_placeholder_survives_regroup_reorder_and_removal_preserves_other_pages(self):
        self.prepare_pages();before=copy.deepcopy(op.pages(self.read()))
        self.toggle(True);document=self.read()
        placeholder=next(p for p in op.pages(document) if p.get('manual_reconstruction_source_page'))
        identity=placeholder['id']
        self.assertEqual(op.status(document, identity)['structural'], 'needs_review')
        self.assertEqual(op.status(document, identity)['source_ranges'], [[1,1]])
        self.assertEqual(len(op.pages(document)),3)
        op.mutate(document,'reorder',{'page_id':identity,'direction':'up'})
        save_review_document(self.root,document)
        self.assertEqual(op.pages(self.read())[0]['id'],identity)
        self.toggle(False)
        self.assertEqual({p['id']:p['block_ids'] for p in op.pages(self.read())},{p['id']:p['block_ids'] for p in before})
        self.toggle(True);document=self.read()
        op.mutate(document,'single_page',{'page_id':before[0]['id']})
        save_review_document(self.root,document)
        self.assertEqual(len([p for p in op.pages(self.read()) if p.get('manual_reconstruction_source_page')]),1)
        document=self.read();op.mutate(document,'apply_suggestions',{});save_review_document(self.root,document)
        self.assertEqual(len([p for p in op.pages(self.read()) if p.get('manual_reconstruction_source_page')]),1)
        self.toggle(False)
        self.assertFalse(any(p.get('manual_reconstruction_source_page') for p in op.pages(self.read())))

    def test_source_toggle_route_read_only_display_and_invalid_pages(self):
        self.prepare_pages()
        response=self.client.post('/api/source-pages/manual-reconstruction',headers=self.headers,json={'page':1,'enabled':True,'expected_review_token':review_token(self.read())})
        self.assertEqual(response.status_code,200,response.text)
        before=(self.root/'review/current.json').read_bytes()
        self.assertIn('Needs manual reconstruction',self.client.get('/structure').text)
        page=self.client.get('/output-pages').text
        self.assertIn('Source page 1 — needs manual reconstruction',page)
        placeholder=next(p for p in op.pages(self.read()) if p.get('manual_reconstruction_source_page'))
        self.assertIn('Unfinished reconstruction placeholder',self.client.get('/output-pages?page_id='+placeholder['id']).text)
        self.assertEqual((self.root/'review/current.json').read_bytes(),before)
        for value in [0,3,True,'1']:
            with self.assertRaisesRegex(ValueError,'existing source page'):
                mr.toggle(self.root,value,False,review_token(self.read()))


if __name__=='__main__':
    unittest.main()
