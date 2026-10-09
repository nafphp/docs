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

Version **v0.2.8** · [Core concepts](lifecycle.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>abort(int $statusCode = 404, string $message = &#x27;&#x27;): never</code> | `Naf` | [Behavior](errors.md#abort-a-request) |
| <code>app(): Naf\Core\App</code> | `Naf` | [Behavior](lifecycle.md) |
| <code>config(?string $key = null, mixed $default = null): mixed</code> | `Naf` | [Behavior](configuration.md#read-configuration) |
| <code>env(): string</code> | `Naf` | [Behavior](configuration.md#application-environment) |
| <code>event(): Naf\Core\EventManager</code> | `Naf` | [Behavior](events.md) |
| <code>guard(): Naf\Support\Guard</code> | `Naf` | [Behavior](guard.md) |
| <code>json(mixed $data, int $status = 200, array $headers = []): Psr\Http\Message\ResponseInterface</code> | `Naf` | [Behavior](request-response.md#responses) |
| <code>log(): Psr\Log\LoggerInterface</code> | `Naf` | [Behavior](troubleshooting.md#logging) |
| <code>param(): Naf\Support\RequestParameter</code> | `Naf` | [Behavior](request-response.md#combined-request-parameters) |
| <code>plugin(?string $name = null): Naf\Support\Plugin&#124;array</code> | `Naf` | [Behavior](plugins.md#accessing-plugin-metadata) |
| <code>redirect(string $url, int $status = 302): Psr\Http\Message\ResponseInterface</code> | `Naf` | [Behavior](request-response.md#redirect-and-refresh) |
| <code>refresh(): Psr\Http\Message\ResponseInterface</code> | `Naf` | [Behavior](request-response.md#redirect-and-refresh) |
| <code>request(): Psr\Http\Message\ServerRequestInterface&#124;Psr\Http\Message\RequestInterface</code> | `Naf` | [Behavior](request-response.md#read-the-request) |
| <code>response(mixed $content = &#x27;&#x27;, int $status = 200, array $headers = []): Psr\Http\Message\ResponseInterface</code> | `Naf` | [Behavior](request-response.md#responses) |
| <code>route(?string $name = null, array $params = []): Naf\Core\Route&#124;string</code> | `Naf` | [Behavior](routing.md) |

## naf/auth

Version **v0.2.2** · [Authentication and permissions](auth.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>auth(): Naf\Auth\Auth</code> | `Naf\Auth` | [Behavior](auth.md) |

## naf/board

Version **v0.1.5** · [Nafinity](built-with/nafinity.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>choice(array $arguments): string</code> | `Naf\Board` | [Behavior](built-with/nafinity.md) |
| <code>extensions(): Naf\Board\ExtensionRegistry</code> | `Naf\Board` | [Behavior](built-with/nafinity.md) |
| <code>field(array $arguments): string</code> | `Naf\Board` | [Behavior](built-with/nafinity.md) |
| <code>partial(string $template, array $data = []): string</code> | `Naf\Board` | [Behavior](built-with/nafinity.md) |
| <code>settings(): Naf\Board\Settings</code> | `Naf\Board` | [Behavior](built-with/nafinity.md) |
| <code>slot(string $slot, Naf\Board\Support\SlotContextInterface&#124;Naf\Board\Support\UiContext $context, array $extra = []): string</code> | `Naf\Board` | [Behavior](built-with/nafinity.md) |
| <code>template(string $template): string</code> | `Naf\Board` | [Behavior](built-with/nafinity.md) |

## naf/cli

Version **v0.2.3** · [Console commands](console.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>command(): Naf\CLI\Support\CommandRegistry</code> | `Naf\CLI` | [Behavior](console.md) |

## naf/client

Version **v0.2.2** · [HTTP client](http-client.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>client(): Naf\Client\Core\Client</code> | `Naf\Client` | [Behavior](http-client.md) |

## naf/database

Version **v0.2.4** · [Database](database.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>database(): ?PDO</code> | `Naf\Database` | [Behavior](database.md) |

## naf/flow

Version **v0.1.0** · [Flow](flow.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>page(string $template, array $vars = [], ?string $fragment = null): Psr\Http\Message\ResponseInterface</code> | `Naf\Flow` | [Behavior](flow.md) |

## naf/form

Version **v0.2.3** · [Forms and validation](forms.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>csrf(): Naf\Form\Support\Csrf</code> | `Naf\Form` | [Behavior](forms.md) |
| <code>error($field, Naf\Form\Core\Validator $validator): ?string</code> | `Naf\Form` | [Behavior](forms.md) |
| <code>error_class($field, Naf\Form\Core\Validator $validator): string</code> | `Naf\Form` | [Behavior](forms.md) |
| <code>has_error($field, Naf\Form\Core\Validator $validator): bool</code> | `Naf\Form` | [Behavior](forms.md) |
| <code>is_post(): bool</code> | `Naf\Form` | [Behavior](forms.md) |
| <code>memory(string $key, mixed $default = null): ?string</code> | `Naf\Form` | [Behavior](forms.md) |
| <code>memory_checked(string $key, mixed $value = &#x27;on&#x27;): string</code> | `Naf\Form` | [Behavior](forms.md) |
| <code>memory_selected(string $key, mixed $expectedValue): string</code> | `Naf\Form` | [Behavior](forms.md) |
| <code>validator(): Naf\Form\Core\Validator</code> | `Naf\Form` | [Behavior](forms.md) |

## naf/i18n

Version **v0.2.2** · [Translations](translations.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>lang(): ?string</code> | `Naf\I18n` | [Behavior](translations.md) |
| <code>t(string $key, array $params = []): string</code> | `Naf\I18n` | [Behavior](translations.md) |
| <code>translation_paths(): Naf\I18n\Support\TranslationPathRegistry</code> | `Naf\I18n` | [Behavior](translations.md) |
| <code>translator(): Naf\I18n\Core\Translator</code> | `Naf\I18n` | [Behavior](translations.md) |

## naf/mail

Version **v0.2.2** · [Sending mail](mail.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>mail(): Naf\Mail\Models\Mail</code> | `Naf\Mail` | [Behavior](mail.md) |
| <code>mailer(?Naf\Mail\Core\TransportInterface $transport = null): Naf\Mail\Core\Mailer</code> | `Naf\Mail` | [Behavior](mail.md) |

## naf/mcp

Version **v0.2.4** · [MCP tools](mcp.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>tokens(): Naf\MCP\Store\TokenStoreInterface</code> | `Naf\MCP` | [Behavior](mcp.md) |
| <code>tool(): Naf\MCP\Support\ToolRegistry</code> | `Naf\MCP` | [Behavior](mcp.md) |

## naf/oauth-client

Version **v0.2.4** · [OAuth client](oauth-client.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>oauth(string $provider): Naf\OAuth\Client\Core\Flow</code> | `Naf\OAuth\Client` | [Behavior](oauth-client.md) |
| <code>oauth_button(string $provider, ?string $label = null, ?string $next = null): string</code> | `Naf\OAuth\Client` | [Behavior](oauth-client.md) |
| <code>oauth_token(string $provider): ?Naf\OAuth\Client\Token\ProviderToken</code> | `Naf\OAuth\Client` | [Behavior](oauth-client.md) |

## naf/oauth-server

Version **v0.2.3** · [OAuth authorization server](oauth-server.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>token(): Naf\OAuth\Server\Core\TokenContext</code> | `Naf\OAuth\Server` | [Behavior](oauth-server.md) |

## naf/orm

Version **v0.2.2** · [ORM and repositories](orm.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>em(): Naf\ORM\Core\EntityManager</code> | `Naf\ORM` | [Behavior](orm.md) |
| <code>repo(string $repository): Naf\ORM\Repository\AbstractRepository</code> | `Naf\ORM` | [Behavior](orm.md) |

## naf/queue

Version **v0.2.4** · [Queues and workers](queues.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>queue(?string $channel = null): Naf\Queue\Core\Queue</code> | `Naf\Queue` | [Behavior](queues.md) |

## naf/rbac

Version **v0.1.3** · [Roles and permissions](rbac.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>permissions(): Naf\Rbac\Registry\PermissionRegistry</code> | `Naf\Rbac` | [Behavior](rbac.md) |
| <code>rbac(): Naf\Rbac\Rbac</code> | `Naf\Rbac` | [Behavior](rbac.md) |
| <code>roles(): Naf\Rbac\Registry\RoleRegistry</code> | `Naf\Rbac` | [Behavior](rbac.md) |

## naf/schedule

Version **v0.2.4** · [Scheduled jobs](scheduling.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>scheduler(): Naf\Schedule\Core\Scheduler</code> | `Naf\Schedule` | [Behavior](scheduling.md) |

## naf/session

Version **v0.2.3** · [Sessions](sessions.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>session(): Naf\Session\Core\Session</code> | `Naf\Session` | [Behavior](sessions.md) |

## naf/storage

Version **v0.1.0** · [File storage](file-storage.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>storage(?string $name = null): Naf\Storage\Storage</code> | `Naf\Storage` | [Behavior](file-storage.md) |

## naf/view

Version **v0.2.2** · [Views and templates](views.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>asset(): Naf\View\Core\Asset</code> | `Naf\View` | [Behavior](views.md) |
| <code>render(string $template, array $vars = []): Psr\Http\Message\ResponseInterface</code> | `Naf\View` | [Behavior](views.md) |
| <code>s(array&#124;string&#124;null $value): array&#124;string&#124;null</code> | `Naf\View` | [Behavior](views.md) |
| <code>view(string $tpl, array $vars = []): string</code> | `Naf\View` | [Behavior](views.md) |

## naf/websocket

Version **v0.1.1** · [WebSocket notifications](websocket.md)

| Signature | Namespace to import from | Guide |
| --- | --- | --- |
| <code>live(): bool</code> | `Naf\Websocket` | [Behavior](websocket.md) |
| <code>publisher(): Naf\Websocket\Publisher</code> | `Naf\Websocket` | [Behavior](websocket.md) |
| <code>token(string $subject, array $channels): string</code> | `Naf\Websocket` | [Behavior](websocket.md) |

</div>

*64 public functions across 21 packages.*
