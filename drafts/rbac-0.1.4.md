# RBAC 0.1.4 administration controls

Pending the merge of nafphp/rbac PR #4, successful checks of its merge commit, and stable
0.1.4 publication on Packagist. Keep this content outside the live guides until then.

Add the following to "Administration fragments" in `pages/rbac.md`:

> RBAC 0.1.4+ renders role and permission checkboxes as native inputs with switch semantics.
> The disclosure caret indicates whether a role or grant group is open. Keyboard activation,
> checked/disabled state and submitted field names remain native form behavior.
> Reduced-motion preferences disable control, thumb and caret transitions. Forced-color
> mode restores the browser's native checkbox rendering. Hosts can customize the thumb
> color through `--rbac-switch-thumb` alongside the other RBAC custom properties.

The initial editor changes were already merged, but the release audit found that the
reduced-motion selector had lower specificity than the default switch selector. PR #4 fixes
that defect and adds an actual browser regression, including keyboard and forced-color
checks. The regression fails against the previous main stylesheet.

Verification also renders the actual role/grant fragments in an authenticated SQLite host.
The host explicitly installs View, Form and i18n; these remain optional UI dependencies.
