# Delayed queue jobs

Draft for `naf/queue` 0.2.5. Keep this outside `pages/` until the maintainer merges and releases the package and Packagist serves its tagged commit. After release, add the task guidance to `pages/queues.md` and refresh generated references.

## Persist a job for later

A driver implementing `Naf\Queue\Drivers\DelayedQueueDriverInterface` supports delayed jobs. The PDO driver implements this optional interface. Existing file, legacy SQLite and channel drivers retain their current behavior and do not advertise this capability.

After host boot, with `Queue::class` bound to a configured PDO driver:

```php
use App\Jobs\CheckUnansweredMessage;
use function Naf\Queue\queue;

queue()->pushAfter(30, CheckUnansweredMessage::class, [
    'messageId' => $messageId,
    '_job_id' => 'unanswered:' . $messageId,
]);
```

`CheckUnansweredMessage` is an application-owned `QueueJobInterface` job. The application must validate current access, whether someone answered and whether the feature is still enabled when the job executes, including after slow work. The queue controls eligibility, not business cancellation or message semantics.

`pushAfter(int $delaySeconds, string $class, array $payload = []): void` persists the job immediately and makes it eligible after the non-negative delay. Zero is valid. Negative delays or timestamp overflow throw `InvalidArgumentException`. A driver without `DelayedQueueDriverInterface` throws `LogicException`; it does not execute immediately or sleep in the worker.

`DelayedQueueDriverInterface` extends `QueueDriverInterface` and adds `enqueueAt(string $class, array $payload, int $availableAt): void`. It accepts a non-negative Unix timestamp; a past timestamp is immediately eligible. The PDO driver uses its existing `available_at` column, so no schema migration is needed. Ordinary `enqueue()` and `Queue::push()` remain immediately eligible.

Delayed enqueue participates in the caller's PDO transaction. Rolling it back removes the job as well. `_job_id` coalescing retains the first pending job and its original due time; another enqueue with the same class/ID does not reschedule it. Other ready work can run while a delayed job waits. Normal leases, acknowledgements, failure retries and manual deadletter recovery remain in force. The due time is the earliest reservation time, not a completion deadline: worker load and job execution can delay the result.

## Combine one-off delays and recurring checks

Use delayed jobs for individual events such as a 30-second unanswered greeting. Use the existing `naf/schedule` ticker and `ScheduledJobInterface` for minutely sweeps, maintenance or recurring notification checks. A sweep can find durable application records that became due while a process was stopped and enqueue their identifiers. Keep those domain records outside queue storage; do not write `naf_queue_jobs` from application code.

An application that still supports older published queue releases can detect the optional driver interface and use its existing minutely sweep when it is absent. This gives minute resolution instead of a precise short delay without requiring an unpublished production dependency.

## Verification before publication

Package tests cover rollback, coalescing, delayed versus immediate reservation, retry, unsupported drivers and invalid delays. The real `QueueConsumeCommand` skips an ineligible job and executes/acknowledges it once due. NAF Chat integration tests additionally cover its normal locked published-driver path and an isolated source-loader override for this optional API. No installed vendor files or production locks are changed by that override.
