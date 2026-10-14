---
title: Monitoring
requires:
  - naf/monitoring
---

# Monitoring

`naf/monitoring` records declared counters, gauges and histograms, exports them to
StatsD or DogStatsD, and can decorate a PSR-3 logger. The application chooses its
metrics, labels and collector. The default exporter performs no network I/O.

Use this guide in an existing [NAF application](first-app.md), with PHP 8.3+ and
Framework 0.2.3 or newer.

NAF discovers the installed Composer plugin automatically. Application code uses
`Naf\Monitoring\monitor()` or injects `Naf\Monitoring\Monitor`. Both share the same
service. No application route, daemon or scheduler is installed by the plugin.

## Quick start

Use a disposable NAF application for this example. Replace `app/config.php` with
the following file; when adding monitoring to an existing application, merge the
`monitoring` entry into its current configuration.

```php title="app/config.php"
<?php

declare(strict_types=1);

return [
    'monitoring' => [
        'metrics' => [
            'orders.created' => ['type' => 'counter', 'labels' => ['channel']],
        ],
    ],
];
```

Create `bin/monitoring-demo.php`:

```php title="bin/monitoring-demo.php"
<?php

declare(strict_types=1);

use Naf\Monitoring\Exporters\InMemoryExporter;
use Naf\Monitoring\MetricExporterInterface;

use function Naf\app;
use function Naf\Monitoring\monitor;

define('BASE_PATH', dirname(__DIR__));
require BASE_PATH . '/vendor/autoload.php';

$application = app();
$exporter = new InMemoryExporter();
$application->container()->set(MetricExporterInterface::class, $exporter);

monitor('orders.created', ['channel' => 'web'])->increment(3);
monitor()->flush();

foreach ($exporter->drain() as $measurement) {
    echo $measurement->definition->name, ': ', $measurement->value,
        ' (channel=', $measurement->labels['channel'], ')', PHP_EOL;
}
```

Run the example from the application root:

```bash
php bin/monitoring-demo.php
```

Expected output:

```text
orders.created: 3 (channel=web)
```

Register the exporter override before the first metric call. The helper and an
injected `Monitor` share that service. The in-memory exporter lets you inspect
measurements without a collector; configure [StatsD or DogStatsD](#statsd-and-dogstatsd)
for production collection.

## Declare your metrics

Merge these entries into the array returned by `app/config.php`:

```php
<?php
use Naf\Monitoring\Exporters\StatsDExporter;

return ['monitoring' => [
    'exporter' => StatsDExporter::class,
    'exporter_options' => [
        'host' => '127.0.0.1',
        'port' => 8125,
        'prefix' => 'shop',
        'protocol' => 'statsd',
        'maxDatagramBytes' => 512,
        'timeout' => 0.05,
    ],
    'labels' => ['service' => 'shop', 'environment' => 'prod'],
    'batch_size' => 256,
    'metrics' => [
        'orders.created' => ['type' => 'counter', 'labels' => ['channel']],
        'queue.depth' => ['type' => 'gauge'],
        'checkout.duration' => ['type' => 'histogram', 'unit' => 's'],
    ],
    'http' => true,
    'logging' => [
        'enabled' => true,
        'min_level' => 'warning',
        'count' => true,
    ],
]];
```

The default exporter is `Naf\Monitoring\Exporters\NullExporter`, with no network
I/O. Default labels and custom metrics are empty; HTTP and logging are disabled.
Changing the configured exporter keeps the metric calls in your application intact.

| Type | Method | Meaning |
| --- | --- | --- |
| `counter` | `increment(int\|float $amount = 1): void` | Add a nonnegative delta; never a cumulative total |
| `gauge` | `set(int\|float $value): void` | Set the current value, including negative values |
| `histogram` | `observe(int\|float $value): void` | Record a nonnegative sample in the declared unit |
| Time histogram | `measure(callable $operation): mixed` | Run and time a callback; return its result |

`measure()` requires unit `s` or `ms`, uses a monotonic clock, records failed
operations too and preserves their exception. `observe()` accepts an already
measured value in the declared unit. Values must be finite; NaN and infinity fail.
An undeclared metric or a method incompatible with its type throws immediately.

```php-inline
use function Naf\Monitoring\monitor;

monitor('orders.created')->increment();
monitor('orders.created', ['channel' => 'web'])->increment(5);
monitor('queue.depth')->set(42);
monitor('checkout.duration')->observe(0.125); // seconds

$result = monitor('checkout.duration')->measure(fn() => $checkout->run());
```

The metric definitions belong to the application configuration, not to request
input. Names contain 1–120 ASCII letters, digits, `_` and `.`, start with a letter,
and cannot contain the reserved `__labels` segment. Units contain up to 24 ASCII
letters, digits, `_` or `/`. Built-in metric names below cannot be redeclared.

## Labels and request isolation

Per-metric `labels` declare the allowed keys, not their values. Omitted labels
remain absent. Global `monitoring:labels` apply to every metric and exported log;
global keys cannot overlap any declared per-metric keys, including built-in keys.

Each helper call owns its label values. Reusing a returned metric retains its own
labels; subsequent calls do not change it. There is no mutable global request
context to leak into another queue job.

Label names start with a letter and contain at most 32 letters, digits or `_`.
Values are strings, integers or booleans; normalized values contain 1–80 ASCII
letters, digits, `_`, `.`, `/` or `-`. Booleans become `true` and `false`. There
may be at most 16 global and metric labels combined. Protocol delimiters and
control characters are rejected rather than silently changing a metric's identity.

Use bounded values such as channel, route name and status. Unique user IDs, order
IDs and full request URLs create a new time series per value. The character and
length limits do not limit the number of distinct series in your backend.

## StatsD and DogStatsD

The shipped `StatsDExporter` uses UDP to a numeric IPv4/IPv6 address. The default
is `127.0.0.1:8125`. Hostnames are rejected so DNS lookup cannot stall a request;
resolve the agent address in deployment configuration or inject a custom
`DatagramTransportInterface`. The socket opens lazily at export and uses
non-blocking writes. The connection timeout is in seconds, greater than zero
and at most one second.

| Behavior | `statsd` | `dogstatsd` |
| --- | --- | --- |
| Counter | `c`, delta | `c`, delta |
| Gauge | `g`, absolute value | `g`, absolute value |
| Histogram | `ms`, requires `s` or `ms`; seconds convert to milliseconds | `h`, retains the declared unit/value |
| Labels | Sorted, hex-encoded suffix in the metric name | Sorted native `\|#key:value` tags |
| Aggregation/buckets | Configured in the StatsD agent | Configured in the DogStatsD agent/backend |

For example, `orders.created` with `channel=web` is sent as
`orders.created.__labels.6368616e6e656c.776562:1|c` in plain StatsD, or
`orders.created:1|c|#channel:web` in DogStatsD, before any configured prefix.
The reserved suffix and hex encoding preserve distinct label values and keys.
Classic StatsD cannot carry native tags, unit metadata or arbitrary histograms;
declaring a non-time histogram with that exporter fails during service creation.
Configure display units in the backend for DogStatsD histograms.

Plain StatsD treats signed gauges as deltas. Negative absolute gauges therefore
send a reset to zero followed by the negative value in the same datagram. Packets
contain whole records, never fragments of a measurement or its reset pair.
`maxDatagramBytes` defaults to 512 and accepts 64–65507; choose a limit appropriate
for your network MTU. A single oversize measurement fails the batch and is diagnosed.

Protocol references: [StatsD metric types](https://github.com/statsd/statsd/blob/master/docs/metric_types.md)
and [DogStatsD datagrams](https://docs.datadoghq.com/extend/dogstatsd/datagram_shell/).

## PSR-3 logging

Enable `monitoring:logging:enabled` to wrap the logger currently registered under
`Psr\Log\LoggerInterface`. Continue using the normal helper:

```php-inline
use function Naf\log;

log()->info('Order accepted');
log()->warning('Inventory below threshold', ['remaining' => 3]);
log()->error('Checkout failed', ['exception' => $exception]);
```

Every call still reaches the original logger. The monitoring copy is filtered
by `min_level`, which defaults to `warning` and accepts all eight PSR-3 levels:
`debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert`, `emergency`.
It includes the chosen severity and all higher severities. Invalid levels fail.

With `count: true`, each qualifying log increments `logs.total` with its `level`.
Log messages, exception texts and context values never become metric labels.
StatsD transports metrics only: enabling the logger does not send raw log messages
to a StatsD agent.

For structured log delivery, optionally register a `LogExporterInterface` service
before the first use of the monitor, or configure `log_exporter` as its class name
and `log_exporter_options` as named constructor arguments. Its `export(array $records)`
receives `LogRecord` objects with the original message, PSR-3 context, severity,
global labels and a Unix timestamp in seconds. The metric and log destinations
are attempted independently. Set `logging:count` to `false` for log export alone.

Records retain PHP context objects by reference until the batch is exported. Avoid
mutating them before flushing; a custom exporter owns serialization, exception
formatting, field selection and redaction. There is no bundled HTTP/OTLP log
exporter in this first version. Export failures and diagnostics are guarded against
recursive monitoring; the default diagnostic path uses PHP `error_log()` directly.

If your host replaces the logger after plugin boot, wrap that final logger explicitly
before constructing its consumers. Keep automatic decoration disabled in that case:

```php-inline
use Naf\Monitoring\{Monitor, MonitoringLogger};
use Psr\Log\LoggerInterface;
use function Naf\app;

$container = app()->container();
$original = $container->get(LoggerInterface::class); // After your custom registration.
$container->set(LoggerInterface::class, static fn() => new MonitoringLogger(
    $original,
    $container->get(Monitor::class),
    minLevel: 'error',
));
```

Register overrides before resolving `Monitor` or the decorated logger. A later
rebinding cannot replace a dependency already held by an instantiated service.

## HTTP instrumentation

With `monitoring:http` enabled, the plugin listens to the existing NAF request,
route, exception and response events. It records:

| Metric | Type/unit | Labels |
| --- | --- | --- |
| `http.requests` | Counter | `method`, `route`, `status` |
| `http.duration` | Histogram, seconds | `method`, `route`, `status` |
| `http.exceptions` | Counter | None |
| `logs.total` | Counter; requires logging/count enabled | `level` |

Duration begins at `REQUEST_START` and normally ends at `RESPONSE_END`, after
the response body is written. It excludes bootstrap and the final monitoring flush.
Threshold-triggered exports during the request remain part of its processing time.
It measures server processing, not the client's download time. A shutdown fallback
handles skipped/interrupted response-end listeners without counting a request twice;
when a response was observed, it uses PHP's emitted status for that fallback.

Routes use their registered name, never the concrete URL. Unmatched routes use
`unmatched`, unnamed routes use `unnamed`, and names outside the portable label
syntax use `other`. Unrecognized HTTP methods use `OTHER`. Exception counting is
once per observed request and includes exceptions raised for normal HTTP errors
such as a missing route. It covers the NAF exception event and observed fatal
shutdowns; it is not a global record of every caught or uncaught PHP exception.

## Buffering, workers and failures

The shared metric/log buffer flushes when it reaches `batch_size` records, at
normal response end and at PHP shutdown. The default is 256, with an allowed
range of 1–10000. The bound is a record count, not a byte limit on arbitrary
structured log contexts. Custom exporters must also bound their own work and memory.

Long-running workers explicitly flush in the job's existing lifecycle:

```php-inline
use function Naf\Monitoring\monitor;

try {
    $job->handle();
} finally {
    monitor()->flush();
}
```

This is an application fragment, not a new NAF worker API. There is no periodic
background flush or queue dependency. Retained metric objects keep their labels,
so create job-specific metrics inside each job. The `InMemoryExporter` used in
tests also needs draining between jobs if retained indefinitely.

Export happens synchronously at flush points. UDP is best-effort: a successful
socket write does not confirm delivery or collector health. Batches are removed
before export and never retried, preventing repeated counter increments. A partial
network failure can deliver some datagrams and lose others. Process termination,
early bootstrap errors, memory exhaustion and a prior shutdown handler that exits
can prevent the final flush. This is telemetry, not an audit trail or billing ledger.

Runtime export exceptions are caught and increase `monitor()->failedBatches()`.
The plugin's default diagnostic callback writes to PHP's `error_log()`. Override
`monitoring:on_error` with a callback receiving `(Throwable $error, string $signal)`;
`$signal` is `metrics` or `logs`. Keep that callback independent of this monitor.
API/configuration mistakes still throw early. `measure()` preserves an application's
return value or exception even if exporting the timing fails.

## Custom exporters and multiple destinations

Implement `MetricExporterInterface` with two methods:

- `validate(MetricDefinition $definition): void` rejects unsupported types/units
  when the monitoring service is constructed, including built-in definitions.
- `export(array $measurements): void` receives a batch of `Measurement` objects.
  Each contains its definition, numeric value and normalized labels. It sends
  once and throws on failure. Counters represent deltas, gauges absolute values
  and histograms individual observations.

Use `exporter` and `exporter_options` for a class constructed through NAF's normal
autowiring, or bind `MetricExporterInterface` explicitly in root `bootstrap.php`,
before `app()->run()` and before the monitor is resolved. For example:

```php-inline
use Naf\Monitoring\MetricExporterInterface;
use Naf\Monitoring\Exporters\{CompositeExporter, InMemoryExporter, StatsDExporter};
use function Naf\app;

$capture = new InMemoryExporter();
app()->container()->set(MetricExporterInterface::class, new CompositeExporter([
    new StatsDExporter(host: '127.0.0.1', port: 8125),
    $capture,
]));
```

`CompositeExporter` attempts every destination even when one fails. A failed
composite batch increments `failedBatches()` once; successful destinations are
not retried. All destinations must support the declared metrics.

For an HTTP adapter, inject a PSR-18 client, such as `naf/client`, and keep URL,
authentication and format inside that adapter. Bind `Psr\Http\Client\ClientInterface`
to the configured client in the host; the monitoring plugin does not install an
HTTP stack. An OTLP adapter should use the existing OpenTelemetry SDK. A future
Prometheus pull adapter additionally needs aggregation across PHP requests and
processes; no `/metrics` endpoint is shipped here.

## Testing without a collector

```php-inline
use Naf\Monitoring\{MetricDefinition, MetricType, Monitor};
use Naf\Monitoring\Exporters\InMemoryExporter;

$exporter = new InMemoryExporter();
$monitor = new Monitor($exporter, [
    new MetricDefinition('orders.created', MetricType::Counter),
]);
$monitor->metric('orders.created')->increment(3);
$monitor->flush();

$measurements = $exporter->drain();
assert($measurements[0]->value === 3);
```

`measurements()` inspects retained records; `drain()` returns and clears them.
The in-memory exporter defaults to a capacity of 10000 records and throws when
full. Through `Monitor`, that failure is counted and the failed batch is dropped.
`NullExporter` discards exported batches and performs no I/O.

The package suite tests these APIs, the PSR-3 severity matrix, independent export
failures, protocol bytes, bounds and label isolation. Real loopback UDP and HTTP/CLI
tests verify Composer discovery, host overrides, response behavior and flushing
against the published framework. See [AGENTS.md](https://github.com/nafphp/monitoring/blob/main/AGENTS.md)
for the development commands.

## Configuration

Add these keys below `monitoring` in `app/config.php`. Configuration merges with
the plugin defaults before the monitoring service is resolved.

| Key | Type | Default | Effect |
|---|---|---|---|
| `monitoring:exporter` | class string | `Naf\Monitoring\Exporters\NullExporter` | Metric exporter implementing `MetricExporterInterface` |
| `monitoring:exporter_options` | array | `[]` | Named constructor arguments for the selected metric exporter |
| `monitoring:log_exporter` | class string or null | `null` | Optional structured log exporter implementing `LogExporterInterface` |
| `monitoring:log_exporter_options` | array | `[]` | Named constructor arguments for the log exporter |
| `monitoring:labels` | array | `[]` | Constant service/environment labels on metrics and exported logs |
| `monitoring:batch_size` | integer | `256` | Shared record-count flush threshold, from 1 to 10000 |
| `monitoring:metrics` | array | `[]` | Metric names mapped to `type`, optional `unit` and allowed `labels` |
| `monitoring:http` | boolean | `false` | Enables request, duration and exception metrics through NAF events |
| `monitoring:on_error` | callable or null | `null` | Independent callback receiving the export exception and `metrics` or `logs`; null uses PHP `error_log()` |
| `monitoring:logging:enabled` | boolean | `false` | Decorates the currently registered PSR-3 logger |
| `monitoring:logging:min_level` | string | `warning` | Lowest severity copied into monitoring |
| `monitoring:logging:count` | boolean | `true` | Adds `logs.total` for qualifying logs when decoration is enabled |

When selecting `StatsDExporter`, its `monitoring:exporter_options` keys are:

| Key | Type | Default | Effect |
|---|---|---|---|
| `host` | string | `127.0.0.1` | Numeric IPv4/IPv6 collector address |
| `port` | integer | `8125` | UDP destination port, from 1 to 65535 |
| `prefix` | string | empty | Prefix using the metric-name syntax |
| `protocol` | string | `statsd` | `statsd` or `dogstatsd` wire format |
| `maxDatagramBytes` | integer | `512` | Whole-record datagram limit, from 64 to 65507 bytes |
| `timeout` | number | `0.05` | Socket connection timeout in seconds, greater than zero and at most one |
| `transport` | `DatagramTransportInterface` or null | `null` | Explicit transport override; null constructs `UdpTransport` |

`InMemoryExporter` accepts a positive `capacity` constructor option, defaulting to
10000 retained measurements. Drain it between tests or worker jobs.

## API details

Import the helper from `Naf\Monitoring`:

```php-inline
use function Naf\Monitoring\monitor;

// monitor(?string $name = null, array $labels = []): Monitor|Metric
$service = monitor();
$metric = monitor('orders.created', ['channel' => 'web']);
```

Calling `monitor()` returns the shared `Monitor`; supplying a name creates a
`Metric` with its own normalized label values. Labels without a name throw
`InvalidArgumentException`. `Monitor::metric(string $name, array $labels = []): Metric`
provides the same lookup on an injected service. Metric mutation methods and
timing requirements are listed under [Declare your metrics](#declare-your-metrics).

`Monitor::flush(): void` exports pending records once.
`Monitor::failedBatches(): int` returns the number of failed metric or log batches.
The extension contracts use these namespaces:

| Contract | Namespace |
|---|---|
| Metric batches | `Naf\Monitoring\MetricExporterInterface` |
| Structured log batches | `Naf\Monitoring\LogExporterInterface` |
| Datagram transport | `Naf\Monitoring\Transport\DatagramTransportInterface` |

See the generated [function index](function-index.md#nafmonitoring) and
[configuration reference](configuration-reference.md#nafmonitoring).

## If the result is different

| Symptom | Check |
|---|---|
| No metric reaches the collector | The default exporter is `NullExporter`. Select a real exporter, check its numeric address/port and call `flush()` in long-running jobs. A successful UDP write does not confirm delivery. |
| An undeclared metric or label throws | Add the metric and allowed label keys to application configuration before the monitor is resolved. |
| A histogram is rejected by StatsD | Plain StatsD accepts only time histograms in `s` or `ms`. Use DogStatsD for other histogram units. |
| HTTP or log metrics are absent | Enable `monitoring:http` or `monitoring:logging:enabled` and inspect the log severity threshold. |
| A custom exporter binding is ignored | Register it before the first use of `Monitor` or the decorated logger. Existing objects retain their dependencies. |
| Export failures recur | Inspect `failedBatches()` and the independent diagnostic callback; bound the exporter work and record sizes. Failed batches are discarded. |

## Related pages

- [Application lifecycle](lifecycle.md) for bootstrap timing and service registration.
- [Dependency injection](dependency-injection.md) for factories and overrides.
- [Events](events.md) for request and response hooks.
- [Queues and workers](queues.md) for background job lifetimes.
- [HTTP client](http-client.md) for PSR-18 adapters.
