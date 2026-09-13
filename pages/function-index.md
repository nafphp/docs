---
title: Function index
---

# Function index

Generated from the installed releases listed below. Regenerate this snapshot after a
release; function signatures and namespaces are read through PHP reflection.
Functions marked `@internal` are excluded. Import helpers with `use function` in each
PHP file, including templates. See [Dependency Injection](dependency-injection.md)
for services exposed through these helpers.

<div class="function-reference" markdown="1">

## naf/framework

Version **v0.2.3** · [Core](first-app.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>abort(int $statusCode = 404, string $message = &#x27;&#x27;): never</code> | `Naf` |
| <code>app(): Naf\Core\App</code> | `Naf` |
| <code>config(?string $key = null, mixed $default = null): mixed</code> | `Naf` |
| <code>env(): string</code> | `Naf` |
| <code>event(): Naf\Core\EventManager</code> | `Naf` |
| <code>guard(): Naf\Support\Guard</code> | `Naf` |
| <code>json(mixed $data, int $status = 200, array $headers = []): Psr\Http\Message\ResponseInterface</code> | `Naf` |
| <code>log(): Psr\Log\LoggerInterface</code> | `Naf` |
| <code>param(): Naf\Support\RequestParameter</code> | `Naf` |
| <code>plugin(?string $name = null): Naf\Support\Plugin&#124;array</code> | `Naf` |
| <code>redirect(string $url, int $status = 302): Psr\Http\Message\ResponseInterface</code> | `Naf` |
| <code>refresh(): Psr\Http\Message\ResponseInterface</code> | `Naf` |
| <code>request(): Psr\Http\Message\ServerRequestInterface&#124;Psr\Http\Message\RequestInterface</code> | `Naf` |
| <code>response(mixed $content = &#x27;&#x27;, int $status = 200, array $headers = []): Psr\Http\Message\ResponseInterface</code> | `Naf` |
| <code>route(?string $name = null, array $params = []): Naf\Core\Route&#124;string</code> | `Naf` |

## naf/auth

Version **v0.2.1** · [Authentication and permissions](auth.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>auth(): Naf\Auth\Auth</code> | `Naf\Auth` |

## naf/cli

Version **v0.2.1** · [Console commands](console.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>command(): Naf\CLI\Support\CommandRegistry</code> | `Naf\CLI` |

## naf/client

Version **v0.2.1** · [HTTP client](http-client.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>client(): Naf\Client\Core\Client</code> | `Naf\Client` |

## naf/database

Version **v0.2.1** · [Database](database.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>database(): ?PDO</code> | `Naf\Database` |

## naf/form

Version **v0.2.2** · [Forms and validation](forms.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>csrf(): Naf\Form\Support\Csrf</code> | `Naf\Form` |
| <code>error($field, Naf\Form\Core\Validator $validator): ?string</code> | `Naf\Form` |
| <code>error_class($field, Naf\Form\Core\Validator $validator): string</code> | `Naf\Form` |
| <code>has_error($field, Naf\Form\Core\Validator $validator): bool</code> | `Naf\Form` |
| <code>is_post(): bool</code> | `Naf\Form` |
| <code>memory(string $key, mixed $default = null): ?string</code> | `Naf\Form` |
| <code>memory_checked(string $key, mixed $value = &#x27;on&#x27;): string</code> | `Naf\Form` |
| <code>memory_selected(string $key, mixed $expectedValue): string</code> | `Naf\Form` |
| <code>validator(): Naf\Form\Core\Validator</code> | `Naf\Form` |

## naf/i18n

Version **v0.2.1** · [Translations](translations.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>lang(): ?string</code> | `Naf\I18n` |
| <code>t(string $key, array $params = []): string</code> | `Naf\I18n` |
| <code>translator(): Naf\I18n\Core\Translator</code> | `Naf\I18n` |

## naf/mail

Version **v0.2.1** · [Sending mail](mail.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>mail(): Naf\Mail\Models\Mail</code> | `Naf\Mail` |
| <code>mailer(): Naf\Mail\Core\Mailer</code> | `Naf\Mail` |

## naf/mcp

Version **v0.2.2** · [MCP tools](mcp.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>tokens(): Naf\MCP\Store\TokenStoreInterface</code> | `Naf\MCP` |
| <code>tool(): Naf\MCP\Support\ToolRegistry</code> | `Naf\MCP` |

## naf/oauth-client

Version **v0.2.2** · [Signing in with a provider](oauth-client.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>oauth(string $provider): Naf\OAuth\Client\Core\Flow</code> | `Naf\OAuth\Client` |
| <code>oauth_button(string $provider, ?string $label = null, ?string $next = null): string</code> | `Naf\OAuth\Client` |
| <code>oauth_token(string $provider): ?Naf\OAuth\Client\Token\ProviderToken</code> | `Naf\OAuth\Client` |

## naf/oauth-server

Version **v0.2.2** · [Being the provider](oauth-server.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>token(): Naf\OAuth\Server\Core\TokenContext</code> | `Naf\OAuth\Server` |

## naf/orm

Version **v0.2.1** · [ORM and repositories](orm.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>em(): Naf\ORM\Core\EntityManager</code> | `Naf\ORM` |
| <code>repo(string $repository): Naf\ORM\Repository\AbstractRepository</code> | `Naf\ORM` |

## naf/queue

Version **v0.2.2** · [Queues and workers](queues.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>queue(?string $channel = null): Naf\Queue\Core\Queue</code> | `Naf\Queue` |

## naf/schedule

Version **v0.2.2** · [Scheduled jobs](scheduling.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>scheduler(): Naf\Schedule\Core\Scheduler</code> | `Naf\Schedule` |

## naf/session

Version **v0.2.1** · [Sessions](sessions.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>session(): Naf\Session\Core\Session</code> | `Naf\Session` |

## naf/view

Version **v0.2.1** · [Views and templates](views.md)

| Signature | Namespace to import from |
| --- | --- |
| <code>asset(): Naf\View\Core\Asset</code> | `Naf\View` |
| <code>render(string $template, array $vars = []): Psr\Http\Message\ResponseInterface</code> | `Naf\View` |
| <code>s(array&#124;string&#124;null $value): array&#124;string&#124;null</code> | `Naf\View` |
| <code>view(string $tpl, array $vars = []): string</code> | `Naf\View` |

</div>

*48 public functions across 16 packages.*
