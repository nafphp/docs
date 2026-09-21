---
external_classes: true
title: How Nafinity is extended
---

# How Nafinity is extended

Nafinity has two extension mechanisms and no others. Not a hook manager beside an event
system beside a filter chain — two, used for everything.

```
Registry   what exists          a plugin adds to a list the application renders
Event      what is happening    a listener takes part in something already running
```

Whether a third is ever needed is a question worth keeping closed. Before proposing one,
the answer has to be: what can this do that a registry and an event cannot express? A
second API for the same problem is not a reason.

## Providers

A plugin contributes by implementing one interface and being registered once. Everything
below happens inside `register()`, which runs after the board's own defaults and before
the installation's `extensions.php` gets the last word.

```php
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
are code, and user data is read in the request that needs it.

## The registries

Every one of them takes definitions of one type, keys them by id, orders them by an index
with the id as tie-breaker, and refuses a duplicate unless you pass `replace: true`.
Learning one is learning all sixteen.

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

## The events

Three, for the whole application.

| Event | Payload | When |
|---|---|---|
| `nafinity.changed` | `Change` | Anything was written: 24 kinds, from `ticket.moved` to `account.created` |
| `rbac.granted` | `GrantsChanged` | Roles or permissions were granted or withdrawn |
| `export.line` | `ExportLine` | One record is about to be written into an export |

One write event rather than twenty-four is deliberate. The listeners that exist mostly
want *everything* — the audit log and the live updates do — and a plugin that wants one
kind writes one line:

```php
event()->listen('nafinity.changed', function (Change $change): void {
    if ($change->type !== 'ticket.moved') {
        return;
    }
    …
});
```

Splitting it would make the two listeners that want everything register twenty-four times
to get it.

### A listener can refuse

`nafinity.changed` is dispatched inside the transaction that did the work. Throwing from a
listener rolls the whole thing back:

```php
event()->listen('nafinity.changed', function (Change $change): void {
    if ($change->type === 'ticket.moved' && $this->isFriday()) {
        throw new Failure(t('Freitags wird nichts nach Fertig geschoben.'), 422);
    }
});
```

The ticket does not move, its version does not advance, and the person is told why. This
is how a rule that no permission can express — one that depends on the data, the time or
another system — gets to stop something.

It costs doing the work and undoing it, which for a rule engine is the right trade: the
listener sees the finished state rather than a proposal, and that is usually what a rule
needs to judge.

## A worked example: changing an export

The case both mechanisms were sharpened on. A plugin keeps a state of its own on tickets,
and one external system needs that state reported as `done` — without the board ever
saying anything different.

Register the format:

```php
$context->exporters()->add(new ExporterDefinition(
    id: 'acme.external',
    label: 'External system',
    extension: 'txt',
    mimeType: 'text/plain; charset=utf-8',
    writer: ExternalSystemExporter::class,
));
```

Then say what it reports:

```php
event()->listen(ExportService::LINE, static function (ExportLine $line): void {
    if (!$line->isFor('acme.external')) {
        return;
    }

    if (($line->data['acme.reviewed'] ?? false) === true) {
        $line->data['status'] = 'done';
    }
});
```

Three things that are not accidents.

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

## What is deliberately not extensible

A ticket's `status` is `open` or `closed`, and no registry offers a third value.

It is not a vocabulary. A column marked as closing sets it, the board counts by it, and
the schema has a constraint on it. The workflow states a team actually works in are the
board's **columns**, which are project data — a team adds "Waiting for approval" in the
interface, without a plugin.

A plugin that needs a state of its own puts it on the ticket as a field:

```php
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

That is the test any proposed extension point has to pass. Not "can a plugin write this",
but "what happens to the data when the plugin is gone".

## The full reference

Every definition's parameters, the contracts, storage, the browser lifecycle for
contributed widgets, and the negative cases — an unknown key, a reserved id, a value the
type refuses — are documented with the code that implements them, in `docs/Extensibility.md`
of `naf/board`.
