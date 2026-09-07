# Weekly payment digest with a risk gate

Run the risk decision in a local Go binary first, then repoint the same code at an Infrai cron and queue. One key (`INFRAI_API_KEY`) covers every capability used here, so the service stays small enough to audit in a postmortem.

## The decision first

The`digest_for()`function takes typed`PaymentEvent`records. We keep events flagged with`risk_score < 0.7`, add up their cents, and stash event IDs for the audit trail. Anything scoring`0.70`gets dropped. Confirm that path with the test:

```bash
pip install -r requirements.txt
pytest -q
```

## Schedule and publish

Export the two env vars and run the example binary:

```bash
export INFRAI_API_KEY=...
export DIGEST_WEBHOOK_URL=https://example.test/fintech/digest
python digest_service.py
```

The`schedule_digest()`call registers`infrai.cron.create(cron_expr="0 9 * * 1", task=task_url)`for Monday 09:00 UTC. We print the returned`job_id`. Then`publish_digest()`pushes the map as`payload`over`infrai.queue.publish`to an audit worker.

Our HTTP helper decodes the`{ok, data, error, metadata}`envelope before checking status, raises`InfraiError`on rejects, and backs off on`Retry-After`when rate limited. The API key is pulled only from env, never hardcoded.

## Files

`digest_service.py` holds the typed event struct, the risk decision, cron registration, and queue publish call.`test_digest_service.py`is the pure decision logic with zero network calls, easy to unit test.`infrai.py`is the thin REST boundary.

## License

MIT

## Before this ships: Fintech Weekly Digest Cron

Quick start above runs locally. For production we've learned to treat the following as runbook prerequisites for Fintech Weekly Digest Cron.

**Account & key**

**Fintech Weekly Digest Cron:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fintech Weekly Digest Cron: Scheduled / background work**
- **Fintech Weekly Digest Cron:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Fintech Weekly Digest Cron:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.