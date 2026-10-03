"""Disposable synthetic fixture for document-structure-browser-check.js."""
import argparse
import base64
import json
import sys
from pathlib import Path

from pypdf import PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from test_output_pages import fixture
from pdf_to_web.project import create_project, save_project
from pdf_to_web.review_state import original_path
from pdf_to_web.web import run_server

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
parser.add_argument('--serve', action='store_true')
parser.add_argument('--port', type=int, default=8782)
args = parser.parse_args()
root = args.directory.resolve()
if (root / 'project.json').exists():
    parser.error('Use a new disposable directory; existing projects are preserved.')
project = create_project(root, 'Document and Structure UI Fixture')
source = root / 'source/fixture.pdf'
writer = PdfWriter()
for _ in range(5):
    writer.add_blank_page(width=612, height=792)
with source.open('wb') as output:
    writer.write(output)
project['source'].update(path='source/fixture.pdf', original_filename='Synthetic Review.pdf', page_count=5)
project['extraction']['status'] = 'complete'
save_project(root, project)

document = fixture()
next(b for b in document['blocks'] if b['id'] == 'p2')['review']['status'] = 'needs_review'
image_bytes = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jS1sAAAAASUVORK5CYII=')
assets = root / 'extraction/raw/images'
for index in range(1, 22):
    block_id = 'figure' if index == 1 else f'image-{index}'
    filename = f'{block_id}.png'
    (assets / filename).write_bytes(image_bytes)
    document['blocks'].append({'id': block_id, 'type': 'image', 'src': f'images/{filename}',
                               'alt': 'Synthetic square', 'provenance': {'source_page': 5},
                               'review': {'status': 'approved'}})
document['blocks'][6]['complex_visual_id'] = 'visual'
document['blocks'].insert(7, {'id': 'table', 'type': 'table', 'rows': [['Year', 'Total'], ['2026', '10']],
                             'table_accessibility': {'header_row': True, 'reviewed': True},
                             'provenance': {'source_page': 5}, 'review': {'status': 'approved'}})
document['review']['complex_visuals'] = [{'id': 'visual', 'source_block_id': 'figure', 'source_page': 5,
                                         'type': 'chart', 'status': 'reviewed',
                                         'accessibility': {'short_alt': 'Synthetic square',
                                                           'long_description': 'Synthetic results: the total is ten in 2026.'}}]
original_path(root).write_text(json.dumps(document, indent=2))
print(root, flush=True)
if args.serve:
    run_server(root, '127.0.0.1', args.port, open_browser=False)
