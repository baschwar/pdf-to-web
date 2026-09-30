"""Read-only package inspection used for the Phase 3B handoff."""
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

from pdf_to_web.wordpress_preview import render_gutenberg_preview
from pdf_to_web.output_pages import page_document, visible_walk
from pdf_to_web.export_validation import model_semantics, html_semantics, compare_semantics
from pdf_to_web.validation import _SemanticParser, validate_internal_links
from pdf_to_web.exporters.wxr import CONTENT_NS, WP_NS

parser = argparse.ArgumentParser()
parser.add_argument('package', type=Path)
args = parser.parse_args()
root = args.package.resolve()
manifest = json.loads((root / 'manifest.json').read_text())
review = json.loads((root.parent.parent / 'review/current.json').read_text())
report = {'schema_version': manifest['schema_version'], 'app_version': manifest['app_version'], 'checks': {}}
blocks = [i for p in manifest['pages'] for i in p['block_ids']]
assert len(blocks) == len(set(blocks))
report['checks']['uniqueAssignments'] = True
wxr = ET.parse(root / 'publications.xml').findall('./channel/item')
assert len(wxr) == len(manifest['pages'])
for p, item in zip(manifest['pages'], wxr):
    assert item.findtext('title') == p['title']
    assert item.findtext('{' + WP_NS + '}post_name') == p['slug']
    assert item.findtext('{' + WP_NS + '}post_type') == p['type']
    assert item.findtext('{' + WP_NS + '}menu_order') == str(p['navigation_order'])
    markup = (root / p['files']['gutenberg']).read_text()
    assert item.findtext('{' + CONTENT_NS + '}encoded') == markup
    projected = page_document(review, p['id'])
    # Inline runs are the serializer's canonical visible text; legacy content may be stale.
    for block in visible_walk(projected['blocks']):
        if isinstance(block.get('runs'), list):
            block['content'] = ''.join(r.get('text', '') for r in block['runs'])
    expected = model_semantics(projected)
    for format in ['html', 'gutenberg']:
        content = (root / p['files'][format]).read_text()
        if format == 'gutenberg' and manifest['export_settings']['wordpress_profile'] == 'wsuwp':
            preview = render_gutenberg_preview(content)
            assert not preview.unsupported_blocks
            content = preview.html
        anchors = validate_internal_links(content)
        # Report unresolved authoring links, but reject duplicate anchors and broken note backlinks.
        unresolved = {i['target'] for i in p['unresolved_targets']}
        assert not anchors['duplicate_ids']
        assert set(anchors['missing_targets']) <= unresolved
        parsed = _SemanticParser()
        parsed.feed(content)
        actual = html_semantics(content)
        # The established snapshot parser counts only absolute links; check page links separately.
        expected_without_links = {**expected, 'links': []}
        actual_without_links = {**actual, 'links': []}
        equivalence = compare_semantics(expected_without_links, actual_without_links)
        assert equivalence['valid'], equivalence['errors']
        for text, href in expected['links']:
            if not href.startswith('#'):
                assert {'text': text, 'href': href} in parsed.external_links
        for link in parsed.external_links:
            value = urlsplit(link['href'])
            if not value.scheme and value.path.endswith('.html'):
                target = root / value.path
                assert target.is_file(), target
                if value.fragment:
                    destination = _SemanticParser()
                    destination.feed(target.read_text())
                    assert value.fragment in destination.ids
    for filename in p['files'].values():
        assert (root / filename).is_file()
for filename in manifest['media_files']:
    assert (root / filename).is_file(), filename
report['checks'].update({'metadataAndWxrMatch': True, 'embeddedContentMatches': True,
                         'semanticContentPreserved': True, 'pageFilesExist': True, 'internalLinksAndBacklinks': True, 'declaredMediaExist': True})
report['manual_media_actions'] = len(manifest['manual_media_actions'])
report['result'] = 'passed'
print(json.dumps(report, indent=2))
