# PHP code style

NAF packages use [PER Coding Style 3.0](https://github.com/php-fig/per-coding-style/blob/3.0.0/spec.md),
the [successor to PSR-12](https://www.php-fig.org/per/coding-style/meta/), with the same
readability rules as Nafinity. Keep syntax compatible with the package's minimum PHP version.
Existing packages adopt the rules on their own RC branches; this document does not claim
that every existing file already conforms.

## Keep code easy to follow

- Use four spaces, one statement per line and one import per statement. Sort imports by
  class, function and constant, alphabetically within each group.
- Separate validation, preparation, I/O and result handling with blank lines. Keep a value
  and the condition that checks it together. Do not insert a blank line after every statement.
- Align `=` and `=>` within related local groups. Separate unrelated values instead of
  stretching alignment across a whole method.
- Prefer descriptive local names: `$statement`, `$configuration`, `$accountIdentifier`
  and `$exception`. Preserve public parameter names because callers may use named arguments.
- Give intermediate values a name when that exposes a decision or removes nesting.
  A simple expression does not need a new helper, class, interface or configuration object.
- Use early returns for rejection paths when they make the successful path clearer.
  Preserve evaluation order, short-circuit behavior and exceptions.
- Format long SQL as readable SQL blocks, with bound values kept separate. Do not change
  the query, its parameter order or transaction boundaries during formatting.
- Keep PHPDoc for information native types cannot express: array shapes, list elements,
  callback signatures, lifecycle guarantees and reasons for protocol/security checks.
  Remove comments that merely repeat a type or a method name when reviewing that code.
- Keep `try` / `catch` / `finally` close to the resources or transactions they protect.
  Shorter code must still release results, close connections and roll back correctly.
- Review mixed PHP/HTML templates manually. Preserve escaping and rendered whitespace,
  especially inside form values. A formatter does not verify HTML layout.

The formatter uses `@PER-CS3x0`, short arrays, spaced casts/concatenation, ordered imports,
local assignment alignment and blank lines before `return` and `try`. Like Nafinity, it
allows empty method bodies on separate lines by disabling the `single_line_empty_body`
fixer. Logical grouping, naming and SQL layout remain review work.

## Adopt the formatter in a package

Copy [the configuration template](tools/php-cs-fixer.dist.php) to the package root as
`.php-cs-fixer.dist.php`. Its finder covers PHP and PHTML, excluding vendor directories
and hidden caches. Add package-specific generated/runtime directories to its exclusions;
review the file list before applying it. The template is copied so standalone clones do
not require a sibling documentation checkout.

Install the development tool in that package:

```sh
composer require --dev friendsofphp/php-cs-fixer:3.95.25
```

Add these entries to the existing Composer `scripts` object:

```json
{
  "style:check": "@php vendor/bin/php-cs-fixer fix --dry-run --diff",
  "style:fix": "@php vendor/bin/php-cs-fixer fix"
}
```

Prefer the package's minimum PHP runtime when resolving development dependencies and
running the formatter. For PHP 8.3 libraries, a development `config.platform.php` of
`8.3.0` prevents dependencies from silently requiring a newer PHP. Respect an existing
package's platform configuration and lock-file policy. Formatter dependencies belong in
`require-dev`; applications consuming the library do not install them.

Run `composer style:fix`, review the full diff, then run `composer style:check`, the
package's declared tests/analysis and `composer validate --strict`. Add the style check to
the package's CI when adopting it. Keep mechanical formatting separate from behavior fixes
so each change can be reviewed. New control-flow simplifications need relevant regression
coverage. Follow the [normal contribution workflow](AGENT_WORKFLOW.md) for commits and PRs.

The [September 2026 plugin review](reviews/plugin-readability-2026-09-15.md) records the
initial inventory and specific places where manual readability work is useful.
