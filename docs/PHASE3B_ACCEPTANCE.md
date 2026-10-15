# Phase 3B acceptance ledger

## Unreleased expanded Preview → Export regression — 2026-10-14

Read-only live observation confirmed page 4 of 16, expanded Preview, document
readyState complete and no captured console warning/error. Both Continue links
and header Export were outside the workspace under inert ancestors. The local
server health endpoint returned HTTP 200 and its process was present. This
establishes unreachable navigation in the observed expanded state; no user
click/network history was available to prove any earlier request sequence.
The earlier pagination QA did not exercise Continue while expanded.

Continue now sits inside the expanded toolbar. It carries selected-page,
mode/profile return context into Export, which explicitly retains whole-document
scope and existing readiness gates. Opening uses a bounded read-only GET check,
visible busy feedback and a repeated-click guard. HTTP errors/timeouts restore
controls and show retry guidance. Restore/Escape remain available. Browser back
resets busy state and cancels the old recovery timer. No serializer, approval,
project schema or export-generation behavior changes.

Verification: six focused preview route tests passed; aggregate suite passed
635 tests. Isolated synthetic 16-page Chrome checks passed page 4, first/last,
and reconstruction pages at 1280×720, 1440×1000 and 320×650, including expanded
Continue, selected context, return/back navigation, blocked incomplete exports,
HTTP 503 recovery, ten-second timeout/retry and one request for repeated clicks.
No JavaScript errors; navigation left review bytes unchanged. Independent code
review checked the fix and its back-navigation timer recovery.

No live tab navigation, reload, quit, restart, project mutation or export action
was performed. No commit/push/release. The current-tab workaround is Restore
preview (or Escape), then Continue; save drafts before any later deliberate
relaunch to load changed Python markup. Human VoiceOver, production WSU
WordPress/plugin compatibility and Windows hardware acceptance remain pending.


## Unreleased preview pagination and compact arrangement — 2026-10-13

Preview has Previous/Next, compact Output page selection, Page N of M, Whole
document and Arrange this page. Navigation carries saved page identity, mode
and WordPress profile. Empty/reconstruction pages remain visible as unfinished.
Expanded preview keeps controls reachable, prevents focus on covered background
controls and restores focus on exit, including Escape from the content frame.
Content typography, export styles, serializers and stored schema are unchanged.

Arrange Pages uses compact metadata, wrapped assign/reorder actions and inline
merge controls. Metadata and reviewer-note drafts block in-app navigation and
mutations; browser departure presents its native unsaved-edit confirmation.
Saved slugs supply preview URLs. No reconstruction, H1 or extraction finding is
resolved by these UI changes. Existing approved work remains in the checkout.

Verification: baseline 629 tests passed; four new read-only route/projection
tests passed; aggregate suite passed 633 tests. Independent screenshot/code UI
review found no remaining blocker after focus and reconstruction roundtrip fixes.
Isolated headless Chrome passed at 1440×1000, 1280×720, 1048×650, 390×844 and
320×650: repeated pagination, boundary focus, empty/held pages, reload, draft
protection, page/mode/profile return and back navigation, expansion, overflow,
and disposable save/reopen/Undo. Scoped WCAG A/AA axe checks reported no
violations; no JavaScript errors were observed. Synthetic review bytes stayed
unchanged throughout navigation; saved Undo restored page metadata and blocks.
The supplied Library screenshot was materialized and inspected locally.

Production WSU WordPress/plugin validation, human VoiceOver and actual Windows
hardware acceptance remain pending. The live server and live project were not
restarted or edited; no commit, push, tag or release was performed. Save drafts
in all open tabs before deliberately quitting/relaunching to load Python markup,
then reopen the same project and reload the browser.


## Unreleased generated page title repair — 2026-10-13

Source and heading groups use their first included H1/H2 in reviewed reading
order, with numbered fallbacks and preserved reconstruction labels. Excluded
ancestors/headings and paragraph merge provenance do not supply a heading.
Repeated titles retain distinct automatic slugs. Exact existing custom metadata
remains preserved. Generated title tracking distinguishes later manual edits;
legacy recognition requires the precise prior source-builder identity/default.

Preview generated page titles proposes only metadata repair, not regrouping.
Apply checks the existing proposal digest/review token and supports saved Undo.
Custom titles and manual slugs stay unchanged; automatic slugs follow refreshed
titles. Assignments, page identities/order/type/parent metadata, block content and
block approvals remain intact. Changed page metadata uses the existing review
invalidation. No automatic repair occurs on project open or code installation.

Verification: 34 focused tests passed, covering source/heading groups, repeated
and excluded headings, numbered fallbacks, merged provenance, custom overrides,
manual slugs, conservative legacy recognition, preview/apply/reopen and Undo.
The full suite passed 629 tests in 37.781 seconds. Separate headless Chrome on
a disposable grouped-project copy passed four workflow groups, including draft
protection and exact saved Undo, at 1440px, 390px and 320px, with no JavaScript
errors or targeted axe violations. Live saved review bytes were verified unchanged.
No live app restart, project repair, commit, push or release was performed.
Production WordPress/plugin, human VoiceOver and Windows acceptance remain pending.

## Unreleased explicit page grouping and visual context — 2026-10-13

Implemented separate physical source-page and optional heading-section methods,
checkbox selection, read-only proposals, exact moves and readable metadata
effects. Apply recomputes the proposal and checks its digest/current review token,
saves once and supports saved Undo. Source grouping retains exact matches,
excluded references, reconstruction placeholders and existing empty drafts;
ambiguous source bundles need an explicit available destination. Heading
selection preserves unselected assignments and metadata. Held fragments are not
implicitly moved into heading sections. Empty/no-included-content pages remain
unfinished, and no arrangement clears review or publication gates.

New title-derived slugs are normalized, unique, reserved-name safe and bounded
to 100 characters. Custom overrides persist. Empty pages expose Add content;
unsaved metadata/reviewer notes prevent arrangement navigation and saves lock
editable fields while pending. Incomplete contents lists every page and recovery
actions without weakening package export validation. Populated source-built
placeholders retain their references as ordinary unfinished pages on restoration;
subsequent single-page regrouping does not create duplicate assignments.

Standalone visual findings now show real source-page context and pending-check
links beside the source preview. Classification remains explicitly heuristic.
Source navigation/filtering, image failure/retry, description decisions,
save/reopen and Undo preserve block approvals and drafts. Busy preview text wraps
correctly. Changes do not alter live project data or extraction.

Verification: 37 focused planner/route/reconstruction/visual tests passed. The
full documented suite passed 622 tests in 37.551 seconds. Generated synthetic
page-package HTML, Gutenberg and WXR retained the correct page content, with two
parsed WXR items and no cross-page duplication. Separate headless Chrome passed
seven grouping workflow groups, explicit ambiguous-source destination selection,
and six complex-visual groups at desktop, 390px and 320px. Targeted axe checks
reported no violations or JavaScript errors. Independent UI review checked the
proposal controls without saving; its wording findings were corrected.

A disposable copy of a local project confirmed distinct physical-page
and heading-section counts, numeric source grouping and a retained reconstruction
hold without applying any arrangement. Private input evidence stays ignored.
Shared Chrome and the live app were untouched. Human VoiceOver, production WSU
WordPress/plugin compatibility and actual Windows hardware acceptance remain
pending. No release or publication was performed.

## Unreleased grouping disclosure appearance — 2026-10-13

Arrange Pages' Grouping suggestions uses a bold dark heading and chevron,
compact tinted section styling, and a visible keyboard focus outline. The
disclosure is 44px high at 1440px, 390px and 320px viewport widths; Enter and
Space toggle it without saving. Separate headless Chrome checks found no
JavaScript errors, POST requests or changes to fixture review bytes. The full
documented suite passed 595 tests in 35.666 seconds. Final CSS touch-target and
chevron adjustments were then verified in the browser. Shared Chrome and live
project data were untouched. Human VoiceOver acceptance remains pending.

Version: 0.7.1. Updated: 2026-10-05.

Local implementation, external acceptance and publication are separate. The
public ledger records behavior and verification without source-document names,
private project identities, attachment IDs, revision histories or input hashes.
Detailed earlier reports are retained only in ignored local evidence. Sanitizing
this checkout does not remove material from previously published Git history.

## Heading approval and visible rejection feedback — local verification, 2026-10-12

The reported saved H2 heading was reproduced on a disposable copy. H2→H1
Save & Approve sent the correct final level, preserved text, saved approval in
one revision and worked again after an in-place patch. No live pending edit was
changed. This establishes current implementation behavior, not the exact cause
in the user's open tab, which remains unconfirmed without its error/state evidence.
Save/approval errors now appear beside the top review actions instead of the
lower footer; client code also relocates messages on earlier page markup. Another
unsaved editor names its Block number. Missing atomic endpoints give explicit
preserve-drafts/relaunch guidance. Stale snapshots, invalid fields and uncertain
responses retain edits and make the required recovery visible.
A synthetic API regression verifies level-only approval, unchanged text, one saved
revision and Undo. 12 focused tests passed; full suite: 592 passed in 33.202s.
Eight copied-project headless groups passed: heading round trips, other dirty
editor, earlier-server guard, stale snapshot, native invalid field, missing
endpoint, responsive feedback and committed-write lost-response protection.
Zero JavaScript errors and zero targeted card WCAG A/AA violations. A narrow
feedback screenshot was inspected. Evidence remains ignored under
build/heading-approval; private content is not checked into Git or shared.
Keep pending live edits intact while identifying the original rejection. Load
updated client feedback only after preserving/saving/reverting drafts; no live
reload or restart was performed. External human acceptance remains pending.

## Compact reading-order type icons — local verification, 2026-10-12

Row type words are replaced by small monochrome icons for paragraph, ordered /
unordered list, heading, image, table and quote, with a labeled fallback for other
types. Full names remain in accessible image labels and tooltips shown on hover
or keyboard focus. Tooltips use the existing manual-popover convention to avoid
clipping inside scroll panels; they remain hoverable, stay within the viewport,
and Escape dismisses the tooltip before closing Repair. Glyphs inherit a dark
contrasting color and have a visible focus outline. No new dependencies.
Six synthetic headless browser groups passed at 1440×900, 390×844, 320×568 and
760×320, covering eight labels, focus/Escape, bounded tooltips, compact rows,
specific mixed-type feedback and compatible staged list merge/Unmerge. Zero
JavaScript errors and zero targeted full-dialog WCAG A/AA violations. Desktop
and narrow screenshots were inspected. Full suite: 591 passed in 33.507s.
Evidence stays ignored under build/type-icons. The live project and browser were
untouched; save edits and finish/cancel drafts before Command–Shift–R. No restart
is needed for this icon update. External human VoiceOver acceptance remains pending.

## Mixed-type merge eligibility — local verification, 2026-10-12

Repair reading order now shows each row's saved block type and explains a mixed
selection with current Block numbers and types. The existing eligibility rule
still prevents paragraph/list joins; selection never converts extracted types or
strips list structure. The backend gives the same specific rejection for callers
that bypass the disabled button. A synthetic regression checks global Block
104/105 numbering and byte-identical saved state after both preview and Apply
rejections. Real reported content was tested only on an ignored disposable copy.
Five browser groups passed: the exact copied selection at desktop, narrow and
short viewport sizes with keyboard toggles and visible explanation/actions, plus
server preview/Apply rejection with no copied review mutation. Zero JavaScript
errors and zero targeted footer WCAG A/AA violations. 20 affected tests passed;
full suite: 591 passed in 34.992s. Screenshots were inspected locally; private
source/project evidence stays ignored under build/mixed-merge. Live saved data,
selection, forms and prior targeted legacy repair were not changed. A separate
explicit repair is needed if source review confirms extraction misclassification.

## Merge confirmation layout and block labels — local verification, 2026-10-12

The supplied screenshot was materialized through Library and inspected as pixels.
Pico's global dialog styles imposed a horizontal flex layout and full-viewport
minimum dimensions. The confirmation now overrides those defaults, stacks one
scrolling preview above a separate action group, and keeps controls visible.
Full-app CSS browser checks passed at 1440×900, 390×844, 320×568 and 760×320 with
long preview text and unbroken strings, keyboard navigation and Escape recovery.
Block labels follow current draft positions and explicitly identify result numbers
after Apply. Absorbed origins use original positions, without inventing current
numbers or changing internal IDs. A fifth browser group verified staged reorder,
merge, retained originals, Apply/reopen and Unmerge/Apply numbering and stable IDs.
No JavaScript errors or targeted confirmation WCAG A/AA violations were found.
19 affected functional tests passed; the full suite passed 590 tests in 33.077s.
Evidence stays ignored under build/merge-modal. Save edits and finish/cancel a
draft before Command–Shift–R to load the updated CSS/bundle; these changes require
no server restart. Live project/browser state was not changed.

## Source-page review pill — local verification, 2026-10-12

A compact text-and-color pill beside Source page reports saved whole-page review:
green Reviewed, yellow Partially Reviewed and red Needs review. Filters, current
selection and unsaved fields cannot redefine its scope. Existing effective block
status, publication requirements, visual readiness and source ranges determine
it. Required image descriptions belong to their owner task, standalone descriptions
add tasks, and retained absorbed origins are not live blocks. Shared blocks use
the same whole-block review decision on each recorded source page.

Exclusions resolve review decisions; all-excluded pages can be Reviewed with an
explicit explanation that no included content is ready to export. Empty pages,
reconstruction holds and blocked conversion stay Needs review. A status pill is
not export approval. Unknown/uncertain write or refresh results stay Needs review
until authoritative reload. Confirmed save/approve/exclude patches, page navigation,
merge/unmerge/structural operations, reconstruction and Undo refresh the page map
before image work or their existing reload, retaining the source pane and edits.

**590 tests passed in 32.955 seconds** using the documented macOS TMPDIR command.
Focused source projection/async/manual/order routes/top approval: **28 passed in
1.550 seconds**. **Eight headless browser groups passed with zero JavaScript
errors and zero targeted source-panel WCAG A/AA violations**. Covered mixed/all/
none/empty/excluded states, filters with zero visible rows, page boundaries,
in-place approve/save/exclusion and next-page advancement, required image
alternatives/descriptions, merged/absorbed origins, persistent Unmerge/Undo,
manual holds/page switching and committed-write lost-response recovery. Mutation
samples showed the displayed page and status snapshot stay aligned. Desktop,
390px and 320px status screenshots were inspected. A fresh disposable merge
dialog also verified row checkboxes and its visible Merge selected footer.

Evidence is retained under ignored `build/source-page-status`. Runtime diagnosis
was read-only: the earlier listener stopped, then process91993 appeared on8765
with this checkout as its working directory, matching public static assets and
staged-preview route. No packaged app replacement/rebuild is required for merge.
A supplied screenshot showed the earlier Undo move / Apply reading order UI,
not hidden/disabled new controls. Detailed private screenshot evidence stays
untracked. No authenticated live tab was reloaded or inspected, so its exact
current origin/cache state was not established. Save edits and finish/cancel an
ordering draft before a cache-bypassing Structure reload for merge visibility;
new pill server markup requires quit/relaunch and reload after saving.

Version0.7.1, branch main, HEAD6f35cbe; existing dirty work retained. No live
project mutations, application restart, shared Chrome control, commits, pushes
or publication were performed. The user's manually saved merge was untouched.
Human VoiceOver, physical hardware and production WordPress/plugin acceptance
remain separate and pending.

## Staged paragraph/list merge and persistent Unmerge — 2026-10-12

Approved implementation is now integrated into Repair reading order. Native
checkboxes select consecutive plain paragraphs or compatible list blocks; Merge
selected beside Cancel/Apply opens an exact confirmation. Stage merge produces
one compact draggable row with original-count badge, full result/originals and
Move to. Draft Undo/Reset/Unmerge/Cancel do not write. Apply replays all ordering,
merges and unmerges atomically as one saved revision/Undo action. Redundant
per-block up/down controls are removed; document start/end and accessible Move to
remain. Existing top Approve / Save & Approve behavior remains intact.

Paragraph joining uses one explicit space and preserves hyphens/internal breaks.
List joining preserves item IDs, nesting and marker semantics; ordered lists must
continue numbering. Refuse mixed/image/heading/unsafe rich or associated content,
numbering restarts, skipped/other-page/excluded/shared-boundary content, incoming
links to absorbed IDs and conflicting page assignments. Run text remains
export-authoritative. New merged content is Needs review, never auto-approved.

Versioned optional provenance retains full originals, source regions/assignments,
review metadata and integrity/fingerprint checks. Persistent Unmerge restores
unchanged origins after reopen at the current position/page assignment. Changed
content, nested exclusions, custom notes/source or corrupted/colliding origin IDs
refuse restoration with an explanation instead of silently losing later work.
Approval-only changes permit Unmerge. No migration or re-extraction of old projects
is performed; older stored schema versions remain. Historical Merge next results
without this provenance do not gain exact Unmerge automatically.

Final documented suite: **584 tests passed in 34.760 seconds** with
`TMPDIR=/private/tmp .venv/bin/python -m unittest discover -s tests -v`.
Focused transaction/order/routes/top-approval tests: **34 passed in 1.442 seconds**.
**25 browser check groups passed with zero JavaScript errors**, including
**10 independent groups** and separate emulated-touch selection/merge/sort checks.
Covered exact paragraph/list preview, checkbox keyboard/pointer/touch, stage
Undo/Reset/Cancel/no writes, one-revision Apply/double-click, persistent Unmerge
and source regions, item nesting/numbering, changed-exclusion protection,
stale/failed-preview/lost-response recovery, confirmation focus, missing-image
feedback, desktop/390/320×600 and 200% equivalent browser-zoom reflow. Independent
and final targeted automated WCAG A/AA checks had **zero violations**. Actual
screenshots were inspected. Short windows scroll the bounded panel body while
footer actions remain reachable; resizing retains the selected row. Source scroll
regions are labelled/focusable; button contrast avoids intermediate fades.

Independent read-only code review found initial plain-run, absorbed-anchor,
exclusion and recovered-outline risks. Each was fixed and regression-tested;
final review found no remaining blocking data-integrity issue. Independent browser
review found focus, pointer-scroll, short-window and contrast issues, all fixed
and rechecked. Generated semantic HTML, Gutenberg, arranged-page HTML and parsed
WXR preserved exact joined text, ordered starts and nested items.

Evidence remains ignored under `build/reading-order-merge` and
`build/reading-order-merge-independent`. Version **0.7.1**, branch `main`, HEAD
`6f35cbe`; dirty work preserved. No commit, push, merge or release. Real projects,
shared Chrome and the live listener at port8765/PID75336 were untouched. Save
edits, quit/relaunch PTW and reload Structure to load the new server/UI together.
Human VoiceOver, physical touch/Windows hardware and production WordPress/plugin
acceptance remain pending; automated/headless results do not complete them.

## One top approval action — local verification, 2026-10-12

Reading order now uses one top Approve / Save & Approve action. Every review
editor's input/change state participates: text, type, heading level, link labels,
image alternatives/captions/decorative choice, displayed description fields and
table accessibility. Reversion restores Approve; edits enable previously approved
blocks. Combined authoring and link changes validate in memory, then approve and
save once under the review-write lock with expected-token checking. Invalid or
conflicting text/link changes never partially save. Draft suggestion editing and
provider/context setup remain separate operations; they are not implicitly
applied during approval. Lower duplicate combined buttons are removed. Ordinary
save and a focus-return link remain available below the fields.

Retain mounted review/source state, next-pending-block advancement, current filters,
image/description approval scope, one revision/saved Undo, double-click guards,
stale rejection and uncertain-result recovery. Newly entered edits in other cards
remain visible without automatic advancement. Older server markup is checked
before any combined-editor request; instruct relaunch rather than silently
approving its old saved content.

Baseline: **560 tests passed in 31.533 seconds**. Final documented suite:
**568 tests passed in 32.567 seconds**. Focused combined approval/image/async/layout
regressions: **68 passed in 5.601 seconds**. **13 separate headless browser check
groups passed with zero JavaScript errors**: dirty/reverted fields, input/change,
keyboard typing, multiple rich-link edits, image/text/table approval, one
revision/double-click, saved Undo, next-block focus without replacing the mounted
document, failed/native validation, server error, stale newer data, committed
save with lost response, busy/other-card race, old-server capability and
1440/390/320 layouts with the return link. Screenshots were inspected. Generated
semantic/Gutenberg HTML retained final text, edited link label and its original
destination. Syntax/compile and `git diff --check` passed. Local evidence remains
ignored under `build/top-approval-oct12`.

Checkout version: **0.7.1**, branch `main`, HEAD `6f35cbe`, with existing dirty
work preserved. The user's listener on 127.0.0.1:8765 remained healthy; process
75336 started 2026-10-10 00:17:44 local host time. Health exposes no build version,
so it cannot establish that this running process has the October 12 Python
changes. Save edits, quit/relaunch PTW and reload Structure to use the complete
change. Shared Chrome and real projects were untouched; only disposable fixtures
were mutated. No commit, push, merge or publication was performed. Human
VoiceOver, Windows hardware and production WordPress/plugin acceptance remain
pending. Multi-select paragraph/list merge is assessed in `FUTURE_FEATURES.md`
only; its implementation is not authorized or included here.

## Integrated reading-order repair and coordinated Structure tools — 2026-10-09

The compact reading-order prototype is now integrated into Structure through
**Repair reading order** for the displayed source page. Five-word cards retain
full-text expansion and explicit Move to alongside pointer/touch/keyboard sorting.
Changes are staged with Undo/Reset/Cancel; Apply uses one existing saved revision
and Undo action. Shared-page boundaries stay fixed, excluded/other-page/nested/
unlocated content is preserved, and no source geometry is invented. Identity,
review-token, complete permutation and active-provider checks protect writes.
Existing output reference reconciliation can invalidate page approvals after an
order change; block content and review decisions remain intact. Dirty editors
prevent opening; stale/uncertain requests retain drafts with truthful recovery.
The shipped sortable UI is locally bundled, with pinned source/build/license files
in `tools/reading-order` and `static/reading-order.*`. This supersedes the earlier
prototype-only status without claiming external accessibility acceptance.

Structure column headings now share typography and vertical baselines. Source
navigation reads **Previous Page / Next Page** and matches block navigation's
44px height. A smaller Repair button shares a row with reconstruction controls
where space allows. Medium/narrow views stack columns and wrap safely. Help
retains a visible info icon, keyboard/hover/touch access and Escape dismissal;
active warnings and reserved source-note space remain intact during async saves.

Final verification: **560 tests passed in 32.122 seconds** using
`TMPDIR=/private/tmp .venv/bin/python -m unittest discover -s tests -v`.
Focused reading-order, reconstruction and layout checks: **33 passed**.
**20 headless browser check groups passed with zero JavaScript errors**, covering
paired heading/nav baselines at 1440px; safe layouts at 1000, 900, 520, 390 and
320px; 44px targets; pointer and keyboard Apply/saved Undo; full-text/direct moves;
dirty/stale guards; repeated open/reload; reconstruction mark/reversal; hover,
keyboard, touch and Escape help; 108 sampled frames across six async approvals
with a stable source stage; image/metadata deadline recovery; positive-size tooltip
at 200% visual zoom; and 200% equivalent browser-zoom reflow. Desktop/narrow
screenshots were inspected. Generated semantic and arranged-page HTML both
reflected the saved order and omitted excluded content. Earlier isolated long-list,
touch-sort and uncertain-write recovery evidence remains under
`build/reading-order-integration`; current evidence is under ignored
`build/structure-toolbar-current`.

All mutations were confined to disposable fixtures. Shared Chrome, the live app
and real project data were untouched. Save edits, quit/relaunch PTW and reload
Structure to load the Python-generated toolbar markup. No commit, push or release
was performed. Human VoiceOver, physical Windows/touch hardware and production
WordPress/plugin validation remain pending.

## Unreleased drafting disclosure — 2026-10-09

Successful image draft history now defaults preparation tools to collapsed on
subsequent Structure visits, including existing projects and manual imports.
Explicit open/closed preferences remain per project, with tab-storage fallback.
Generating, failed, awaiting-response and ready-for-review status remains visible
outside the tools; completion does not collapse live edits or move focus. Direct
links still reveal tools for a visit. Review/approval rules are unchanged.

**550 tests passed in 31.939 seconds** using the documented macOS
`TMPDIR=/private/tmp` command. An initial run with the default temporary path had
six failures and one error from /var versus /private/var alias expectations;
no unrelated production fix was made. Seven disposable browser groups passed
without JavaScript errors: first use, successful completion with retained active
text/focus and collapsed next visit, explicit choices/revisits, project switching,
closed-pane generation/failure status, unrelated in-place approval and unavailable
local-storage fallback. Manual import and older retained history are also covered
by functional tests. A narrow screenshot was inspected. The disposable server
was stopped and its fixture removed. Actual project content and the running app
were not changed; new server markup requires user-led relaunch/reload after
preserving drafts. External acceptance remains pending.

A separately authorized reading-order design demo lives only in ignored local
evidence under `build/reading-order-prototype/`. It has copied source reference
and paragraph excerpts, one sortable list, recorded highlights, direct position
controls, keyboard/pointer/touch moves, Undo/Reset and demo-only Apply/Cancel.
Pinned current `@dnd-kit/dom` 0.5.0 and `esbuild` 0.28.2 are installed only there
with package scripts disabled; the bundled adapter has no runtime CDN dependency.
Twelve headless browser groups passed without errors or project-write requests,
including real pointer cancellation and 1417px long-list edge scrolling. Touch
evidence is desktop Chrome emulation. Physical touch, VoiceOver and Windows are
pending. This is a design-review artifact, not production reading-order integration.

## Unreleased source-column clarity — 2026-10-09

Source metadata and region status reserve stable space; same-page approvals keep
the rendered image visible while checking the next region. Unmarked reconstruction
status is hidden; active warnings remain. Help supports hover, keyboard, touch and
Escape, with an ARIA description and viewport-clamped popover. Missing geometry
does not claim a highlight. Image loading is bounded to 30 seconds and region
metadata to 10 seconds, with explicit image error/Retry/Open PDF recovery.

**547 tests passed in 32.056 seconds.** Eleven disposable browser groups passed
without JavaScript errors, including six approvals across 111 intermediate frames
with one source-stage position, reviewed type changes, missing geometry, marked
page switching, touch and keyboard help, Move to start retaining source selection,
and stalled image/metadata recovery. A separate tightened 200% zoom check verified
positive tooltip bounds inside the visual viewport and Escape retaining focus;
narrow and zoom screenshots were inspected. These checks establish local behavior;
the reported live-tab spinner remains unobserved. No actual project write, Undo,
app restart or existing-tab navigation was performed. User-led relaunch/reload is
needed for new server markup after preserving drafts. Human VoiceOver, Windows
hardware and production-authoritative WordPress acceptance remain pending.

## Unreleased dirty-Approve guidance — 2026-10-09

Heading-level-only edits correctly require Save and approve; top Approve validates
saved content and rejects dirty fields without a write. New live guidance below
the top actions explains this before activation and is associated with Approve
for assistive technology. Reverting fields or saving clears it. Six disposable
headless browser groups passed: H2-to-H1-only guard/retained edit/focus, reversion,
combined async save, text/image dirty fields, clean approval and required-image
validation. No JavaScript errors occurred; a narrow screenshot was inspected.
Final verification: **547 tests passed in 30.186 seconds**; JavaScript syntax and
diff checks passed. The disposable server was stopped and its fixture removed.
The actual tab's state was unavailable: Chrome Apple-event inspection returned
authorization error -1743, and no browser tool exposed console/DOM inspection.
No browser permission was changed. New server markup requires a user-led relaunch
followed by reload; the running process predates the changes.

Read-only source/model inspection of a reported two-column jump found interleaving
already present in normalized extraction and retained review order. The next
pending rule follows that order; the remaining left-column paragraphs were still
unreviewed. This does not justify a navigation-code change or an automatic
project reorder. Actual content-order repair remains pending user authorization.
The live filter could not be inspected. Detailed private block/geometry evidence
is ignored under `build/runtime-triage/`; no project data or existing tab was changed.

## Unreleased post-success recovery investigation — 2026-10-09

The live tab could not be inspected with the available tools. Bounded read-only
probes showed a listening, responsive app and a persisted last approval; this
does not establish that the reported frontend stall is resolved. A disposable
243-block fixture with a source-page hold advanced normally after approval.
Six controlled browser groups verified normal advancement, form/action responses
stalled after a successful write, malformed successful refreshes, and an older
server response without review fragments. A seventh group verified that rejection
of a pending description on an already-approved image leaves top Approve usable,
then correcting via Save and approve completes it. No JavaScript errors occurred.

Review saves now bound the response wait to 30 seconds. Browser abort exceptions
are normalized to give actionable recovery text; busy/request state clears while
the uncertain-write guard blocks retries and preserves fields. Confirmed saves
with failed refresh explicitly report Saved and require reload. Timeout checks
used a shortened test deadline; they made exactly one saved revision and no retry.
Live-tab cause remains unknown. Preserve drafts before reload; new JavaScript
loads on reload, while changed Python markup and top-image validation require a
user-led relaunch followed by reload. The running app was not restarted or altered.
Local evidence is ignored under `build/top-image-approve/`.
Final follow-up verification: **547 tests passed in 31.039 seconds**, seven
focused recovery browser groups passed, and JavaScript syntax/diff checks passed.

## Unreleased image top approval — 2026-10-09

Image cards again show Approve in the top review actions. Saved image content and
exactly the displayed descriptions use the existing atomic image validator,
snapshot guard and in-place advancement. Dirty fields are retained and direct
the reviewer to Save and approve; both bottom save actions remain. Completed
image/description approval disables the top action. **547 tests passed in 33.603
seconds.** Six disposable headless check
groups passed with no JavaScript errors: dirty draft protection/focus, valid
image plus description/double-click/next item, desktop/narrow layout, missing alt
and equivalent rejection without writes, decorative approval and last-image
completion without reload. Four additional server tests cover atomic approval,
Undo, missing alternatives/equivalents, decorative decisions, stale snapshots and
displayed-description scope. Evidence is ignored under `build/top-image-approve/`.
No actual project, existing tab, or running app was changed by these tests.

## Unreleased in-place review and page-state follow-up — 2026-10-09

Structure Save, Save and approve, and direct review actions now update bounded
review fragments after a confirmed write, keeping the document and source pane
mounted. Counts, filters, saved block Preview, completion and snapshot tokens
update together. Dirty editors are preserved, including drafts entered while a
request is active. Overlapping/double-click approvals are blocked. Validation and
stale-snapshot failures retain fields; uncertain responses require reload before
another mutation. A confirmed write with failed display refresh is reported as
saved with recovery instructions. Undo retains the existing snapshot/navigation
behavior. Structure responses use no-store: history navigation previously could
combine the original cached form baselines with later browser-restored values.

Reconstruction checkboxes are bound to the displayed source page and resynchronize
after native form restoration. Delayed success/failure for page 3 retains the
newer displayed page 4 without carrying its checked state or writing to page 4.
Read-only inspection found no saved holds or excluded page-4 blocks in the reported
project at that time; no actual user project was changed. The exact live-tab
interaction could not be observed; the reproducible browser-restoration case was
fixed and fresh/rapid/filter/history/response-race cases were tested separately.

Scoped header/footer margins and wrapping legends remain inside block borders.
Before/after measurement found an inherited header extending 3.75px outside each
side; the override contains it. Desktop, 390px and 320px screenshots were checked,
including a long legend. The supplied Library screenshot download returned 403,
so its pixels were not inspected. Existing 320px source-control width remains.

**543 tests passed in 37.552 seconds.** **25 headless Chrome check groups passed**:
18 async editor/action/history/draft/failure/Undo/layout/completion groups on a
224-block synthetic fixture, plus seven page-state and delayed-response groups.
No JavaScript errors were reported. Twelve successive combined approvals retained
document identity, made no main-document navigation requests and never visited
page top; six direct approvals likewise advanced only after confirmation. Local
click-to-confirmed-update medians were 458ms combined and 325ms direct approval;
these fixture measurements are not a production performance guarantee. Narrow
approval and the last pending item retained the document and correct focus/status.
Evidence is ignored under `build/async-review/` and
`build/reconstruction-page-switch/`. Shared Chrome, existing tabs and actual user
projects were untouched. Loading the new server and markup requires a user-led
save/quit/relaunch and reload. Production WordPress, human VoiceOver and physical
Windows acceptance remain pending; no commit, push or release was performed.

## Unreleased compact image review and reconstruction holds — 2026-10-09

Image review has smaller readable authoring fields, full-width long descriptions,
earlier decorative choice and save actions directly after the fields. Drafting
tools are optional disclosures below authoring; existing requests remain open.
Source provenance is collapsed at the bottom of each block. Save/approval restores
the intended review destination before paint, with no delayed load callback or
startup selection overriding completion focus. The normal saved-page reload remains.

Needs manual reconstruction under Source Page reversibly excludes exclusively
owned fragments and restores their exact prior decisions on unchecking. Shared
page content is retained and reported. Holds, source-page selection, stale/dirty
protection and Undo persist through review. Arrange Pages retains one stable,
unfinished placeholder per hold through reorder/regrouping. Unchecking removes
only that placeholder; existing arrangements are not automatically split. Holds
remain unresolved and block publication despite excluded fragments. The feature
does not perform OCR or author replacement content; restoration precedes editing.

**540 tests passed in 34.916 seconds.** **21 headless Chrome check groups passed**:
11 compact-editor/approval checks, eight reconstruction workflow checks and two
independent narrow approval-position checks. Coverage includes long existing
text, 390/320 layouts, keyboard order, disclosures, drafts, Save/approval/Undo,
validation failure, filters, repeated and last-item approval, Back/Forward,
source-page reversal/reopen, placeholder reorder and stale-tab rejection.
Narrow first-frame samples selected the next pending block; completion retained
focus and status feedback. Browser reports contain no JavaScript errors.
Representative disposable UI screenshots were inspected. Existing Structure
source controls still cause a 336px document width at 320px; no new editor overflow
was introduced. Evidence remains ignored under `build/compact-image-review/`
and `build/manual-reconstruction/`.

The supplied Library screenshots could not be materialized on this Mac; no visual
claim is based on those attachments. A fresh read-only render of an approved real
source page confirmed visually present statistics absent from selectable PDF text
and extracted blocks. No project was modified or re-extracted. The active app
and shared Chrome were untouched. Save, quit and relaunch PTW to load new server
markup. Changes remain uncommitted; external acceptance below remains pending.

## Unreleased secondary helper typography — 2026-10-08

Supporting notes now opt into one shared helper style across Structure, image
drafting, Accessibility, Arrange Pages, Preview and Export, plus the secondary
launcher explanation. The two requested Structure notes measured 16.67px before
and 15px after at a 1440px desktop viewport; comparable paragraph notes changed
from 20px to 15px. Sizing is `.75rem` with a 14px minimum and a 1.5 line height.
Warnings, primary instructions, labels, content and review blockers retain their
existing sizes. Live draft/save/stale merge blockers retain the prior status size.

**530 tests passed in 29.782 seconds.** **39 disposable headless Chrome check
groups passed:** 17 review/edit/Undo regressions and 22 typography checks across
five workflow screens at 1440px, 390px, 320px and 200% equivalent reflow. The zoom
check used a 720px CSS viewport at device scale 2, with a separate doubled-root-font
check; actual browser-menu zoom and human VoiceOver remain unverified. Helpers
wrapped without clipping, had at least 5.99:1 measured contrast, and retained
keyboard focus. Representative screenshots were inspected. The existing 336px
Structure document width at a 320px viewport remains; this pass adds no new
horizontal overflow. No real project or active app was changed. Updated server
markup requires saving edits, quitting/relaunching PTW and reloading the page.
No commit, push or release was performed; external acceptance remains pending.

## Unreleased saved block content preview — 2026-10-08

Local implementation adds one accessible Edit / Preview area for paragraph/list
cards. Edit opens first; saved-content Preview preserves drafts, makes no project
writes, and keeps existing Save, Save-and-approve, nested-list controls and Undo.
Styled-run footnote placement and local WordPress preview sanitization are corrected.
Paragraph/list Gutenberg wrappers remain native. The existing separate Custom HTML
endnotes section is unchanged; additional footnote ARIA and citation association
are deferred pending native-block compatibility. Explicit reference sections receive
one nonblocking manual-review reminder per Structure/Export screen.

Saved line breaks, including blank lines, now pass through shared rendering to
block/document previews and HTML/Gutenberg/WXR. Native block wrappers and raw
footnote offsets remain intact. The borderless block preview follows its content's
natural height, growing on narrow layouts and shrinking when widened.

**530 tests passed in 31.324 seconds**, including 14 new rendering/route regressions.
**20 disposable headless Chrome check groups passed**, covering mode/draft preservation,
keyboard tabs, note navigation and return focus, hidden controls and hidden-draft
Undo protection, nested-list approval/Undo, save/approval, stale rejection, reopening,
help/filter cancellation and saved back navigation. Additional checks confirmed
single/blank-line spacing, natural preview growth/shrinkage, no inner scrollbar,
and exact Undo after saving breaks. Desktop/390/320 screenshots were inspected.
The new area fits narrow viewports; pre-existing source controls still
cause a 336px document width at a 320px viewport (339px before the grid adjustment).
Generated HTML/Gutenberg/WXR and converted WordPress preview were inspected: WXR
contains exact Gutenberg content and only the existing endnotes HTML block remains.
Saved breaks also survived local WordPress preview conversion. A read-only render
of a saved user paragraph preserved all eight stored breaks, including four blank
lines; neither its model nor project files were changed by that check.
These are local checks, not actual WordPress open/save/reopen or human VoiceOver
acceptance. Production WSUWP/plugin compatibility, human listening and Windows
hardware checks remain pending. No real project, active app or shared Chrome was
changed, and no commit, publication or release was performed for this work.

## Version 0.7.1 branch handoff — 2026-10-05

The authorized handoff reconciles the changes since `07d9311` on
`codex/phase3b/output-page-builder`. Version 0.7.1 is a patch for existing review,
source-preview, manual-response and export behavior; stored schemas are unchanged.
Bulk PDF importing was not started. General bold/italic preservation and automatic
small-running-header title selection remain backlog/limitations. The saved-title
preservation correction and manual arranged-title repair are verified below;
no actual project repair, re-extraction or approval was performed.

Final runtime/test/tool/launcher candidate:
`a24f4a3acb88ff98f42000c7fa5839e416d610699399734b38da4b93b84fb716`
(144 files, documentation excluded). **515 tests passed in 35.193 seconds** with
`TMPDIR=/private/tmp .venv/bin/python -m unittest discover -s tests -v`.
Separate previously authored functional and artifact drivers were rerun against
this exact candidate: **32 filter/merge browser groups**, **four manual-response
browser groups**, **11 source/export/readiness/Copy browser groups**, and **five
saved-artifact groups**. These are overlapping coverage, not extra unit tests or
a new independent human review. The source-header repair additionally passed six
disposable browser groups, inspected saved artifacts and exact Undo.

Final coverage includes every review/type intersection, first-result focus below
sticky controls, empty/reset behavior, dirty cancellation with exact selection/
scroll/text preservation, delayed source rendering, keyboard/narrow/reduced-motion
behavior, stale saves/merges, Save/approval/Undo/reopen, source pixel alignment,
manual ZIP/clipboard destination agreement, preserved earlier responses, clipboard
fallback, partial/complete media-to-readiness, saved-export focus, exact Copy,
stale Copy recovery and owned Quit. Actual HTML/Gutenberg/WXR/Markdown and arranged
package inspections retain authored standalone equivalents once, all 19 fixture
images with exact alternatives/local bytes, and WXR's exact Gutenberg content.
Acceptance stamps on the disposable artifact fixture are test instrumentation,
not editorial approval. Providers were forbidden and native folder opening mocked.
An initial copied artifact fixture required renewed page review after changed
export settings; the gate correctly blocked it, and the instrumented rerun passed.

Private evidence is retained under `build/release-0.7.1-20261005/`. The final
before/after checks matched all 144 candidate hashes and all 314 files across four
original projects. Six final screenshots were visually inspected, and all owned
test servers exited 0. Public source
and documentation scans found only synthetic test attachment IDs, with no actual
source names, project paths or private attachment metadata. No private PDF,
source screenshot, generated project export or evidence file is included in Git.
The existing public origin is `https://github.com/baschwar/pdf-to-web.git`; its
branch matched `07d9311` before publication. GitHub reports zero configured Actions
workflows. The final completion report supplies the pushed commit, verified remote
SHA and any check results. No main merge, tag, GitHub release or deployment is
included. Human VoiceOver, production WSUWP/plugin imports, Windows hardware and
the representative multi-page WordPress round trip remain pending.

## Small running-header title recovery — 2026-10-05

The author reported good content results apart from a missing document H1 in a
four-page sample. Read-only inspection confirmed that its small repeated header
is present in source pixels and PDF text on every page, but absent from raw JSON,
normalized blocks and saved exports. It has no block ID and was not removed by
review exclusion. Both the committed baseline and current largest-font selector
choose a larger body section instead; automatic title detection remains limited.

A disposable repair probe exposed a separate preservation defect: after demoting
that section, reopening added it again as a recovered title. Source-title
initialization now refuses to add a title once a review revision has been saved,
while fresh normalization and existing matching-title box backfill retain their
behavior. One new regression test covers the saved demotion. **49 normalization
and source-geometry tests passed in 0.571 seconds**, and **28 arrangement tests
passed in 0.720 seconds** before the preservation fix.

The final disposable browser repair passed **six groups**: section H1-to-H2 change,
explicit arranged title, exactly one semantic H1 with both tables retained,
save/reopen at 390px, actual saved HTML/Gutenberg/WXR exports and exact Undo of
block and arrangement records. Source text, IDs, provenance, links, tables and
other block decisions stayed intact. The WordPress template-title option was
honored: WXR carries the correct page title while body Gutenberg omits H1.
Zero JavaScript errors or horizontal overflow; desktop/narrow screenshots were
visually inspected. The owned server exited 0. An initial probe exposed the real
recovery defect; a subsequent driver synchronization race was corrected and its
log retained. No blanket initial-pass claim is made.

Existing projects need an explicit author repair through Structure and Arrange
Pages after relaunch; automatic re-extraction, source-header insertion or review
approval was not performed. README describes the arranged export route and
WordPress title-field distinction. Private source text, IDs, screenshots, saved
artifacts and recovery instructions remain under
`build/bloodborne-title-readonly-20261005/`. Final candidate-wide verification and
publication status are recorded separately.

## Inline formatting feasibility — 2026-10-05

This low-priority read-only follow-up inspected the requested table-heavy sample,
identified by the newest Recent projects record and matching project/source
metadata. The authenticated live session was not separately queried or navigated.
Both cached source-page images and PDF font dictionaries were inspected. The
sample has clear regular, bold, italic and combined font metadata, but some raw
elements coalesce differently styled PDF spans under one font label.

Of 51 normalized table cells, 27 retain multiple raw font names in provenance;
39 contain raw bold/italic text. No cell has normalized formatting runs. General
normalization does not translate font names into runs; table normalization joins
descendant text, and HTML/Gutenberg table rendering escapes plain cell content.
The actual saved WordPress export matches its manifest hash and the current
serializer byte-for-byte: four tables, no strong elements, and one emphasis
element for the recovered source note. This confirms partial support, not a
regression in an already-supported formatting path. Markdown also currently
ignores typed formatting runs.

Thirteen existing focused tests passed in 0.198 seconds, covering Gutenberg,
recovered-note emphasis, unchanged list saves and rich list editing with Undo.
Synthetic artifact probes confirm existing paragraph strong/emphasis runs survive
HTML, Gutenberg and WXR, while table-cell output and Markdown remain plain.
The 514-test full-suite result in the first-matching-block entry below applies to
the runtime unchanged by this follow-up's documentation-only edits. README and
Future Features
record a bounded proposal that separates reliable source presentation from
author-confirmed semantic emphasis and retains links, footnotes, IDs, table spans,
review fingerprints and explicit existing-project recovery. No formatting feature,
re-extraction, migration, dependency installation or live-app restart was performed.
All 44 original project files retained their before/after hashes, and all 144
runtime candidate hashes remained unchanged. Diff whitespace checks passed.
Private evidence is retained in `build/inline-style-readonly-20261005/`.

## First matching block after filtering — 2026-10-05

Explicit changes to either Structure filter, including Reset filters, select the
first matching block in saved reading order and reveal it below the sticky
controls with its source context selected. Both filter values remain active.
Empty intersections focus and announce Reset filters without selecting a hidden
block. Save, approval, Undo, reopening and finding-link navigation retain their
existing behavior; they do not use the new first-result action.

The existing unsaved-editor guard runs before a filter change. Cancel and Escape
preserve both filters, selection, exact scroll position and entered fields.
Confirmation closes the dialog before focusing the first permitted result.
Delayed source rendering resettles the selected block only while it still owns
focus. Narrow-layout and reduced-motion checks passed without forced animation.

The 144-file runtime/test/tool/launcher candidate is
`21d2fe216770714635ddc55a6c379e8a5d4a2152065d06edc9cdaa9790f39a51`
(documentation excluded). **514 tests passed in 35.227 seconds** using
`TMPDIR=/private/tmp .venv/bin/python -m unittest discover -s tests -v`.
Synthetic browser verification passed **32 groups** at 1440px and 390px, including
all 28 review/type intersections at each width, first-result focus, an already
matching later selection, empty results, dirty cancel/confirm, delayed source
rendering, keyboard navigation, reduced motion and retained Save/approval/Undo/
reload behavior. Zero JavaScript errors or horizontal overflow. Both representative
screenshots were visually inspected. JavaScript syntax and diff whitespace checks
passed. All 144 candidate hashes matched after testing; all 84 files in the
original project's before/after inventory retained their hashes. The owned fixture
server exited 0; the real app was not restarted or navigated.

A dense infographic remains an explicit regression case: its author's assessment
of the preview did not pass automatic grouping/layout acceptance. Retained assets
are useful, but manual semantic reconstruction may be necessary. Local filter,
source-outline and export tests do not establish acceptable automatic content
grouping. No real-project reconstruction, re-extraction or migration was performed.
This limitation is recorded in README and ignored local evidence.

Private evidence is retained in `build/filter-first-result-20261005/`, including
the browser report, full-suite log, before/after inventory and infographic
regression record. README and changelog describe first-result navigation. Work
remains uncommitted on `codex/phase3b/output-page-builder` at base `07d9311`;
nothing was pushed, merged, tagged or released. Human VoiceOver, production
WSUWP/plugin imports and actual Windows acceptance remain pending.

## Structure filters and Merge next safeguards — 2026-10-05

Structure now combines Review state and Block type in two compact rows. Their
intersection drives visible cards, contextual counts and Previous/Next. Linked
image descriptions affect their owner's state without adding block rows. Choices
remain separate per canonical project folder in browser-tab storage, including
projects with identical source filenames. Save, approval, classification changes,
Undo and reopening preserve both filters; empty views retain them and focus Reset
filters. Explicit finding links reveal their target with an explanation of the
necessary filter changes. Hiding dirty editors requires confirmation and keeps
their fields in the tab. Other saves, structural actions and Undo cannot discard
those fields; snapshot checks reject stale saves without overwriting newer work.

Merge next retains the shared server eligibility for adjacent matching text
blocks and same-level headings. List, mixed-type, rich/nested, excluded and final
block boundaries remain disabled with accessible reasons. Unsaved edits, saving
and hidden actual neighbors disable merging; filters never change its candidate.
Snapshot and target validation reject stale merges. Older server markup remains
disabled until relaunch rather than being enabled by newer JavaScript. Supported
merges retain their existing fresh-review and Undo behavior. Existing projects
are not re-extracted, migrated, merged or approved by these changes.

The final 144-file runtime/test/tool/launcher candidate is
`4bde04fb2c2fd621a6ab5b7dfa55711bf32b7daa9d7a1c23a4a7be1d9bdb1492`
(documentation excluded). **514 tests passed in 34.524 seconds** with the
documented macOS command `TMPDIR=/private/tmp .venv/bin/python -m unittest discover
-s tests -v`. The first default-temporary-directory run exposed seven existing
`/var` versus `/private/var` path-sensitive failures; its log is retained. No
unrelated path implementation or dependency changes were made.

Eight merge tests, five new filter tests and 16 existing layout tests passed.
Synthetic browser verification passed **23 groups** at 1440px and 390px, including
all 28 review/type combinations at each width, keyboard navigation, contextual
counts, dirty confirmation and Escape, classification save/Undo, finding links,
last matching Save and approve, stale save/merge rejection, supported merge/Undo,
older markup and project isolation. Zero JavaScript errors or horizontal overflow.
Both representative filter screenshots were visually inspected. All 144 candidate
hashes matched after testing; all 58 original project files retained their hashes.
Owned fixture servers were stopped; the real app was not restarted or navigated.

README and changelog explain the workflow and relaunch step. Work remains
uncommitted on `codex/phase3b/output-page-builder` at base commit `07d9311`;
nothing was pushed, merged, tagged or released. Private evidence is retained in
`build/merge-safeguards-20261005/`. Human VoiceOver, production WSUWP/plugin imports
and actual Windows acceptance remain pending.

## Manual response destination and infographic review — 2026-10-04

This local follow-up builds on published branch commit `07d9311`. New work is
uncommitted; no additional push, merge, tag, release or deployment is authorized.
Original projects and the live app remain untouched. Authorized source inspection,
editing, review and export checks use disposable copies or synthetic fixtures.

- Copied manual drafting instructions, ZIP instructions and request metadata name
  the selected project's absolute response destination and unique suggested JSON
  filename. Earlier files are preserved. Tools without authorized local access
  return an attachment/download instead of inventing a folder or claiming a save.
  Manual sharing discloses the local path. Exchange-v1 identities and explicit
  validate/import/review remain unchanged; responses may be selected elsewhere.
- Recovered title/subtitle outlines compose PDF text and graphics transforms and
  encoded glyph widths. Ordinary source boxes account for the actual MediaBox
  origin and rotation. A read-only display overlay preserves existing saved text,
  coordinates and decisions. Edited or ambiguous text receives an explanatory
  no-outline state. Tall rendered pages and highlights share the visible image
  dimensions; the desktop pane reveals selected regions within the available
  viewport and supports keyboard scrolling. Narrow layouts keep natural page
  scrolling; long response paths wrap.
- Authored standalone visual equivalents are included in document HTML,
  Gutenberg, WXR and Markdown. The shared arranged-page projection avoids
  duplication, preserves image associations and exclusions, and leaves original
  records unchanged. Pending reviews still prevent publication; unaccepted
  drafting suggestions are not included.

The independent source review accounts for all 44 saved blocks and all 19 image
assets in an approved source snapshot. It identifies repeated/shadow title text,
a truncated duplicate introduction, numbered-section placement and icon/group
reading-order decisions. These are explicit author-review findings, with private
block-level evidence retained locally. No deduplication, reclassification,
automatic ordering or medical/editorial approval is applied to real data.

Focused regressions pass: six manual-destination tests, 15 geometry tests, seven
standalone-description export tests and 28 existing arranged-page tests. Browser
review checks exercise description counts, image saves/approval, exact filters,
late rendering, Undo and reopening on a disposable source copy. Saved export
checks inspect HTML, Gutenberg, WXR, Markdown, image bytes and arranged output.
The final 142-file runtime/test/tool/launcher candidate is
`2e37a0575a4c03cdede736f1a6cdbea89d461022a27eb50303c1894514c48e5c`
(documentation excluded). **505 tests passed in 30.748 seconds**; all 142 hashes
matched afterward. JavaScript syntax and diff whitespace checks passed. The
source owner's actual copied-PDF browser probe passed 26 geometry/resize/late-load
assertions with zero JavaScript errors. Twelve actual Poppler rendering cases
cover three paper sizes, four rotations, nonzero MediaBox origins and a distinct
CropBox; all exited 0 and pixel alignment stayed within two pixels.

Before the final sticky-pane correction, the independent functional reviewer
passed **18 groups** on runtime candidate `bed0812a`:
four destination checks, five actual saved-export/package inspections and nine
browser source/navigation/review-gate groups. All 142 hashes matched before/after
and at cleanup; zero JavaScript errors were recorded. Original project inventories
remained byte-identical across all 41 files. The owned server exited 0 through
Quit. Earlier eight review groups cover counts, ordinary Save, Save and approve,
advance, exact filters, late rendering, newer editor focus, Undo and reopen.
Native folder opening was mocked; native macOS select keystrokes and external
acceptance were not established.

On the final candidate, independent visual review passed **88 selections** across
all 44 blocks at desktop/390px, all 44 desktop selected-region visibility checks,
resize alignment, keyboard pane scrolling and editor-focus preservation. Ten
representative screenshots were visually inspected; title and References outlines
are correct and visible. All 142 candidate hashes matched before/after; all 41
original files retained their hashes, sizes and mtimes. Zero JavaScript errors or
horizontal overflow; the owned visual QA server exited 0. The source owner also
passed ten integrated pane/keyboard/resize/late-load groups.

The final independent functional smoke passed **11 groups** on `2e37a057`,
covering desktop footer visibility, preserved review focus, keyboard pane
scrolling, natural narrow layout, source-title alignment, pending review gates,
partial/complete media matching to readiness, Continue to controls, saved-export
results, exact Copy bytes/focus, no-image export and stale-copy recovery. All
142 hashes matched before/after and cleanup; original 41 files remained unchanged.
Zero JavaScript errors; the owned functional QA server exited 0 through Quit.

Private evidence: `build/response-destination-highlight-20261004/`,
`build/infographic-source-review-20261004/` and
`build/infographic-functional-independent-20261005/`. Local browser/fixture
approval does not establish human VoiceOver, production WSUWP or Windows
acceptance; those remain pending.

## Latest authorized UI continuation — 2026-10-04

This continuation builds on `70d0a72` and retains the earlier edits. The user
requested a scoped branch push after final checks. No main merge, tag, release,
deployment, real-project migration or real app restart is included.

- Quit reaches an announced terminal stopped state after accepted shutdown and
  two unavailable local health probes. Confirmation controls disappear; offline,
  HTTP-error and timeout cases retain uncertainty and retry feedback.
- Drafting method controls show the selected manual/provider workflow. One manual
  ZIP export offers counted pending/selected scope before completed-response import.
  Blank templates receive an actionable summary; strict alt and identity checks
  remain. Imported drafts remain suggestions requiring human review.
- Successful image Save and approve follows solo Approve's visible reading order,
  preserves the exact filter and handles empty filters, final completion and Undo.
  A narrow-layout source-render race now resettles the focused next card only while
  it still owns focus; newer editor focus and typing are preserved.
- Link Save and approve atomically corrects the displayed nested link and approves
  its containing block's final content fingerprint in one revision. Ordinary Save
  still marks changed content pending. Other link findings remain unresolved;
  blank, stale and foreign-target attempts cannot partially save or approve.
- App exports stay in the chosen project's output subfolders. Exact paths and
  authenticated Open output folder replace prominent browser downloads; optional
  browser copies are collapsed and explicitly follow browser settings. Unique
  history snapshots preserve reusable previous outputs before replacement. Original
  source files and existing Downloads files are preserved. No-image documents skip
  image drafting and WordPress media mapping.
- Export readiness remains visible and receives focus/scroll after media matching,
  for blocked or stale export/copy actions. Ready exports focus completion and
  saved files; successful copying stays at its control. Continue to Export and
  copy content focuses that section. The earlier always-readiness behavior is
  superseded by this result-specific navigation.

Final runtime/test/tool/launcher candidate:
`07bc2930903225181e8fb0c5b82df08e2031444a1423e9b40b405aa1493afac6`
(139 files; documentation excluded). **477 tests passed in 30.910 seconds**.
The focused link-workflow suite passed **18 tests in 1.504 seconds**; output routes
also verify report, media, HTML, Gutenberg, WXR and arranged-package persistence,
prior-output recovery, authorization, confinement and no-image text review gates.
Earlier failed runs are retained locally, including outdated no-image layout
expectations corrected without weakening export review checks.

Read-only response inspection distinguished an unchanged blank template from a
completed valid response. Historical task snapshots demonstrate that importing
image suggestions did not invalidate existing approvals or create extra image
review tasks; linked descriptions are included in their image-owned tasks.
Historical counts are not treated as current while the user actively reviews.
The user confirmed successful image-containing and no-image document results; this does not establish
production WordPress, human VoiceOver or actual Windows acceptance.

Independent navigation verification passed 17 review-navigation groups and three
no-image export groups on the preceding candidate. A final five-group check on
this candidate reconfirmed narrow-card geometry, exact filter retention, no-image
export-result focus, valid generated HTML, no automatic download, exact optional
copy bytes and graceful owned-server exits. All 139 hashes matched before/after;
zero browser JavaScript errors were recorded. Native folder opening was mocked.
These browser groups overlap the full suite and are not added to its test count.

Independent output verification passed 15 desktop/narrow groups plus five
nested-link groups on the preceding runtime-identical candidate. Four final
manual-exchange groups verified empty-model save, immediate method visibility,
saved reload, keyboard ZIP export, actual copied instructions, read-only JSON
validation and explicit import. The request trace contained settings/export/import
and Quit only, with no provider/preflight calls. Final 139-file hashes matched
before/after, zero JavaScript errors were recorded and owned servers exited 0.
Native folder opening was mocked; native select keystrokes and arranged-package
browser coverage were not established in this check. Full package functional
coverage remains in the suite. An added no-Ollama regression passed within the
focused 15-route suite (1.449 seconds) and final 477-test suite. Detailed
private evidence stays ignored under `build/quit-stopped-feedback-20261004/`,
`build/image-navigation-independent-20261004/` and
`build/structure-zip-independent-20261004/`. External acceptance remains pending.

## Earlier local continuation — 2026-10-04

The published checkout at `70d0a72` remains the baseline. This continuation keeps
all existing edits. At this earlier checkpoint its changes were uncommitted;
no push, merge, tag, release, deployment or real-project processing occurred.

- Manual CSV mapping has a visible entry beside XML matching. Unmatched or
  ambiguous results and XML failures reveal the existing tools and recovery links.
  Existing identity validation, review decisions and Undo remain in use.
- Optional image-description tools precede Reading order and open when pending
  image review or draft requests/results make them useful. An explicit browser
  choice persists per project; direct links reveal tools for a visit without
  replacing that choice. Opening tools does not save or approve content.
- Quit is available throughout the app, confirms unsaved current-tab fields and
  warns about all tabs. It refuses during requests, streamed downloads and queued
  or running generation. It stops only the owned server; external servers refuse.
  Cancel/Escape preserve edits, callback failure supports retry, and another tab
  reports an already requested shutdown. An exact copied macOS launcher ended
  normally; actual Terminal window closing and Windows hardware remain unverified.

Earlier runtime/test/tool/launcher candidate:
`6697bf09f11b29adc5a76ab9538e11c2a80487253ae3a9114c58dddd7fdc4558`
(137 files; documentation excluded). **463 tests passed in 27.924 seconds**;
the focused lifecycle/discovery/layout checks passed **32 tests in 2.804 seconds**.
The first full run's two obsolete always-collapsed expectations were updated to
the useful-default behavior while retaining the other layout assertions. Both
failure and final passing logs are retained locally.

Independent checks include six functional Quit tests, earlier 16 discovery/media
and seven Quit browser groups, and separate final five- and four-group smoke
checks on matching runtime hashes. They verify CSV import/Undo, preferences,
keyboard and 390px layouts, unsaved Cancel, busy refusal, shutdown races,
failure/retry and actual owned-process exit. Final smoke reports record zero
JavaScript errors, unchanged saved fixture bytes and stopped owned servers.
These groups overlap the full suite and are not added to its test total.

A further independent check of the user's readiness-navigation request verified
successful XML matching, CSV import, Export and actual Copy HTML at both 1440px
and 390px. All eight actions focus the readiness heading below the sticky header;
clipboard contents exactly match generated HTML. Zero browser errors, unchanged
137-file candidate and normal owned-server exit are recorded in
`build/discoverability-quit-independent-20261004/readiness-actions/report.json`.
This behavior was already implemented; no duplicate runtime change was needed.

Installed Homebrew Poppler 26.08.0 was reverified without another installation.
The launcher paths resolve both rendering commands even with a minimal initial
PATH. Fresh uncached rendering of two pages from an approved real-PDF disposable
copy produced 1020 × 1320 PNGs; source bytes remained unchanged. Prior caches
support earlier successful rendering, but the later PATH failure's cause is
unknown. Existing diagnostic coverage passes in the full suite; its historical
54-task warning was one included block review, and the inspected current review
now records that diagnostic as resolved. Pillow was not installed. The live
app and actual project state were not changed or restarted.

Evidence: `build/held-items-sprint-20261004/`,
`build/discoverability-quit-independent-20261004/`, and
`build/safe-quit-independent-20261004/`. Earlier rendering and diagnostic evidence
is retained in `build/poppler-diagnostic-20261002/`. External acceptance below
remains pending.

## Current implementation and local verification

The Phase 3B page/article builder is implemented. Existing single-document
review, preview and export workflows remain available; arranging several output
pages is optional. See [workflow and schema](PHASE3B_OUTPUT_PAGES.md).

The accumulated stabilization work covers:

- Atomic Save and approve for editable blocks. Image approval validates the
  displayed image and linked descriptions together; ordinary saves and material
  edits still require manual review. Missing text, stale snapshots and conflicting
  associations reject approval without partial writes.
- One image-owned review task for linked descriptions, with a unified editable
  form, direct recovery links and consistent counts across Document, Structure,
  Accessibility and Export. Provided text awaiting review is distinguished from
  missing text. Standalone descriptions keep their own editor.
- Accessibility bulk review with exact visible scope, explicit confirmation,
  stale-scope rejection, normal save/reopen and Undo. Completed decisions remain
  editable history. Document findings, content approvals and automated HTML checks
  have distinct scopes; overlapping counts are not added together.
- Document diagnostics with a recorded cause, affected source/block context,
  publication impact and a recovery action. Historical resolved diagnostics stay
  separate from current manual review tasks. Missing targets have useful guidance
  without broken links.
- Media routing that preserves existing content approvals when only WordPress
  URLs or attachment IDs change. Source-image or authored-text changes still
  require fresh review; generated publications remain sensitive to mapping changes.
- Exact-filename media matching after unchanged-image re-upload. Changed IDs
  require explicit confirmation and the same saved URL; XML does not prove image
  bytes unchanged. Missing, ambiguous or different-URL entries keep current
  mappings and explain why. Choosing another XML clears confirmation visibly.
  Results distinguish updates, already-current mappings and confirmation required.
- Explicit preview/confirmation for restoring approvals lost to earlier routing-only
  changes. Retained history must prove the original decision, unchanged content,
  coherent project identity and exact current scope. Recovery preserves original
  approval dates, descriptions, mappings and newer decisions; uncertain histories
  require manual review. Undo consequences are disclosed before confirmation.
- Export readiness visible for both ready and blocked projects. Matching media,
  document export and Copy content move focus and scroll to readiness; links return
  to matching results or content controls. Stale-copy recovery preserves the
  clipboard, clears obsolete results and directs the user to reload Export.
- Contextual Help opening separately from authoring, concise action feedback,
  floating Back to top, saved block/filter focus and keyboard focus below sticky
  controls. WSUWP previews explicitly use approximate local CSS.
- Source rendering with actionable missing-Poppler/start/render failures and retry.
  Chosen project folders retain original inputs and partial processing output;
  global Recent projects failures do not invalidate saved projects.
- Manual image-drafting instructions beside ZIP controls. Copy uses the existing
  clipboard helper, restores focus, preserves unsaved edits and offers fully
  selected readonly text if both copy methods fail. The fallback scrolls into view
  on narrow screens. Imported suggestions require human review.
- Retained nested text regions included in source outlines, with partial-coverage
  explanations where needed. Text-bearing lists without children remain visible,
  block incomplete publication and support explicit recovery with Undo. Mixed-block
  list conversion and real-project reconstruction remain separate author actions.

Earlier published runtime/test/tool candidate:
`09f0816c993f51990609721e87d7798c6570e946aa0bde1b1b3538feaa3fb892`
(134 files; documentation excluded). At this candidate, **452 tests passed in
26.708 seconds**; focused image-draft checks passed **36 tests in 1.744 seconds**.
Publication checks below record the final checkout after documentation sanitization.

### Browser and artifact evidence

Isolated Chrome workflows verified review/edit/save/reopen/Undo, explicit approval,
bulk review, pending/complete counts, Help, media matching/recovery, ready/blocked
export feedback, downloaded artifacts and clipboard behavior. Synthetic regression
fixtures contain generated local images and example.test URLs; approved real-input
checks used disposable copies and kept detailed evidence local.

- Media-to-WSUWP draft Page journeys parsed downloaded PNG ZIPs, mapping reports and
  WXR content. Image URLs, attachment metadata, alternatives and linked descriptions
  agreed with the reviewed fixture. Repeating current XML made no new revision;
  Undo/rematching and rejection of genuine edits were checked.
- Manual drafting exported and downloaded a real ZIP from a synthetic project.
  INSTRUCTIONS.txt, request.json, response-template.json, review-sheet.csv and PNG
  bytes were inspected. Exchange-v1, all five identity fields and null optional
  response fields matched the copied prompt. Six primary browser groups and an
  independent UI review passed, including exact clipboard contents, real native
  fallback, total/throwing failure, retry and separately opened Help. Unsaved fields
  and saved revisions remained unchanged; the independent copy-only check sent no
  POST requests. The failure textarea was fully visible below the sticky header at
  390px. Zero JavaScript errors; screenshots were visually inspected.
- Source pages rendered freshly from an approved disposable real PDF copy using
  Homebrew Poppler 26.08.0. The two inspected PNGs were 1020 × 1320 pixels. Prior
  local caches confirm earlier rendering; the later missing-PATH cause is unknown.
  Pillow remains separately absent and was not installed by assumption.
- Existing arranged-package tests exercise assignments, navigation, internal links,
  page-local footnotes/backlinks, image descriptions and representative downloaded
  HTML/Gutenberg/WXR/ZIP output. These are local fixture checks, not production or
  human acceptance of representative multi-page publications.

Local ignored evidence directories:

| Area | Evidence |
| --- | --- |
| Latest candidate, clipboard and full suite | `build/image-draft-copy-instructions-20261004/` |
| Independent clipboard review | `build/manual-copy-instructions-independent-20261004/` |
| Media refresh and result semantics | `build/media-xml-rematch-20261004/` |
| Readiness, approval recovery and broader coverage | `build/export-readiness-scroll-20261004/` |
| Poppler setup and diagnostic clarity | `build/poppler-diagnostic-20261002/` |
| Publication privacy audit and final checks | `build/publication-20261004/` |

These evidence files are not part of the published source. Owned test servers were
stopped; actual project data and the live app were not rewritten or restarted.
No private source PDFs, caches, generated publications, credentials or screenshots
are added by this stabilization publication.

## Historical local milestones

These are recorded earlier results, not current test counts or external approval.
Detailed historical notes, source identities and private comparisons are withheld
from this public summary and retained in ignored local evidence.

| Milestone | Recorded local result |
| --- | --- |
| Poppler setup and Document diagnostic clarity, 2026-10-02 | 338 tests passed; fresh real-source rendering on disposable copies |
| Draft discovery, project-local ZIPs and merge feedback, 2026-10-02 | 347 tests passed; nine desktop/narrow Chrome groups |
| Source-backup verification, 2026-10-03 | 361 tests passed; syntax and diff checks |
| Media refresh and result semantics, 2026-10-04 | 450 tests passed; actual-XML disposable-copy and synthetic regression checks |
| Manual instructions clipboard, 2026-10-04 | 452 tests passed; primary and independent browser checks |

## WordPress preview defaults — local verification, 2026-10-08

Preview and Arrange Pages now initially display WordPress Preview with the
project's saved WordPress profile. Semantic HTML remains selectable. Arrange
Pages refreshes an active WordPress preview when its profile changes, without
discarding unsaved page drafts. Local styling remains an approximation of the
destination theme and plugins.

Verification: **531 tests passed in 29.859 seconds**, including a test of both
initial iframe responses and saved-profile selection. **Seven headless Chrome
check groups passed** across desktop and 390px layouts, mode/profile switching,
reloads, and draft preservation. There were no browser errors or POST requests;
the disposable project's saved project and review files remained byte-identical.
Evidence is retained locally under ignored `build/wordpress-default/`.

The live app and real projects were untouched. Save work, quit and relaunch PTW
to load the new Python-generated screen defaults. These edits remain local;
external acceptance below is still pending.

## External acceptance — still pending

| Required check | Status and reason |
| --- | --- |
| Production-authoritative WSU WordPress/plugin Gutenberg and WXR imports | Pending: local serializers, shims and fixture imports do not establish compatibility with the destination's actual versions. A reported successful import is not full editor/render acceptance. |
| Human VoiceOver review | Pending: a person must listen and interact with representative workflows and exported output on macOS. Browser assertions do not replace this. |
| Actual Windows hardware | Pending: no actual Windows run established. |
| Dedicated representative multi-page WordPress round trip | Pending: verify complete content, arrangement, images, navigation, footnotes and edit/save/reopen on the authoritative destination. Synthetic package checks do not fulfill it. |

A later Docker startup check confirmed the installed engine and cached WordPress
images, but the WordPress Importer dependency was unavailable for that new local
run. No additional dependency was installed. Earlier local importer evidence is
historical; no fresh local WordPress import/editor acceptance is claimed here.

Provider draft quality, OCR/extraction hardening and optional backlog items remain
outside this publication. [Future work](FUTURE_FEATURES.md) does not authorize its
implementation. Local browser/axe checks do not certify WCAG conformance.

## Publication status

Version **0.7.1** records stabilization in CHANGELOG.md. The patch version reflects
corrections to existing workflows with unchanged stored schemas. The authorized
destination is the existing public repository's
`codex/phase3b/output-page-builder` branch. Publication is a source handoff, not a
backup of private projects. No main merge, tag, deployment or release is included.
The completion report identifies the exact pushed commit and any CI outcome.

Earlier branch publication at `07d9311`: **452 tests passed in 26.531 seconds** after
documentation sanitization. Python/JavaScript syntax, corpus JSON parsing,
version consistency and `git diff --check` passed. Runtime hashes still match the
browser-tested candidate above, so existing affected-workflow browser evidence
applies. Detailed private reports are preserved under ignored local `build/`.
