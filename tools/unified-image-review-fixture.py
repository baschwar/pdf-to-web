"""Clone a synthetic 21-image/19-pending project and serve with isolated settings."""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from test_unified_image_review import UnifiedImageReviewTests
from pdf_to_web.web import WebAppConfig, browser_url, create_app

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
parser.add_argument('--serve', action='store_true')
parser.add_argument('--existing-fixture', action='store_true')
parser.add_argument('--port', type=int, default=18770)
args = parser.parse_args()
root = args.directory.resolve()
if args.existing_fixture:
    if not (root / 'qa-fixture.json').is_file():
        parser.error('Only a marked synthetic QA fixture may be reused.')
else:
    if root.exists():
        parser.error('Choose a new disposable directory; existing data is preserved.')
    test = UnifiedImageReviewTests()
    test.setUp()
    try:
        test.model()
        shutil.copytree(test.root, root)
        (root / 'qa-fixture.json').write_text(json.dumps({'synthetic': True}))
    finally:
        test.doCleanups()
print(root, flush=True)
if args.serve:
    import uvicorn
    config = WebAppConfig(project=root, host='127.0.0.1', port=args.port,
                          recent_store=root.parent / 'isolated-recent.json')
    print(browser_url(config), flush=True)
    uvicorn.run(create_app(config), host=config.host, port=config.port, log_level='warning')
