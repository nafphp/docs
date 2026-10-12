---
title: Working with Nafinity tickets
---

# Working with Nafinity tickets

Use `naf/board` 0.1.6 or newer for workspace search, personal views, relevant notifications and the shared ticket editor. Board permissions and version checks apply to every ticket change.

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
The board's filter row contains dedicated filters, with no second text search.
Existing links with a board text filter still work; changing another filter retains
it, and **Reset** clears it with the other filters.

## Save and share board views

Open **Saved views** below a board's filters. Name the current filter combination and save it. Each person can keep up to 20 views per board. The displayed link contains the filters, so another project member can open the same view without receiving your private bookmark or any additional permissions. The recipient's current access is checked when opening it.

Views retain core and contributed filters. Removing a plugin leaves its saved filter intact; opening that view reports an unknown filter rather than showing a wider result. A stale save asks you to reload instead of overwriting another change. **Remove** deletes only your bookmark.

## Find your assignments

Choose **My tickets** in the workspace menu. The list contains your current assignments across all readable, active projects. It starts with open tickets; choose closed or all non-archived tickets and sort by due date or last change. Pages contain up to 50 tickets, including results beyond the board's 300-card display limit. Archived tickets/projects and projects you can no longer read are excluded.

## Choose relevant notifications

In personal settings, **Notify me about** defaults to all project changes. Choose **My tickets, mentions and followed tickets** to receive changes for tickets you created, are assigned to, follow or are newly mentioned in. Open a ticket and choose **Follow ticket** to subscribe personally; readers can follow too. Following does not change the ticket version. A transfer clears subscriptions from the original project.

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

## Edit and discuss a ticket

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
| A followed ticket stays silent | Check the personal notification channel, project muting and current membership. |
| A save reports a conflict | Reload the latest ticket or view and apply the change to its current version. |
