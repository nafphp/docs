---
title: Nafinity accounts and invitations
---

# Nafinity accounts and invitations

With `naf/board` 0.1.6 or newer, invite people into a board, manage authorized accounts and issue one-use password recovery links. Installation roles and board membership remain separate.

## Inviting people and assigning boards

**Invite person** in installation settings and **Invite new person** in a board's
member settings share the same invitation service. Choose an initial board, email and board
role. The default is Member; only a current owner can grant Owner or Manager. Project custom
roles follow the same permission checks as direct membership changes. With email delivery
enabled, the form can send the invitation; otherwise it returns a link to copy and share.
No administrator chooses the recipient's password.

The recipient opens the link, enters a name and their own password, and immediately reaches
the inviting board. The email is bound to the invitation and cannot be changed at registration.
The password follows the same 15-character/72-byte rule as password changes. New invited
accounts receive only the selected board membership, with no installation role or right to
create projects. An invitation does not set `email_verified_at`: administrators may copy links,
so possession alone does not prove delivery to the named mailbox.

Use **Search accounts** in another board's member settings to add that person later. After
two characters, autocomplete finds active accounts by name or email, and selecting a result
fills the email. A complete email also works without JavaScript. Only people allowed to manage
members of that board can use the directory; it returns at most 20 names and email addresses.
Adding existing accounts continues to use the regular membership service and its role checks.
Already existing accounts cannot be recreated through an invitation. If an account is created
after a link was issued, its owner must sign in with that account before joining. Existing active
membership and credentials are preserved.

Links expire after seven days, can be used once and can be revoked under **Pending invitations**.
Inviting the same address to the same board again replaces the previous link. Different boards
can have separate invitations. Acceptance rechecks the inviting person's current membership,
role permissions, the custom role and the board's archive state. Revocation, expiry, loss of
the sponsor's rights, archiving and project deletion prevent registration through that link.
Registration, membership assignment and consuming the token commit together. The database
stores only the SHA-256 token hash; audit events contain no invitation token or email.

The public link and confirmation pages use `Cache-Control: private, no-store` and
`Referrer-Policy: no-referrer`. Creation, searches and acceptance use NAF's persistent rate
limiter; all writes require native CSRF protection. The public URL comes from `app:url`, not
the request's Host header. Email is sent synchronously through NAF's Mailer. A delivery failure
returns 503 and preserves any previous invitation. SMTP and SQL cannot commit atomically:
a delivered link can be unusable if a later event or commit refuses the write.

`M202610100001ProjectInvitations` adds `project_invitations`. The public contract is
`InvitationServiceInterface`; UI entry points call it rather than creating accounts directly.
Installation administrators retain the programmatic `AccountServiceInterface::create()` API
for provisioning. Regression coverage lives in `InvitationTest`, `InvitationOverHttpTest` and
the browser account-search tests.

## Find accounts

The installation's Users card uses a searchable table, ordered by name and id,
with at most 50 accounts per page. Search matches literal name/email substrings;
`%` and `_` are not wildcards. A row opens an account editor in a separate native
dialog. Editors are fetched on demand rather than rendered for every account.
The primary invitation action sits at the top right above the table.

## Manage an account

The editor starts with account details: name, email and active status. It shows
the account source, creation time in UTC and email verification state. Roles and
access appear in a separate collapsed section. Each place has one compact row:
the board label on the left and its directly assigned roles on the right. A pencil
disclosure reveals the existing searchable multiselect; several roles can be held
on the same board. Global, all-board and individual-board grants remain separate.
Changing a selection updates its summary; **Save roles** submits all rows together,
including closed rows, through the native RBAC endpoint and privilege policy.
Grants in unavailable or archived scopes are displayed read-only and preserved.
Your own roles and roles viewed without `rbac.manage` have no edit controls.

Disabling an account preserves
its content, roles and memberships. You cannot disable your own account or the
last active installation administrator.

Reading requires `settings.manage` and `users.view`. Editing also requires
`users.manage`. The current permissions of the target must be contained in the
actor's permissions in every scope the target can reach: editing credentials
must not bypass private board or administrator boundaries. Administrators have
the account capabilities. Password recovery additionally requires the separate
`users.reset_password` permission, so delegating account edits does not
implicitly delegate password recovery.

`POST /settings/users/{user}` accepts `name`, `email`, `active` (0 or 1) and the
editor's opaque `revision`, plus CSRF. Unknown fields are refused. Writes lock
current roles, permissions, grants and affected accounts before reauthorizing.
An outdated revision or unavailable email returns 409 without changing data.
The UI preserves failed edits and asks the person to reopen a stale editor.
Changing name preserves sessions. Changing email or status increases the native
security version, invalidates all prior sessions and pending account recovery
and email-change links; a new email is unverified. Changing your own email asks
you to sign in again. The old address receives the existing security notice.

Externally managed accounts show their source. Their display name and activation
can be edited, but their email and password remain with their sign-in provider.

### Recover a local password

For an active local account, **Create reset link** creates a random one-use link,
valid for 30 minutes. Optionally send it using configured mail; otherwise copy it
and pass it privately to the person. The link uses `app:url`, never the request
Host header. Only its SHA-256 hash is stored. A new link replaces the old one.
Issuing a link leaves the password and sessions intact.

`POST /settings/users/{user}/password-reset` takes the account `revision`, optional
`send_email` (0 or 1), and CSRF. Issuance is limited to 20 attempts per actor/hour
and 3 per target/15 minutes. A mail failure refuses the operation and preserves
the previous link. JSON responses expose the link only to the authorized actor;
plain forms redirect to an authorized, one-time result page.

The recipient opens `GET /password-reset/{token}` and submits a new password with
confirmation and CSRF to the same path. The native password rule requires at
least 15 characters and at most 72 bytes. The page reveals no account identity,
uses `no-store` and `no-referrer`, and never echoes password input. Consumption
checks expiry, account activation, credential version, bound email and the
issuer's current rights again under locks. Revocation of issuer rights makes
outstanding links unusable. A concurrent second consumer receives 410.

Success atomically writes the password, consumes the link, invalidates pending
email changes, increases the security version and queues a security notice.
The recipient signs in normally afterwards; recovery never creates a session.
Invalid and expired links return 410. Consumption is rate limited per token and
peer. Maintenance removes expired rows. Database-backed audit events participate
in the transaction; a failing listener refuses the write. External mail delivery
cannot be rolled back and may contain a link that a later refusal invalidates.

Account audit data records the changed field names, without credential values,
email values or raw recovery tokens.

## Sessions after credential changes

Password and email changes invalidate the account's existing sessions. Sign in
again before submitting another change. With `naf/auth` 0.2.4 or newer, restoring
a revoked session also clears its CSRF token: a form prepared before revocation
can receive HTTP 400 from the CSRF guard. A competing confirmation that already
passed that guard is refused with 401 by the account recheck. Neither response
can apply the email change or consume its code a second time.

With `naf/board` 0.1.9 or newer, remembered sign-ins also take the account lock
through token revalidation, validator rotation and session publication. A
password reset either invalidates the already published session version or
commits first and makes the old remembered credential unusable. Two concurrent
callers cannot both rotate the same validator. Sign-in events still run after
the transaction commits. No new migration or configuration is required.

## Update global roles

Select individual rows or all eligible rows on the current page to reveal the
bulk action bar with its **Update** action. Search and pagination clear the selection. The confirmation
form states the target count and requires explicitly enabling each property;
unselected properties are omitted, and empty strings, false and null remain
values when their field type accepts them. Own-account rows cannot be selected.
The compact selection controls retain native keyboard and screen-reader behavior;
disabled controls show a lock, and the page selector marks partial selection.

The initial properties add or remove one **global role**. These operations merge
with current grants, preserve other roles and every scoped grant, and are
idempotent. Scoped roles remain in the individual editor: board membership has
additional rules and must not be inferred from a global grant operation.
The role choices are restricted to the actor's current authority. Account names,
credentials, account activation and personal preferences are not mass editable.

## Initial HTTP surface and guarantees

`GET /settings/users` returns the bounded table fragment (`users_q`, `users_page`).
`GET /settings/users/{user}` returns a single editor. Both require current login,
`settings.manage` and `users.view`, and successful fragments are not cacheable.
`POST /settings/users/bulk` additionally requires `users.manage`, `rbac.manage`,
CSRF and the privilege policy for every target. Its body contains only explicit
`targets` and a `values` patch (initial keys: `add_role`, `remove_role`). Adding and
removing the same role in one request is refused as ambiguous.

Global role definitions, their permissions and global assignments are locked
before the privilege snapshot is read; selected accounts are checked under locks.
This deliberately serializes global privilege batches. It avoids widening rights
from a stale role definition. Changes dispatch the existing `GrantsChanged` events
inside the batch transaction, so audit listener failures roll back the grants too.
Listeners must keep external side effects out of this transaction.

Regression coverage checks bounded reads, lazy editors, literal searches, CSRF,
unauthorized reads/writes, malformed selection, self protection, privilege reach,
role preservation, idempotency, multiple-property merging, contributed field types
and full rollback after a later property write fails.

## If the result is different

| Symptom | Check |
| --- | --- |
| The reset-link action is unavailable | Check `users.reset_password` separately from account-edit rights; role synchronization preserves existing role definitions. |
| An invitation or reset link is no longer valid | Check expiry, revocation, current sponsor/issuer rights and the target account's current state. |
| An old form returns 400 or 401 after an account change | Sign in again and reload the form; session revocation can also invalidate its CSRF token. |
| An account editor reports a conflict | Reopen it to obtain the latest revision before applying the change. |
| Email delivery fails | Verify the configured transport; the operation preserves the previous invitation/reset link on a delivery failure. |
