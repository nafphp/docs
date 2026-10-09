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
| `Change` | project, ticket, actor, type, payload | Anything was written — 24 kinds, from `ticket.moved` to `account.created` |
| `GrantsChanged` | actor, subject, scope, before, after | Roles or permissions moved (from [`naf/rbac`](../rbac.md)) |
| `SignIn` | email, provider, outcome, account | Somebody tried to sign in, successfully or not |
| `ExportStarted` | format, project, columns | An export is about to write its first record |
| `ExportLine` | format, project, ticket, row | One record, before it is written |
| `ExportFinished` | format, project, columns, count | An export wrote its last record |

One write event rather than twenty-four is deliberate. The listeners that exist mostly
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

Splitting it would make the two listeners that want everything register twenty-four times
to get it.

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

## Extension reference { #the-full-reference }

Every definition's parameters, the contracts, storage, the browser lifecycle for
contributed widgets, and the negative cases — an unknown key, a reserved id, a value the
type refuses — are documented with the code that implements them, in `docs/Extensibility.md`
of `naf/board`.
