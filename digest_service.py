"""Schedule a risk-filtered weekly payment digest."""

import os
from dataclasses import dataclass

import infrai


@dataclass(frozen=True)
class PaymentEvent:
    event_id: str
    merchant: str
    amount_cents: int
    risk_score: float


def digest_for(events: list[PaymentEvent]) -> dict:
    """Return an audit-friendly digest, excluding events at or above the risk threshold."""
    included = [event for event in events if event.risk_score < 0.7]
    return {
        "event_count": len(included),
        "total_cents": sum(event.amount_cents for event in included),
        "event_ids": [event.event_id for event in included],
        "excluded_high_risk": len(events) - len(included),
    }


def schedule_digest() -> str:
    """Register the Monday digest webhook and return its job id."""
    task_url = os.environ["DIGEST_WEBHOOK_URL"]
    job = infrai.cron.create(cron_expr="0 9 * * 1", task=task_url)
    return str(job["job_id"])


def publish_digest(events: list[PaymentEvent]) -> dict:
    """Publish the computed digest for an audit worker."""
    return infrai.queue.publish(payload=digest_for(events))


if __name__ == "__main__":
    sample = [PaymentEvent("evt_100", "Northwind", 12500, 0.12), PaymentEvent("evt_101", "Unknown", 9900, 0.91)]
    print("digest:", digest_for(sample))
    job_id = schedule_digest()
    try:
        print("scheduled job:", job_id)
    finally:
        infrai.cron.delete(job_id)
