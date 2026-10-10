# Workspace search and ticket creation

Waiting for `naf/board` v0.1.6 to be merged, released and available on Packagist.
Do not publish this feature in `pages/` before then.

After release, extend `pages/built-with/nafinity.md` with the following section and
add `topbar.tools` to its UI-slot reference.

## Searching across boards

Use the search in the top bar to find boards by name or ticket key, and tickets by
title, plain description or reference. Enter at least two characters. Suggestions
appear after a short pause and are grouped under their board names. Each response
replaces the groups dynamically; new boards do not need a predefined result slot.
Only boards you can currently read appear. Matching closed tickets and archived
tickets or boards remain available.

Use the arrow keys to select a board or ticket and Enter to open it. Escape closes
the suggestions. Clearing, closing or changing the search discards earlier answers.
Enter without a selected suggestion, the search icon, or **Open search results**
opens a separate result page. That page also works without JavaScript.

Suggestions include at most eight tickets and six additional matching boards. The
result page includes at most 50 tickets and 20 matching boards. If more results
exist, refine the query. Percent signs and underscores are searched literally.

**New ticket** appears in the project heading and opens that board's ticket dialog.
It uses the same primary action style as **New project** in the project overview.
The action is available only in a writable project; workspace pages and read-only
boards omit it. The top bar contains search only. The project name remains visible
there on board, ticket and project-settings pages. Other pages use their existing
heading without a repeated top-bar label.

### Extending the top bar

The `topbar.tools` UI slot uses `PageSlotContext`. Extensions can add controls there
or explicitly replace the `core.topbar.workspace` contribution through the existing
UI registry. The standard contribution contains workspace search; ticket creation
belongs to the project heading. Account actions remain in `topbar.actions`.

Implementation and verification: see the package's `docs/Settings-And-AI.md`,
`docs/Extensibility.md`, `WorkspaceSearchOverHttpTest` and
`tests/js/workspace-search.test.js`.
