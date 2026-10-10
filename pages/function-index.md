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

Version **v0.2.8** · [Fundamentals](lifecycle.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>abort(int $statusCode = 404, string $message = &#x27;&#x27;): never</code> | Abort request with status code and message | `Naf` | [Abort a request](errors.md#abort-a-request) |
| <code>app(): Naf\Core\App</code> | Get the application instance | `Naf` | [Application lifecycle](lifecycle.md) |
| <code>config(?string $key = null, mixed $default = null): mixed</code> | Get configuration value by key | `Naf` | [Read configuration](configuration.md#read-configuration) |
| <code>env(): string</code> | Get the current environment | `Naf` | [Application environment](configuration.md#application-environment) |
| <code>event(): Naf\Core\EventManager</code> | Get the event dispatcher instance | `Naf` | [Events](events.md) |
| <code>guard(): Naf\Support\Guard</code> | Get the guard instance | `Naf` | [Guard rules](guard.md) |
| <code>json(mixed $data, int $status = 200, array $headers = []): Psr\Http\Message\ResponseInterface</code> | Create JSON response | `Naf` | [Responses](request-response.md#responses) |
| <code>log(): Psr\Log\LoggerInterface</code> | Get logger instance | `Naf` | [Logging](troubleshooting.md#logging) |
| <code>param(): Naf\Support\RequestParameter</code> | Get request parameter handler instance | `Naf` | [Combined request parameters](request-response.md#combined-request-parameters) |
| <code>plugin(?string $name = null): Naf\Support\Plugin&#124;array</code> | Get a specific plugin, or all when no argument is given | `Naf` | [Plugin metadata](plugins.md#accessing-plugin-metadata) |
| <code>redirect(string $url, int $status = 302): Psr\Http\Message\ResponseInterface</code> | Create a redirect response | `Naf` | [Redirect and refresh](request-response.md#redirect-and-refresh) |
| <code>refresh(): Psr\Http\Message\ResponseInterface</code> | Create a refresh response redirecting to the current path | `Naf` | [Redirect and refresh](request-response.md#redirect-and-refresh) |
| <code>request(): Psr\Http\Message\ServerRequestInterface&#124;Psr\Http\Message\RequestInterface</code> | Get current request instance | `Naf` | [Read the request](request-response.md#read-the-request) |
| <code>response(mixed $content = &#x27;&#x27;, int $status = 200, array $headers = []): Psr\Http\Message\ResponseInterface</code> | Create a new response | `Naf` | [Responses](request-response.md#responses) |
| <code>route(?string $name = null, array $params = []): Naf\Core\Route&#124;string</code> | Get the route instance or generate URL for a named route | `Naf` | [Routing](routing.md) |

## naf/auth

Version **v0.2.2** · [Authentication and permissions](auth.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>auth(): Naf\Auth\Auth</code> | The shared manager registered by the plugin bootstrap | `Naf\Auth` | [Authentication and permissions](auth.md) |

## naf/board

Version **v0.1.5** · [Nafinity](built-with/nafinity.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>choice(array $arguments): string</code> | Render the reusable select | `Naf\Board` | [Nafinity](built-with/nafinity.md) |
| <code>extensions(): Naf\Board\ExtensionRegistry</code> | The container-bound extension registry | `Naf\Board` | [Nafinity](built-with/nafinity.md) |
| <code>field(array $arguments): string</code> | Render a labelled form field | `Naf\Board` | [Nafinity](built-with/nafinity.md) |
| <code>partial(string $template, array $data = []): string</code> | Render a mapped partial through the application's page renderer | `Naf\Board` | [Nafinity](built-with/nafinity.md) |
| <code>settings(): Naf\Board\Settings</code> | Declared settings for the signed-in person | `Naf\Board` | [Nafinity](built-with/nafinity.md) |
| <code>slot(string $slot, Naf\Board\Support\SlotContextInterface&#124;Naf\Board\Support\UiContext $context, array $extra = []): string</code> | Render everything contributed to a named slot | `Naf\Board` | [Nafinity](built-with/nafinity.md) |
| <code>template(string $template): string</code> | Resolve a logical view name through the registered view mappings | `Naf\Board` | [Nafinity](built-with/nafinity.md) |

## naf/cli

Version **v0.2.3** · [Console commands](console.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>command(): Naf\CLI\Support\CommandRegistry</code> | — | `Naf\CLI` | [Console commands](console.md) |

## naf/client

Version **v0.2.2** · [HTTP client](http-client.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>client(): Naf\Client\Core\Client</code> | — | `Naf\Client` | [HTTP client](http-client.md) |

## naf/database

Version **v0.2.4** · [Database](database.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>database(): ?PDO</code> | — | `Naf\Database` | [Database](database.md) |

## naf/flow

Version **v0.1.0** · [Flow](flow.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>page(string $template, array $vars = [], ?string $fragment = null): Psr\Http\Message\ResponseInterface</code> | The host chooses both templates; clients never supply a template path | `Naf\Flow` | [Flow](flow.md) |

## naf/form

Version **v0.2.3** · [Forms and validation](forms.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>csrf(): Naf\Form\Support\Csrf</code> | — | `Naf\Form` | [Forms and validation](forms.md) |
| <code>error($field, Naf\Form\Core\Validator $validator): ?string</code> | — | `Naf\Form` | [Forms and validation](forms.md) |
| <code>error_class($field, Naf\Form\Core\Validator $validator): string</code> | — | `Naf\Form` | [Forms and validation](forms.md) |
| <code>has_error($field, Naf\Form\Core\Validator $validator): bool</code> | — | `Naf\Form` | [Forms and validation](forms.md) |
| <code>is_post(): bool</code> | — | `Naf\Form` | [Forms and validation](forms.md) |
| <code>memory(string $key, mixed $default = null): ?string</code> | — | `Naf\Form` | [Forms and validation](forms.md) |
| <code>memory_checked(string $key, mixed $value = &#x27;on&#x27;): string</code> | — | `Naf\Form` | [Forms and validation](forms.md) |
| <code>memory_selected(string $key, mixed $expectedValue): string</code> | — | `Naf\Form` | [Forms and validation](forms.md) |
| <code>validator(): Naf\Form\Core\Validator</code> | — | `Naf\Form` | [Forms and validation](forms.md) |

## naf/i18n

Version **v0.2.2** · [Translations](translations.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>lang(): ?string</code> | — | `Naf\I18n` | [Translations](translations.md) |
| <code>t(string $key, array $params = []): string</code> | — | `Naf\I18n` | [Translations](translations.md) |
| <code>translation_paths(): Naf\I18n\Support\TranslationPathRegistry</code> | The registry of directories translations are read from | `Naf\I18n` | [Translations](translations.md) |
| <code>translator(): Naf\I18n\Core\Translator</code> | — | `Naf\I18n` | [Translations](translations.md) |

## naf/mail

Version **v0.2.2** · [Sending mail](mail.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>mail(): Naf\Mail\Models\Mail</code> | — | `Naf\Mail` | [Sending mail](mail.md) |
| <code>mailer(?Naf\Mail\Core\TransportInterface $transport = null): Naf\Mail\Core\Mailer</code> | Use a separate mailer for an explicit transport, or retrieve the shared mailer | `Naf\Mail` | [Sending mail](mail.md) |

## naf/mcp

Version **v0.2.6** · [MCP tools](mcp.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>tokens(): Naf\MCP\Store\TokenStoreInterface</code> | — | `Naf\MCP` | [MCP tools](mcp.md) |
| <code>tool(): Naf\MCP\Support\ToolRegistry</code> | — | `Naf\MCP` | [MCP tools](mcp.md) |

## naf/oauth-client

Version **v0.2.4** · [OAuth client](oauth-client.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>oauth(string $provider): Naf\OAuth\Client\Core\Flow</code> | The configured external provider of that name, registered by the plugin bootstrap | `Naf\OAuth\Client` | [OAuth client](oauth-client.md) |
| <code>oauth_button(string $provider, ?string $label = null, ?string $next = null): string</code> | A link that starts a login with this provider | `Naf\OAuth\Client` | [OAuth client](oauth-client.md) |
| <code>oauth_token(string $provider): ?Naf\OAuth\Client\Token\ProviderToken</code> | A provider token for the signed-in account that can be used right now | `Naf\OAuth\Client` | [OAuth client](oauth-client.md) |

## naf/oauth-server

Version **v0.2.5** · [OAuth authorization server](oauth-server.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>token(): Naf\OAuth\Server\Core\TokenContext</code> | What the bearer token on this request allows | `Naf\OAuth\Server` | [OAuth authorization server](oauth-server.md) |

## naf/orm

Version **v0.2.2** · [ORM and repositories](orm.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>em(): Naf\ORM\Core\EntityManager</code> | — | `Naf\ORM` | [ORM and repositories](orm.md) |
| <code>repo(string $repository): Naf\ORM\Repository\AbstractRepository</code> | — | `Naf\ORM` | [ORM and repositories](orm.md) |

## naf/queue

Version **v0.2.4** · [Queues and workers](queues.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>queue(?string $channel = null): Naf\Queue\Core\Queue</code> | — | `Naf\Queue` | [Queues and workers](queues.md) |

## naf/rbac

Version **v0.1.3** · [Roles and permissions](rbac.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>permissions(): Naf\Rbac\Registry\PermissionRegistry</code> | What this installation knows how to grant | `Naf\Rbac` | [Roles and permissions](rbac.md) |
| <code>rbac(): Naf\Rbac\Rbac</code> | The roles and permissions themselves | `Naf\Rbac` | [Roles and permissions](rbac.md) |
| <code>roles(): Naf\Rbac\Registry\RoleRegistry</code> | The roles a host ships with, and the kinds of place they may be granted in | `Naf\Rbac` | [Roles and permissions](rbac.md) |

## naf/schedule

Version **v0.2.4** · [Scheduled jobs](scheduling.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>scheduler(): Naf\Schedule\Core\Scheduler</code> | — | `Naf\Schedule` | [Scheduled jobs](scheduling.md) |

## naf/session

Version **v0.2.3** · [Sessions](sessions.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>session(): Naf\Session\Core\Session</code> | — | `Naf\Session` | [Sessions](sessions.md) |

## naf/storage

Version **v0.1.0** · [File storage](file-storage.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>storage(?string $name = null): Naf\Storage\Storage</code> | Retrieve the configured default disk or a named disk | `Naf\Storage` | [File storage](file-storage.md) |

## naf/view

Version **v0.2.2** · [Views and templates](views.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>asset(): Naf\View\Core\Asset</code> | — | `Naf\View` | [Views and templates](views.md) |
| <code>render(string $template, array $vars = []): Psr\Http\Message\ResponseInterface</code> | — | `Naf\View` | [Views and templates](views.md) |
| <code>s(array&#124;string&#124;null $value): array&#124;string&#124;null</code> | — | `Naf\View` | [Views and templates](views.md) |
| <code>view(string $tpl, array $vars = []): string</code> | — | `Naf\View` | [Views and templates](views.md) |

## naf/websocket

Version **v0.1.1** · [WebSocket notifications](websocket.md)

| Signature | Purpose | Namespace to import from | Guide |
| --- | --- | --- | --- |
| <code>live(): bool</code> | Whether an installation has this switched on at all | `Naf\Websocket` | [WebSocket notifications](websocket.md) |
| <code>publisher(): Naf\Websocket\Publisher</code> | How the application says that something changed | `Naf\Websocket` | [WebSocket notifications](websocket.md) |
| <code>token(string $subject, array $channels): string</code> | A token for these channels, for the browser that is being served right now | `Naf\Websocket` | [WebSocket notifications](websocket.md) |

</div>

*64 public functions across 21 packages.*
