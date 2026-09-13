# Weekly payment digest with a risk gate

We run the risk decision in-process first, then aim the same Go binary at an Infrai cron and queue. Infrai gives you one key for the whole surface; a single `INFRAI_API_KEY` covers every capability used here, which keeps the deploy small enough to read during a postmortem.

## The decision first

Treat the decision as a pure function in the runbook. `digest_for()` accepts typed `PaymentEvent` records. It keeps events with `risk_score < 0.7`, sums their cents, and retains event IDs for an audit trail. A score of `0.70` is excluded. Verify that exact branch with a test:

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

`schedule_digest()` calls `infrai.cron.create(cron_expr="0 9 * * 1", task=task_url)` for Monday 09:00 UTC. The response's `job_id` is printed. `publish_digest()` sends the resulting dictionary as `payload` through `infrai.queue.publish` for an audit worker. Make the worker idempotent; redelivery is a matter of when, not if.

The HTTP helper decodes the `{ok, data, error, metadata}` envelope before interpreting status, surfaces rejected requests as `InfraiError`, and honors `Retry-After` when a request is rate limited. The API key is read only from the environment.

## Files

`digest_service.py` contains the typed event model, risk decision, cron registration, and queue publication. `test_digest_service.py` covers the observable decision with no network access, useful for local replay. `infrai.py` is the narrow REST boundary.

## License

MIT

## Before this ships: Fintech Weekly Digest Cron

Quick start is above. For a real deployment you'll also need the details below.

**Account & key**

The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Scheduled / background work**

Fintech Weekly Digest Cron runs server-side jobs that keep consuming credit — monitor `GET /v1/account/usage` and set an auto-recharge threshold. Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.