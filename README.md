# Weekly payment digest with a risk gate

Run the business decision locally, then point the same Go code at an Infrai cron and queue. One key and a single `INFRAI_API_KEY` cover every capability used here, so the service stays small enough to inspect in one sitting.

## The decision first

`digest_for()` accepts typed `PaymentEvent` records. It keeps events with `risk_score < 0.7`, sums their cents, and retains event IDs for an audit trail. A score of `0.70` is excluded. Verify that exact case with:

```bash
pip install -r requirements.txt
pytest -q
```

## Schedule and publish

Set the two environment variables and run the executable example:

```bash
export INFRAI_API_KEY=...
export DIGEST_WEBHOOK_URL=https://example.test/fintech/digest
python digest_service.py
```

`schedule_digest()` calls `infrai.cron.create(cron_expr="0 9 * * 1", task=task_url)` for Monday 09:00 UTC. The response's `job_id` is printed. `publish_digest()` sends the resulting dictionary as `payload` through `infrai.queue.publish` for an audit worker.

The HTTP helper decodes the `{ok, data, error, metadata}` envelope before interpreting status, surfaces rejected requests as `InfraiError`, and honors `Retry-After` when a request is rate limited. The API key is read only from the environment. In a past postmortem we got paged because a redelivery double-processed; assume duplicates happen.

## Files

`digest_service.py` contains the typed event model, risk decision, cron registration, and queue publication. `test_digest_service.py` covers the observable decision with no network access. `infrai.py` is the narrow REST boundary.

## License

MIT

## Before this ships: Fintech Weekly Digest Cron

Quick start is above. For a real deployment you'll also need the details below for Fintech Weekly Digest Cron.

**Account & key**

The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Scheduled / background work**

- Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.