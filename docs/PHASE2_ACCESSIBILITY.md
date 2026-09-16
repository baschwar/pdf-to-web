# Phase 2 Accessibility Findings

## Automated macOS smoke pass

The review application was exercised in local Chrome on macOS with
`tools/phase2-accessibility-check.js`. The pass covered:

- opening a recent project with the keyboard;
- named primary navigation and live status regions;
- Structure headings for every normalized block;
- source-page image alternative text;
- visible form controls and buttons with accessible names;
- keyboard changes to block type and heading level;
- keyboard reorder and undo;
- keyboard save;
- named semantic preview iframe and narrow-width selection; and
- keyboard export.

All scripted checks passed. Repeated block actions include the reading-order
number in their accessible names, while retaining concise visible labels.

## VoiceOver-oriented review

The heading outline is logical: page `h1`, section `h2`, and one `h3` for each
review block. Labels wrap their associated controls, status updates use polite
live regions, source images have contextual names, current navigation uses
`aria-current`, and no operation requires drag-and-drop or pointer input.

This environment cannot independently hear or judge VoiceOver speech output.
The keyboard and accessibility-tree smoke pass therefore verifies the mechanics
behind the requested VoiceOver workflow, but a short human-listening pass is
still recommended before broader distribution. That pass should confirm rotor
navigation and spoken verbosity on a long Structure screen.

## Residual concerns

- Long documents create many controls. Block headings and numbered action names
  make this navigable, but a future per-page filter would reduce traversal time.
- The source PDF opens in the browser's PDF viewer, whose accessibility behavior
  is outside this application.
- The HTML preview is an iframe. It has a useful title, but users must enter the
  frame to inspect exported content.
