"""Whole-page saved readiness ignores selected/filtered subsets."""
import copy
import unittest
from pdf_to_web.source_review import page_reviews
from pdf_to_web.review_state import _set_status
import test_reading_order_merge as fixtures

class SourceReviewTests(unittest.TestCase):
    def block(self,identity,page=1,approved=False,**extra):
        block={'id':identity,'type':'paragraph','content':'Saved '+identity,'provenance':{'source_page':page},**extra}
        if approved:_set_status(block,'approved')
        return block
    def document(self,blocks,**review):
        return {'blocks':blocks,'review':{'status':'review_ready',**review},'footnotes':[]}
    def test_all_none_mixed_excluded_and_zero(self):
        doc=self.document([self.block('a',approved=True),self.block('b'),self.block('c',2,approved=True)])
        result=page_reviews(doc,3)
        self.assertEqual([result[str(p)]['state'] for p in [1,2,3]],['partial','reviewed','needs'])
        _set_status(doc['blocks'][0],'needs_review');self.assertEqual(page_reviews(doc,3)['1']['state'],'needs')
        _set_status(doc['blocks'][0],'excluded');self.assertEqual(page_reviews(doc,3)['1']['state'],'partial')
        _set_status(doc['blocks'][1],'excluded');self.assertEqual(page_reviews(doc,3)['1']['state'],'reviewed')
        self.assertIn('all recorded blocks',page_reviews(doc,3)['1']['detail'].lower())
        self.assertIn('no extracted',result['3']['detail'].lower())
    def test_holds_and_conversion_override_complete(self):
        doc=self.document([self.block('a',approved=True)],manual_reconstruction_pages={'1':{'block_ids':['a']}})
        self.assertEqual(page_reviews(doc,1)['1']['state'],'needs')
        self.assertIn('reconstruction',page_reviews(doc,1)['1']['detail'])
        doc['review']={'status':'conversion_blocked'};self.assertEqual(page_reviews(doc,1)['1']['state'],'needs')
    def test_shared_membership_stale_approval_and_read_only_projection(self):
        block=self.block('a');block['provenance']['merged_source_pages']=[2];_set_status(block,'approved')
        doc=self.document([block,self.block('b',2),self.block('unknown',None)]);before=copy.deepcopy(doc)
        result=page_reviews(doc,3)
        self.assertEqual(doc,before);self.assertEqual(result['1']['state'],'reviewed');self.assertEqual(result['2']['state'],'partial')
        block['content']='Changed';result=page_reviews(doc,3)
        self.assertEqual(result['1']['state'],'needs');self.assertEqual(result['2']['state'],'needs')
    def test_image_descriptions_count_once_and_missing_alt_blocks_green(self):
        image=self.block('image',type='image',alt='Actual purpose');_set_status(image,'approved')
        doc=self.document([image],complex_visuals=[{'id':'desc','source_block_id':'image','source_page':1,'type':'image','status':'needs_text_equivalent','accessibility':{}}])
        result=page_reviews(doc,1)['1'];self.assertEqual(result['state'],'needs');self.assertEqual(result['total_tasks'],1);self.assertEqual(result['pending'],1)
        doc['review']['complex_visuals'][0]['status']='not_applicable';self.assertEqual(page_reviews(doc,1)['1']['state'],'reviewed')
        image['alt']='';_set_status(image,'approved');self.assertEqual(page_reviews(doc,1)['1']['state'],'needs')
        image['decorative']=True;_set_status(image,'approved');self.assertEqual(page_reviews(doc,1)['1']['state'],'reviewed')
    def test_standalone_and_nested_images_are_required(self):
        doc=self.document([self.block('a',approved=True)],complex_visuals=[{'id':'visual','source_page':1,'type':'diagram','status':'needs_text_equivalent','accessibility':{}}])
        self.assertEqual(page_reviews(doc,1)['1']['state'],'partial');self.assertEqual(page_reviews(doc,1)['1']['total_tasks'],2)
        doc['review']['complex_visuals'][0]['status']='not_applicable';self.assertEqual(page_reviews(doc,1)['1']['state'],'reviewed')
        parent=self.block('list',type='list',children=[{'id':'item','type':'list_item','content':'Item','children':[{'id':'nested','type':'image','alt':''}]}]);_set_status(parent,'approved')
        self.assertEqual(page_reviews(self.document([parent]),1)['1']['state'],'needs')

class SourceReviewPersistenceTests(unittest.TestCase):
    setUp=fixtures.ReadingOrderMergeTests.setUp
    paragraph=fixtures.ReadingOrderMergeTests.paragraph
    blocks=fixtures.ReadingOrderMergeTests.blocks
    request=fixtures.ReadingOrderMergeTests.request
    def test_absorbed_origins_are_not_counted_and_undo_unmerge_restore_scope(self):
        from pdf_to_web.review_state import update_block,ensure_review_document,undo_last
        self.blocks([self.paragraph('a'),self.paragraph('b')])
        update_block(self.root,'a',{'review_status':'approved'});update_block(self.root,'b',{'review_status':'approved'})
        self.assertEqual(page_reviews(ensure_review_document(self.root),2)['1']['state'],'reviewed')
        result=page_reviews(self.request([{'action':'merge','block_ids':['a','b']}]),2)['1']
        self.assertEqual(result['state'],'needs');self.assertEqual(result['blocks'],1)
        self.assertEqual(page_reviews(self.request([{'action':'unmerge','block_id':'a'}]),2)['1']['state'],'reviewed')
        self.assertEqual(page_reviews(undo_last(self.root),2)['1']['state'],'needs')
