---
title: Queues and workers
requires:
  - naf/queue
---

# Queues and workers

Work that should not happen while somebody is waiting. A confirmation mail, a
thumbnail, a call to a slow third party — the request hands it over and finishes.

The default driver writes to files, so there is nothing to install before you can try it.
Running the jobs is a command, which is why `naf/cli` comes along with this package: a
queue nobody drains is just a directory filling up.

## A job

A job is a class with one method. The payload it was queued with arrives in the
constructor.

```php
namespace App\Jobs;

use Naf\CLI\Core\Output;
use Naf\Queue\Core\QueueJobInterface;

final class SendWelcomeEmail implements QueueJobInterface
{
    public function __construct(private array $payload) {}

    public function execute(Output $output): void
    {
        // send it
    }
}
```

Throwing from `execute()` is how a job reports failure — the worker catches it and moves
the job to the deadletter.

## Queueing it

```php
use function Naf\Queue\queue;

queue()->push(SendWelcomeEmail::class, ['email' => 'user@example.com']);
```

The payload is serialised, so it holds data and not objects. Pass an id, not the entity.

## Channels

A channel is a separate line of work. Without one everything shares a queue, and a thousand
thumbnails delay the password-reset mail behind them.

```php
queue('emails')->push(SendWelcomeEmail::class, ['email' => $email]);
```

Then run a worker per channel, or one worker across several:

```bash
vendor/bin/naf queue:consume --channel=emails
vendor/bin/naf queue:consume --channels=default,emails,thumbnails
```

## Running the worker

```bash
vendor/bin/naf queue:consume
```

It keeps going until you stop it. The options that matter for running it under a process
supervisor:

| Option | What it does |
|---|---|
| `--once` | take one job and exit |
| `--max-jobs=N` | exit after N jobs |
| `--max-runtime=N` | exit after N seconds |
| `--channel=name` | one channel |
| `--channels=a,b,c` | several |
| `--verbose`, `-v` | print each job |

`--max-jobs` and `--max-runtime` exist because a long-running PHP process accumulates
memory. Let it exit on its own terms and have the supervisor start a fresh one, rather than
waiting for the OOM killer to decide.

```ini
[program:naf-queue]
command=php bin/naf queue:consume --channels=default,emails --max-jobs=500
autostart=true
autorestart=true
```

## Jobs that failed

A job whose `execute()` throws goes to the deadletter instead of being retried forever.

```bash
vendor/bin/naf queue:retry-failed          # put them back in the queue
vendor/bin/naf queue:retry-failed --keep   # ...and keep the deadletter copy
```

`--keep` is worth it while you are still finding out why they failed: without it, a second
failure is the only record you have left.

!!! warning "There is no per-channel retry"
    `queue:retry-failed` takes no `--channel`. The driver can do it — the interface has
    `retryFailedFrom()` — but the command does not pass one through, so anything you give it
    is ignored and every failed job is retried regardless of channel.

## Where the jobs live

The default driver writes files under your application's base path — one directory for the
queue, one for the deadletter. Nothing to install, and you can look at what is waiting.

It is also the reason a file-backed queue does not survive being spread over two machines:
the second server cannot see the first server's directory. The package ships an
`SQLiteDriver` as well, and the driver is a single interface, so a Redis or database one is
a class and a rebinding away:

```php
use Naf\Queue\Core\Queue;
use function Naf\app;

app()->container()->set(Queue::class, fn() => new Queue(new MyRedisDriver()));
```

Channels and the deadletter are separate interfaces on top of the basic one
(`ChannelQueueDriverInterface`, `QueueDeadletterDriverInterface`). A driver that implements
only the basic contract still works — it just has no channels and no deadletter, and
`queue:retry-failed` tells you so rather than failing.
