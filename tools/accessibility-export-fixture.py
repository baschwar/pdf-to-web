"""Disposable fixture for accessibility-export-browser-check.js."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from pdf_to_web.review_state import original_path
from pdf_to_web.web import run_server

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
parser.add_argument('--serve', action='store_true')
parser.add_argument('--port', type=int, default=8783)
args = parser.parse_args()
root = args.directory.resolve()
subprocess.run([sys.executable, str(Path(__file__).with_name('document-structure-fixture.py')), str(root)], check=True)
source = original_path(root)
document = json.loads(source.read_text())
resources = []
for index, (url, label) in enumerate([
    ('https://example.test/resources', 'Resource library'),
    ('https://example.test/student-help', 'https://example.test/student-help'),
    ('https://example.test/contact', 'Contact support')], 1):
    content = f'Resource {index}: ({label})'
    resources.append({'id': f'resource-{index}', 'type': 'list_item', 'content': content,
                      'children': [], 'runs': [{'type': 'text', 'text': f'Resource {index}: ('},
                                                {'type': 'link', 'text': label, 'url': url},
                                                {'type': 'text', 'text': ')'}],
                      'provenance': {'source_page': 3}, 'review': {'status': 'approved'}})
for block in document['blocks']:
    block['review']['status'] = 'approved'
    if block['id'] == 'p2':
        block.update(type='list', content='\n'.join(r['content'] for r in resources), children=resources)
    if block['type'] == 'image' and block['id'] not in {'image-19', 'image-20', 'image-21'}:
        block['wordpress_url'] = f'http://127.0.0.1:{args.port}/api/preview/images/{Path(block["src"]).name}'
document['review']['issues'] = [{'code': 'block_review_required', 'message': 'A block needed review during extraction.', 'block_ids': ['h1']}]
document['accessibility_review']['decisions']['diagnostic:block_review_required:document'] = {'status': 'approved', 'note': 'Synthetic reviewed note'}
source.write_text(json.dumps(document, indent=2))
if args.serve:
    run_server(root, '127.0.0.1', args.port, open_browser=False)
