import copy
import re
import unittest

from pdf_to_web.page_grouping import auto_slug, plan
from pdf_to_web import output_pages as op


def block(identity, page=None, **extra):
    return {'id': identity, 'type': 'paragraph', 'content': identity,
            'provenance': {} if page is None else {'source_page': page},
            'review': {'status': 'approved'}, **extra}


def document():
    return {'metadata': {'title': 'Report'}, 'review': {'complex_visuals': []},
            'blocks': [block('a', 1), block('b', 2)],
            'output_pages': {'schema_version': op.SCHEMA, 'project_id': 'project-test',
                             'pages': [op.new_page('Custom', ['a', 'b'], id='old')]}}


class PageGroupingTests(unittest.TestCase):
    def test_slug_normalizes_unicode_reserved_words_collisions_and_length(self):
        self.assertEqual(auto_slug('École Déjà Vu'), 'ecole-deja-vu')
        self.assertEqual(auto_slug('Contents'), 'contents-2')
        used = {'publications-2', 'publications-3'}
        self.assertEqual(auto_slug('Publications', used), 'publications-4')
        self.assertEqual(used, {'publications-2', 'publications-3'})
        base = auto_slug('A' * 120)
        suffixed = auto_slug('A' * 120, [base])
        self.assertLessEqual(len(suffixed), 100)
        self.assertTrue(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', suffixed))
        self.assertEqual(auto_slug('中文'), 'page')

    def test_source_plan_is_pure_repeatable_numeric_and_discloses_metadata(self):
        d = document()
        d['blocks'].reverse()
        old = copy.deepcopy(d)
        first = plan(d, 3, 'source')
        self.assertEqual(first, plan(d, 3, 'source'))
        self.assertEqual(d, old)
        self.assertTrue(first['can_apply'])
        self.assertEqual([p['block_ids'] for p in first['pages']], [['a'], ['b'], []])
        self.assertEqual([p['source_page_group'] for p in first['pages']], [1, 2, 3])
        self.assertEqual([p['navigation_order'] for p in first['pages']], [0, 1, 2])
        self.assertEqual(first['effects'][0]['page_id'], 'old')
        self.assertEqual(first['effects'][0]['fields']['title']['before'], 'Custom')
        self.assertTrue(any('no included content' in n for n in first['notes']))
        self.assertTrue(all(p['approval']['status'] == 'needs_review' for p in first['pages']))

    def test_legacy_document_is_not_migrated_by_preview(self):
        d = document()
        del d['output_pages']
        before = copy.deepcopy(d)
        self.assertTrue(plan(d, 2, 'source')['can_apply'])
        self.assertEqual(d, before)

    def test_repeat_source_plan_retains_generated_empty_page_once(self):
        d = document()
        first = plan(d, 3, 'source')
        d['output_pages']['pages'] = copy.deepcopy(first['pages'])
        d['output_pages']['pages'][2]['title'] = 'Custom empty source title'
        second = plan(d, 3, 'source')
        self.assertTrue(second['can_apply'])
        self.assertEqual(len(second['pages']), 3)
        self.assertEqual(second['pages'][2]['id'], first['pages'][2]['id'])
        self.assertEqual(second['pages'][2]['title'], 'Custom empty source title')

    def test_changed_generated_source_group_does_not_guess_metadata_reuse(self):
        d = document()
        first = plan(d, 2, 'source')
        d['output_pages']['pages'] = copy.deepcopy(first['pages'])
        d['output_pages']['pages'][0]['title'] = 'Custom authored title'
        d['blocks'].append(block('new', 1))
        proposal = plan(d, 2, 'source')
        self.assertNotEqual(proposal['pages'][0]['id'], first['pages'][0]['id'])
        self.assertNotEqual(proposal['pages'][0]['title'], 'Custom authored title')
        self.assertTrue(any(e['fields']['title']['before']=='Custom authored title' for e in proposal['effects'] if e['action']=='replace'))

    def test_exact_matching_retains_identity_custom_metadata_and_excluded_refs(self):
        d = document()
        d['blocks'].append(block('excluded', 1, review={'status': 'excluded'}))
        first = op.new_page('Authored', ['a', 'excluded'], id='first', type='post', slug='authored-custom', approval={'status': 'reviewed', 'note': 'Human note'})
        second = op.new_page('Second', ['b'], id='second', parent=None, navigation_order=1)
        d['output_pages']['pages'] = [first, second]
        proposal = plan(d, 2, 'source')
        self.assertEqual(proposal['pages'][0]['id'], 'first')
        for key in ('title', 'slug', 'type', 'parent', 'approval'):
            self.assertEqual(proposal['pages'][0][key], first[key])
        self.assertEqual(proposal['pages'][0]['block_ids'], ['a', 'excluded'])
        self.assertEqual(proposal['moves'], [])
        self.assertEqual(proposal['effects'], [])

    def test_empty_existing_page_survives_as_disclosed_extra(self):
        d = document()
        empty = op.new_page('New page', id='empty', slug='custom-empty', navigation_order=7)
        d['output_pages']['pages'].append(empty)
        proposal = plan(d, 2, 'source')
        expected = copy.deepcopy(empty)
        expected['navigation_order'] = 2
        self.assertEqual(proposal['pages'][-1], expected)
        self.assertTrue(any('Existing empty page retained' in n for n in proposal['notes']))

    def test_shared_unknown_and_out_of_range_require_explicit_destinations(self):
        d = document()
        d['blocks'] += [block('shared', 1, provenance={'source_page': 1, 'merged_source_pages': [2]}), block('unknown'), block('outside', 99)]
        proposal = plan(d, 2, 'source')
        self.assertFalse(proposal['can_apply'])
        self.assertEqual({e['key'] for e in proposal['exceptions']}, {'shared', 'unknown', 'outside'})
        assigned = plan(d, 2, 'source', choices={'shared': 2, 'unknown': 1, 'outside': 2})
        self.assertTrue(assigned['can_apply'])
        self.assertEqual(assigned['pages'][0]['block_ids'], ['a', 'unknown'])
        self.assertEqual(assigned['pages'][1]['block_ids'], ['b', 'shared', 'outside'])
        self.assertTrue(all(e['resolved'] for e in assigned['exceptions']))
        self.assertFalse(plan(d, 2, 'source', choices={'shared': True})['can_apply'])

    def test_transitive_semantic_bundle_moves_once_as_whole(self):
        d = document()
        d['blocks'] = [block('im1', 1, type='image', caption_block_id='caption'), block('caption', 2, caption_block_id='im2'), block('im2', 2, type='image')]
        d['output_pages']['pages'][0]['block_ids'] = ['im1', 'caption', 'im2']
        unresolved = plan(d, 2, 'source')
        self.assertEqual(unresolved['exceptions'][0]['block_ids'], ['im1', 'caption', 'im2'])
        proposal = plan(d, 2, 'source', choices={'im1': 2})
        self.assertTrue(proposal['can_apply'])
        self.assertEqual(proposal['pages'][1]['block_ids'], ['im1', 'caption', 'im2'])

    def test_held_placeholder_identity_and_snapshot_metadata_retained(self):
        d = document()
        d['blocks'][0]['review']['status'] = 'excluded'
        placeholder = op.new_page('Source page 1 — needs manual reconstruction', id='hold', manual_reconstruction_source_page=1)
        d['review']['manual_reconstruction_pages'] = {'1': {'blocks': {'a': {}}, 'placeholder': copy.deepcopy(placeholder)}}
        d['output_pages']['pages'].append(placeholder)
        before = copy.deepcopy(d)
        proposal = plan(d, 2, 'source')
        self.assertTrue(proposal['can_apply'])
        self.assertEqual(proposal['pages'][0]['id'], 'hold')
        self.assertEqual(proposal['pages'][0]['block_ids'], ['a'])
        self.assertEqual(proposal['pages'][0]['manual_reconstruction_source_page'], 1)
        self.assertEqual(d, before)
        self.assertTrue(any('unfinished reconstruction' in n for n in proposal['notes']))
        saved = copy.deepcopy(d)
        saved['output_pages']['pages'] = copy.deepcopy(proposal['pages'])
        repeated = plan(saved, 2, 'source')
        self.assertEqual(repeated['pages'], proposal['pages'])
        self.assertEqual(len([p for p in repeated['pages'] if p.get('manual_reconstruction_source_page')]), 1)
        fallback = copy.deepcopy(d)
        fallback['output_pages']['pages'].remove(placeholder)
        self.assertEqual(plan(fallback, 2, 'source')['pages'][0]['id'], 'hold')
        d['blocks'].append(block('shared', 1, provenance={'source_page': 1, 'merged_source_pages': [2]}))
        self.assertFalse(plan(d, 2, 'source', choices={'shared': 1})['can_apply'])
        self.assertTrue(plan(d, 2, 'source', choices={'shared': 2})['can_apply'])

    def test_heading_selection_leaves_unselected_content_and_metadata_unchanged(self):
        d = document()
        d['blocks'] = [block('h1', 1, type='heading', level=1, content='First'), block('a', 1), block('h2', 2, type='heading', level=2, content='Second'), block('excluded', 2, review={'status': 'excluded'}), block('b', 2)]
        parent = op.new_page('Parent', ['h1', 'a'], id='parent', slug='authored-parent', approval={'status': 'reviewed', 'note': 'Keep'})
        child = op.new_page('Child', ['h2', 'excluded', 'b'], id='child', parent='parent', type='page')
        d['output_pages']['pages'] = [parent, child]
        unchanged = plan(d, 2, 'headings')
        self.assertEqual(unchanged['pages'], d['output_pages']['pages'])
        self.assertFalse(unchanged['can_apply'])
        self.assertEqual(unchanged['errors'], [])
        chosen = plan(d, 2, 'headings', selected=[1])
        self.assertTrue(chosen['can_apply'])
        self.assertEqual(chosen['pages'], d['output_pages']['pages'])
        self.assertEqual(chosen['groups'][1]['page_id'], 'child')
        self.assertEqual(chosen['moves'], [])

    def test_heading_partial_reassignment_keeps_emptied_parents_and_excluded_refs(self):
        d = document()
        d['blocks'] = [block('h1', 1, type='heading', level=1), block('a', 1), block('h2', 2, type='heading', level=2), block('excluded', 2, review={'status': 'excluded'}), block('b', 2)]
        d['output_pages']['pages'][0]['block_ids'] = [b['id'] for b in d['blocks']]
        old_metadata = {k: v for k, v in d['output_pages']['pages'][0].items() if k != 'block_ids'}
        proposal = plan(d, 2, 'headings', selected=[1])
        self.assertTrue(proposal['can_apply'])
        self.assertEqual(proposal['pages'][0]['block_ids'], ['h1', 'a'])
        self.assertEqual(proposal['pages'][1]['block_ids'], ['h2', 'excluded', 'b'])
        self.assertEqual({k: v for k, v in proposal['pages'][0].items() if k != 'block_ids'}, old_metadata)
        all_groups = plan(d, 2, 'headings', selected=[0, 1])
        self.assertEqual(all_groups['pages'][0]['block_ids'], [])
        self.assertTrue(any('no included content' in n for n in all_groups['notes']))

    def test_invalid_selection_duplicate_blocks_and_unknown_method_reject(self):
        d = document()
        self.assertFalse(plan(d, 2, 'headings', [0, 0])['can_apply'])
        self.assertFalse(plan(d, 2, 'headings', [100])['can_apply'])
        self.assertFalse(plan(d, 2, 'other')['can_apply'])
        self.assertFalse(plan(d, True, 'source')['can_apply'])
        d['blocks'].append(copy.deepcopy(d['blocks'][0]))
        self.assertFalse(plan(d, 2, 'source')['can_apply'])

    def test_missing_duplicate_references_cannot_be_silently_discarded(self):
        d = document()
        d['output_pages']['pages'][0]['block_ids'].append('gone')
        proposal = plan(d, 2, 'source')
        self.assertFalse(proposal['can_apply'])
        self.assertEqual(proposal['pages'], d['output_pages']['pages'])
        d['output_pages']['pages'][0]['block_ids'] = ['a', 'a', 'b']
        self.assertFalse(plan(d, 2, 'source')['can_apply'])

    def test_source_numeric_order_change_is_disclosed_for_reused_metadata(self):
        d = document()
        p = op.new_page('Custom', ['a'], id='a-page', navigation_order=8)
        d['output_pages']['pages'] = [p, op.new_page('B', ['b'], id='b-page', parent='a-page')]
        proposal = plan(d, 2, 'source')
        self.assertEqual(proposal['pages'][0]['navigation_order'], 0)
        effect = next(e for e in proposal['effects'] if e['action'] == 'source_order')
        self.assertEqual(effect['fields']['navigation_order'], {'before': 8, 'after': 0})
        self.assertEqual(proposal['pages'][1]['parent'], 'a-page')

    def test_source_removed_parent_reset_is_visible(self):
        d = document()
        d['output_pages']['pages'] = [op.new_page('Removed parent', ['a'], id='parent'),
            op.new_page('Child', ['b'], id='child', parent='parent')]
        d['blocks'].append(block('extra', 1))
        d['output_pages']['pages'][0]['block_ids'].append('extra')
        d['blocks'].append(block('new', 1))
        proposal = plan(d, 2, 'source')
        self.assertEqual({e['page_id'] for e in proposal['effects'] if e['action']=='replace'}, {'parent'})
        self.assertIsNone(proposal['pages'][1]['parent'])
        self.assertTrue(any(e['action']=='reset_parent' for e in proposal['effects']))

    def test_excluded_only_source_page_is_retained_incomplete_not_approved(self):
        d = document()
        d['blocks'][0]['review']['status'] = 'excluded'
        proposal = plan(d, 2, 'source')
        self.assertTrue(proposal['can_apply'])
        self.assertEqual(proposal['pages'][0]['block_ids'], ['a'])
        self.assertTrue(any('no included content' in n for n in proposal['notes']))

    def test_heading_partial_selection_rejects_bundle_with_excluded_association(self):
        d = document()
        d['blocks'] = [block('h1', 1, type='heading', level=1),
            block('im', 1, type='image', caption_block_id='caption'),
            block('h2', 2, type='heading', level=2),
            block('caption', 2, review={'status':'excluded'})]
        d['output_pages']['pages'][0]['block_ids'] = [b['id'] for b in d['blocks']]
        proposal = plan(d, 2, 'headings', selected=[0])
        self.assertFalse(proposal['can_apply'])
        self.assertTrue(any('semantic bundle' in error for error in proposal['errors']))

    def test_last_heading_selection_leaves_following_held_fragments_and_placeholder(self):
        d = document()
        d['blocks'] = [block('h1',1,type='heading',level=1), block('a',1),
            block('h2',2,type='heading',level=2), block('b',2),
            block('held',3,review={'status':'excluded'})]
        placeholder = op.new_page('Source page 3 — needs manual reconstruction', id='hold', manual_reconstruction_source_page=3)
        d['review']['manual_reconstruction_pages'] = {'3': {'blocks': {'held': {}}, 'placeholder': copy.deepcopy(placeholder)}}
        d['output_pages']['pages'][0]['block_ids'] = ['h1','a','h2','b','held']
        d['output_pages']['pages'].append(placeholder)
        proposal = plan(d,3,'headings',selected=[1])
        self.assertTrue(proposal['can_apply'],proposal['errors'])
        self.assertEqual(proposal['groups'][1]['block_ids'], ['h2','b'])
        self.assertEqual(proposal['pages'][0]['block_ids'], ['h1','a','held'])
        self.assertEqual(proposal['pages'][1], placeholder)
        self.assertNotIn('held', [move['block_id'] for move in proposal['moves']])
        # A live member still cannot move away from its held semantic partner.
        d['blocks'][3]['caption_block_id'] = 'held'
        self.assertFalse(plan(d,3,'headings',selected=[1])['can_apply'])


if __name__ == '__main__':
    unittest.main()
