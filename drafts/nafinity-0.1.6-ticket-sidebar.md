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
