# Search and relationship types for linked tickets

Waiting for `naf/board` v0.1.6 to be released and available on Packagist.
Keep this draft outside `pages/` until then. After release, add these steps to the
Nafinity ticket guide.

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
