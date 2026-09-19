---
title: Page text waiting for the 0.2.3 releases (draft)
---

# Page text waiting for releases

Contributor draft. Finished prose for `pages/`, held here because the published site
describes published releases and none of these behaviours is released yet. Each section says
which release it waits for and which page it belongs in. After that release, move the section
into the named page and rerun `tools/check_pages.py` and `mkdocs build --strict`.

`drafts/http-client-streams.md` and `drafts/rc-validation.md` cover the same ground as notes;
this file is the wording meant for readers.

## Waits for naf/client v0.2.2 → `pages/http-client.md`

Insert before `## TLS and HTTP versions`.

---

## Large bodies do not go through memory

The cURL transport streams. It transfers a PSR-7 request body in chunks from its current
position, and spools the response into a temporary file that is deleted for you. That is
what makes an upload or a download bigger than your memory limit possible at all.

Two things follow from it, and both bite quietly if you do not know them:

```php
$response = client()->sendRequest($request);
$body     = $response->getBody();

while (!$body->eof()) {
    fwrite($target, $body->read(8192));
}

$body->close();          // the temporary file goes away here
```

Close the body when you are done. And `(string) $response->getBody()` still loads the whole
thing into memory — casting undoes the streaming, which is fine for a JSON answer and not
for a 2 GB file. A request stream you opened yourself stays open; the client does not close
what it did not create.

!!! note "The temporary filesystem has to be big enough"
    The response is spooled before `sendRequest()` returns, so the network transfer is
    finished by then. What you need free is disk, not memory.

Existing `TransportInterface` implementations and string-based `send()` calls keep working
unchanged. A custom transport can additionally implement `StreamingTransportInterface`, and
if your code must not silently fall back to buffering, say so:

```php
$streaming = client()->withOptions(['streaming' => true]);
```

That requires a transport with the capability rather than accepting the buffering fallback.
The stream-wrapper transport remains string-based.

A few sharp edges worth knowing:

| Situation | Behaviour |
|---|---|
| A retry after a failure | seeks the request body back to where it started |
| A non-seekable streaming request | never retried automatically — it cannot be rewound |
| `'decode_content' => false` | keeps the encoded bytes, for passing straight to object or file storage |
| Redirects | only the final response's headers and body are kept |
| `'max_redirects' => 0` | do not follow redirects at all |

## Waits for naf/queue v0.2.3 → `pages/queues.md`

Insert after the worker options table in `## Running the worker`.

---

With `--once`, the exit code tells you what happened: nonzero when the job failed, including
when its class is missing. A supervisor or a CI step can act on that instead of parsing
output. The failure is still kept for retry or the deadletter — a nonzero exit does not mean
the work was thrown away.

`--max-jobs` and `--max-runtime` exist because a long-running PHP process accumulates
memory. Let it exit on its own terms and have the supervisor start a fresh one, rather than
waiting for the OOM killer to decide.

```ini
[program:naf-queue]
directory=/var/www/my-app
command=php /var/www/my-app/vendor/bin/naf queue:consume --channels=default,emails --max-jobs=500
autostart=true
autorestart=true
```

Replace `/var/www/my-app` with the absolute path of your deployed application.

## Waits for naf/queue v0.2.3 → `pages/queues.md`

Append to `## Where the jobs live`.

---

### The database driver, for more than one machine

`PDODriver` is the answer to the directory problem above: the queue lives in your database,
so every server sees the same work. It implements `LeaseQueueDriverInterface`, which adds
reserve, acknowledge, release and renew on top of the basic contract.

```php
use Naf\Queue\Core\Queue;
use Naf\Queue\Drivers\PDODriver;
use function Naf\app;

$driver = new PDODriver(app()->container()->get(PDO::class), 300);
$driver->install();                       // once, creates the tables

app()->container()->set(Queue::class, fn() => new Queue($driver));
```

A claim is a lease, not a deletion. PostgreSQL and MariaDB take a row lock with
`SKIP LOCKED` so two workers never pick the same job; SQLite gets a serialized
implementation of the same contract. If a worker crashes mid-job, the lease expires and the
work becomes available again on its own — nobody has to clean up after it. Fenced tokens
make the late acknowledgement of a crashed worker bounce instead of marking finished work
that somebody else has since redone.

Two rules follow from that, and both are easy to get wrong:

!!! warning "Claim outside a transaction, finish inside the lease"
    Enqueueing takes part in a caller transaction, so queueing a job and writing the row it
    refers to commit together. **Claiming** must happen outside one. And a job has to finish
    within its lease or call renew — otherwise the lease expires while the job is still
    running and a second worker starts the same work. Delivery is at least once, so make the
    job itself tolerate being run twice.

`queue:consume` handles all of this and acknowledges only after the job succeeded. If you
write your own consumer around `dequeue()`, acknowledging the reservation you were given is
your job. Setting `queue:heartbeat_file` in the configuration has the worker record that it
is polling, which is what a health check can look at.

## Waits for naf/schedule v0.2.3 → `pages/scheduling.md`

Insert after the ticker options table in `## Running the ticker`.

---

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

## Waits for naf/schedule v0.2.3 → `pages/scheduling.md`

Append to `## Not running the same minute twice`.

---

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

## Waits for naf/database v0.2.2 → `pages/database.md`

Insert before `## Configuration`.

---

### Migrations and transactions

Migrations run in the order every registered path agrees on, are tracked by class name, and
roll back in the reverse of the order they were applied.

How much of that is transactional depends on the engine, and the difference matters when one
fails halfway:

| Engine | Behaviour |
|---|---|
| PostgreSQL, SQLite | schema changes and the tracking happen in one transaction — a failure leaves nothing behind |
| MySQL, MariaDB | DDL commits implicitly, so a failed migration can leave part of its work applied |

Write MySQL migrations so that running them again after a failure is safe. There is no
transaction to undo the statements that already committed.

!!! warning "Do not run migrations inside your own transaction"
    The runner manages its own, and nesting one inside an application transaction leaves the
    tracking and the schema able to disagree with each other.

