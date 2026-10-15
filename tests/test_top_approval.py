"""Top approval combines the displayed block's editors into one recoverable write."""
import copy
import unittest
from unittest import mock
import test_save_and_approve as fixtures
from pdf_to_web.image_review import review_token, descriptions_for
from pdf_to_web.review_state import ensure_review_document, review_path, undo_last, save_review_document


class TopApprovalTests(unittest.TestCase):
    setUp = fixtures.SaveAndApproveTests.setUp
    document = fixtures.SaveAndApproveTests.document

    def post(self, identity, entries, **extra):
        document = ensure_review_document(self.root)
        return self.client.post(f'/api/blocks/{identity}/save-and-approve', headers=self.headers, json={
            'expected_review_token': review_token(document), 'form_edits': entries, 'review_refresh': True, **extra})

    def test_heading_level_only_save_and_approve_preserves_text_and_has_one_undo(self):
        before = self.document({'id': 'heading', 'type': 'heading', 'level': 2, 'content': 'Example section'})
        result = self.post('heading', [{'type': 'heading', 'level': 1, 'content': 'Example section'}])
        self.assertEqual(result.status_code, 200, result.text)
        saved = ensure_review_document(self.root)
        self.assertEqual((saved['blocks'][0]['level'], saved['blocks'][0]['content'], saved['blocks'][0]['review']['status']),
                         (1, 'Example section', 'approved'))
        self.assertEqual(saved['review_session']['revision'], before['review_session']['revision'] + 1)
        self.assertEqual(undo_last(self.root)['blocks'], before['blocks'])

    def test_text_and_multiple_rich_link_labels_save_and_approve_once_and_undo(self):
        before = self.document({'id':'text','type':'paragraph','content':'See Guide and Help.', 'runs':[
            {'type':'text','text':'See '},{'type':'link','text':'Guide','url':'https://example.test/guide'},
            {'type':'text','text':' and '},{'type':'link','text':'Help','url':'https://example.test/help'},
            {'type':'text','text':'.'}]})
        result = self.post('text', [{'type':'paragraph','content':'See Guide and Help. Now.'},
            {'link_block_id':'text','link_index':'1','link_text':'Read guide'},
            {'link_block_id':'text','link_index':'3','link_text':'Get help'}])
        self.assertEqual(result.status_code,200,result.text)
        after=ensure_review_document(self.root);block=after['blocks'][0]
        self.assertEqual(block['content'],'See Read guide and Get help. Now.')
        self.assertEqual(block['runs'][1]['url'],'https://example.test/guide')
        self.assertEqual(block['review']['status'],'approved')
        self.assertEqual(after['review_session']['revision'],before['review_session']['revision']+1)
        self.assertIn('review_patch',result.json())
        self.assertEqual(undo_last(self.root)['blocks'],before['blocks'])

    def test_nested_link_and_owner_review_are_combined_without_flattening(self):
        self.document({'id':'list','type':'list','children':[{'id':'child','type':'list_item','content':'Guide',
            'runs':[{'type':'link','text':'Guide','url':'https://example.test/guide'}]}]})
        result=self.post('list',[{'review_status':'needs_review'}, {'link_block_id':'child','link_index':'0','link_text':'Read guide'}])
        self.assertEqual(result.status_code,200,result.text)
        block=ensure_review_document(self.root)['blocks'][0]
        self.assertEqual(block['children'][0]['content'],'Read guide')
        self.assertEqual(block['review']['status'],'approved')

    def test_image_alternatives_all_description_fields_and_decision_save_together(self):
        document=self.document({'id':'image','type':'image','alt':'Before','caption':'Before caption'})
        document['review']['complex_visuals']=[{'id':'visual','source_block_id':'image','type':'image','status':'needs_text_equivalent',
            'accessibility':{'long_description':'Before long','adjacent_text':''}}]
        save_review_document(self.root,document)
        before=copy.deepcopy(ensure_review_document(self.root))
        result=self.post('image',[{'alt':'After alt','caption':'After caption','decorative':False,
            'description_edits':[{'id':'visual','long_description':'After long','adjacent_text':'After adjacent',
                'disposition':'include','type':'diagram','recovered_text':'Recovered labels','review_note':'Checked chart'}]}],
            displayed_description_ids=['visual'])
        self.assertEqual(result.status_code,200,result.text)
        after=ensure_review_document(self.root);block=after['blocks'][0];visual=descriptions_for(after,block)[0]
        self.assertEqual((block['alt'],block['caption'],block['review']['status']),('After alt','After caption','approved'))
        self.assertEqual(visual['accessibility']['long_description'],'After long')
        self.assertEqual(visual['accessibility']['adjacent_text'],'After adjacent')
        self.assertEqual((visual['type'],visual['recovered_text'],visual['review_note']),('diagram','Recovered labels','Checked chart'))
        self.assertEqual(visual['status'],'reviewed')
        self.assertEqual(after['review_session']['revision'],before['review_session']['revision']+1)
        self.assertEqual(undo_last(self.root)['review']['complex_visuals'],before['review']['complex_visuals'])

    def test_failed_link_validation_foreign_scope_duplicate_and_stale_do_not_write(self):
        self.document({'id':'text','type':'paragraph','content':'Guide', 'runs':[{'type':'link','text':'Guide','url':'https://example.test/guide'}]})
        cases=[([{'content':'Changed Guide'},{'link_block_id':'text','link_index':'0','link_text':''}],{}),
            ([{'link_block_id':'foreign','link_index':'0','link_text':'Read'}],{}),
            ([{'link_block_id':'text','link_index':'0','link_text':'Read'}]*2,{}),
            ([{'content':'Changed'}],{'expected_review_token':'stale'}),
            ([{'content':'Changed'},{'content':'Other'}],{})]
        for entries,extra in cases:
            with self.subTest(entries=entries,extra=extra):
                before=review_path(self.root).read_bytes();history=list((self.root/'review/revisions').glob('*.json'))
                result=self.post('text',entries,**extra)
                self.assertEqual(result.status_code,400,result.text)
                self.assertEqual(review_path(self.root).read_bytes(),before)
                self.assertEqual(list((self.root/'review/revisions').glob('*.json')),history)

    def test_bad_image_description_rejects_alt_and_caption_without_partial_write(self):
        document=self.document({'id':'image','type':'image','alt':'Before','caption':'Before caption'})
        document['review']['complex_visuals']=[{'id':'visual','source_block_id':'image','type':'image','status':'needs_text_equivalent',
            'accessibility':{'long_description':'','adjacent_text':''}}]
        save_review_document(self.root,document);before=review_path(self.root).read_bytes()
        result=self.post('image',[{'alt':'After','caption':'After caption','description_edits':[{'id':'visual','long_description':'','adjacent_text':'','disposition':'include'}]}],displayed_description_ids=['visual'])
        self.assertEqual(result.status_code,400,result.text)
        self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_overlapping_text_and_link_label_changes_are_rejected_without_lost_text(self):
        self.document({'id':'text','type':'paragraph','content':'Guide',
            'runs':[{'type':'link','text':'Guide','url':'https://example.test/guide'}]})
        before=review_path(self.root).read_bytes()
        result=self.post('text',[{'content':'Guide revised'},
            {'link_block_id':'text','link_index':'0','link_text':'Read guide'}])
        self.assertEqual(result.status_code,400,result.text)
        self.assertIn('also changes a selected link',result.json()['error'])
        self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_final_expected_token_check_retains_a_newer_external_save(self):
        from pdf_to_web import review_state
        import json
        self.document({'id':'text','type':'paragraph','content':'Before'})
        real_save=review_state.save_review_document
        newer=[]
        def intervening_save(root, document, **kwargs):
            current=ensure_review_document(root)
            current['blocks'][0]['content']='Newer external content'
            review_path(root).write_text(json.dumps(current))
            newer.append(review_path(root).read_bytes())
            return real_save(root,document,**kwargs)
        with mock.patch('pdf_to_web.review_state.save_review_document', side_effect=intervening_save):
            result=self.post('text',[{'content':'Stale combined content'}])
        self.assertEqual(result.status_code,400,result.text)
        self.assertEqual(review_path(self.root).read_bytes(),newer[0])

    def test_table_accessibility_changes_approve_final_values_in_one_revision(self):
        before=self.document({'id':'table','type':'table','rows':[['Label','Value'],['Example','One']]})
        result=self.post('table',[{'table_caption':'Checked data','table_header_row':True,
            'table_header_column':False,'table_reviewed':True}])
        self.assertEqual(result.status_code,200,result.text)
        after=ensure_review_document(self.root);block=after['blocks'][0]
        self.assertEqual(block['caption'],'Checked data')
        self.assertEqual(block['table_accessibility'],{'header_row':True,'header_column':False,'reviewed':True})
        self.assertEqual(block['review']['status'],'approved')
        self.assertEqual(after['review_session']['revision'],before['review_session']['revision']+1)
