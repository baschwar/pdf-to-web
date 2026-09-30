"""Create a disposable synthetic legacy project; optionally serve it for browser checks."""
import argparse
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from test_output_pages import fixture
from pdf_to_web.project import create_project
from pdf_to_web.review_state import original_path, review_path
from pdf_to_web.web import run_server

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
parser.add_argument('--serve', action='store_true')
parser.add_argument('--port', type=int, default=8768)
args = parser.parse_args()
root = args.directory.resolve()
create_project(root, 'Handbook')
document = fixture()
document['blocks'].extend([
    {'id': 'figure', 'type': 'image', 'src': 'images/figure.png', 'alt': 'Synthetic single-pixel square', 'caption': 'Fixture figure', 'provenance': {'source_page': 5}, 'review': {'status': 'approved'}},
    {'id': 'table', 'type': 'table', 'caption': 'Fixture results', 'rows': [['Year', 'Total'], ['2026', '10']], 'table_accessibility': {'header_row': True, 'header_column': False, 'reviewed': True}, 'provenance': {'source_page': 5}, 'review': {'status': 'approved'}}
])
document['review']['complex_visuals'] = [{'id': 'visual', 'source_page': 5, 'type': 'chart', 'status': 'reclassified', 'accessibility': {'short_alt': 'Fixture result', 'long_description': 'The synthetic result is ten for 2026.'}}]
original_path(root).write_text(json.dumps(document, indent=2))
document['review_session'] = {'schema_version': 'pdf-to-web-review-v1', 'revision': 8}
document['blocks'][2]['content'] = 'Saved older-project edit'
review_path(root).parent.mkdir(parents=True, exist_ok=True)
review_path(root).write_text(json.dumps(document, indent=2))
assets = root / 'extraction/raw/images'
assets.mkdir(parents=True, exist_ok=True)
# Tiny synthetic image, not a private source asset.
(assets / 'figure.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jS1sAAAAASUVORK5CYII='))
print(root, flush=True)
if args.serve:
    run_server(root, '127.0.0.1', args.port, open_browser=False)
