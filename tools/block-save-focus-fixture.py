"""Disposable nested-list fixture for block-save-focus-browser-check.js."""
import argparse
import json
import sys
from pathlib import Path
from pypdf import PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from review_helpers import stamp_fixture_approvals
from pdf_to_web.project import create_project, save_project
from pdf_to_web.review_state import original_path

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
args = parser.parse_args()
root = args.directory.resolve()
if (root / 'project.json').exists():
    parser.error('Use a new disposable directory; existing projects are preserved.')
project = create_project(root, 'Block save focus fixture')
source = root / 'source/fixture.pdf'
writer = PdfWriter()
for _ in range(3):
    writer.add_blank_page(width=612, height=792)
with source.open('wb') as stream:
    writer.write(stream)
project['source'].update(path='source/fixture.pdf', original_filename='Synthetic focus review.pdf', page_count=3)
project['extraction']['status'] = 'complete'
save_project(root, project)

def block(id, type, content, page, **extra):
    return {'id': id, 'type': type, 'content': content, 'provenance': {'source_page': page},
            'review': {'status': 'approved'}, **extra}

url = 'https://example.test/resources'
child = block('resource', 'list_item', 'Resources: (' + url + ')', 2,
              runs=[{'type': 'text', 'text': 'Resources: ('},
                    {'type': 'link', 'text': url, 'url': url}, {'type': 'text', 'text': ')'}],
              source_links=[{'url': url, 'inline_preserved': True}], children=[])
child['children'] = [block('nested', 'list', 'Follow the instructions.', 2,
                           children=[block('nested-item', 'list_item', 'Follow the instructions.', 2, children=[])])]
document = {'schema_version': 'pdf-to-web-normalized-v1', 'metadata': {'title': 'Focus fixture'},
            'review': {'status': 'needs_review', 'issues': [], 'complex_visuals': []},
            'blocks': [block('title', 'heading', 'Focus fixture', 1, level=1),
                       block('instructions', 'list', child['content'], 2, children=[child]),
                       block('tail', 'paragraph', 'Final instructions.', 3)]}
stamp_fixture_approvals(document)
original_path(root).write_text(json.dumps(document, indent=2))
print(root)
