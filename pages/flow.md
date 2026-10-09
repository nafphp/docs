---
title: Flow
---

# Flow

Native JavaScript components for server-rendered NAF views. Bind an ordinary class or
object to a container, change its public fields and update the page. Load HTML fragments
or JSON through the host's normal routes. The plugin registers and starts its runtime
automatically through `naf/view`.

## How the pieces connect

Flow connects PHP templates to ordinary JavaScript objects. PHP owns routing, input
validation, authentication and response generation. The browser owns the current page's
interactive state. The following chain uses those responsibilities directly:

1. Composer installs Flow and View. NAF discovers both plugins and boots Flow after View.
2. Flow adds its runtime to `asset()`. The layout renders that collector once, together
   with the application's external module.
3. `Flow.register()` connects a factory to a `flow` container. Flow creates one instance,
   prepares observable fields and refs, then calls `init()` and `mount()`.
4. An action or `flow-model` changes a public field. Synchronous changes are batched;
   bindings and getters update before the component's `update()` hook runs.
5. The hook checks `changes.has()` and calls its scoped client when backend data is needed.
   HTML loads debounce, supersede earlier loads into the same target and stop on disposal.
6. The same PHP route can return its full page or an explicitly selected fragment through
   `Naf\Flow\page()`. JSON endpoints continue to return `Naf\json()` responses.
7. Flow reconciles the target's children, preserving compatible keyed nodes and instances.
   Removed components unmount; new containers mount automatically.

Keep business rules in PHP services. A component needs state and a backend request only
when its own interaction needs them. A store is useful when multiple containers share
state; a standalone counter does not require one.

## Installation

Available as `naf/flow` 0.1.0+. In an existing NAF application:

```bash
composer require naf/flow:^0.1 --with-all-dependencies
```

Requires PHP 8.3+, `naf/framework` 0.2.7+ and `naf/view` 0.2+. Composer installs these
dependencies and NAF discovers the plugin. `--with-all-dependencies` also updates a
framework version held by an older starter lock file. No Node installation or frontend
build is needed in the consuming application. Only the host's `public/` directory is a web root.

With PHP's built-in development server, use the [router file below](#development-server)
so requests for the runtime URL reach NAF too. Configure other web servers to send
requests for nonexistent files to `public/index.php`, as for the application's other routes.

## A counter

Create `public/js/components/Counter.js`:

```javascript
export default class Counter {
    count = 0;

    constructor(props) {
        this.count = props.initial ?? 0;
    }

    get doubled() {
        return this.count * 2;
    }

    increment() {
        this.count++;
    }
}
```

Create `public/js/app.js`:

```javascript
import { Flow } from '/_flow/flow.js';
import Counter from './components/Counter.js';

Flow.register('counter', props => new Counter(props));
```

Register the application module in the host's PHP layout, before rendering its scripts:

```php-inline
use function Naf\View\asset;

asset()->add('/js/app.js', 'module');
```

The layout renders its collected scripts once, through the existing View hook:

```html+php
<?= asset()->render('js') ?>
```

Put the component in a PHP template:

```html
<section flow="counter" flow-props='{"initial":2}'>
    <button type="button" flow-on:click="increment">More</button>
    <output flow-text="count">2</output>
    <output flow-text="doubled">4</output>
</section>
```

There is no manual start call. Flow waits for the document, mounts registered types and
also picks up later registrations and added containers. Repeated `Flow.start()` calls
are harmless when an integration needs an explicit scan.

For server-generated props, escape the complete JSON string as a quoted HTML attribute:

```php-inline
use function Naf\View\s;
?>
<section flow="counter" flow-props="<?= s(json_encode(['initial' => 2], JSON_THROW_ON_ERROR)) ?>">
    <output flow-text="count"></output>
</section>
```

## Component factories: classes and exported functions

`Flow.register(name, factory)` always receives a synchronous factory function. Flow calls
it with `(props, context)` when mounting a matching HTML container. The factory returns
a new object for that container; it can construct an ordinary class or return an object
literal. Classes need no base class.

For a class, wrap its constructor in a factory:

```javascript
Flow.register('counter', props => new Counter(props));
```

The arrow function is registered first. `new Counter(props)` runs when Flow calls that
function during mounting, once for each matching container. If Flow has already started,
registration can immediately mount containers already on the page. Otherwise they mount
when Flow starts after the document is ready. Containers added later receive new instances.

An ES module can instead export the factory itself:

```javascript title="public/js/components/createCounter.js"
export default props => ({
    count: props.initial ?? 0,
    increment() { this.count++; },
});
```

```javascript
import createCounter from './components/createCounter.js';

Flow.register('factory-counter', createCounter);
```

Here `createCounter` is already a function returning a new component object, so pass its
reference. Do not call `createCounter({ initial: 0 })` while registering: that passes the
resulting object instead of a factory. Similarly, passing the class itself as
`Flow.register('counter', Counter)` is unsupported: Flow calls factories as functions,
without adding `new`.

The playground demo uses both techniques deliberately. `Counter`, `PackageSearch` and `GreetingPreview`
are classes wrapped in factories. Its `StoreInspector` and `CounterStage` exports are
factory functions, despite their capitalized import names. In application code, names
such as `createStoreInspector` make that distinction clearer. Both forms have the same
reactivity, bindings, context and lifecycle. The complete example below follows the same
pattern with its `CatalogSearch` class and exported `FilterMirror` factory.

| Call | What you pass | When the object is created | Ownership |
| --- | --- | --- | --- |
| `Flow.register(name, props => new Counter(props))` | Factory constructing a class | On each new mount | One new instance per container |
| `Flow.register(name, createCounter)` | Exported factory function | On each new mount | One new object per container |
| `Flow.mount(root, new Counter(props))` | An already constructed instance | Immediately when `new` is evaluated | That instance belongs to one container |
| `Flow.store(name, new Filters())` | An already constructed shared object | Immediately when `new` is evaluated | One store shared by its consumers |

Repeated scans keep existing component instances. A factory must return a fresh object
for each new container; returning the same preconstructed component for multiple containers
is rejected. Use a store for intentionally shared state.

Use normal methods when referring to the instance through `this`. Arrow functions keep
JavaScript's native lexical `this` behavior.

## Direct mounting

For explicit ownership of an existing object:

```javascript
const counter = new Counter({ initial: 0 });
const dispose = Flow.mount(document.querySelector('#manual-counter'), counter);
counter.count++;
// Dispose before removing a container yourself. Repeated disposal is harmless.
dispose();
```

One instance belongs to one container. Use a store for intentionally shared state.
For direct mounting, give the container an ID and omit its `flow` registration attribute.
Mounting the same instance on the same container returns the existing disposer. Dispose
an existing binding before mounting a different instance there.

## Reactivity

Declare public state fields before mounting. Flow observes writable data fields in place,
preserving the original receiver of class methods, including access to private `#fields`.
Nested plain objects and arrays are observed through proxies. Mutate them through the
component or store field, rather than an earlier reference to their raw input object.

Synchronous writes are batched into a microtask. Flow updates that container's bindings,
reevaluates its getters and then invokes `update()`. Getters should be free of side effects.
Private fields, `Date`, `Map`, `Set`, custom nested class instances and newly added top-level
fields do not become reactive automatically. Assign a new public value when appropriate;
register a nested class as a store when it needs its own observable fields.

The initial implementation evaluates all bindings in an affected container; it does not
cache getters or maintain a dependency graph per DOM binding. There is no virtual DOM or JSX.

## Markup bindings

Values are property paths, action names or JSON data. HTML contains no executable expressions.

| Attribute | Meaning |
| --- | --- |
| `flow="counter"` | Component registered under this name |
| `flow-props='{"initial":2}'` | Deeply frozen, public JSON props |
| `flow-text="cart.total"` | Text from a field or getter, using text content |
| `flow-model="query"` | Two-way input binding |
| `flow-show="open"` | Visibility through native `hidden` |
| `flow-on:click="save"` | Declared action, receiving `(event, context)` |
| `flow-class:active="selected"` | Toggle one class |
| `flow-bind:disabled="pending"` | Bind an allowed DOM property |
| `flow-bind:aria-expanded="open"` | Bind an ARIA attribute |
| `flow-ref="results"` | Local named element for a client or widget |
| `flow-key="product-42"` | Stable sibling identity during fragment updates |

`flow-model` supports text inputs, textareas, selects, checkbox booleans, radio values,
numeric/range inputs and arrays for multiple selects. An empty numeric input becomes `null`.
File inputs use native `FormData`. Event actions call `event.preventDefault()` themselves
when needed. Bindings and refs inside a nested component belong to that component.

Allowed bound properties are `disabled`, `checked`, `selected`, `readonly`, `required`,
`multiple`, `hidden`, `open` and `value`. Allowed attributes are `aria-*`, `title`, `role`
and `tabindex`. Arbitrary HTML, event-handler attributes and expression strings are rejected.

## Lifecycle

All hooks are optional. `context` contains `root`, local `refs`, readonly `props`, a scoped
`client`, `store(name)` and `onCleanup(callback)`.

| Hook | Timing |
| --- | --- |
| `init(context)` | After reactivity is prepared; refs are available, before initial rendering |
| `mount(context)` | After the first DOM update |
| `update(changes, context)` | After a batched state change, changed props or a fragment update |
| `unmount(context)` | Once during disposal |

`init` and `mount` may return promises; initialization waits for them. Writes during `init`
are part of the initial state. Writes during `mount` cause a subsequent update.
Async `update` hooks may overlap: later state changes render immediately and invoke their
own update rather than waiting for an old request. Scoped HTML loads cancel superseded
requests and reject late responses. Handle the ordering of other asynchronous work in the
component. Do not let an unguarded update write the property it observes indefinitely;
Flow diagnoses continuous update loops.

`changes.paths` lists changed public paths. `changes.has('filters.query')` matches that
path, a replacement of an ancestor or a change below it. `changes.reason` is `state`,
`props` or `fragment`. New props do not overwrite local fields; read them explicitly in
`update` if needed.

The synchronous part of `unmount` runs before Flow removes DOM. External removals are
detected afterwards by a MutationObserver. Use the direct disposer for widgets that need
cleanup while their nodes are connected. Async teardown is not awaited before removal.
Flow removes listeners and subscriptions, aborts scoped requests and runs cleanup callbacks
even when a hook fails. Register widget disposal through `onCleanup()`.
Once disposed, the scoped client rejects new work with `AbortError`; a stale component
cannot supersede a current request into its former container.

Unhandled action/hook errors dispatch a bubbling, cancelable `flow:error` event with
`detail: { error, root, phase }`. Calling `preventDefault()` suppresses the default console
report. Expected request cancellations use `AbortError` and are not reported as failures.

## Backend requests

Both `context.client` and `Flow.client` provide:

| Method | Result |
| --- | --- |
| `get(url, options)` | JSON, or `null` for 204 |
| `post(url, data, options)` | JSON, or `null` for 204 |
| `load(url, options)` | Update an HTML target; return the HTTP `Response` |

Options include `query`, `headers` and `signal`. `load` additionally takes `target`,
`debounce` in milliseconds, and optionally `method` and `data`. A scoped `target` is a
local ref name or an element belonging to that component. The standalone client takes
an element. Query arrays produce repeated parameters. Requests use the same origin and
same-origin credentials; writes are never retried automatically.

```javascript
export default class ProductSearch {
    query = '';
    error = '';

    async update(changes, { client, props }) {
        if (!changes.has('query')) return;

        try {
            await client.load(props.searchUrl, {
                query: { q: this.query }, target: 'results', debounce: 200,
            });
        } catch (error) {
            if (error.name !== 'AbortError') this.error = 'The search could not be loaded.';
        }
    }
}
```

Use a normal GET form as the initial HTML so the search also has a non-JavaScript path.
Generate its action and `searchUrl` with `Naf\route()` and escape quoted attributes with
`Naf\View\s()`.

### Full page or fragment

`load` sends `Accept: text/html` and `X-Flow: fragment`. The response must identify itself
with `Content-Type: text/html` and `X-Flow: fragment`. The PHP helper selects an explicitly
named template and sets the response headers, including `Vary: X-Flow`:

```php-inline
use function Naf\abort;
use function Naf\Flow\page;
use function Naf\param;

// In an existing routed controller; both templates are provided by the host.
$query = param()->get('q', '');
if (!is_string($query)) {
    abort(400, 'Query must be text.');
}

return page('products.index', ['query' => $query], fragment: 'products.results');
```

Only the target's children are updated. Stable `id` or `flow-key` values preserve nodes
and component instances; keys must be unique among siblings. Unkeyed nodes match by
position and compatible type. Edited native input values and focus are preserved when
their nodes survive. Bound inputs reflect their component's state.
Keyed reordering retains focus and input selection too. Flow uses native state-preserving
moves when available and restores focus when older browsers require detach/reinsert moves.

Successful 204 responses leave contents alone. HTML validation fragments with status 422
are rendered, then reject with `FlowHttpError`. Other failed responses retain the old DOM.
`FlowHttpError` exposes `status`, `data` and `response`; errors with JSON bodies retain
their structured data. Redirects, complete HTML documents and unexpected content types
are rejected. Handle authentication/navigation explicitly. The target's `aria-busy` is
restored after completion, including cancellation and errors.

### CSRF and forms

`naf/form` is optional at runtime. Keep its protections and validation in the host.
Generate a CSRF token once per page and include it in the form. Native `FormData` preserves
that token and file uploads:

```javascript
async save(event, { client }) {
    event.preventDefault();
    const result = await client.post('/save', new FormData(event.currentTarget));
    // Apply the JSON result to the component's fields.
}
```

Use `flow-on:submit="save"` on the form. For JSON writes, send `X-CSRF-Token` when using
`naf/form` 0.2.3+. Server validation, authorization and response generation stay in PHP.
Cancelling a browser request does not roll back an operation already running on the server.

## Stores

A store takes an object, rather than a component factory. In the following registration,
JavaScript evaluates `new Filters()` immediately and Flow observes that same instance.
`Flow.store('filters')` retrieves it without constructing another object. Create the store
before registering components that read it during `init()`.

```javascript
class Filters {
    query = '';
    reset() { this.query = ''; }
}

Flow.store('filters', new Filters());
Flow.register('filter-form', () => ({
    filters: null,
    init({ store }) { this.filters = store('filters'); },
    reset() { this.filters.reset(); },
}));
```

Bind `flow-model="filters.query"` in each consumer. `Flow.store('filters')` retrieves the
same observed object. Stores live in the browser's page and have no automatic persistence,
server synchronization or lifecycle hooks.

## A complete example: a shared search and server-rendered results

This example extends an application created with `composer create-project naf/app` and
the Flow installation above. It uses a normal GET form as its non-JavaScript path,
two separate components sharing one store, and a PHP fragment returned by the same route.
The small catalog is example data. Replace it with an application service when connecting
your domain; no database or form plugin is needed for this read-only example.

Add this route to the existing `app/routes.php`:

```php-inline
use App\Controllers\FlowExampleController;
use function Naf\route;

route()->add('GET', '/flow-example', [FlowExampleController::class, 'index'], 'flow.example');
```

```php title="app/Controllers/FlowExampleController.php"
<?php

declare(strict_types=1);

namespace App\Controllers;

use Psr\Http\Message\ResponseInterface;

use function Naf\abort;
use function Naf\Flow\page;
use function Naf\param;

final class FlowExampleController
{
    public function index(): ResponseInterface
    {
        $query = param()->get('q', '');
        if (!is_string($query) || mb_strlen($query) > 80) {
            abort(400, 'Query must be text with at most 80 characters.');
        }

        $catalog = [
            ['id' => 'view', 'title' => 'Views and templates'],
            ['id' => 'form', 'title' => 'Forms and validation'],
            ['id' => 'queue', 'title' => 'Queues and workers'],
        ];
        $items = array_values(array_filter(
            $catalog,
            static fn(array $item): bool => mb_stripos($item['title'], $query) !== false,
        ));

        return page(
            'flow-example.index',
            ['query' => $query, 'items' => $items],
            fragment: 'flow-example.results',
        )->withHeader(
            'Content-Security-Policy',
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'",
        );
    }
}
```

The full page registers the application module and prints collected scripts after its
containers. It passes query and URL props as escaped JSON. Logic stays in external modules.

```html+php title="app/views/flow-example/index.phtml"
<?php
use function Naf\route;
use function Naf\View\asset;
use function Naf\View\s;
use function Naf\View\view;

asset()->add('/js/flow-example.js', 'module');
$props = json_encode(['query' => $query, 'url' => route('flow.example')], JSON_THROW_ON_ERROR);
?>
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Flow example</title></head>
<body>
    <h1>Flow example</h1>

    <section flow="catalog-search" flow-props="<?= s($props) ?>">
        <h2>Search the catalog</h2>
        <form method="get" action="<?= s(route('flow.example')) ?>" flow-on:submit="search">
            <label>Search <input name="q" value="<?= s($query) ?>" flow-model="filters.query"></label>
            <button type="submit">Search</button>
        </form>
        <p role="alert" flow-show="error" flow-text="error" hidden></p>
        <div flow-ref="results">
            <?= view('flow-example.results', ['items' => $items]) ?>
        </div>
    </section>

    <section flow="filter-mirror">
        <h2>The same store, another component</h2>
        <label>Shared query <input flow-model="filters.query" value="<?= s($query) ?>"></label>
        <button type="button" flow-on:click="reset">Reset filters</button>
    </section>

    <?= asset()->render('js') ?>
</body>
</html>
```

The fragment renders the results. Stable keys identify entries when the
list changes; all displayed catalog values still use the View escaping helper.

```html+php title="app/views/flow-example/results.phtml"
<?php use function Naf\View\s; ?>
<p><?= count($items) ?> results</p>
<ul>
    <?php foreach ($items as $item): ?>
        <li flow-key="<?= s($item['id']) ?>"><?= s($item['title']) ?></li>
    <?php endforeach ?>
</ul>
```

Give the store its own module. Its fields are declared before observation:

```javascript title="public/js/flow-example/stores/Filters.js"
export default class Filters {
    query = '';

    constructor(query = '') {
        this.query = query;
    }

    reset() {
        this.query = '';
    }
}
```

The search component retrieves the store during `init()`. It checks the changed path
before loading a fragment, so setting its error field does not trigger another search.
The explicit submit action prevents normal navigation while retaining the GET fallback.

```javascript title="public/js/flow-example/components/CatalogSearch.js"
export default class CatalogSearch {
    filters = null;
    error = '';

    init({ store }) {
        this.filters = store('catalog-filters');
    }

    async update(changes, context) {
        if (changes.has('filters.query')) {
            await this.loadResults(context);
        }
    }

    async search(event, context) {
        event.preventDefault();
        await this.loadResults(context);
    }

    async loadResults({ client, props }) {
        this.error = '';
        try {
            await client.load(props.url, {
                query: { q: this.filters.query },
                target: 'results',
                debounce: 200,
            });
        } catch (error) {
            if (error.name !== 'AbortError') {
                this.error = 'The results could not be loaded.';
            }
        }
    }
}
```

The second component demonstrates an anonymous exported factory. It shares the store,
while receiving its own component instance, refs and lifecycle:

```javascript title="public/js/flow-example/components/FilterMirror.js"
export default () => ({
    filters: null,

    init({ store }) {
        this.filters = store('catalog-filters');
    },

    reset() {
        this.filters.reset();
    },
});
```

The entry module creates the store before registering consumers. Both fields start with
the query already rendered by PHP; no extra initial request or client-side template is needed.

```javascript title="public/js/flow-example.js"
import { Flow } from '/_flow/flow.js';
import CatalogSearch from './flow-example/components/CatalogSearch.js';
import FilterMirror from './flow-example/components/FilterMirror.js';
import Filters from './flow-example/stores/Filters.js';

const root = document.querySelector('[flow="catalog-search"]');
const props = JSON.parse(root.getAttribute('flow-props'));

Flow.store('catalog-filters', new Filters(props.query));
Flow.register('catalog-search', () => new CatalogSearch());
Flow.register('filter-mirror', FilterMirror);
```

### Development server

PHP's built-in server can treat URLs containing a file extension as missing static files.
The Flow runtime is an application route, so create this router in the application root.
Existing public files are served directly; other requests reach the normal entry point:

```php title="router.php"
<?php

declare(strict_types=1);

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
if (is_string($path) && is_file(__DIR__ . '/public' . $path)) {
    return false;
}

require __DIR__ . '/public/index.php';
```

Start the development server from the application root:

```bash
php -S 127.0.0.1:8000 -t public router.php
```

Open `/flow-example`. Typing in either field updates the other and reloads only the
results. Clicking reset does the same through a store method. Submitting with JavaScript
disabled still requests `/flow-example?q=...` and renders a complete page. To inspect the
backend response directly:

```bash
curl -H 'X-Flow: fragment' 'http://127.0.0.1:8000/flow-example?q=view'
```

The response has `X-Flow: fragment` and `Vary: X-Flow`, and contains the result template
without a document shell or additional scripts. The input check also rejects `?q[]=view`.

## Runtime boundaries { #practical-boundaries-and-next-improvements }

Keep `update()` selective: use `changes.has()` before requesting data, and avoid a hook
that continuously writes the field it observes. Async hooks can overlap; the HTML client
handles superseded target loads, while ordering unrelated JSON requests belongs to the
application. `AbortError` is expected when replacing a load or disposing its component.

Use unique sibling keys for reorderable lists. Compatible keyed containers retain their
component instance; new props do not silently reset its local fields. Use a new key when
you intentionally want a fresh instance. Clean up external widgets through `onCleanup()`.

The current engine updates an affected container as a unit. Measure realistic list sizes
and update frequency when evaluating performance for an application.

## Assets and CSP

The readable entry point is `src/Resources/public/flow.js`; its implementation is split
into focused modules in `src/Resources/public/runtime/`. esbuild bundles these into the
prebuilt `flow.min.js` shipped by the package. The plugin boots after View and registers
`/_flow/flow.js` as a module. This fixed URL serves the complete minified bundle, so asset
tags and imports share one module instance without additional runtime module requests.
Applications need no Node installation or build step. Its named route
`flow.runtime` serves only that known file through PSR-7, with a JavaScript MIME type,
`nosniff`, an ETag and `public, max-age=0, must-revalidate`. Matching `If-None-Match`
requests return 304. There is no generic vendor-file endpoint or publishing command to run.
Use the exact same import URL as the asset tag so application imports share one registry.

`asset()` collects tags; the layout still needs to render them. JSON and fragment responses
do not get scripts appended. A static deployment can copy the runtime to the same URL;
keep its import URL and cache invalidation consistent.

The runtime works with `script-src 'self'` without `unsafe-eval` or `unsafe-inline`.
All component logic resides in allowed external modules. Flow discards fragment scripts,
inline event handlers, embedded browsing contexts and executable URL attributes before
insertion. Serve fragments from trusted application templates; this is not a general
sanitizer for arbitrary user-authored HTML. Keep user content separate from Flow directives.
Hosts using nonce-only or Trusted Types policies need their corresponding asset/HTML
integration; the default View hook does not add nonces or a Trusted Types policy.


Contributor checks and the one-command esbuild build are documented in
[the package instructions](https://github.com/nafphp/flow/blob/main/AGENTS.md).
