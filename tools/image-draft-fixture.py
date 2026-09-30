"""Disposable image-review fixture. Pillow is a developer-only fixture dependency."""
import argparse
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from pdf_to_web.project import create_project, save_project
from pdf_to_web.review_state import original_path
from pdf_to_web.web import run_server

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
parser.add_argument('--photo', type=Path, help='Approved test photograph; copied only to ignored fixture')
parser.add_argument('--serve', action='store_true')
parser.add_argument('--mock-provider', action='store_true')
parser.add_argument('--port', type=int, default=8771)
args = parser.parse_args()
root = args.directory.resolve()
if not (root / 'project.json').exists():
    from PIL import Image, ImageDraw
    project = create_project(root, 'Image Draft Review Fixture')
    assets = root / 'extraction/raw/images'
    canvas = Image.new('RGB', (640, 400), 'white')
    draw = ImageDraw.Draw(canvas)
    draw.text((20, 15), 'SYNTHETIC RESULTS: A=10, B=20', fill='black')
    draw.line((50, 60, 50, 330, 600, 330), fill='black', width=4)
    draw.rectangle((120, 200, 230, 330), fill='#245c87'); draw.text((160, 350), 'A: 10', fill='black')
    draw.rectangle((340, 70, 450, 330), fill='#834132'); draw.text((370, 350), 'B: 20', fill='black')
    canvas.save(assets / 'chart.png')
    decoration = Image.new('RGB', (640, 90), '#295d7a'); decoration.save(assets / 'decoration.png')
    if args.photo:
        shutil.copy2(args.photo, assets / 'photo.jpg')
    else:
        Image.new('RGB', (400, 300), '#7b9675').save(assets / 'photo.jpg')
    photograph = Image.open(assets / 'photo.jpg').convert('RGB'); photograph.thumbnail((300, 300))
    source = Image.new('RGB', (850, 1100), 'white'); draw = ImageDraw.Draw(source)
    draw.text((50, 25), 'IMAGE DRAFT REVIEW FIXTURE', fill='black')
    draw.text((50, 50), 'Test photograph and chart. Identification context is supplied by reviewer.', fill='black')
    source.paste(photograph, (50, 100)); source.paste(canvas.resize((600, 375)), (50, 500))
    source.save(root / 'source/fixture.pdf', 'PDF')
    project['source'].update(path='source/fixture.pdf', original_filename='fixture.pdf', page_count=1)
    project['extraction']['status'] = 'complete'; save_project(root, project)
    for name in ('photo.jpg', 'chart.png'):
        shutil.copy2(assets / name, root / 'extraction/assets/images' / name)
    (root / 'extraction/assets/manifest.json').write_text(json.dumps({'assets': [{'filename': n, 'source_page': 1} for n in ('photo.jpg', 'chart.png')]}))
    def image(id, src, **extra):
        return {'id': id, 'type': 'image', 'src': src, 'alt': '', 'caption': '', 'provenance': {'source_page': 1}, 'review': {'status': 'needs_review'}, **extra}
    document = {'schema_version': 'pdf-to-web-normalized-v1', 'metadata': {'title': 'Image Draft Review Fixture', 'page_count': 1}, 'review': {'status': 'needs_review', 'issues': [], 'complex_visuals': [{'id': 'chart-visual', 'source_page': 1, 'type': 'chart', 'status': 'needs_text_equivalent', 'asset_references': ['chart.png'], 'accessibility': {}}]}, 'blocks': [
        {'id': 'heading', 'type': 'heading', 'level': 1, 'content': 'Image Draft Review Fixture', 'provenance': {'source_page': 1}, 'review': {'status': 'approved'}},
        {'id': 'context', 'type': 'paragraph', 'content': 'Photograph credit: NASA. Identification is supplied by the reviewer; do not guess people from their appearance. Chart values are synthetic A=10 and B=20.', 'provenance': {'source_page': 1}, 'review': {'status': 'approved'}},
        image('photo', 'images/photo.jpg'), image('approved', 'images/photo.jpg', alt='Existing approved portrait description', caption='Existing approved caption', review={'status': 'approved'}),
        image('ambiguous', None), image('decoration', 'images/decoration.png', decorative=True, caption='Retained decorative caption', review={'status': 'approved'}),
        image('chart', 'images/chart.png', complex_visual_id='chart-visual'),
    ]}
    original_path(root).write_text(json.dumps(document, indent=2))
print(root, flush=True)
if args.serve:
    if args.mock_provider:
        from pdf_to_web.image_drafts import OllamaProvider, OpenAIProvider
        attempts = {}
        def generate(provider, entry, image_path):
            import time
            time.sleep(.15)
            id = entry['block_id']; attempts[id] = attempts.get(id, 0) + 1
            if id == 'chart' and attempts[id] == 1:
                raise RuntimeError('Synthetic provider failure for retry check')
            return {k: entry[k] for k in ('document_id', 'block_id', 'asset_hash', 'context_hash', 'request_id')} | {'alt': 'Mock draft for ' + id, 'caption': 'Mock caption for ' + id, 'long_description': 'Synthetic chart: A is 10 and B is 20.' if id == 'chart' else None, 'warnings': ['Fixture-only draft: verify against source'], 'decorative': False}
        OllamaProvider.generate = generate
        OpenAIProvider.generate = generate
    run_server(root, '127.0.0.1', args.port, open_browser=False)
