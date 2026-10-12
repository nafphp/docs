---
title: How Nafinity is extended
---

# How Nafinity is extended

Nafinity exposes typed registries for definitions and object events for application changes.
A plugin registers a provider before Board boots; Board invokes it after its own defaults.
The host's optional `extensions.php` applies final overrides.

## Providers

A plugin contributes by implementing one interface and being registered once. Everything
below happens inside `register()`, which runs after the board's own defaults and before
the installation's `extensions.php` gets the last word.

```php-inline
use Naf\Board\Contracts\ExtensionProviderInterface;
use Naf\Board\ExtensionContext;

final class AcmeProvider implements ExtensionProviderInterface
{
    public function register(ExtensionContext $context): void
    {
        $context->priorities()->add(new PriorityDefinition('acme.blocker', 'Blocker', …));
    }
}
```

The context carries the container and the registries, never a current user: definitions
are code, and user data is read in the request that needs it. An extension's `composer.json`
requires `naf/board` for its API and declares
`"extra": {"naf": {"boot": {"before": ["naf/board"]}}}`. Its bootstrap only notes the
provider; Board boots after it, adds its defaults, runs providers by index and id, then loads
the host's optional `extensions.php`. Resolve Board services and replace definitions inside
`register()`, when those defaults exist.

## Definition registries { #the-registries }

Every one of them takes definitions of one type, keys them by id, orders them by an index
with the id as tie-breaker, and refuses a duplicate unless you pass `replace: true`.
Use the same registration conventions across the registries below.

| Registry | What a plugin puts in it |
|---|---|
| `permissions()` | Project actions, which then appear in the role editor |
| `priorities()` | A fifth priority beside the board's four |
| `ticketFields()` | Fields on a ticket, stored as ticket metadata |
| `fieldTypes()` | How a kind of value is validated, stored and drawn |
| `boardFilters()` | A filter, with its own SQL condition |
| `estimationScales()` | A scale a project can pick |
| `bulkProperties()` | Explicitly opted-in properties and domain handlers for transactional batches |
| `activityTypes()` | An entry kind for the history |
| `exporters()` | A format a board can be written in |
| `ui()` | Contributions into named slots and panels |
| `navigation()` | Entries in the sidebar |
| `views()` | A replacement for a named view |
| `settings()`, `settingSections()` | Settings and the panels they live in |
| `assets()`, `assetPackages()` | Stylesheets and modules, and where they are published from |
| `aiTools()` | Tools offered to a local model |

A plugin can also do everything any NAF plugin can: routes, controllers, commands, jobs,
migrations, translations, and replacing a core service through the container.

## Application events { #the-events }

Application events use objects: `dispatch(new Change(…))` and `listen(Change::class, …)`.
Their classes define payloads. PHP does not check existence for a `::class` string; use static
analysis and tests to catch misspelled listener keys.

| Event | Carries | When |
|---|---|---|
| `Change` | project, ticket, actor, type, payload | A registered application change, from `ticket.moved` to `account.created` |
| `GrantsChanged` | actor, subject, scope, before, after | Roles or permissions moved (from [`naf/rbac`](../rbac.md)) |
| `SignIn` | email, provider, outcome, account | Somebody tried to sign in, successfully or not |
| `ExportStarted` | format, project, columns | An export is about to write its first record |
| `ExportLine` | format, project, ticket, row | One record, before it is written |
| `ExportFinished` | format, project, columns, count | An export wrote its last record |

One write event serves all registered change kinds. The listeners that exist mostly
want *everything* — the audit log and the live updates do — and a plugin that wants one
kind writes one line:

```php-inline
event()->listen(Change::class, function (Change $change): void {
    if ($change->type !== 'ticket.moved') {
        return;
    }
    …
});
```

`SignIn` exists because signing in writes no row, so `Change` structurally cannot carry it.
Both outcomes travel on it, because the interesting one is usually the failure, and it carries
the address as typed even when no account answers to it.

Listeners interested in every change register once against `Change::class`.

### A listener can refuse

`Change` is dispatched inside the application transaction. Throwing from its listener rolls
back that database work. This fragment assumes registration inside a service whose
`isFriday()` method implements the application's rule:

```php-inline
event()->listen(Change::class, function (Change $change): void {
    if ($change->type === 'ticket.moved' && $this->isFriday()) {
        throw new Failure(t('Freitags wird nichts nach Fertig geschoben.'), 422);
    }
});
```

The ticket does not move, its version does not advance, and the person is told why. This
is how a rule that no permission can express — one that depends on the data, the time or
another system — gets to stop something.

The listener observes the resulting state before commit. External effects such as HTTP calls
or mail are not undone by a database rollback; defer them or use a reliable job/outbox design.

`SignIn` is dispatched after its transaction and cannot veto completed authentication.
Reject credentials or inactive accounts through the authentication provider.

## A worked example: changing an export

This example maps a custom ticket state to `done` in one export format without changing
the stored ticket. Register a format, then modify its exported row through an event.

Register the format:

```php-inline
$context->exporters()->add(new ExporterDefinition(
    id: 'acme.external',
    label: 'External system',
    extension: 'txt',
    mimeType: 'text/plain; charset=utf-8',
    writer: ExternalSystemExporter::class,
));
```

Then say what it reports:

```php-inline
event()->listen(ExportLine::class, static function (ExportLine $line): void {
    if (!$line->isFor('acme.external')) {
        return;
    }

    if (($line->data['acme.reviewed'] ?? false) === true) {
        $line->data['status'] = 'done';
    }
});
```

The example preserves these boundaries:

`$line->ticket` is `readonly`, and PHP enforces it: reassigning it, editing a key,
taking a reference and `unset` all raise an error. An export that edited the tickets it
was reading would be the worst possible way to find out. What a listener changes is
`$line->data`, a row that exists for the length of one download.

`isFor()` comes first. A mapping that was true of every format would also rewrite the
spreadsheet the team reads, which is rarely what anybody means by "the external system
needs `done`".

And the columns needed no registration. Every field a plugin registered through
`ticketFields()` is a column in every format, with the field's own read permission still
deciding whether this reader sees it.

## Ticket status and custom states { #what-is-deliberately-not-extensible }

A ticket's `status` is `open` or `closed`, and no registry offers a third value.

It is not a vocabulary. A column marked as closing sets it, the board counts by it, and
the schema has a constraint on it. The workflow states a team actually works in are the
board's **columns**, which are project data — a team adds "Waiting for approval" in the
interface, without a plugin.

A plugin that needs a state of its own puts it on the ticket as a field:

```php-inline
$context->ticketFields()->add(new TicketFieldDefinition(
    key:     'acme.approval',
    label:   'Approval',
    type:    'select',
    options: ['choices' => ['pending' => 'Pending', 'granted' => 'Granted']],
));
```

Stored, typed, permission-guarded, filterable and exportable — and, crucially, inert when
the plugin goes away. Values of an absent plugin stay where they are and the application
can name them. A value in `status` could not be inert: every count of open tickets is
`WHERE status = 'open'`, so tickets carrying a status nothing explains would silently
vanish from the board's own arithmetic.

When adding extension data, define how the application handles it after the plugin is removed.

## Browser lifecycle

A contributed module exports `mount(root, context, api)` and may return a disposer,
synchronously or through a promise. The board mounts each contributed root once and calls
its disposer once when closing the drawer or replacing a fragment. A disposer returned
after the root was removed is still called. Own listeners, timers and retained nodes
must be released there; a module failure leaves the fixed ticket areas available.



## Personal ticket field visibility

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

## Top-bar contributions

The `topbar.tools` UI slot uses `PageSlotContext`. Extensions can add controls there
or explicitly replace the `core.topbar.workspace` contribution through the existing
UI registry. The standard contribution contains workspace search; ticket creation
belongs to the project heading. Account actions remain in `topbar.actions`.

## Content after board filters

The `board.filters.after` slot receives `BoardSlotContext`, including normalized `filters`, project scope and CSRF `token`. The `core.board.saved_views` contribution supplies personal views through a data provider. Extensions may explicitly replace it through the UI registry; boards rendered through the common page renderer retain the same contribution.


## Opt into transactional bulk properties

`BulkProperty` is an explicit opt-in, separate from settings and ticket-field
definitions. A registered field does not automatically become mass editable.
A provider registers a resource/key pair, existing field type and domain handler:

```php-inline
use Naf\Board\Definition\BulkProperty;

$context->bulkProperties()->add(new BulkProperty(
    key: 'review_state',
    resource: 'example.records',
    label: 'Review state',
    type: 'select',
    handler: ReviewStateBulkHandler::class,
    options: ['choices' => ['pending' => 'Pending', 'reviewed' => 'Reviewed']],
));
```

The registry follows the normal ordering, duplicate/replacement and removal rules.
Identity is `resource:key`; `forResource()` returns definitions keyed by property.
Providers and host overrides can replace/remove definitions through
`bulkProperties()`. Removal removes the capability, without deleting stored data.

Implement `Naf\Board\Contracts\BulkPropertyHandlerInterface`:

- `options(BulkProperty $property, int $actor): array` authorizes the operation
  and resolves server-side type options, including currently permitted choices.
  It must refuse unauthorized use even if the property was visible earlier.
- `prepare(BulkProperty $property, int $actor, array $targets, mixed $value): Closure`
  runs in the batch transaction. Lock aggregates in deterministic order, verify
  every target's existence, authorization and domain invariants, and check expected
  versions for replacement operations. Return a write closure using the same PDO
  connection. Never commit, send mail, perform network calls or write files here.
  For several properties on the same aggregate, the closure must merge with earlier
  writes in this transaction rather than replaying a prepared stale snapshot.

`BulkUpdateService::properties($resource)` returns authorized definitions and
resolved options for a form. It hides only permission denials; unexpected errors
remain visible. `apply($resource, $targets, $values)` accepts 1–50 explicit ids and
1–20 opted-in keys, validates raw values before normalization through the existing
field types, prepares every write before executing any, and commits once. Any
exception rolls back every target, property and database-backed audit event.
Targets are deduplicated and sorted. Omitted keys are unchanged. Unknown keys,
invalid shapes, invalid values and implicit “all results” selections are refused.
No table or column names come from request input.

The service is reusable by other controllers. A new resource still needs its own
read/UI authorization and CSRF-protected endpoint; registering a property creates
no public route. Ticket handlers must retain project authorization, project locks,
ticket versions and board revisions. The framework cannot infer those rules.

## Shared multiselect controls

For controls contributing to the same native array, `choice()` accepts distinct
`id` values and `clearField: false`; `listId` is derived from the native control ID and
can be overridden explicitly. Put one empty marker before all
of those controls. Repeating the bare marker between array entries would discard
earlier selections when PHP parses the form. Closed role rows retain their native
checkboxes and submit with the rest of the form; JavaScript only draws the dropdown.
The component enhances controls in `nafinity:fragment-updated` containers and
closes their popovers on `nafinity:fragment-removing`.

Short choice lists focus their labelled listbox rather than an anonymous popup. Arrow keys
move between options; Home/End reach the first/last option, and Enter or Space selects it.
Searchable choices focus the combobox and keep text editing keys available. Escape closes the
choice and returns focus to its trigger. The application layout offers **Skip to content**
as the first keyboard link, targeting the focusable main region.

## Reusable notices

Invitations, user administration, settings, exports and invoice drafts use the
shared `src/views/components/notice.phtml` component. Invitation forms separate
introductory guidance, form fields and delivery notices with consistent spacing.

Render reusable notices through the native partial helper:

```html+php
<?= \Naf\Board\partial('components/notice', [
    'severity' => 'warning',
    'title'    => \Naf\I18n\t('Check before saving'),
    'message'  => \Naf\I18n\t('This change ends existing sessions.'),
]) ?>
```

`message` and the optional `title` are translated plain text; the component escapes both.
There is no raw HTML argument. `severity` accepts `notice`, `info` (the default), `warning`
and `error`. Unknown values fall back to `info`. Each variant has a local Material Symbols
icon, its own colour and an accessible severity label. Errors use `role="alert"`; other
variants use `role="note"`. Use errors for actual failures rather than general guidance.

For a dynamic message, `messageAttributes` can carry trusted view attributes such as
`['data-account-status' => true, 'role' => 'status']`. The hook is on the message paragraph,
so replacing its `textContent` preserves the icon. An empty notice without a title is hidden.
Keep attribute names in application code; message and attribute values remain escaped.
Shared styling lives in `app.css`, icons in `icons.css`. The ordinary application layout
loads both. A standalone page using this component must also load those stylesheets.

Notice partials use the same override lookup as other views. Existing `field()` and
`choice()` components remain the entry points for form controls; this component does not
change form submission or introduce a second rendering layer.

## Shared token contract

`src/Resources/public/assets/theme-tokens.json` is the canonical catalog for
built-in palettes, editable tokens and numeric bounds. `Themes::compile()`
builds saved and preview CSS from it. `tools/build-themes.php` generates
`tokens.css` as the shipped fallback. After changing the catalog, run:

```bash
php tools/build-themes.php
npx prettier --write src/Resources/public/assets/tokens.css
```

Components use the same semantic colors (`--bg`, `--surface`, `--text`,
`--muted`, `--line`, `--accent` and status colors) and the derived scales:
`--font-N`, `--space-N` and `--radius-N`. The common `--font-size`,
`--density` and `--radius` values determine those scales. Use
`--radius-full` for pills. Structural dimensions, such as panel widths,
icon geometry and image aspect ratios, remain component dimensions.

Extensions should consume these tokens in their own stylesheets. User-supplied
ticket colors remain ticket data. Explicit branding font/color settings apply
to the brand word only and continue to take precedence there.

Stylesheet addresses contain a SHA-256 content version and can be cached for
one year. A saved edit creates a new URL. An old uncached version returns 404;
an already cached file may remain available until its cache expires.
Theme definitions and revision state are read on the next request.

## Shared mail layout

See [host defaults and template overrides](nafinity-appearance.md#host-defaults-and-template-overrides) for the `mail/...` view contract and `data-email-layout` marker. Message producers share the same branding, CSS inliner and plain-text alternative.


## Enforce an optional WIP policy

Core WIP values are advisory. The separately installable Composer example in `examples/nafinity-wip-policy` demonstrates an admission rule through native project settings and `Change` listeners. Creating, moving, reopening, restoring or transferring open work into a full column returns 409 and rolls back native database effects. Ordinary edits, reordering and departures remain available. Project managers can disable enforcement. See the [versioned setup and policy reference](https://github.com/nafphp/board/blob/main/docs/Workflow-Policies.md); the example is not an independently published Packagist package.


## Extension reference { #the-full-reference }

Every definition's parameters, the contracts, storage, the browser lifecycle for
contributed widgets, and the negative cases — an unknown key, a reserved id, a value the
type refuses — are documented with the code that implements them, in `docs/Extensibility.md`
of `naf/board`.
