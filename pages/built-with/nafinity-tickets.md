---
title: Working with Nafinity tickets
---

# Working with Nafinity tickets

Use `naf/board` 0.1.7 or newer for Advanced DQL, compact board filters, workspace search, personal views, relevant notifications and the shared ticket editor. Board permissions and version checks apply to every ticket change.

## Searching across boards

Use the single global search in the top bar to find boards by name or ticket key,
and tickets by title, plain description or reference. Enter at least two characters. Suggestions
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
boards omit it. The top bar contains search without a project-name prefix on every
application page. The project heading and sidebar identify the current board.
The board's **Filter** control opens dedicated dropdowns. Simple mode has no
second text search; Advanced DQL can express the existing board text search.
Existing board text-filter links remain valid. Switching modes retains every
condition, and **Reset** clears them with the other filters.

## Filter a board with dropdowns or DQL

Open **Filter** above the board to use the dropdowns. **Advanced** replaces the
dropdowns with a DQL field and translates their current values. Press Enter or
**Apply** to run the query. **Simple filters** validates and applies the query,
then fills the dropdowns that can represent its conditions.

```text
status = open AND assignee = me
priority IN (high, urgent) AND due < 2030-01-01
board = NAF AND column = "In Arbeit"
(label = "Design" OR label = "Produkt") AND assignee != none
```

| Property | Accepted values |
|---|---|
| `status` | `open`, `closed`, `archived` |
| `board` | Board ticket key, such as `NAF`, or project id |
| `assignee` | `me`, `none`, user id, exact active project member name or email |
| `column`, `swimlane` | Id or exact displayed name |
| `label` | Id, exact displayed name, or `none` |
| `priority` | Registered priority id, including contributed priorities |
| `title` | Title equality; `~` matches a literal substring |
| `text` | Existing database fulltext search over title and description, using `~` or `=` |
| `number` | Positive ticket number; also `<`, `<=`, `>`, `>=` |
| `due`, `created`, `updated` | `YYYY-MM-DD`; also `<`, `<=`, `>`, `>=`; `due = none` finds missing dates |

Use `=`, `!=`, `IN (...)` or `NOT IN (...)` for every property. `NOT` binds before
`AND`, then `OR`; parentheses set an explicit order. Property names and keywords
are case-insensitive. Value ids and displayed names keep their exact spelling.
Quote names containing spaces with single or double quotes. Escape a quote of the
same kind or a backslash with a backslash. `ticket.status`, `board.identifier`
and `assigned` are aliases for `status`, `board` and `assignee`; `q` aliases `text`.

The expression always filters the current authorized board. A `board` condition
cannot turn it into a cross-board search or grant access to another project.
Archived tickets remain excluded unless the expression explicitly references
the `archived` status. An open/closed dropdown continues to exclude archives
when combined with such an expression. Created/updated comparisons use stored
UTC dates.

`me` means the current reader, including after returning to dropdowns and when
another member opens the link. Selecting a named person retains a fixed user id.
Conditions involving `OR`, negation, lists, repeated properties or values a
dropdown cannot represent remain visible as additional DQL. Switching modes
preserves every condition. Structured plugin filters remain in their original
filter envelope, with a visible summary in Advanced.

Queries use one line and reject control characters. They allow up to 2000
characters, 256 tokens, 12 nested groups/negations and
20 values per list. Invalid syntax, properties or values show an editable field
error and return HTTP 422. They do not display unfiltered cards. Board cards,
counts and live updates use the same query and retain the 300-card display limit.

The Filter disclosure, dropdowns, mode controls and query field remain keyboard
operable. Advanced has a field label, a short input hint, expandable help and
an announced error message. Native GET forms also support mode switching and
filtering without JavaScript.

## Save and share board views

Open **Views** beside **Filter** to manage personal views in the shared dialog.
Name the current filter combination and save it. Each person can keep up to
20 views per board. The displayed link contains dropdown filters, DQL and
contributed filters, so another project member can open the same view without
receiving your bookmark or additional permissions. The recipient's current
access is checked when opening it. An `assignee = me` view means the recipient's
assignments when shared.

Views retain core and contributed filters. A removed DQL property returns HTTP 422 instead of widening the saved view. Removing a plugin leaves its saved filter intact; opening that view reports an unknown filter rather than showing a wider result. A stale save asks you to reload instead of overwriting another change. **Remove** deletes only your bookmark.

## Find your assignments

Choose **My tickets** in the workspace menu. The list contains your current assignments across all readable, active projects. It starts with open tickets; choose closed or all non-archived tickets and sort by due date or last change. Pages contain up to 50 tickets, including results beyond the board's 300-card display limit. Archived tickets/projects and projects you can no longer read are excluded.

## Follow tickets

Use `naf/board` 0.1.8 or newer for the compact eye and followed-ticket overview.
The eye beside a ticket's number and status toggles your personal subscription.
An accent-colored eye with an outlined background means you follow the ticket;
a muted eye means you do not. Its tooltip names the action, and screen readers
receive the action label and pressed state. Read-only project members can
follow too. Following does not change the ticket version; transferring a
ticket clears its subscriptions from the original project.

With JavaScript, toggling the eye preserves the open drawer, keyboard focus
and unsaved ticket edits. Native forms remain available without JavaScript.

Choose **Followed tickets** beside **My tickets** in the workspace menu to see
only tickets you follow. The list spans currently readable, active projects,
starts with open tickets and supports closed/all status, due-date/last-change
sorting and pages of 50 tickets. Archived tickets/projects and projects you can
no longer read are excluded. Assignments and subscriptions remain separate lists.

## Choose relevant notifications

In personal settings, **Notify me about** defaults to all project changes. Choose **My tickets, mentions and followed tickets** to receive changes for tickets you created, are assigned to, follow or are newly mentioned in. Use the [ticket eye](#follow-tickets) to follow a ticket. Your personal scope and channel settings still determine whether following produces notifications.

Comment mentions use the displayed member handles. Email addresses do not count, and editing an existing mention does not notify the same person again. Your own changes, inactive memberships, muted projects and disabled channels remain silent. The mail worker checks current preferences and involvement again before delivery. Pre-feature in-app notifications have no relevance classification and remain available in all-changes mode.

## Use the keyboard and readable card metadata

The first keyboard link skips to the main content. Short choice lists support arrows, Home/End, Enter/Space and Escape; Escape returns focus to their trigger. Use the card action menu to move tickets without dragging, including in filtered or truncated boards.

Card metadata exposes priority, status, due-date purpose and full assignee names to screen readers. Decorative initials and icons stay out of the accessibility tree. Card action targets remain at least 32 × 32 CSS pixels across built-in densities, and built-in label colors retain readable text contrast. Custom themes and CSS need their own accessibility review.

## Choose the attributes in your ticket view

Open a ticket and choose **Deine Ticketansicht anpassen** at the bottom of its
sidebar. The board settings open **Deine Ticketansicht**, where you can switch
individual attributes on or off and save your choices. The selection belongs
to your account in that board; another board and another person's view keep
their own selection. Read-only board members can also customize their view.

Attributes retain their existing groups and order. Empty groups disappear.
**Standard wiederherstellen** removes your selection and shows all readable
attributes again. Newly registered attributes appear automatically unless you
have already stored a choice for that key. Existing read permissions continue
to determine which attributes you can choose and see.

Hiding a field changes its display only. Ticket values, exports, other people's
views and creation inputs retain their existing behavior. Title, description
and comments are fixed ticket areas and stay visible. Hiding tracked time also
hides its timer controls; an already running timer continues running. Restore
the field to use those controls again.

## Track time in the timer dialog

Use `naf/board` 0.1.9 or newer for the dedicated timer dialog. The stopwatch in
the recorded-time row opens it. It shows the ticket, elapsed time, whole minutes
ready to book and carried seconds. Choose **Start**, **Pause** or **Resume** to
control the clock, and **Book** to add whole minutes to the ticket. Pausing keeps
elapsed seconds without booking them; remaining seconds carry into the next booking.

One person can run a timer on one ticket at a time across boards. The dialog
names another running ticket before you start; starting here pauses that timer.
Concurrent starts from two tabs still leave only one running clock. Opening the
dialog reads current server state. Closing or redrawing it preserves the running
display until another server response supplies its state.

Booking reloads the ticket so later edits use its current version. Booked minutes
also enter your [personal hours journal](nafinity-invoices.md#exporting-personal-hours); editing the ticket's
manual total does not create a personal booking. Hiding recorded time in your
custom ticket view also hides the stopwatch and leaves a running timer active.

## Edit and discuss a ticket

With `naf/board` 0.1.9 or newer, title, description and sidebar editors occupy the
same space as their reading view. Status and assignee controls share one style,
and the sidebar stacks below the description on narrow screens.

Click the description text to open its editor, as with the title. Links and
other interactive content inside the description retain their own actions.
The edit control remains available to keyboard users. Board permissions still
determine whether editing is available.

The comment composer follows the discussion without covering its last comment.
Reply context, comment actions, expanded edit forms and the wrapping composer
footer have separate spacing. The composer stays outside the refreshed comment
list, preserving an unsent draft when new comments arrive. Sidebar labels and
values share their first text baseline, including open inline editors.

## Create with the same ticket view

**+ Neues Ticket** opens the shared ticket view with a local draft. The title opens
for typing immediately. Description and metadata show their values or muted
placeholders. Click **Beschreibung einfügen** to open one description editor;
click an attribute to open its input. Leaving a field updates the draft's display.
Escape restores only the field currently being edited to its value when opened.
The ticket is saved once you choose **Ticket erstellen**.

Opening the creation drawer keeps the board address, including its filters. Back
closes the drawer through the existing changed-draft confirmation. Reloading returns
to the board; changed drafts trigger the browser's native warning before reloading
or leaving the page. An untouched draft, an opened empty description editor, and a
draft with every change restored do not warn. Once creation succeeds, the address
changes to the saved ticket. Open the direct creation address in a new tab for a
standalone page; it also remains the fallback without JavaScript.

The drawer and the standalone creation address use `ticket.phtml` and
`ticket/field.phtml`, as do saved tickets. The shared field component provides the
read display and editor container, and the same browser open/close and keyboard
handlers serve both modes. Draft fields belong to one native creation form;
saved fields retain their existing automatic save forms. Required draft fields
open when native validation needs them. Without JavaScript, the native inputs
and plain-text description remain available.

The `core.extensions` asset loads the ticket module once, so it owns one editor
registry and one write queue. Quill initializes when the description is first
opened and is reused on later edits.

## Link related tickets

Open a ticket and choose **Link ticket**. Select a relationship from this ticket's
perspective, then open the ticket search. Type a number such as `42`, a full key
such as `NAF-42`, or words from its title. Suggestions show the key and title;
exact numbers come first. Arrow keys move through the results, Enter selects,
and Escape closes the search. Click **Link** to save.

Relationships include **relates to**, **blocks / is blocked by**, **duplicates /
is duplicated by**, **clones / is cloned by** and **resolves / is resolved by**.
The other ticket shows the corresponding inverse. For example, if ticket A
**is cloned by** ticket B, B **clones** A. These are descriptive relationships;
linking does not clone a ticket or change either ticket's workflow status.

Search suggests at most 12 tickets from the current board. It excludes the
current ticket, archived tickets and already linked tickets. It uses the same
board read permissions as opening a ticket and never searches other boards.
Without JavaScript, enter the ticket's number in the native field.

The full ticket page and the board's ticket modal use the same widget and shared
search control. Removing a link removes only the relationship. Existing links
remain **relates to** after migration. Changes require the normal ticket edit
permission and version; a stale edit is refused.

For installation upgrades, run the ordinary migration and asset publication
steps. `M202610110002TicketLinkRelations` adds the relationship type and direction
without replacing existing ticket pairs.

## If the result is different

| Symptom | Check |
| --- | --- |
| A shared view cannot be opened | Check current project membership and whether a contributed filter's plugin is installed. |
| An assignment is missing from My tickets | Check that the ticket and project are active, the assignment is current and you can still read the project. |
| A ticket is missing from Followed tickets | Check the eye state, list status filter, active ticket/project and current project access. |
| A followed ticket stays silent | Check the personal notification channel, project muting and current membership. |
| The timer dialog is unavailable | Use Board 0.1.9+, publish its assets and show recorded time in your ticket view. |
| A save reports a conflict | Reload the latest ticket or view and apply the change to its current version. |
