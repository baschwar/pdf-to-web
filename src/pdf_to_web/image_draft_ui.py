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
            apply = ''.join(f'<button type="button" data-draft-action="apply" data-field="{field}"{" disabled" if status != "Draft ready" or value.get(field) is None else ""}>Apply {label}</button>' for field, label in [('alt', 'alt text'), ('caption', 'caption'), ('long_description', 'long description')])
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
    return f'''<section class="image-draft-panel" data-block-id="{esc(block_id)}" data-pending="{str(checked).lower()}" data-request-status="{esc(entry["status"] if entry else "")}" aria-label="Image description drafts for {esc(block_id)}">
<label><input class="draft-selection" type="checkbox" value="{esc(block_id)}"{" checked" if checked else ""}> Select for drafting</label>
<p class="draft-status" role="status">{status}</p>
<details><summary>Image and context</summary><p>Confirm the actual image for this block. Page matches are candidates only.</p>{thumbs or '<p>No supported local image is available.</p>'}
<form class="draft-association-form" data-block-id="{esc(block_id)}"><label>Image asset<select name="asset_path">{options}</select></label><label>Complex visual<select name="visual_id">{visual_options}</select></label><label>Image purpose / verified context<textarea name="purpose" rows="3">{esc(purpose)}</textarea></label><button type="submit">Save image context</button></form><p>Nearby extracted text:</p><pre class="draft-context">{nearby}</pre></details>
<div class="draft-actions"><button type="button" data-draft-action="export">Export drafting request</button><button type="button" data-draft-action="export-new">New manual request</button><button type="button" data-draft-action="generate">Generate drafts</button><button type="button" data-draft-action="regenerate">Regenerate / retry</button><button type="button" data-draft-action="cancel"{" hidden" if not entry or entry["status"] not in {"requested", "generating"} else ""}>Cancel request</button></div>{panel}</section>'''


PROVIDER_HELP = {
    'ollama-local': 'Run Ollama with an already installed vision model, then enter its name above. Images and context stay on this computer. Nothing is downloaded.',
    'openai': 'Set PDF_TO_WEB_OPENAI_API_KEY when launching this app. API usage is paid. You will review and authorize the selected images and context before sending them to OpenAI.',
    'manual': 'Export pending images or selected images to download the images, CSV review sheet, context and response JSON template. Attach the package manually to ChatGPT, Codex or another tool, or write the drafts yourself. Return the completed JSON, then validate and import it. No API key is needed.'
}

MANUAL_EXCHANGE_PROMPT = drafts.MANUAL_EXCHANGE_PROMPT

def toolbar(document, root=None):
    delivery = drafts.manual_response_delivery(root) if root is not None else None
    prompt = drafts.manual_exchange_prompt(root)
    destination = (f'<p id="draft-response-destination">Completed response destination: <code id="draft-response-path">{esc(delivery["directory"])}</code>. Export chooses a unique filename; keep earlier responses.</p><small>Copied instructions and the ZIP include this absolute local path. Share them with your chosen tool only when intended.</small>' if delivery else '<p id="draft-response-destination">Choose a project and export a ZIP to set the response destination.</p>')
    settings = drafts.state(document).get('settings', {})
    provider = settings.get('provider', 'ollama-local')
    model = settings.get('model', 'llava:latest')
    options = ''.join(f'<option value="{value}"{" selected" if provider == value else ""}>{label}</option>' for value, label in [('ollama-local', 'Local Ollama'), ('openai', 'OpenAI API · paid cloud generation'), ('manual', 'ChatGPT / other tool · manual exchange')])
    return f'''<section data-document-id="{esc(document['output_pages']['project_id'])}" id="image-draft-toolbar" aria-labelledby="image-draft-heading"><p>Select images below. New drafts fill empty image fields for review. Existing text is preserved; use Apply to replace it. Images still require approval.</p>
<details id="draft-provider-setup" open><summary>Drafting method</summary><form id="draft-provider-form"><label>Drafting method<select id="draft-provider" name="provider">{options}</select></label><label id="draft-model-label"{" hidden" if provider != "ollama-local" else ""}>Installed Ollama vision model<input id="draft-model" name="model" value="{esc(model)}"></label><button type="submit">Save drafting method</button><p id="draft-provider-message" role="status" aria-live="polite"></p></form><p id="draft-provider-help" data-provider-help="{esc(json.dumps(PROVIDER_HELP))}">{esc(PROVIDER_HELP[provider])}</p></details><p id="draft-selection-summary" role="status" aria-live="polite"></p>
<section id="draft-manual-route"{" hidden" if provider != "manual" else ""} aria-labelledby="draft-manual-heading"><h3 id="draft-manual-heading">Manual drafting with Codex or ChatGPT</h3><p>No API key or model setup is needed. Export a ZIP, download it and send it with the copied instructions, then upload the completed JSON, validate, import drafts and review before approving.</p>
<p>Drafting request ZIPs stay in <code>output/image-drafts/</code> inside the project folder shown above. Open the output folder to use the saved ZIP directly. Optional browser copy creates an extra copy wherever the browser saves downloads.</p><div id="draft-export-controls"><label>Images to export<select id="draft-export-scope" aria-describedby="draft-scope-help"><option value="pending">All pending images</option><option value="selected">Selected images</option></select></label><p id="draft-scope-help"><strong>All pending</strong> uses saved image-review needs, regardless of checkbox selection, and skips requests already generating, ready or rejected. <strong>Selected</strong> uses exactly the image checkboxes you choose below. An empty scope cannot export.</p><div class="button-row"><button type="button" id="draft-export-zip" data-draft-batch="export">Export image-draft ZIP</button></div></div>
{destination}<div id="draft-export-result"><p id="draft-export-message" role="status" aria-live="polite"></p><div id="draft-downloads"></div></div>
<p id="draft-manual-flow">After downloading, copy these instructions. Attach the ZIP in Codex or ChatGPT, paste the instructions, then import the returned JSON below and review each image. <a href="/help#image-descriptions">Manual drafting help</a>.</p><div class="button-row"><button type="button" id="draft-copy-instructions" class="neutral-action" aria-describedby="draft-manual-flow">Copy instructions for Codex/ChatGPT</button></div><p id="draft-copy-instructions-status" role="status" aria-live="polite"></p><textarea id="draft-copy-instructions-text" aria-label="Instructions for manual copying" rows="8" readonly hidden>{esc(prompt)}</textarea>
<details id="draft-manual-import"><summary>Import manual responses</summary><ol><li>Upload the completed <strong>Response JSON file</strong> returned by your drafting tool, then select <strong>Validate responses</strong>. Every alt field needs usable text. The ZIP's original response-template.json is blank and cannot be imported as completed drafts; the CSV is a review companion.</li><li>Validation checks the file without importing. Inspect the results, then choose <strong>Import drafts into image fields</strong>. Save unsaved authoring first. Importing suggestions does not approve images; review each image and description before approving.</li></ol><label>Completed response JSON file<input type="file" id="draft-response-file" accept=".json,application/json"></label><button type="button" id="draft-import-preview">Validate responses</button><div id="draft-import-findings" role="status" aria-live="polite"></div><button type="button" id="draft-import-confirm" disabled>Import drafts into image fields</button></details></section>
<section id="draft-provider-route"{" hidden" if provider == "manual" else ""} aria-labelledby="draft-provider-heading"><h3 id="draft-provider-heading">Generate with the selected provider</h3><p id="draft-generation-help">Generate only the checked images. Local Ollama uses an installed model on this computer; OpenAI uses paid API access and asks for confirmation before sending. Generated drafts still need review.</p><div class="button-row"><button type="button" data-draft-batch="generate" aria-describedby="draft-generation-help">Generate selected with provider</button><button type="button" data-draft-batch="cancel" hidden>Cancel selected requests</button></div>
<div id="draft-transmission" hidden><h3>Review cloud request</h3><p>Send these images and their displayed context to OpenAI (gpt-4.1-nano). API usage is paid. This permission applies only to this selection.</p><div id="draft-transmission-images"></div><pre id="draft-transmission-content" class="draft-context"></pre><button type="button" id="draft-transmission-send">Send selected images to OpenAI</button><button type="button" id="draft-transmission-cancel">Cancel</button></div>
</section><p id="draft-message" role="status" aria-live="polite"></p><div class="button-row"><button type="button" id="draft-refresh">Refresh draft results</button><button type="button" id="draft-populate">Fill empty fields from existing drafts</button></div></section>'''
