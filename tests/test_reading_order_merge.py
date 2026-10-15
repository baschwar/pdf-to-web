"""Staged merge/unmerge plans preserve origin data, adjacency and one saved Undo."""
import copy
import unittest
from unittest.mock import patch
from pdf_to_web import reading_order as ro
from pdf_to_web.review_state import ensure_review_document, save_review_document, review_path, undo_last, update_block
from pdf_to_web.image_review import review_token
from pdf_to_web.exporters import html,gutenberg
from pdf_to_web.source_pages import source_regions_for_blocks
import test_reading_order as fixtures


class ReadingOrderMergeTests(unittest.TestCase):
    setUp=fixtures.ReadingOrderTests.setUp

    def paragraph(self,identity,text=None,**extra):
        return {'id':identity,'type':'paragraph','content':text or f'Fragment {identity}',
            'provenance':{'source_page':1,'bounding_box':[10,20+10*len(identity),200,40+10*len(identity)]},**extra}

    def blocks(self,blocks):
        document=ensure_review_document(self.root)
        document['blocks']=blocks
        page=document['output_pages']['pages'][0]
        page['block_ids']=[b['id'] for b in blocks]
        save_review_document(self.root,document)
        return ensure_review_document(self.root)

    def request(self,operations,commit=True,**extra):
        document=ensure_review_document(self.root)
        args=(self.root,1,operations,review_token(document),document['output_pages']['project_id'])
        if commit:return ro.apply(args[0],args[1],None,args[3],args[4],operations=args[2],**extra)
        return ro.preview(*args)

    def test_preview_no_write_then_reorder_merge_is_one_revision_with_full_origins_exports_undo(self):
        before=self.blocks([self.paragraph('a','Orphan hy-'),self.paragraph('b','phen stays.'),self.paragraph('c','Third fragment')])
        token_bytes=review_path(self.root).read_bytes();history=list((self.root/'review/revisions').glob('*.json'))
        operations=[{'action':'order','block_ids':['c','a','b']},{'action':'merge','block_ids':['a','b']}]
        preview=self.request(operations,False)
        self.assertEqual([r['id'] for r in preview['rows']],['c','a'])
        self.assertEqual(preview['rows'][1]['text'],'Orphan hy- phen stays.')
        self.assertEqual(review_path(self.root).read_bytes(),token_bytes)
        self.assertEqual(list((self.root/'review/revisions').glob('*.json')),history)
        after=self.request(operations);block=after['blocks'][1]
        self.assertEqual(block['provenance'][ro.MERGE_KEY]['originals'],before['blocks'][:2])
        self.assertEqual(block['review']['status'],'needs_review')
        self.assertEqual(after['review_session']['revision'],before['review_session']['revision']+1)
        self.assertEqual(len(list((self.root/'review/revisions').glob('*.json'))),len(history)+1)
        self.assertEqual(after['output_pages']['pages'][0]['block_ids'],['c','a'])
        for renderer in [html.render_document,gutenberg.render_document]:
            markup=renderer(after);self.assertIn('Orphan hy- phen stays.',markup);self.assertNotIn('Fragment b',markup)
        self.assertEqual(undo_last(self.root)['blocks'],before['blocks'])
        self.assertEqual(ensure_review_document(self.root)['output_pages']['pages'][0]['block_ids'],['a','b','c'])

    def test_persistent_unmerge_reopen_review_only_changes_and_current_page_assignment(self):
        before=self.blocks([self.paragraph('a'),self.paragraph('b'),self.paragraph('c')])
        self.request([{'action':'merge','block_ids':['a','b']}])
        update_block(self.root,'a',{'review_status':'approved'})
        snapshot=ro.snapshot(self.root,1)
        self.assertEqual(snapshot['rows'][0]['merge_count'],2)
        self.assertEqual(snapshot['rows'][0]['unmerge_reason'],'')
        after=self.request([{'action':'unmerge','block_id':'a'}])
        self.assertEqual(after['blocks'],before['blocks'])
        self.assertEqual(after['output_pages']['pages'][0]['block_ids'],['a','b','c'])

    def test_edited_merged_content_blocks_unmerge_without_losing_later_edits(self):
        self.blocks([self.paragraph('a'),self.paragraph('b')])
        self.request([{'action':'merge','block_ids':['a','b']}])
        update_block(self.root,'a',{'content':'Later authored content'})
        before=review_path(self.root).read_bytes()
        self.assertIn('edited',ro.snapshot(self.root,1)['rows'][0]['unmerge_reason'])
        with self.assertRaisesRegex(ValueError,'discard'):
            self.request([{'action':'unmerge','block_id':'a'}])
        self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_merge_unmerge_in_one_draft_is_no_saved_change(self):
        self.blocks([self.paragraph('a'),self.paragraph('b')]);before=review_path(self.root).read_bytes()
        self.request([{'action':'merge','block_ids':['a','b']},{'action':'unmerge','block_id':'a'}])
        self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_adjacency_hidden_scope_mixed_types_and_formatting_are_rejected_atomically(self):
        cases=[([self.paragraph('a'),self.paragraph('hidden',excluded=True),self.paragraph('b')],['a','b']),
               ([self.paragraph('a'),self.paragraph('other',provenance={'source_page':2}),self.paragraph('b')],['a','b']),
               ([self.paragraph('a'),self.paragraph('b')],['b','a']),
               ([self.paragraph('a'),self.paragraph('b',type='heading',level=2)],['a','b']),
               ([self.paragraph('a'),self.paragraph('b',runs=[{'type':'strong','text':'Bold'}])],['a','b']),
               ([self.paragraph('a'),self.paragraph('b',footnote_references=[{'id':'fn','start':0,'end':1}])],['a','b'])]
        for blocks,identities in cases:
            with self.subTest(identities=identities,blocks=blocks):
                self.blocks(blocks);before=review_path(self.root).read_bytes()
                with self.assertRaises(ValueError):self.request([{'action':'merge','block_ids':identities}])
                self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_paragraph_and_lettered_list_explain_global_block_numbers_without_changing_data(self):
        prefix = [self.paragraph(f'prefix-{i}', provenance={'source_page': 2}) for i in range(103)]
        paragraph = self.paragraph('fragment', 'Example services include checks such')
        continuation = self.list_block('continuation', 1, marker='lower-alpha')
        self.blocks(prefix + [paragraph, continuation])
        before = review_path(self.root).read_bytes()
        for commit in (False, True):
            with self.subTest(commit=commit):
                with self.assertRaisesRegex(ValueError, r'Block 104 is a paragraph, but Block 105 is a list'):
                    self.request([{'action': 'merge', 'block_ids': ['fragment', 'continuation']}], commit=commit)
                self.assertEqual(review_path(self.root).read_bytes(), before)

    def list_block(self,identity,start,ordered=True,marker=None):
        result={'id':identity,'type':'list','ordered':ordered,'start':start,'children':[
            {'id':identity+'-item','type':'list_item','content':'Item '+identity,'provenance':{'source_page':1,'bounding_box':[10,100+start*10,300,120+start*10]},
             'children':[{'id':identity+'-nested','type':'list','ordered':False,'children':[{'id':identity+'-detail','type':'list_item','content':'Nested detail','provenance':{'source_page':1,'bounding_box':[40,150,250,170]}}]}]}],
            'provenance':{'source_page':1,'bounding_box':[10,start*10,300,20+start*10]}}
        if marker:result['marker_style']=marker
        return result

    def test_ordered_lists_continue_preserve_items_nesting_regions_exports_and_unmerge(self):
        before=self.blocks([self.list_block('a',3),self.list_block('b',4)])
        after=self.request([{'action':'merge','block_ids':['a','b']}]);block=after['blocks'][0]
        self.assertEqual(block['start'],3)
        self.assertEqual(block['children'],[before['blocks'][0]['children'][0],before['blocks'][1]['children'][0]])
        regions=source_regions_for_blocks(self.root,[block])['a']['regions']
        self.assertGreaterEqual(len(regions),5)
        snapshot=ro.snapshot(self.root,1)
        self.assertEqual(snapshot['rows'][0]['preview']['items'][1]['children'][0]['items'][0]['text'],'Nested detail')
        for renderer in [html.render_document,gutenberg.render_document]:
            markup=renderer(after);self.assertIn('start="3"',markup);self.assertIn('Item a',markup);self.assertIn('Item b',markup);self.assertIn('Nested detail',markup)
        self.assertEqual(self.request([{'action':'unmerge','block_id':'a'}])['blocks'],before['blocks'])

    def test_unordered_lists_join_but_number_restarts_kind_marker_conflicts_reject(self):
        self.blocks([self.list_block('a',1,False),self.list_block('b',1,False)])
        self.assertEqual(len(self.request([{'action':'merge','block_ids':['a','b']}])['blocks'][0]['children']),2)
        for second in [self.list_block('b',1),self.list_block('b',2,False),self.list_block('b',2,True,'lower-alpha')]:
            self.blocks([self.list_block('a',1),second]);before=review_path(self.root).read_bytes()
            with self.assertRaises(ValueError):self.request([{'action':'merge','block_ids':['a','b']}])
            self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_page_assignment_conflicts_stale_plan_and_failed_later_step_do_not_write(self):
        self.blocks([self.paragraph('a'),self.paragraph('b'),self.paragraph('c')])
        document=ensure_review_document(self.root);token=review_token(document);pid=document['output_pages']['project_id']
        update_block(self.root,'c',{'content':'Newer content'})
        before=review_path(self.root).read_bytes()
        with self.assertRaisesRegex(ValueError,'project changed'):
            ro.apply(self.root,1,None,token,pid,operations=[{'action':'merge','block_ids':['a','b']}])
        self.assertEqual(review_path(self.root).read_bytes(),before)
        with self.assertRaises(ValueError):self.request([{'action':'merge','block_ids':['a','b']},{'action':'merge','block_ids':['a','c']}])
        self.assertEqual(review_path(self.root).read_bytes(),before)
        document=ensure_review_document(self.root)
        document['output_pages']['pages'].append({**copy.deepcopy(document['output_pages']['pages'][0]),'id':'second','block_ids':['b']})
        document['output_pages']['pages'][0]['block_ids'].remove('b');save_review_document(self.root,document)
        before=review_path(self.root).read_bytes()
        with self.assertRaisesRegex(ValueError,'assignments'):self.request([{'action':'merge','block_ids':['a','b']}])
        self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_origin_identity_collision_and_changed_source_refuse_unmerge(self):
        self.blocks([self.paragraph('a'),self.paragraph('b')]);self.request([{'action':'merge','block_ids':['a','b']}])
        document=ensure_review_document(self.root);document['blocks'].append(self.paragraph('b','New reused ID'));save_review_document(self.root,document)
        before=review_path(self.root).read_bytes()
        with self.assertRaisesRegex(ValueError,'identities'):self.request([{'action':'unmerge','block_id':'a'}])
        self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_plain_runs_are_authoritative_and_list_preview_uses_run_text(self):
        before=self.blocks([self.paragraph('a','Stale',runs=[{'type':'text','text':'Actual first'}]),self.paragraph('b','Second')])
        after=self.request([{'action':'merge','block_ids':['a','b']}])
        self.assertEqual(after['blocks'][0]['content'],'Actual first Second')
        self.assertEqual(self.request([{'action':'unmerge','block_id':'a'}])['blocks'],before['blocks'])
        a=self.list_block('a',1);b=self.list_block('b',2)
        a['children'][0]['runs']=[{'type':'text','text':'Actual list item'}]
        self.blocks([a,b]);preview=self.request([{'action':'merge','block_ids':['a','b']}],False)
        self.assertEqual(preview['rows'][0]['preview']['items'][0]['text'],'Actual list item')

    def test_incoming_link_caption_and_review_decisions_cannot_be_silently_lost(self):
        for link in [{'type':'link','text':'Jump','url':'#b'}, {'type':'link','text':'Jump','target_block_id':'b','url':'page.html#b'}]:
            self.blocks([self.paragraph('a'),self.paragraph('b'),self.paragraph('link','Jump',runs=[link])])
            before=review_path(self.root).read_bytes()
            with self.assertRaisesRegex(ValueError,'link targets'):self.request([{'action':'merge','block_ids':['a','b']}])
            self.assertEqual(review_path(self.root).read_bytes(),before)
        self.blocks([self.list_block('a',1),self.list_block('b',2)])
        merged=self.request([{'action':'merge','block_ids':['a','b']}])
        merged['blocks'][0]['children'][1].setdefault('review',{})['status']='excluded'
        save_review_document(self.root,merged);before=review_path(self.root).read_bytes()
        with self.assertRaisesRegex(ValueError,'discard'):self.request([{'action':'unmerge','block_id':'a'}])
        self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_recovered_source_origins_are_outlined_individually(self):
        self.blocks([self.paragraph('a',provenance={'source_page':1,'source_type':'recovered first-page header'}),
                     self.paragraph('b',provenance={'source_page':1,'source_type':'recovered first-page subtitle'})])
        merged=self.request([{'action':'merge','block_ids':['a','b']}])['blocks'][0]
        with patch('pdf_to_web.source_pages.source_text_regions',return_value=(None,[])), patch('pdf_to_web.source_pages.matched_source_text_box',side_effect=[[10,100,200,120],[20,200,250,230]]) as match:
            regions=source_regions_for_blocks(self.root,[merged])['a']['regions']
        self.assertEqual(match.call_count,2)
        self.assertEqual(len(regions),2)

    def test_empty_run_text_and_invalid_nested_item_layout_are_not_inferred(self):
        self.blocks([self.paragraph('a','Stale',runs=[]),self.paragraph('b')]);before=review_path(self.root).read_bytes()
        with self.assertRaisesRegex(ValueError,'empty paragraph'):self.request([{'action':'merge','block_ids':['a','b']}])
        self.assertEqual(review_path(self.root).read_bytes(),before)
        malformed=self.list_block('a',1);malformed['children'][0]['children']=[{'id':'wrong','type':'list_item','content':'Orphan child'}]
        self.blocks([malformed,self.list_block('b',2)]);before=review_path(self.root).read_bytes()
        with self.assertRaisesRegex(ValueError,'hierarchy'):self.request([{'action':'merge','block_ids':['a','b']}])
        self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_unmerge_restores_original_approvals_at_the_current_arrange_page(self):
        self.blocks([self.paragraph('a'),self.paragraph('b'),self.paragraph('c')])
        update_block(self.root,'a',{'review_status':'approved'});update_block(self.root,'b',{'review_status':'approved'})
        before=ensure_review_document(self.root)
        self.request([{'action':'merge','block_ids':['a','b']}])
        document=ensure_review_document(self.root)
        document['output_pages']['pages'][0]['block_ids'].remove('a')
        document['output_pages']['pages'].append({**copy.deepcopy(document['output_pages']['pages'][0]),'id':'current-owner','block_ids':['a']})
        save_review_document(self.root,document)
        after=self.request([{'action':'unmerge','block_id':'a'}])
        self.assertEqual(after['blocks'],before['blocks'])
        self.assertEqual(after['output_pages']['pages'][1]['block_ids'],['a','b'])
        self.assertEqual(after['output_pages']['pages'][0]['block_ids'],['c'])

    def test_custom_review_notes_and_corrupted_origins_refuse_loss(self):
        for mode in ['review_note','origin','version']:
            with self.subTest(mode=mode):
                self.blocks([self.paragraph('a'),self.paragraph('b')])
                document=self.request([{'action':'merge','block_ids':['a','b']}])
                if mode=='review_note':document['blocks'][0]['review']['note']='Later reviewer note'
                elif mode=='origin':document['blocks'][0]['provenance'][ro.MERGE_KEY]['originals'][1]['content']='Altered retained data'
                else:document['blocks'][0]['provenance'][ro.MERGE_KEY]['version']=99
                save_review_document(self.root,document);before=review_path(self.root).read_bytes()
                self.assertTrue(ro.snapshot(self.root,1)['rows'][0]['unmerge_reason'])
                if mode in {'origin','version'}:
                    self.assertEqual(ro.snapshot(self.root,1)['rows'][0]['regions'], [])
                with self.assertRaises(ValueError):self.request([{'action':'unmerge','block_id':'a'}])
                self.assertEqual(review_path(self.root).read_bytes(),before)
