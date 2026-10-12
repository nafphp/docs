# Nafinity dropdown filters and DQL

Publication gate: `naf/board` v0.1.7 must be merged, released and verified on
Packagist at its tagged revision. This draft describes the tested implementation
prepared for that release. It does not change the current published guides.

After publication, apply the following changes to
`pages/built-with/nafinity-tickets.md` and
`pages/built-with/extending-nafinity.md`. Run the documentation checks against
the published package and remove this draft once the guide updates are deployed.
No database migration or additional dependency is required.

## Filter a board with dropdowns or DQL

Insert this section before **Save and share board views** in the ticket guide.
Keep workspace search as the documented way to search across readable boards.
The board's simple mode retains its dedicated dropdowns without a second search
field; Advanced can express the existing board text search.

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

Replace the first paragraph of the existing section:

Open **Views** beside **Filter** to manage personal views in the shared dialog.
Name the current filter combination and save it. Each person can keep up to
20 views per board. The displayed link contains dropdown filters, DQL and
contributed filters, so another project member can open the same view without
receiving your bookmark or additional permissions. The recipient's current
access is checked when opening it. An `assignee = me` view means the recipient's
assignments when shared.

Retain the existing unknown-filter, stale-save and bookmark-removal explanation.
Add that a removed DQL property returns 422 rather than widening the saved view.

## Extension guide: board filter actions

Replace **Content after board filters**, preserving its existing heading anchor
if it is linked elsewhere:

`board.filters.actions` receives `BoardSlotContext`, including normalized
`filters`, project scope and CSRF `token`. It holds compact actions beside
Filter. The `core.board.saved_views` contribution supplies the Views dialog
through its existing data provider. Extensions may explicitly replace it through
the UI registry. `board.filters.after` remains available below the complete filter
tool and receives the same context.

## Extension guide: DQL properties

Add beside the board filter definition example:

DQL uses the existing `BoardFilterDefinition` registry. A lowercase extension
id matching `[a-z][a-z0-9_.-]*`, such as `example.reviewed`, is also a property:
`example.reviewed = "1"` uses its normalizer and bound `SqlCondition`. The
compiler composes `!=`, `IN`, `NOT IN` and boolean negation centrally. A removed
definition returns 422 when a saved expression references it.

An optional trailing `dql` closure adds property-specific operators or values:
`(string $operator, string $value, BoardFilterContext $context): SqlCondition`.
It receives `=` for negated equality and individual list members. Validate
operators and values, throw `Failure` for unsupported input, and bind every
user value. The supplied context contains the already authorized project and
actor scope; apply additional read permissions there. The callback serves both
counts and cards. The project predicate, archive rule and card limit surround
the compiled expression.

Simple equality using the default normalizer/condition can return to a contributed
dropdown. Compound conditions and definitions with custom DQL callbacks remain
visible as residual DQL. Structured values, ids outside the property grammar and
scalar normalizers that cannot round-trip through text remain in `filters[...]`.
Template overrides must preserve those inputs. The read-only, project-authorized
`board.filters` GET route translates drafts; the regular board GET applies them.
Neither route writes personal settings.

## Verification before publication

- Verify the final v0.1.7 tag and Packagist source revision.
- Run the package's PHP and browser module suites and formatting checks.
- Use dropdowns, switch to Advanced, edit a query and return to Simple filters.
  Confirm matching cards and residual conditions agree with the query.
- Check keyboard focus, malformed-query feedback, mobile layout and Views dialog.
- Verify shared `me` links under a different authorized account and denied project access.
- Apply the guide changes, run `tools/check_pages.py`, strict MkDocs and the
  documented example runner, then verify the deployed pages.
