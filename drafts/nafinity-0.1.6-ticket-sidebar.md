# Personal ticket sidebar and editing

Waiting for `naf/board` v0.1.6 to be merged, released and available on Packagist.
Keep this draft outside `pages/` until then. After release, add the user-facing
sections to the Nafinity chapter and the slot contract to its extension guide.

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

## Contribute fields through the existing registry

The visibility form uses `TicketFieldRegistry` and persists registered field
keys through the existing `project_user` setting `ticket_fields`. Its value is
a key-to-boolean map; an omitted key means visible. No separate field list,
preference table or write endpoint is needed. The standard sidebar renderers
apply the selection to core and contributed attributes.

A contributed panel receives the existing `TicketSlotContext`. Use
`$slot->shows($key)` for a registered field and `$slot->fieldsIn($group)` for
readable, visible metadata definitions. `$slot->showsGroup($group, $unavailable)`
checks whether a group contains a visible field; its optional second argument
lists field keys unavailable on the current ticket. These helpers preserve read
permissions and do not hide creation inputs. A custom panel that renders fields
directly must use these helpers to respect the person's selection.

Removing a contributed field leaves its stored choice harmless. Registering the
same key again restores that choice unless the person saved a new selection in
the meantime. Conditional information retains its refresh marker, so a timestamp
can appear when the ticket is closed after the view opened.

Verification: Board `TicketSidebarPreferencesOverHttpTest` and
`TicketFieldVisibilityTest` cover per-person/per-board isolation, viewer access,
standalone and drawer views, native save/reset, invalid choices, unchanged ticket
values, creation inputs, conditional refresh, contributed fields, escaping and
unique switch labels. Browser checks cover desktop and 390/320 px widths.

Creation verification: `TicketCreationOverHttpTest` checks the shared field contract
in drawer and standalone draft/detail responses and the native form fallback.
`ticket-creation.test.js` checks one module identity, lazy single editor creation,
local field confirmation and field-scoped Escape. Browser checks cover the draft,
creation, saved description editing and 390/320 px layouts.
