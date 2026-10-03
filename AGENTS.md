# PDF to Web — Agent Instructions

These instructions apply throughout this repository. The active development directive defines the task-specific scope and acceptance criteria. Explicit user instructions take precedence over this file.

## Product scope

- Build a local-first application for converting PDFs into accessible web content.
- Support extraction, structural review, accessibility authoring, semantic HTML, Gutenberg, and WordPress WXR exports.
- Preserve the existing document model and review workflow when adding features.
- Keep document processing and project data local unless the user explicitly authorizes an external service.
- Keep implementation within the active directive. Record useful future work without silently adding it to the current milestone.

## Before editing

1. Read the active directive, README.md, CHANGELOG.md, and relevant design or acceptance documentation that exists in the repository.
2. Inspect the relevant implementation and tests before choosing an approach.
3. Check the branch, remote, and working tree. Preserve all pre-existing changes.
4. Establish the relevant test baseline using the repository's documented commands.
5. Continue authorized implementation autonomously. Ask only when a missing decision materially affects scope, data integrity, or required behavior.

## Implementation and data integrity

- Reuse existing models, serializers, validation, and persistence mechanisms rather than creating parallel implementations.
- Preserve stable block IDs, document structure, reading order, accessibility metadata, review decisions, exclusions, and source provenance.
- Keep content recoverable. Exclusion must not become destructive deletion.
- Preserve save/reopen behavior, existing project compatibility, and Undo for new editable state. Use explicit migrations when the stored schema changes.
- For page arrangements, reference reviewed block IDs rather than copying their content. Content edits must remain consistent across review, previews, and exports.
- Validate missing, duplicate, or invalid assignments according to the directive. Prevent a package from being labeled complete when required assignments are incomplete.
- Preserve table semantics, image alternatives, complex-visual descriptions, heading structure, links, and footnote backlinks through exports.
- Resolve page-local footnotes and cross-page links consistently. Record unresolved findings in the package manifest or existing reporting mechanism.
- Never fabricate extracted content, review approval, accessibility results, or compatibility claims.

## User interface

- Use plain language and show the information needed for the current task.
- Put secondary explanations in accessible help text or tooltips when appropriate.
- Keep keyboard navigation, labels, focus behavior, and status feedback usable.
- Make incomplete work and unresolved findings visible before export.

## Verification

- Add or update meaningful tests for behavior changes, especially persistence, Undo, validation, and export correctness.
- Run focused tests during development, then the full documented suite before handoff.
- Check changed UI workflows in a browser. Exercise review, editing, Undo, save/reopen, previews, and downloads where affected.
- Inspect representative generated exports. A successful serializer call alone does not establish output correctness.
- Use synthetic or approved fixtures in Git. Keep private PDFs, local corpus files, generated exports, credentials, and temporary artifacts untracked.
- Report any verification that could not be performed and the specific reason. Do not substitute an automated check for human or production acceptance.

## External acceptance

Keep these items pending until evidence confirms completion:

- Gutenberg and WXR validation against the production-authoritative WSU WordPress and plugin versions.
- Human VoiceOver review of representative workflows and output.
- Windows verification on actual hardware.

Local tests and browser checks may establish implementation readiness while these external acceptance items remain pending. State that distinction in status and release documentation.

## Documentation

- Update README.md when workflows, commands, or supported behavior change.
- Update CHANGELOG.md for user-visible changes.
- Update the active directive or acceptance record with completed work, evidence, and remaining items when appropriate.
- Derive versions, test counts, and Git status from the current checkout. Do not treat old status reports as current evidence.

## Git workflow and permissions

- Authorized implementation includes local edits, verification, and focused local commits of completed, verified work.
- Work on the current branch unless the user or active directive specifies another workflow. Do not switch branches over uncommitted user changes.
- Stage only task-related changes. Never discard user work, rewrite shared history, force-push, or perform destructive cleanup without explicit authorization.
- Pushing, merging, creating or pushing tags, publishing releases, and deploying require explicit authorization in the current task or an applicable standing user instruction.
- Honor authorization already given. Do not ask again for an action that the user has already authorized.
- Do not infer release authorization from a request to process a development directive.
- Prepare and verify the work before requesting any required release or publishing decision. Leave a concrete, reviewable result.

## Completion report

Provide a concise handoff containing:

- What changed and the resulting user behavior.
- Tests and browser checks performed, with actual results.
- Remaining defects, limitations, and pending external acceptance items.
- Branch, commit if created, working-tree status, and whether anything was pushed or released.
- The next action needed, if any.

Distinguish implementation completion, local verification, external acceptance, and release status. Continue until the authorized task is complete or a concrete blocker requires user input.
