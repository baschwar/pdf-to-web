"""Structure controls for drafts; accepted fields remain in the existing editor."""
import html
import json
from urllib.parse import quote
from . import image_drafts as drafts


def esc(value):
    return html.escape(str(value), quote=True)


def controls(root, document, block):
    block_id = str(block['id'])
    store = drafts.state(document)
    choices = drafts.candidates(root, block)
    association = store['associations'].get(block_id)
    exact = next((c['path'] for c in choices if c['confirmed']), '')
    selected = association or exact
    options = '<option value="">Choose the actual image</option>' + ''.join(f'<option value="{esc(c["path"])}"{" selected" if selected == c["path"] else ""}>{esc(c["path"])}</option>' for c in choices)
    thumbs = ''.join(f'<figure><img class="image-block-preview" src="/api/image-drafts/asset?path={quote(c["path"])}" alt="Candidate {i+1} for image block {esc(block_id)}"><figcaption>Candidate {i+1}: {esc(c["path"])}</figcaption></figure>' for i, c in enumerate(choices))
    visuals = document.get('review', {}).get('complex_visuals', [])
    visual_options = '<option value="">No complex visual association</option>' + ''.join(f'<option value="{esc(v["id"])}"{" selected" if block.get("complex_visual_id") == str(v["id"]) else ""}>{esc(v["id"])} · page {esc(v.get("source_page"))}</option>' for v in visuals)
    entry = store['requests'].get(store['active'].get(block_id))
    status = 'No draft'
    panel = ''
    if entry:
        status = 'Context changed' if drafts.stale(root, document, entry) else {'requested': 'Awaiting response', 'generating': 'Generating', 'ready': 'Draft ready', 'failed': 'Failed', 'cancelled': 'Cancelled', 'rejected': 'Rejected'}[entry['status']]
        if entry.get('draft'):
            value = entry['draft']
            fields = ''.join(f'<label>Draft {label}<textarea name="{field}" rows="3">{esc(value.get(field) or "")}</textarea></label><label><input type="checkbox" name="omit_{field}"{" checked" if value.get(field) is None else ""}> Omit {label}</label>' if field != 'alt' else f'<label>Draft alt text<textarea name="alt" rows="3">{esc(value["alt"])}</textarea></label>' for field, label in [('alt', 'alt text'), ('caption', 'caption'), ('long_description', 'long description')])
            apply = ''.join(f'<button type="button" data-draft-action="apply" data-field="{field}"{" disabled" if status != "Draft ready" or value.get(field) is None or (field == "long_description" and not block.get("complex_visual_id")) else ""}>Apply {label}</button>' for field, label in [('alt', 'alt text'), ('caption', 'caption'), ('long_description', 'long description')])
            panel = f'<form class="draft-edit-form" data-block-id="{esc(block_id)}" data-request-id="{esc(entry["request_id"])}" data-warnings="{esc(json.dumps(value.get("warnings", [])))}" data-decorative="{str(value.get("decorative", False)).lower()}">{fields}<p>{esc("; ".join(value.get("warnings", [])))}</p>{"<p>Decorative suggested: use the existing decorative control to decide.</p>" if value.get("decorative") else ""}<button type="submit"{" disabled" if entry["status"] != "ready" else ""}>Save draft edits</button><div class="draft-actions">{apply}<button type="button" data-draft-action="reject">Reject draft</button></div></form>'
        panel += f'<p class="draft-error" role="status">{esc(entry.get("error") or "")}</p><details><summary>Draft provenance</summary><p>{esc(entry["provider"])} / {esc(entry["model"])} · {esc(entry["prompt_version"])} · {esc(entry["updated_at"])}</p><code>{esc(entry["request_id"])}</code></details>'
    if not entry:
        panel += '<p class="draft-error" role="status"></p>'
    checked = block_id in drafts.selected(document)
    purpose = store['purposes'].get(block_id, '')
    try:
        context = drafts.context(document, block)
        nearby = esc('\n'.join(c['text'] for c in context['nearby_text']))
    except Exception:
        nearby = ''
    return f'''<section class="image-draft-panel" data-block-id="{esc(block_id)}" aria-label="Image description drafts for {esc(block_id)}">
<label><input class="draft-selection" type="checkbox" value="{esc(block_id)}"{" checked" if checked else ""}> Select for drafting</label>
<p class="draft-status" role="status">{status}</p>
<details><summary>Image and context</summary><p>Confirm the actual image for this block. Page matches are candidates only.</p>{thumbs or '<p>No supported local image is available.</p>'}
<form class="draft-association-form" data-block-id="{esc(block_id)}"><label>Image asset<select name="asset_path">{options}</select></label><label>Complex visual<select name="visual_id">{visual_options}</select></label><label>Image purpose / verified context<textarea name="purpose" rows="3">{esc(purpose)}</textarea></label><button type="submit">Save image context</button></form><p>Nearby extracted text:</p><pre class="draft-context">{nearby}</pre></details>
<div class="draft-actions"><button type="button" data-draft-action="export">Export drafting request</button><button type="button" data-draft-action="export-new">New manual request</button><button type="button" data-draft-action="generate">Generate drafts</button><button type="button" data-draft-action="regenerate">Regenerate / retry</button><button type="button" data-draft-action="cancel">Cancel request</button></div>{panel}</section>'''


PROVIDER_HELP = {
    'ollama-local': 'Run Ollama with an already installed vision model, then enter its name above. Images and context stay on this computer. Nothing is downloaded.',
    'openai': 'Set PDF_TO_WEB_OPENAI_API_KEY when launching this app. API usage is paid. You will review and authorize the selected images and context before sending them to OpenAI.',
    'manual': 'Export selected requests to download the images, CSV review sheet, context and response JSON template. Attach the package manually to ChatGPT, Codex or another tool, or write the drafts yourself. Return the completed JSON, then validate and import it. No API key is needed.'
}


def toolbar(document):
    settings = drafts.state(document).get('settings', {})
    provider = settings.get('provider', 'ollama-local')
    model = settings.get('model', 'llava:latest')
    options = ''.join(f'<option value="{value}"{" selected" if provider == value else ""}>{label}</option>' for value, label in [('ollama-local', 'Local Ollama'), ('openai', 'OpenAI API · paid cloud generation'), ('manual', 'ChatGPT / other tool · manual exchange')])
    return f'''<section data-document-id="{esc(document['output_pages']['project_id'])}" id="image-draft-toolbar" aria-labelledby="image-draft-heading"><h2 id="image-draft-heading">Image description drafts</h2><p>Select images below. Drafts are separate from accepted text; applying a field does not approve an image.</p>
<details id="draft-provider-setup"><summary>Provider setup</summary><form id="draft-provider-form"><label>Provider<select id="draft-provider" name="provider">{options}</select></label><label id="draft-model-label"{" hidden" if provider != "ollama-local" else ""}>Installed Ollama vision model<input id="draft-model" name="model" value="{esc(model)}"></label><button type="submit">Save provider settings</button><p id="draft-provider-message" role="status" aria-live="polite"></p></form><p id="draft-provider-help" data-provider-help="{esc(json.dumps(PROVIDER_HELP))}">{esc(PROVIDER_HELP[provider])}</p></details>
<button type="button" data-draft-batch="export">Export selected requests</button><button type="button" data-draft-batch="generate">Generate selected drafts</button><button type="button" data-draft-batch="cancel">Cancel selected requests</button>
<details id="draft-manual-import"><summary>Import manual responses</summary><p>First select images below, then choose <strong>Export selected requests</strong>. The ZIP contains images, a CSV review sheet, a context manifest and a response JSON template. Attach them manually to ChatGPT, Codex or another tool, or write the drafts yourself. Return the completed response JSON for validation and import; the CSV is a review companion.</p><button type="button" data-draft-batch="export">Export selected requests ZIP</button><label>Response JSON file<input type="file" id="draft-response-file" accept=".json,application/json"></label><button type="button" id="draft-import-preview">Validate responses</button><div id="draft-import-findings" role="status" aria-live="polite"></div><button type="button" id="draft-import-confirm" disabled>Import valid drafts</button></details>
<div id="draft-transmission" hidden><h3>Review cloud request</h3><p>Send these images and their displayed context to OpenAI (gpt-4.1-nano). API usage is paid. This permission applies only to this selection.</p><div id="draft-transmission-images"></div><pre id="draft-transmission-content" class="draft-context"></pre><button type="button" id="draft-transmission-send">Send selected images to OpenAI</button><button type="button" id="draft-transmission-cancel">Cancel</button></div>
<p id="draft-message" role="status" aria-live="polite"></p><div id="draft-downloads"></div><button type="button" id="draft-refresh">Refresh draft results</button></section>'''
