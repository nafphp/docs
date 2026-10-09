---
title: Roles and permissions
requires:
  - naf/rbac
---

# Roles and permissions

`naf/rbac` stores roles and grants in a database and provides administration fragments.
Applications and plugins declare available permissions in code. The privilege policy controls
which accounts can manage roles or grant access.

Install the package, configure a database, run its migrations and synchronize declared roles.
The migration and synchronization commands also require `naf/cli`.


```bash
composer require naf/cli
vendor/bin/naf db:migrate up
vendor/bin/naf rbac:sync
```

For MySQL 8.x, use `naf/rbac` 0.1.3+; older releases do not quote the `system` column.

## Declaring what can be granted

In your plugin's `bootstrap.php`:

```php-inline
use Naf\Rbac\Definition\PermissionDefinition;
use Naf\Rbac\Definition\RoleDefinition;

use function Naf\Rbac\permissions;
use function Naf\Rbac\roles;

permissions()->add(
    new PermissionDefinition('users.view', 'See users', '', 'Users', 10),
    new PermissionDefinition('users.invite', 'Invite users', '', 'Users', 20),
);
roles()->add(new RoleDefinition(
    'admin',
    'Administrator',
    'Runs this installation.',
    ['rbac.manage', 'users.view', 'users.invite'],
));
```

A declared permission is only *offerable*. It never grants itself to an existing role, so
installing a package cannot widen anybody's access.

## Integrate identity grants { #answering-with-it }

Your user model already implements `Naf\Auth\Identity\UserInterface`. Point its two grant
methods here and everything downstream — `auth()->can()`, `requirePermission()` — works
unchanged:

```php-inline
public function getRoles(): iterable
{
    return rbac()->rolesOf((int) $this->getId());
}

public function getPermissions(): iterable
{
    return rbac()->permissionsOf((int) $this->getId());
}
```

Both are read once per request and cached. Call `rbac()->forget()` after a change that a
later part of the same request will read back.

## Privilege policy { #the-rules }

`PrivilegePolicy` enforces the following administration rules:

1. Administration requires `rbac.manage`.
2. You can grant only permissions you hold. A role used to administer all permissions must
   therefore hold all permissions it may grant.
3. You cannot manage an account holding permissions you lack. Removing its roles first does
   not bypass the grant restriction.
4. The last role carrying `rbac.manage` cannot be emptied or deleted.
5. Changing your own roles also requires `rbac.manage.own`. Grant and lockout restrictions
   still apply; this permission does not allow self-escalation.

Which permission counts for rules 2 and 4 is `rbac:lockout_permission`, so a host may call its
top role whatever it likes and may have several that qualify.

Every denial throws `PrivilegedActionDenied` with a stable `reason` for logs and tests, and a
message for the person who tried.

## Scoped grants { #places }

A grant is a person, a role, and where it applies:

```php-inline
use Naf\Rbac\Scope;

$rbac->assignments->assign(7, [$adminId]);                                 // everywhere
$rbac->assignments->assign(7, [$maintainerId], Scope::allOf('project'));   // on every board
$rbac->assignments->assign(7, [$memberId], Scope::of('project', 5));       // on board 5
```

Asking is the same shape:

```php-inline
$rbac->allows(7, 'board.settings', Scope::of('project', 5));
```

Three spellings reach a place — everywhere, every instance of its kind, and that instance —
and `Scope::covers()` is the only thing that decides which.

An installation-wide grant covers every board. Use distinct permission names when global
administration and board-specific access must be separate capabilities.

A role says where it may be handed out at all, so an installation-wide role cannot be granted
on one board and a board role cannot be granted installation-wide:

```php-inline
new RoleDefinition('admin', 'Administrator', permissions: [...]);
new RoleDefinition('maintainer', 'Maintainer', permissions: [...], scopeType: 'project');
```

Editing a role is deliberately **not** scoped. A role is one object held in many places, so
changing what it carries reaches all of them — that is authority over the installation, not
over a board, and the policy asks for it accordingly.

## Register a scope source { #adding-a-kind-of-place }

The package knows a grant can attach to something, and nothing about what. A host registers
one source per kind, and every screen offers it from then on:

```php-inline
use Naf\Rbac\Contracts\ScopeSourceInterface;

final class Boards implements ScopeSourceInterface
{
    public function type(): string   { return 'project'; }
    public function label(): string  { return 'Boards'; }

    /** @return array<string,string> */
    public function instances(): array
    {
        return $this->repository->namesById();   // 7 => 'Nafinity'
    }
}

roles()->scope(new Boards($repository));
```

Teams, tenants, single tickets: another registration, no change in here. The type is a string
the host chooses, and `Scope::of('team', 'design')` works the moment something answers for
`team`.

`instances()` is called while a screen renders, so it may return only what the person granting
is allowed to see. An empty list hides the kind.

## Synchronize declared roles { #keeping-declarations-and-stored-roles-honest }

Synchronization preserves changes made to stored roles. New declarations do not overwrite
an administrator's customized grants automatically.

`rbac:sync` reports differences between stored roles and their current declarations,
including newly declared permissions:

```text
 6 declared role(s); nothing to add
 24 permission(s) declared across 6 group(s).
   owner is missing delete, export
   manager is missing export
 The roles above no longer carry everything their packages declare. …
```

Review reported differences and grant permissions through the role editor. To restore all
declared roles to their package definitions, run `rbac:sync --reapply`; this discards local
changes to those roles.

Only declared roles are compared, and each only against its own declaration. A permission no
role carries at all is ordinary, because packages ship permissions meant for roles an
installation builds itself.

## Administration fragments { #the-screens }

The administration views are fragments intended for the host's settings layout:

```html+php
<?= partial('rbac/roles', ['return' => '/admin/settings']) ?>
<?= partial('rbac/grants', ['user' => 12, 'name' => 'Alice', 'return' => '/admin/users/12']) ?>
```

`rbac/roles` edits what roles carry. `rbac/grants` edits what one person holds and where —
every place in one form, submitted at once, because a person's access is one decision and not
a series of them.

The host supplies the account being managed. RBAC does not list, create or deactivate accounts.

`src/Resources/public/assets/rbac.css` styles both through custom properties with neutral
defaults, so mapping them to a host's design is one block:

```css
.rbac-roles, .rbac-grants { --rbac-line: var(--line); --rbac-accent: var(--accent); }
```

Set `rbac:path` to `null` to register no endpoints and drive the services from screens of your
own.

## Grant change events { #telling-a-host-what-moved }

A grant change is dispatched as an event, so a host that keeps a history can record it:

```php-inline
use Naf\Rbac\Events\GrantsChanged;

event()->listen(GrantsChanged::class, function (GrantsChanged $moved): void {
    // actorId, targetId, scope, before, after
});
```

One event is dispatched for each grant change. Record audit history in an application listener
when the product requires it.

## Application responsibilities { #what-this-does-not-do }

**Users.** Who exists, inviting them, deactivating them: that is the host's, and this package
only says what they may do.

**Permission definitions in the database.** Permissions come from code. One that an
administrator typed into a form grants nothing, because nothing checks it — a row that looks
like power and is not. Roles are what an installation composes freely, from the vocabulary its
packages declare.
