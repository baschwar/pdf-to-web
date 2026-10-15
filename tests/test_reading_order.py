"""Page-order changes are complete permutations, one saved action and recoverable."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from pypdf import PdfWriter
from pdf_to_web.project import create_project, load_project, save_project
from pdf_to_web.review_state import original_path, review_path, ensure_review_document, save_review_document, undo_last, update_block
from pdf_to_web.image_review import review_token
from pdf_to_web import reading_order


class ReadingOrderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()/'project';create_project(self.root,'Order fixture')
        project=load_project(self.root);project['source'].update(path='source/original.pdf',page_count=2);save_project(self.root,project)
        pdf=PdfWriter();[pdf.add_blank_page(width=612,height=792) for _ in range(2)];pdf.write(self.root/'source/original.pdf')
        def block(identity,page=1,**extra):
            return {'id':identity,'type':'paragraph','content':f'Paragraph {identity}', 'provenance':{'source_page':page},**extra}
        doc={'schema_version':'pdf-to-web-normalized-v1','metadata':{'title':'Order fixture'},'review':{'status':'review_ready','issues':[]},'blocks':[
            block('a'),block('shared',provenance={'source_page':1,'merged_source_pages':[1,2]}),block('b'),block('excluded',excluded=True),block('d'),block('other',2),block('geometryless'),block('unlocated',provenance={})]}
        original_path(self.root).write_text(json.dumps(doc));ensure_review_document(self.root)
        update_block(self.root,'a',{'review_status':'approved'})

    def document(self):return ensure_review_document(self.root)
    def apply(self,ids,token=None,page=1,project_id=None):
        doc=self.document();return reading_order.apply(self.root,page,ids,token or review_token(doc),project_id or doc['output_pages']['project_id'])
    def history(self):return list((self.root/'review/revisions').glob('*.json'))

    def test_snapshot_is_read_only_and_identifies_shared_excluded_and_geometryless(self):
        before=review_path(self.root).read_bytes();snap=reading_order.snapshot(self.root,1)
        self.assertEqual([r['id'] for r in snap['rows']],['a','shared','b','d','geometryless'])
        self.assertEqual([r['id'] for r in snap['excluded']],['excluded'])
        self.assertTrue(snap['rows'][1]['locked']);self.assertEqual(snap['rows'][-1]['regions'],[])
        self.assertNotIn('unlocated',[r['id'] for r in snap['rows']]);self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_one_atomic_permutation_preserves_all_values_other_slots_and_output_references_then_undo(self):
        before=self.document();values={b['id']:copy.deepcopy(b) for b in before['blocks']};count=len(self.history())
        after=self.apply(['a','d','geometryless','b'])
        self.assertEqual([b['id'] for b in after['blocks']],['a','shared','d','excluded','geometryless','other','b','unlocated'])
        self.assertEqual({b['id']:b for b in after['blocks']},values)
        self.assertEqual(len(self.history()),count+1)
        self.assertEqual(after['review_session']['revision'],before['review_session']['revision']+1)
        self.assertEqual(after['review'],before['review'])
        self.assertEqual(set(after['output_pages']['pages'][0]['block_ids']),set(before['output_pages']['pages'][0]['block_ids']))
        self.assertEqual(after['output_pages']['pages'][0]['id'],before['output_pages']['pages'][0]['id'])
        self.assertEqual(self.document()['blocks'],after['blocks'])
        restored=undo_last(self.root);self.assertEqual(restored['blocks'],before['blocks']);self.assertEqual(restored['output_pages'],before['output_pages'])

    def test_invalid_sets_types_crosspage_nested_excluded_and_shared_crossing_do_not_write(self):
        for ids in (['a','b','d'],['a','b','d','d'],['a','b','d','other'],['a','b','d','excluded'],['a','b','d','shared'],['a','b','d',1],None,['b','a','d','geometryless']):
            with self.subTest(ids=ids):
                before=review_path(self.root).read_bytes();history=self.history()
                with self.assertRaises(ValueError):self.apply(ids)
                self.assertEqual(review_path(self.root).read_bytes(),before);self.assertEqual(self.history(),history)

    def test_stale_or_wrong_project_and_intervening_write_are_rejected(self):
        token=review_token(self.document());update_block(self.root,'other',{'content':'New saved content'})
        before=review_path(self.root).read_bytes()
        with self.assertRaises(ValueError):self.apply(['a','d','b','geometryless'],token)
        with self.assertRaises(ValueError):self.apply(['a','d','b','geometryless'],project_id='wrong')
        self.assertEqual(review_path(self.root).read_bytes(),before)
        token=review_token(self.document());changed=self.document();changed['blocks'][0]['content']='Concurrent authoring'
        save_review_document(self.root,changed)
        with self.assertRaises(ValueError):save_review_document(self.root,self.document(),expected_review_token=token)

    def test_noop_adds_no_history_and_invalid_page_or_hold_is_rejected(self):
        before=review_path(self.root).read_bytes();history=self.history();self.apply(['a','b','d','geometryless'])
        self.assertEqual(review_path(self.root).read_bytes(),before);self.assertEqual(self.history(),history)
        for page in (True,0,3,'1'):
            with self.subTest(page=page),self.assertRaises(ValueError):reading_order.snapshot(self.root,page)
        from pdf_to_web.manual_reconstruction import toggle
        toggle(self.root,1,True,review_token(self.document()))
        before=review_path(self.root).read_bytes()
        with self.assertRaises(ValueError):self.apply([])
        self.assertEqual(review_path(self.root).read_bytes(),before)

    def test_active_provider_and_duplicate_identity_are_rejected_without_write(self):
        doc=self.document();doc['image_description_drafts']['requests']['busy']={'status':'generating','provider':'ollama-local'};doc['image_description_drafts']['active']['a']='busy';save_review_document(self.root,doc)
        before=review_path(self.root).read_bytes()
        with self.assertRaisesRegex(ValueError,'generation is active'):self.apply(['a','d','b','geometryless'])
        self.assertEqual(review_path(self.root).read_bytes(),before)
        doc=self.document();doc['blocks'][2]['id']='a'
        with self.assertRaisesRegex(ValueError,'duplicate'):reading_order._scope(doc,1)

    def test_failed_atomic_save_preserves_document_and_undo_history(self):
        before=review_path(self.root).read_bytes();history=self.history();project=(self.root/'project.json').read_bytes()
        from pdf_to_web import review_state
        write=review_state._atomic_write
        def fail(path,data):
            if path==review_path(self.root):raise OSError('Fixture write failed')
            return write(path,data)
        with mock.patch.object(review_state,'_atomic_write',side_effect=fail),self.assertRaises(OSError):self.apply(['a','d','b','geometryless'])
        self.assertEqual(review_path(self.root).read_bytes(),before);self.assertEqual(self.history(),history);self.assertEqual((self.root/'project.json').read_bytes(),project)
