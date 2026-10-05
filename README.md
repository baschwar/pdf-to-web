# PDF to Web

Current development version: **0.7.1**. This patch stabilizes existing review,
source-preview and export workflows without changing stored schema versions.
Bulk PDF importing has not been started in this version.

PDF to Web is a local-first conversion tool that turns PDF publications into a
reviewable normalized document, semantic HTML, Gutenberg block markup, and
WordPress WXR/XML. [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf)
is the Apache-2.0-licensed extraction engine on which this project builds. PDF
to Web adds its own normalized document model, review workflow, source-aware
editing, validation, and web and WordPress exporters; it is not a fork of
OpenDataLoader. The normalized document remains independent of the extraction
engine and every export format. See [Third-party notices](THIRD_PARTY_NOTICES.md)
for the principal runtime and bundled dependencies.

Extraction uses deterministic local processing and never enables OpenDataLoader
hybrid or external AI processing. The completed Phase 2 foundation provides a
local FastAPI/PicoCSS structural-review application over the same normalized
document model and exporters used by the CLI. Phase 3A adds human accessibility
authoring and downloadable review reports without claiming automated WCAG
conformance.

![PDF to Web Structure screen showing a selected heading outlined in the source PDF beside its reading-order review controls](docs/images/structure-review.png)

[Watch the 54-second silent end-to-end walkthrough](docs/media/pdf-to-web-walkthrough.mp4)

## Generated files stay in the project

Every app export saves inside the current project's `output/` folder, including
projects opened from a chosen folder. Results show the exact path and **Open
output folder**. This action opens the system file manager without downloading.
If it is unavailable, use the displayed path. No global browser settings change.

| Output | Folder inside the current project |
| --- | --- |
| Image drafting requests | `output/image-drafts/` (unique ZIP filenames) |
| Semantic HTML and its local assets | `output/html/` |
| Gutenberg / WXR | `output/wordpress/blocks/` / `output/wordpress/wxr/` |
| Image upload ZIP and mapping CSV | `output/wordpress/media-upload.zip` / `output/wordpress/reports/` |
| Arranged page packages | `output/pages/`, `output/pages.zip`, or `output/page-N/` and its ZIP |
| Accessibility and export reports | `output/reports/` |
| Previous app output snapshots | `output/history/` (dated unique folders) |

Before replacing reusable output filenames, the app copies previous generated
files into a unique history folder; prior drafts already have unique names.
History is retained locally for recovery and is not offered as a current
publication download. Failed preservation stops the new export before replacement.
Source PDFs, extracted originals and existing Downloads files are preserved.
**Optional browser copy** is collapsed by default; using it creates another copy
wherever the browser saves downloads. Attach or upload saved project files directly
for a project-only workflow. CLI commands retain their documented output behavior.

Documents without included images skip drafting and WordPress media mapping;
review the text, then export and copy content directly. Link-label editors offer
**Save and approve** to save the label and approve the displayed containing block
in one Undoable change. Other unresolved link findings still require correction.
Ordinary **Save link text** and later material edits require fresh review.

## Development setup

macOS or Linux:

```sh
cd pdf-to-web
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
npm install
pdf-to-web doctor
```

Windows PowerShell:

```powershell
cd pdf-to-web
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
npm install
pdf-to-web doctor
```

OpenDataLoader requires Python 3.10 or newer and Java 11 or newer. The doctor
command checks both and looks for common Homebrew Java installations when the
default `java` command is too old.

Poppler is a separate system dependency for source-page rendering; installing
the Python project does not install its `pdfinfo` and `pdftoppm` commands.
On macOS with [Homebrew](https://formulae.brew.sh/formula/poppler) already set up:

```sh
brew install poppler
command -v pdfinfo
command -v pdftoppm
pdftoppm -v
.venv/bin/pdf-to-web doctor
```

On Debian/Ubuntu, use `sudo apt-get install poppler-utils`. On Windows, install
Poppler through your approved package source and add its executable directory
to `PATH`; verify with `where.exe pdfinfo`, `where.exe pdftoppm`, and
`pdf-to-web doctor`. Respect any administrator or security prompt.

If Structure reports **Poppler pdftoppm was not found on the app’s PATH**,
finish setup, stop and relaunch PDF to Web, then reopen the same project. The
macOS launcher includes `/opt/homebrew/bin` and `/usr/local/bin` so standard
Homebrew installations work even with a minimal Finder/Terminal PATH. For a
custom installation, launch from a terminal whose PATH includes Poppler.
Moving the PDF or creating another project does not supply the renderer, and
project regeneration is unnecessary. **Retry source page** handles transient
failures; **Open source PDF** remains available for comparison.

Extracted image assets are different from rendered source pages. Existing
`review/source-pages/page-*.png` files can display even without Poppler, while
uncached pages need it. A supplemental-extraction error mentioning **Pillow**
concerns the Python image package, not Poppler; inspect that separate error
before installing anything or re-extracting a project.

Node.js 20.19 or newer and `npm install` are required only for the
WordPress Preview; Semantic Preview and the other Python workflows do not need
Node.js.

### Desktop launchers

After completing development setup once, macOS users can double-click
`Launch PDF to Web.command` in Finder. If macOS blocks the first launch,
Control-click the file, choose **Open**, and approve it. Windows users can
double-click `Launch PDF to Web.bat` after setup. Both launchers use the local
`.venv` and run the same `pdf-to-web serve` command documented below.

The launchers report missing setup without installing software. The macOS
launcher adds the standard Homebrew executable paths for its app process only.

**Quit PDF to Web** is available in the navigation on every screen. Keep working
is the initial confirmation choice. Check and save edits in every open tab before
quitting; the dialog identifies unsaved fields or choices in the current tab and
offers an explicit Quit without saving action. Cancel or Escape preserves those
fields. Saved project files are kept; Quit does not save or change review decisions.

Quit refuses while processing, saves, downloads or queued/running image generation
are active. Finish the work, then open Quit again. Only the server owned by
`pdf-to-web serve` is stopped, and its dedicated launcher process ends normally.
Terminal or shared command-prompt windows may stay open according to their profile
settings; unrelated windows/processes are never terminated. An externally managed
FastAPI server has no Quit capability and must be stopped through its own launcher.
After accepted Quit and repeated unavailable local health checks, the dialog
becomes **PDF to Web has stopped. It’s safe to close this browser tab or window.**
Confirmation controls disappear and focus moves to the stopped heading. Offline,
HTTP-error and timeout cases keep uncertainty/retry feedback rather than claiming
success. Failures remain visible and allow retry. Actual Windows/window-closing
acceptance remains pending.

### Platform support

The application is developed and manually tested on macOS. Its Python paths,
local configuration, browser startup, and native file chooser have Windows and
Linux implementations, and OpenDataLoader supports Windows when Java is on
`PATH`. Windows also requires Python 3.10+, Java 11+, and Poppler utilities on
`PATH`; Node.js is optional as described above.

Windows should currently be treated as **supported but not yet validated**:
the automated suite has not been run on a Windows host and there is not yet a
Windows CI job. Please report platform-specific installation or file-picker
issues in GitHub Issues.

## Extraction spike workflow

```sh
pdf-to-web project create /path/to/my-report
pdf-to-web import /path/to/report.pdf --project /path/to/my-report
pdf-to-web extract --project /path/to/my-report
pdf-to-web normalize --project /path/to/my-report
pdf-to-web export all --project /path/to/my-report
pdf-to-web validate-exports --project /path/to/my-report
pdf-to-web validate-export-corpus /path/to/projects --output /path/to/reports
```

Use `--profile wsuwp` with the Gutenberg or all export command to exercise the
WSUWP profile. Project-level profile, hero, section, and WordPress publication
defaults live in `project.json`.

`validate-exports` generates the complete publication set through the existing
exporters and writes `output/reports/export-validation.json` plus
`output/reports/export-validation.md`. The gate checks HTML structure, internal
anchors, Gutenberg block balance, local Gutenberg preview conversion, WXR
metadata and embedded content, and semantic content preservation across the
reviewed model and each output. External URLs are preserved syntactically; core
validation never depends on network access.
`validate-export-corpus` runs that gate for each immediate document-project
folder and generates a corpus-level JSON and Markdown result matrix.

WordPress exports distinguish local extracted assets from publishable media.
Configured HTTP(S) URLs generate normal image blocks, with attachment IDs only
when explicitly supplied. Unresolved meaningful images generate visible
replacement placeholders instead of broken URLs. Their extracted files and
metadata are written to `output/wordpress/assets/` and
`output/wordpress/reports/media-manifest.{json,md}` for later Media Library
mapping. Direct upload is intentionally outside the current scope.

On **Export**, first choose an **Image filename prefix** and select **Prepare
images ZIP and mapping CSV**. The default uses the document title; for example,
`my-report-` produces `my-report-image1.png`, `my-report-image2.png`,
etc. Original assets are unchanged. Names follow immutable extraction order and
remain stable when content is reordered, excluded or arranged into output pages.
The prefix persists with review state and supports **Undo last change**.

Export step 1 groups **Prepare images ZIP and mapping CSV** with **Undo last
change**. In step 2, each media file chooser and its matching/import button share
a row. Step 3 groups **Copy page title** and **Export reviewed document** in one
action row. These rows wrap on narrow screens. Primary actions that move the
export workflow forward are green; Undo and Copy are gray, and disabled actions
remain visibly disabled.

Download `output/wordpress/media-upload.zip` and
`output/wordpress/reports/media-mapping.csv` before exporting content. The ZIP
contains all included local image assets, including decorative images; excluded
content stays excluded, and repeated references share a file. Decorative images
do not need mapping rows. Missing local assets are reported in the media manifest.

Instead of entering every URL and attachment ID manually, use WordPress Tools >
Export to download a Media WXR/XML file after uploading the images, then choose
**Match WordPress media** on PDF to Web's Export screen. Exact filenames are
matched into `media-mapping.csv`; unmatched or duplicate filenames are left for
manual review rather than guessed. XML matching preserves current reviewed alt
text and captions, even if they changed after preparing the CSV.

**Use manual CSV mapping** is visible beside XML matching. Unmatched/ambiguous
results and XML errors reveal the existing manual tools and link directly to them;
successful matching still focuses Export readiness. Open the project output folder
and edit the current mapping CSV in `output/wordpress/reports/` after preparing images, edit `wordpress_url` and optionally
`wordpress_attachment_id`, and keep `block_id` and `asset_filename` unchanged.
Verify each image before importing. This uses the existing validation and Undo;
opening the tools never modifies mappings or approvals.

Deleting and re-uploading unchanged WordPress images can assign new attachment
IDs while keeping their filenames and URLs. Matching reports these as awaiting
explicit refresh. Select **These are the same reviewed images; refresh existing
attachment IDs**, then match the same XML again. Only a unique exact filename
with the same saved URL can refresh; ambiguous, missing or different-URL matches
keep the current mapping and show their reason. Repeating current matches reports
them as already current without another saved revision. XML cannot establish that
image bytes are unchanged. Changed source images require fresh alternatives and
linked-description review; this mapping operation never approves pending content.
Use manual CSV mapping to explicitly select different URLs.
The result leads with **Mappings updated**, not filename matches. If confirmation
was not selected, it explicitly says the attachment IDs were not refreshed and
repeats that warning at the focused Export readiness section. Filename matches
only establish names; Already current means no change was needed. Choose the XML
first, then select refresh: a new file selection clears the checkbox and displays
a notice when it clears an existing confirmation.

Mapping instructions appear as ordered steps. XML matching and CSV import scroll
to Export readiness and focus its heading. Ready exports focus the saved-output
result; successful content copying stays at its button. Blocked or stale actions
focus readiness with recovery guidance. Use **Continue to Export and copy content** to
return to the content controls. Readiness includes a link to a result table
with prominent totals and lists every unmatched or ambiguous image's filename,
description, source page and link to its Structure block. Open the saved mapping
CSV in the output folder to finish any remaining mappings manually; the optional
browser-copy link makes a separate copy.

Alternatively, enter each full WordPress media URL and optional attachment ID in
the CSV and import it under **Map images manually with a CSV**. Stable `block_id`
values correlate attachments with source figures even when WordPress renames
files. After mapping, **Export and copy content** generates the HTML, Gutenberg
or WXR with mapped URLs. Unresolved meaningful images remain visible WordPress
upload placeholders. Mapping changes clear stale copy/download results until
export is regenerated. Media routing changes preserve content approval; source, alt, caption and
authored-description edits require fresh review. Counts, review links and the
Export button update immediately after XML/CSV mapping and Undo. Earlier approvals
lost to media-only changes can be restored explicitly from retained history as
described below. A failed import leaves saved review state unchanged. Standalone semantic HTML copies unmapped local images to
its `assets/` folder with the same meaningful names and uses mapped URLs when
available. Changing the prefix after uploading requires manual filename matching
or a new upload. This workflow needs no WordPress credentials in PDF to Web.

Authenticated WordPress media upload and direct draft publishing are deferred
in `docs/FUTURE_FEATURES.md`.

## Local review application

Launch the local review interface:

```sh
pdf-to-web serve
```

The Projects screen can create a project, import its source PDF, run extraction
and normalization, open an existing project, and reopen recent projects. Choose
**Folder I choose** and **Choose destination folder** to use that exact folder as
the project root. The name does not add another directory below it. **Default
location** creates a named folder under `~/Documents/PDF to Web Projects`; the
full destination is shown before you choose the input PDF. The input PDF's folder
and project folder are separate choices. The original is preserved and a copy
is placed in `source/` (a PDF already there is used in place).

Each project contains its own `project.json`, source copy, extraction/assets,
review/history/source-page cache and exports. The full working path appears on
every workflow page and in Recent projects. Existing loose files are preserved,
but an existing project or conflicting `extraction`, `review` or `output` entry
is rejected. An existing `source` folder may contain only regular PDF files;
filename collisions use a suffix without overwriting. Picker cancellation
creates no files. A later conversion failure retains the partial project at its
reported destination and leaves the previous project open. Reopen the retained
folder to inspect its incomplete status; correct the error, use the existing CLI
to import the PDF if its source copy is missing, then finish extraction and
normalization before reviewing. No existing projects
are moved. Global Recent projects preferences remain in the application config
directory described below. A failure to update that list displays a warning;
the saved project can still be opened directly. Choosing a folder does not install
the PDF renderer.

The command prints
and opens a one-use bootstrap URL, binds only to `127.0.0.1`, and keeps all
project data local. Use `--project /path/to/my-report` to open a known project at
startup or `--no-browser` to print the URL without opening it automatically.
Docker is not required to run, review, preview, or export a project.

Chrome, Safari, Firefox, and Edge are supported for the localhost review app.
Normal startup opens the one-use `/bootstrap/...` URL in the system default
browser, sets the local session cookie, and redirects to `http://127.0.0.1:8765/`.
With `--no-browser`, open the clearly printed bootstrap URL in the browser you
want to test.

Recent-project configuration contains only project title, canonical local path,
and last-opened timestamp. On macOS it is stored at
`~/Library/Application Support/PDF to Web/recent-projects.json`; Windows uses
`%LOCALAPPDATA%/PDF to Web/recent-projects.json`, and Linux uses
`$XDG_CONFIG_HOME/pdf-to-web/recent-projects.json` (falling back to
`~/.config/pdf-to-web`). Set `PDF_TO_WEB_CONFIG_DIR` to override the directory.
The app does not scan the filesystem for projects.

The Semantic HTML preview uses only Python dependencies. The optional WordPress
Preview additionally requires Node.js 20.19 or newer and the local packages
installed by `npm install`; it never requires WordPress, PHP, MySQL, Docker, or
an external service. See `docs/GUTENBERG_PREVIEW.md` for its compatibility and
security boundaries.

The original document filename appears above each workflow screen and in the
browser tab title. Two compact filter rows below Previous/Next combine **Review
state** (All, Needing review, Approved, Excluded) with **Block type** (All types,
Headings, Paragraphs, Lists, Images, Tables, Other). Other includes quotes,
captions, callouts and unclassified blocks. Each row's counts reflect the other
row's selection; the visible/total count reports their intersection. Linked image
descriptions affect the image's review state and do not create extra block rows.
The active links are emphasized; both choices persist separately for each project
in the browser tab, including Save, approval, Undo and reopening.
Choosing either filter row selects the first matching block in saved reading
order and brings it below the sticky controls, with its source context selected.
This first-result behavior applies to explicit filter changes and Reset filters.

Saving returns to the edited block when it still matches; otherwise it advances
within the chosen filters. Approval advances within the results. An empty view
keeps both choices, explains that nothing matches and offers **Reset filters**.
Before filters hide an unsaved editor, Keep editing is the initial confirmation
choice. Confirming keeps its text in this tab; reset filters to show it again and
save before leaving or reloading. Other saves, structural actions and Undo refuse
to discard those unsaved fields. Stale saves preserve entered fields and newer
saved decisions. Explicit finding links reveal their target and explain any
filter changes; ordinary saves do not silently open All. Nested link edits remain
associated with their owning list. Corrections opened from Accessibility still
return to the finding.
Arrange Pages keeps **Continue to Preview** separate from the
four arrangement actions, aligned to the right. Preview's top and bottom
**Continue to Export** buttons also align to the right, with space between the
Semantic HTML and WordPress Preview mode buttons.

Final workflow actions align to the right throughout Document, Structure,
Accessibility, Arrange Pages, Preview and Export, including the green completion
handoffs and page/document export actions. Action rows wrap on narrow screens.
A floating **Back to top** button appears at the lower right on every app screen
after scrolling down. It returns to the top and focuses the application header
for keyboard navigation, without animation, navigation or changes to unsaved edits.

Accessibility findings identify their source page and current Reading order block
number, including the owning list for nested-link findings. Open block controls
align to the right; numbering follows reordering and Undo and includes excluded
blocks in the same numbering used by Structure.

Visual-description cards show current text-equivalent readiness instead of an
unconditional warning. Short alt text plus either a long description or adjacent
equivalent is required for a complex image; adjacent text is optional when a long
description is present, and recovered source text is always optional. The long
description or its adjacent-text fallback is included beside the image in exports. **Reviewed**
explicitly approves the linked image too. **Not applicable** records that this
description is unnecessary without excluding the image. Saving unchanged text
preserves image approval. All changes support Undo. Structure's green completion
message requires resolved block decisions and reviewed or inapplicable descriptions.
Filled text alone does not complete a description: **Reclassified** still needs a
manual **Reviewed** or **Not applicable** decision. Document, Structure,
Accessibility and Export use this same distinction. Export findings link directly
to the affected block or description, with its source page and readable context.

For older approved lists containing pending nested items, reopening can preserve
the existing approval only when a local retained snapshot proves the exact same
content, project, review session and approval timestamp, with no newer conflicting
history or child edit. The versioned evidence records the snapshot filename and
SHA-256 without approving children or changing the original decision timestamp.
Without that proof, the list appears as needing review with an explanation that
the earlier approval cannot be verified. Review it and approve the saved content;
Undo restores the preceding decision and its evidence.

Each primary block editor offers **Save and approve** beside its ordinary save
button. It saves the displayed fields and explicitly approves the resulting block
in one operation, with one Undo step. This includes recovering retained list text
as one item; it does not infer nested steps. Invalid list structure or an image
without alt text or a decorative decision prevents the operation and shows an
inline explanation while retaining your entered fields. Ordinary Save still
requires fresh review after content changes. Approve uses saved content; when
there are unsaved fields it directs you to Save and approve. Save or undo edits
in other editors first so approval cannot discard them. Image editors display alt,
caption, every explicitly associated long/adjacent description and current review
state together. Their **Save and approve** action approves exactly that image and
its displayed descriptions in one Undo revision. Missing text, ambiguous/missing
associations or a stale project snapshot reject the entire action. Existing pending
descriptions are never bulk-approved merely by opening or saving a project.
Successful image Save and approve advances like solo Approve to the next block
needing review in the current filter and reading order, wrapping to earlier pending
work when necessary. The active filter stays selected; after its last item, the
empty state offers Show all blocks with usable navigation. Failed validation/save
or a stale snapshot stays on the current image and preserves entered fields.
This navigation change does not alter existing approvals or require repeat review.
Ordinary image Save keeps edited content awaiting review; later material edits
invalidate current approval. A long description is sufficient without adjacent
text. Adjacent text is authored text, not a reference to an existing instruction
block. Linked descriptions have one editor inside their Reading order image;
there is no extra description approval stage. An image with a pending description
appears in **Needing review**, even when an older image-only approval is saved.
**Description use** allows an explicit **No separate description needed** or
exclusion decision in the same Save and approve action. Optional classification,
recovered source text and reviewer notes remain editable there. Standalone or
ambiguous visual records retain their separate editor. Affected output-page review
remains separate.

On **Accessibility**, unresolved document findings appear first. **Bulk review**
is optional and starts collapsed, showing **Pending only** records when opened.
Use **Show records** to inspect **Completed** or **All records**; approved,
excluded and not-applicable records remain available for explicit changes.
Visible status pills use green for Approved/Reviewed, amber for pending states
and gray for Excluded/Not applicable, with text identifying the actual state.
The visible saved-record count can include both an image and its description;
it is not added to the overall task count. Groups use classification. Use
**Classification filter**, per-row checkboxes or **Select all visible records**,
then **Review state options** and **Apply**. Inspect the displayed scope/count and
confirm it explicitly. Changing classification or Show records clears selection
and any unconfirmed batch. Select all includes only the current visible scope. Block approvals,
description reviews and accessibility decisions have separate permitted states;
mixed record types cannot be changed in one batch. Image-block approval also
reviews its associated descriptions shown in that row. Server validation checks
the selected IDs, visible scope, project snapshot, permissions and required text.
Any invalid item rejects the entire batch with its exact reason; one Undo restores
a successful batch. No actual user approvals are made automatically.

Document shows review progress and **Review structure** at the top, with one set
of counts. **Pending** counts remaining block and description review tasks, with
each kind shown separately. A pending linked description is included in its
image's task, rather than counted again. For example, 54 blocks with five images
awaiting description review show **49 blocks reviewed**, **5 image reviews** and
**Pending 5 review tasks**, with the five included description reviews explained
separately. Standalone descriptions add their own tasks. **Total 54 blocks** still
counts document blocks. The same
task summary appears in Structure, Accessibility, Arrange Pages, Preview and
Export. Once block decisions and required descriptions are resolved, it offers
the same green **Continue to Accessibility** handoff as Structure. Remaining
Accessibility findings are reviewed there; an empty diagnostic count does not
produce a yellow warning. Unresolved extraction diagnostics appear inside this
same summary, with the recorded cause, publication impact and links to the
affected block or description. A diagnostic concerning one of 54 pending block
reviews does not make 55 review tasks. Checks without a block target explain
their source-page or document scope and offer the original PDF and Accessibility
decision link. Missing targets are identified rather than replaced with guessed
links. Manual approval or exclusion resolves historical block-review notes;
Undo restores them, and resolved notes remain in Accessibility history.
Metadata labels are larger and bold above their values.

Description links open the exact editor and keep a visible selection outline and
**Selected description for review** marker. Each editor shows status once, source
context, the reason review is needed and the next action. Reclassified text needs
a manual decision; a saved timestamp alone does not prove earlier approval.
Only an actual edit invalidating a recorded Reviewed decision adds a changed
since Reviewed reason and the affected field names. Fresh review clears that
reason; save/reopen and Undo preserve it. These optional review annotations use
the existing stored document and do not migrate or approve existing data.

Field labels are consistently bold, including generated controls; values and help
remain ordinary weight. Export has one readiness list per target, Arrange Pages
labels its separate Structure and Page decisions, and repeated status/guidance is
removed. Title-export details remain available in **How the title is exported**.
Preview retains forward actions at the top and bottom of its long content.

Structure gives **Image description drafts** a distinct heading and outlined
section. **Open drafting tools (optional)** keeps its longer tools collapsed;
**Draft image descriptions** links beside image alternatives and in Accessibility
open and focus that workflow. **Longer image descriptions** also stays collapsed
so Source page and Reading order stay in view. The description summary
shows how many need review; finding links expand and focus the relevant card.
The section explains when to add a longer description and when to choose
**Not applicable** because short alt text is sufficient. Extraction details are
collapsed under **Why these images appear here**.
Extraction flags pages with at least five retained images or assets as possible
complex visuals. This heuristic requires human classification; a saved image
long description also creates a description record. All images remain in Reading
order, and completed descriptions remain available for editing and export.
Manual response instructions use four ordered steps. Approved blocks have a
disabled gray Approve button until an edit or Needs review action requires review
again. **Saved review history** contains Undo, including earlier sessions' saved
changes. A compact gray **Undo last saved change** button is also available in
the sticky Reading order toolbar while editing blocks. Both restore the most
recent saved project change and are disabled when no revision snapshots remain.
Undo keeps the selected block in view when that block remains in the restored
document. Unsaved typing is not a saved revision.

Historical extraction block-review notes collapse under **Resolved extraction
note** after their referenced blocks are approved or excluded. Other Accessibility
findings can still need review. URL-as-link-text warnings link to Structure, where
**Link text** edits preserve the destination and rich formatting; edits require
review again. Link-label edits with footnote offsets are held for structural
review rather than changing citation positions silently.

Reload keeps the selected reading-order block. Changing the filter selects the
next matching block (or the previous match) when necessary; an empty filter
shows a contextual explanation and **Show all blocks** link beside the disabled
navigation in the sticky toolbar. An empty Needing review filter says no items
are left in that filter; other description or Accessibility tasks may remain.
Recovery restores All and focuses the remembered block (or the first available
block) without reloading or discarding unsaved typing. Filters do not switch
automatically when the last matching block is approved.
When saved evidence shows an approved block changed, Structure and Accessibility
explain why fresh approval is needed. Never-approved blocks keep their ordinary
review status. Undo restores both the content and its approval reason.

In Export, **My WordPress template supplies the page title (H1)** defaults to on.
Copy the displayed page title into WordPress's title field, then paste the generated
body or Gutenberg blocks. Semantic HTML provides both a standalone page with one
H1 and a separate `.body.html` without the title heading; only the body gets the
copy action in this mode. Gutenberg and WXR omit the title heading. **Body headings**
defaults to H2 sections; choose nested headings to retain hierarchy without skipped
levels. Settings persist in the review document and support Undo. Source heading
IDs, text, provenance and review decisions are retained. Legacy CLI exports keep
their title unless template mode was saved, and all publication heading projections
limit title H1s to one. The page template must supply its own single H1.

Reviewed content is stored in `review/current.json`; immutable normalized input
remains in `extraction/normalized/document.json`, and revision snapshots are
kept under `review/revisions/`. Files under `extraction/raw/` are never changed
by review operations. See `docs/PHASE2_REVIEW_APP.md` for the architecture,
security model, and current limits. The completion evidence and remaining
external acceptance checks are recorded in `docs/PHASE2_CLOSEOUT.md`.

Accessibility shows three separate scopes: block/image approvals, document
accessibility findings, and automated HTML checks. Completed content approvals
can coexist with unresolved human judgments such as visible URLs used as link
labels. Fix a label in the linked Structure editor, or record a justified decision
where allowed. Zero axe issues or incomplete checks do not resolve these findings.
Reviewed document decisions and resolved extraction notes remain in collapsed
history; neither is presented as pending work.

Accessibility automatically runs bundled axe-core 4.13.0 against the saved
semantic HTML snapshot when the screen opens. The iframe snapshot token must
match the displayed document. A changed snapshot prevents scanning and asks you
to reload; completion stays hidden. Successful results show the saved revision
and scan time. Reload after edits to scan again. WCAG 2.2 A/AA findings and uncertain checks
appear separately from document review, with links to affected Structure blocks
where available. No generate button, account, API key, Node runtime or external
request is needed for this browser scan. Reopening or refreshing Accessibility
checks the latest edits. Summary and finding tables emphasize rule and
affected-element counts. **View tested rules** opens a compact dialog, initially
showing the passed rules. Filter by result to see each rule's name, ID, purpose,
element count, WCAG criteria and guidance. Not-applicable rules found no matching
content; passed rule counts are not counts of WCAG success criteria. The dialog
uses the current scan and does not change review decisions.
Results are for the semantic document at desktop width; individual arranged pages,
final WordPress styling/plugins and human assistive
technology testing remain separate. CLI archival reports contain document review,
not browser axe results. To update the bundled engine, install the pinned npm
package and copy `axe.min.js` and `LICENSE` into the package's static directory.

Accessibility's **Open block** buttons carry a return to the originating finding.
Saving an edit or review action on that block returns to Accessibility and reruns
the HTML scan. Ordinary Structure edits stay in Structure. Label edits still need
block review; approving that block from the same return link also returns to the
issue list. Resolved extraction notes are collapsed under a history heading and
require no action. Save decision buttons use a compact width. Once document
findings are resolved and the current scan has neither detected issues nor
uncertain checks, a green **Continue to Arrange Pages** button appears at the bottom.

Arranged semantic page previews use the retained local images even when WordPress
URLs have been mapped. Arrange Pages' Undo is gray. Preview offers green
**Continue to Export** buttons above and below the preview. Export shows only
outstanding readiness checks and extraction diagnostics, lists unmapped images,
and confirms **Copied** beside Copy page title. Unresolved images still need
WordPress URL mapping; content WXR import is optional and does not
replace Media XML/CSV mapping when pasting Gutenberg.

Whole-list text edits preserve existing item IDs, source metadata, nested content,
exclusions and links when editing their labels. Unchanged list saves preserve
review decisions and rich formatting. Dedicated link-label edits update the parent
list editor too, so a later list save cannot restore an old label. Source PDF
annotations can recover a visible URL damaged only by missing or added hyphens;
the PDF supplies the destination, while the extracted words remain unchanged.

If a list retains text but has no items, Structure displays that text and the
reason it needs recovery. **Save block** recovers the displayed text as one item;
it does not infer nested steps from indentation. Unchanged-text conversion to
List also preserves one item, including existing links and formatting. Review
the result before approving it. Blank saves are rejected, and publication stays
blocked until the structure is recovered and reviewed. Preview serializers keep
the retained content visible. Existing projects are not automatically repaired;
Undo restores the prior state.

List source outlines include recorded regions for nested text, including
paragraphs. If an element has no recorded region, the source status explains
that coverage is partial; unoutlined text may still be present in the block.
No source coordinates are invented.

Source outlines use the PDF's actual MediaBox origin and rotation, including
nonstandard page sizes. The highlight layer follows the visible page image as
the window resizes, without including margins around a tall page. Recovered
first-page titles and subtitles use composed
PDF text and graphics transforms and encoded glyph widths. Existing projects
receive a read-only display correction; their stored text, source boxes, review
decisions and Undo history stay intact. When edited text cannot be associated
confidently with one source region, the app omits the outline and explains why.
On desktop, the source pane stays within the available window height and scrolls
internally to reveal the selected region. It is keyboard focusable for manual
scrolling; selecting a block preserves focus in its review controls. Narrow
layouts retain normal page scrolling.
An accurate outline does not establish correct classification, reading order or
text completeness. Compare infographic headings, duplicate text, numbered groups
and icon meaning with the original before approving publication.

The Accessibility screen derives review items from the current reviewed
document, including incomplete structural decisions, image alternatives,
complex-visual text equivalents, table semantics, heading hierarchy, link
purpose, unknown content, and extraction diagnostics. Reviewer decisions and
notes are stored in `review/current.json`. Results appear immediately on the
Accessibility screen; extraction diagnostics link to affected blocks and show
their current status. Structure shows Reviewed (approved), Pending (unreviewed
or needs review), and Excluded counts. Excluded content remains recoverable.
For archival reports, generate
`output/reports/accessibility-review.html` and `.json` with:

```sh
pdf-to-web export accessibility --project /path/to/my-report
```

These reports document human review. They do not certify WCAG conformance.

**Structure** shows “Structure review complete” when every block is approved
or excluded, with required descriptions reviewed or inapplicable, and offers
**Continue to Accessibility**. Pending blocks or descriptions keep the message
hidden. Final approval brings the message into view; Undo
or a new pending review decision removes it. This completes block review, while
Accessibility remains a separate step.

Structure also offers optional **Image description drafts** before Reading order.
Tools initially open when images need review or draft requests/results exist;
completed images with no drafts stay compact. Your summary toggle remembers open
or closed for this project in this browser, including later visits. A direct
drafting link can reveal tools for that visit without changing your preference.
Default visibility does not save, approve, generate, move focus or collapse an
editor automatically. Select images,
confirm ambiguous image associations, save the provider choice per project,
generate through an existing local Ollama
vision model or an explicitly authorized paid OpenAI request, or export a manual
request ZIP for your chosen tool. Selecting **Manual exchange** shows export,
saved project files, instructions and response import; direct generation/model controls are
hidden, and Ollama help is replaced immediately. Manual exchange requires no
installed model or model-field value; ZIP export/import works even before saving
the changed method. Selecting Local Ollama or OpenAI shows its generation route.
Switching methods preserves unsaved content, checkbox selection and export scope
without sending requests. In the single export area, choose **All pending images**
or **Selected images**, then **Export image-draft ZIP**. Pending uses saved review
needs and skips generating, ready or rejected requests; Selected uses exactly the
checked images and an empty scope cannot export. Both choices show counts.
The green **Open output folder** action and saved ZIP path appear beneath export,
before import controls. Attach that saved ZIP directly; optional browser copies
are separately labeled and follow your browser’s download settings. Beside the ZIP controls,
**Copy instructions for Codex/ChatGPT**
copies a ready-to-use prompt: attach the saved ZIP, paste the instructions,
upload and validate the completed JSON returned by the tool, explicitly import
the drafts, then review each image. The ZIP's original `response-template.json`
is blank and cannot supply completed descriptions. An unfilled template gets one
actionable validation message. Validation alone does not import or approve.
Copying preserves unsaved edits. If clipboard copying fails, selectable instructions
appear for manual copying. The copied instructions, ZIP `INSTRUCTIONS.txt` and
`request.json` identify this project's absolute `output/image-drafts/` destination
for the completed response. Export chooses a unique response filename; a tool
with authorized local access must keep existing files and choose the next unused
numeric suffix if that name is occupied. A tool without access returns the
completed JSON as an attachment/download, without inventing another folder or
claiming a local save. The instructions disclose your local project path when
you manually share them or the ZIP. The app does not send them automatically.
You can validate a completed JSON from its current location in the original
project; moving it is unnecessary. Validation and import still check its original
identities and context, regardless of filename. The request ZIP is saved in the
current project's `output/image-drafts/` folder, including explicitly chosen
project roots. The saved full path appears beside Open output folder.
Names contain the project title, `image-drafting-request`, UTC time and a unique
suffix; repeated exports retain earlier packages. Completed ZIPs appear atomically
and failed writes preserve earlier packages. This drafting exchange is separate
from publication exports and WordPress's `media-upload.zip`. Cancel controls appear only for
active requests. Validate and import responses to fill empty alt, caption and long-description
fields directly. Existing text is preserved; use Apply to replace it deliberately.
Long descriptions are editable beside the image and retained through exports.
Their image-description cards show the associated image and share its short alt
text. Saving a visual review confirms in place and retains keyboard focus.
Authored standalone visual equivalents also appear in semantic HTML, Gutenberg,
WXR and Markdown, after the document content. Arranged-page projections retain
each applicable equivalent once. Image-linked equivalents stay beside their
image; excluded records are omitted. Required review still blocks publication
until complete, and unaccepted drafting suggestions are not published.
Structure places **Needs review**, **Exclude**, and **Approve** above each block
header and source details, in yellow, red, and green respectively.
Use **Fill empty fields from existing drafts** for previously imported drafts.
Null response fields leave existing content unchanged. Review, reject, retry and
Undo remain available; populated images still need human approval. No key or network access is needed for manual
exchange. See [workflow, providers and exchange schema](docs/IMAGE_DESCRIPTION_DRAFTS.md)
and [acceptance evidence](docs/IMAGE_DESCRIPTION_DRAFTS_ACCEPTANCE.md).

**Merge next** joins a block with the immediately following block in saved reading
order. It supports matching paragraphs, quotes, captions, callouts, unclassified
text blocks, and headings at the same level. List blocks cannot be merged here.
Unsupported pairs are disabled with an explanation. Filters never make a merge
skip hidden blocks; show All to inspect a hidden neighbor before merging.
Unsaved edits disable merging immediately, and the saved snapshot and next block
are checked again before saving. An older running app must be relaunched to load
the updated controls; existing projects do not need regeneration. Linked,
formatted, nested and excluded content is protected from merges that would
discard it. Supported text merges preserve footnote
references and backlinks, retain source pages, require fresh approval and support
Undo. A mixed-block list conversion needs an explicit item/nesting design rather
than a bulk type-change workaround.

Dense infographics can retain useful image assets while their extracted grouping
and reading order still need manual semantic reconstruction. Review the actual
preview against the source; retained assets and passing local UI tests do not
establish automatic infographic conversion acceptance.

Publication exports require current manual approval of included source blocks and
visual descriptions. Arranged-page exports also require approval of each exported
page. Changes to saved content return its review owner to Needs review; save the
changes first, then approve the saved content. Editing a previously Reviewed
description requires a fresh Reviewed decision. Undo preserves its saved snapshot
when either document or project persistence fails, allowing a retry.

Import, Populate and Refresh draft actions ask you to save or undo unsaved
Structure edits before replacing the screen. Completed media CSVs associate
WordPress URLs and attachment IDs without replacing current alt text or captions.
Routing-only media matching preserves existing content review decisions and dates;
changing the source image, alt, caption or authored description still requires
review. Mapping changes invalidate older generated publications, so export fresh
content after matching. The saved document owns mapping state; Undo followed by
the same Media XML can re-match filenames even if the generated CSV still contains
older URLs. Existing document mappings take precedence over stale CSV reports.

After matching media, Export always moves keyboard focus and scrolls to
**Export readiness**, which stays visible when ready or blocked. The result
links back to detailed matching feedback, including unmatched or ambiguous images.
**Export reviewed document** and **Copy content** also bring readiness into view;
its Continue link returns to the content controls. The export button keeps an
adjacent explanation and a **View Export readiness** link.
Export shows a busy state, prevents repeat requests and locks media mutations
until it finishes. Failures remain visible and allow retry. Copy page title only
changes the clipboard; it preserves readiness, errors and generated-file feedback.
The complete local fixture journey tests images ZIP/CSV, Media XML matching,
WXR/XML + WSUWP + Page, title copying, generated downloads and artifact contents.

If an older media match cleared existing approvals, **Preview recorded approvals**
appears at Export readiness when retained history proves a mapping-only change.
It lists the exact eligible images and their original approval dates. **Confirm
restore N recorded approvals** restores those recorded decisions in one saved
change, keeping current media mappings and newer review decisions. Preview is
read-only; reopening never silently approves pending content. A changed project,
selection or history invalidates confirmation. Missing or nonconsecutive history,
ambiguous identities, manual pending decisions and genuine edits (even if later
reverted) remain for review. **Undo last change** restores the pending states;
conservative history verification may then require manual review again. No image
re-upload is needed. The confirmation explains this limit before restoring;
its Confirm button also exposes the warning to screen readers. Historical source
identities and recorded content are checked;
history does not independently establish earlier image-file bytes.

**Help** is available from every screen, including before project selection.
Contextual links open the exact explanation in a separate tab so unsaved fields
stay open. Background details about project files, review counts, image descriptions,
bulk review, HTML checks, media, preview appearance, title exports and acceptance
limits live there. Required errors, current states, exact review links and useful
long-page actions remain on their workflow screens.
New list items receive new identities; retained items keep their links, source
provenance and list start after reordering. Editing a footnote source body updates
its exported text while retaining note IDs, markers and backlinks. Ambiguous
changes involving repeated, nested or excluded items require individual edits. Nested headings are the default; an explicitly saved H2 sections
choice remains available.

Generated publication downloads and clipboard reads must match the current saved
document and export settings. Pending, changed, unstamped or outdated publications
are blocked; review and regenerate them. A rejected stale copy clears outdated
results and readiness counts, brings **Reload Export** into view and keeps the
clipboard unchanged. Reload checks current reviews before you generate fresh content. Existing files remain on disk. Internal
previews, accessibility reports, and media/draft exchange preparation remain
available during review. Validation reports fail without generating publication
files when review is incomplete.

**Arrange Pages** (previously Output Pages) is optional: a long document can stay on one web page using
**Preview** and **Export** directly. The workspace builds independently previewable Pages or
Articles from one reviewed document. Inspect heading-based grouping suggestions,
apply an arrangement, move whole content blocks, split or merge pages, edit
metadata and internal Page parents, set contents order, and Undo changes. Page
arrangements persist with the reviewed document. Unassigned content and invalid
arrangements remain visible and block page exports.
Use **Include unassigned content in this page** to recover missing assignments,
or **Keep everything on one page** to replace the arrangement without editing
content. Both support Undo. The arrangement outline is collapsed until needed.

Export one page or the complete ZIP package with HTML, Gutenberg, WXR, media,
contents, review findings, a versioned manifest and manual import instructions.
The CLI equivalent is `pdf-to-web export pages --project /path/to/project`.
Existing single-document exports retain their behavior. See
[Phase 3B workflow and schema](docs/PHASE3B_OUTPUT_PAGES.md) and the
[acceptance ledger](docs/PHASE3B_ACCEPTANCE.md). WordPress media upload,
permalink replacement and absent parent assignments remain manual.

Run tests without third-party test tooling:

```sh
python -m unittest discover -s tests -v
```

On macOS, path-sensitive fixture checks may distinguish `/var` from `/private/var`.
Use the canonical temporary directory for those checks:

```sh
TMPDIR=/private/tmp python -m unittest discover -s tests -v
```

Run the extraction spike corpus through both deterministic modes:

```sh
pdf-to-web spike sample_files --output sample_runs
```

The corpus report assigns one readiness state to every normalized result:

- `review_ready`: structurally exportable, with only advisory issues.
- `needs_review`: exportable, but a human must resolve material extraction or
  complex-visual issues.
- `conversion_blocked`: semantic HTML remains available for diagnosis, while
  Gutenberg and WXR generation are withheld.

Generate the repeatable local WordPress fixture set with:

```sh
pdf-to-web wordpress-fixtures --output build/wordpress-fixtures
```

The Docker and block-editor procedure is documented in
`tools/wordpress-roundtrip/README.md`.

The source PDFs remain unchanged. Each timestamped run contains separate
self-contained projects for heuristic and structure-tree extraction, plus JSON
and CSV comparison summaries. `sample_files/` and `sample_runs/` are ignored by
Git because source publications may contain internal or copyrighted material.

## Current boundary

Proposed source-recovery workflows and observed review edge cases are tracked
in [Future Features](docs/FUTURE_FEATURES.md). The backlog distinguishes missing
text from nested text whose source outline is incomplete; it does not imply
these features or corrections are already implemented.

A small repeated running header can be omitted by extraction while title
recovery chooses a larger section heading. Compare the first source page with
the chosen title. For an existing project, Arrange Pages lets you set an explicit
page title without re-extraction: keep all content on one page, demote an incorrect
document H1 to the appropriate section level in Structure and review that change,
then save the intended Title in Arrange Pages. Preview, review the page and use
**Export page** or **Export complete package** there. Standalone HTML includes
the page H1; when the WordPress template supplies H1, the WXR page title supplies
it and Gutenberg body markup omits it. Copying body markup alone also requires
setting the WordPress title field. Ordinary document exports retain their own
document title. Reopening after a saved review change no longer recreates a
demoted title; automatic running-header title selection remains a limitation.

Phase 2 structural review and Phase 3A accessibility authoring are complete.
The application does not include OCR remediation, a spreadsheet-like table
editor, media sideloading, direct publishing, or
a claim of automated WCAG conformance. The Phase 1B fixtures have been imported,
edited, saved, and reopened in an isolated local WordPress instance. Production
WSUWP compatibility still requires the exact deployed WSU block versions.

PDF bold and italic formatting is only partially preserved. Existing typed
strong/emphasis runs in paragraphs and list items survive Semantic HTML,
Gutenberg and WXR content; general PDF font styles are not automatically converted
to those runs. Table cells currently export plain text with their reviewed header
and span semantics, and Markdown does not serialize formatting runs. A recovered
source note can retain italics without implying support for every styled span.
Broader formatting preservation is a low-priority proposal in
[Future Features](docs/FUTURE_FEATURES.md).

## License

PDF to Web is released under the [Apache License 2.0](LICENSE). See
[NOTICE](NOTICE) and [Third-party notices](THIRD_PARTY_NOTICES.md) for
attribution information.
