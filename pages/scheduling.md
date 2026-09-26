---
title: Scheduled jobs
requires:
  - naf/schedule
---

# Scheduled jobs

Things that should happen at a time rather than on a request: a nightly cleanup, a
report at eight, a sync every fifteen minutes.

Jobs are described with cron expressions and handed to the queue, so the scheduler decides
*when* and the worker decides *how*. The part worth reading before you rely on it is what
happens when the machine was off at eight — a scheduler that silently skips is a scheduler
you find out about in the wrong week.

## A scheduled job

A scheduled job is a queue job that also says when it wants to run.

```php
namespace App\Jobs;

use Naf\CLI\Core\Output;
use Naf\Queue\Core\QueueJobInterface;
use Naf\Schedule\Core\ScheduledJobInterface;

final class RebuildSitemap implements QueueJobInterface, ScheduledJobInterface
{
    public function __construct(private array $payload = []) {}

    public function getCronExpression(): string
    {
        return '0 3 * * *';     // every day at 03:00
    }

    public function execute(Output $output): void
    {
        // rebuild it
    }
}
```

## Registering it

```php
use function Naf\Schedule\scheduler;

scheduler()->addScheduledJob(RebuildSitemap::class);
scheduler()->addScheduledJob(SyncInventory::class, ['warehouse' => 'north']);
```

In your application's `bootstrap.php`. The optional payload reaches the job's constructor,
but each class can be registered only once: a second registration of the same class
replaces the first payload. Use distinct job classes for distinct registered schedules.

`vendor/bin/naf schedule:list` shows what is registered and when each one runs next.

## Two processes, not one

**The scheduler does not run your jobs.** It decides that something is due and pushes it
onto the queue; a queue worker picks it up. Both have to be running:

```bash
vendor/bin/naf schedule:ticker     # decides what is due
vendor/bin/naf queue:consume       # actually runs it
```

A ticker without a worker fills the queue and nothing happens. This is the failure people
hit first, and it looks exactly like a scheduler that is not working.

## Running the ticker

```bash
vendor/bin/naf schedule:ticker
```

| Option | What it does |
|---|---|
| `--once` | run one scheduling pass and exit |
| `--max-jobs=N` | exit after queueing N jobs |
| `--max-runtime=N` | exit after N seconds |
| `--workers=N` | start this many workers alongside the ticker |

`--workers` is not a hint: the ticker starts that many real `queue:consume` processes and
owns them. They write to the host's `logs/queue/` directory and use whatever PSR-3 logger
you configured. When the ticker exits — cleanly or by failing — it closes its children
rather than leaving orphaned workers behind.

That makes `schedule:ticker --workers=1` a way to run the pair under one supervisor entry
instead of two. Running separate `queue:consume` processes is still the more flexible
arrangement, because you can scale and restart them independently.

```ini
[program:naf-schedule]
directory=/var/www/my-app
command=php /var/www/my-app/vendor/bin/naf schedule:ticker --max-runtime=3600
autostart=true
autorestart=true
```

Replace `/var/www/my-app` with your application path.

## What happens to a window that was missed

Nothing. `isDue()` is asked about the minute the ticker is in, so a job due at 03:00 on a
machine that was off until 03:05 does not run — it runs the next day.

That is worth knowing before you rely on it for anything that must happen. If a run cannot
be skipped, the job itself has to notice that it has not run since yesterday, because the
scheduler will not tell it.

## Why a backlog does not build up

The interesting case is the other one: the ticker running while no worker is. Every minute
a due job is queued again, and by the time a worker comes back there are six hundred copies
of a sync that only ever needed the latest state.

The scheduler gives each run a deterministic id — `sha1('schedule:' . $class . ':' . $expression)`
— and the file driver uses that id as the job's filename. Queueing the same job again
overwrites the same file, so what waits for the worker is one run, not six hundred.

```php
'schedule' => [
    'queue' => [
        'coalesce' => true,     // the default
    ],
],
```

Turning it off gives every run its own random id and every run reaches the worker, which is
what you want for a job where each occurrence means something on its own — a billing tick,
not a cache rebuild.

!!! note "This depends on the driver"
    Coalescing works because the file driver keys jobs by that id. A driver that ignores
    `_job_id` and appends every job will not coalesce, no matter what the setting says.

## Not running the same minute twice

Within one minute a job is queued once, even if the ticker loops several times. The
scheduler remembers the last minute each job ran in and persists that, so restarting the
ticker mid-minute does not queue everything a second time.

That state is held under a file lock and replaced atomically, so two tickers cannot both
decide a minute is theirs, and a crash mid-write does not leave a half-written file. If
queueing a job fails, the minute is deliberately *not* marked complete — the next pass tries
again rather than silently skipping it.

!!! note "Crossing the crash boundary needs a durable job id"
    The guarantee covers the ticker's own state. A crash between enqueueing and recording
    that minute can still deliver a job twice. If that matters, give the job a durable id so
    the consumer can recognise the duplicate — the same at-least-once thinking the queue
    asks for.

Setting `schedule:heartbeat_file` in the configuration has the ticker record that it is
polling, which gives a health check something to read.
