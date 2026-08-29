from digest_service import PaymentEvent, digest_for


def test_digest_excludes_high_risk_payment_and_keeps_audit_ids():
    events = [
        PaymentEvent("ok-1", "Acme", 1200, 0.20),
        PaymentEvent("review-1", "Risky Shop", 8000, 0.70),
    ]
    assert digest_for(events) == {
        "event_count": 1,
        "total_cents": 1200,
        "event_ids": ["ok-1"],
        "excluded_high_risk": 1,
    }
