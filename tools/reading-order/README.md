# Local reading-order UI bundle

Pinned framework-independent dnd-kit DOM/sortable 0.5.0 supplies pointer/touch,
sortable keyboard behavior, accessibility announcements and edge autoscroll.
The application's own Move to controls, focus handling and validation remain
available. No React rewrite or runtime CDN is involved. Runtime needs only the
bundled static assets; npm/Node are development-time build tools for this UI.

Build from this directory:

    npm ci --ignore-scripts
    npm run build

The locked esbuild 0.28.2 build writes the checked-in static bundle. Package scripts
are disabled during dependency installation. Ship reading-order.LICENSE.txt beside
the bundle; it contains the dnd-kit, signals-core and tslib notices. node_modules
stays ignored. Source contains no private project content.

Sortable's optimistic DOM movement is staged. Commit array state once from
source.initialIndex/source.index on drag end; canceled gestures restore unchanged
state. Shared-page anchors are disabled, accepted targets must match their section,
and both client/server validate the resulting fixed boundaries. Managers and
sortables are destroyed on rerender, close and pagehide. Apply sends one staged operation sequence (complete ID permutations, merge groups,
and unmerge IDs) with project identity/review token. Read-only preview and final
Apply replay the same in-memory planner. Only Apply uses existing review persistence
and output-reference reconciliation, making one revision. Full retained originals
live in optional versioned provenance. Unmerge refuses content/exclusion/source
changes or conflicting IDs instead of discarding edits. New merged content needs
review. Paragraph-only or compatible list-only selection respects physical
adjacency, list numbering/nesting, source boundaries and output ownership.

Source and sequence regions scroll independently on desktop. Short mobile windows
also scroll the bounded panel body so fixed footer actions remain reachable. Pointer
focus never changes outer scroll mid-click. Confirmation cancellation restores the
fresh trigger after rerender, and buttons avoid transient low-contrast fades.

Official API reference: https://dndkit.com/concepts/sortable/
Sensor/default plugins: https://dndkit.com/concepts/drag-drop-manager/

Physical touch devices, human VoiceOver and Windows hardware remain separate
acceptance requirements.
