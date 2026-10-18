from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.domain import EventAdapter, apply_event, baseline, money, replay


def event(kind, **fields):
    return EventAdapter.validate_python(dict(
        event_id="test-event", type=kind, business_id="demo",
        timestamp="2026-10-17T08:00:00Z", **fields,
    ))


def test_money_exact_and_rounding():
    assert money("0.10") + money("0.20") == 30
    assert money("12.345") == 1234
    assert money("12.355") == 1236


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-1", "1000000000000"])
def test_invalid_money(value):
    with pytest.raises(ValueError):
        money(value)


def test_baseline_and_proposal_do_not_change_cash():
    state = baseline()
    assert state.cash_paise == 10000000
    changed = apply_event(state, event("PAYMENT_PROPOSED", proposal={
        "id": "new-proposal", "obligation_id": "supplier", "amount_paise": 5000000,
    }))
    assert changed.cash_paise == state.cash_paise
    assert changed.receivables["customer"].received_paise == 0


def test_receipt_and_payment_settle_once():
    state = apply_event(baseline(), event("RECEIVABLE_RECEIVED", receivable_id="customer", amount_paise=4000000))
    assert state.cash_paise == 14000000
    assert state.receivables["customer"].status == "settled"
    payment = event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=6000000)
    paid = apply_event(state, payment)
    assert paid.cash_paise == 8000000
    assert paid.obligations["supplier"].outstanding_paise == 0
    with pytest.raises(ValueError, match="outstanding"):
        apply_event(paid, payment)


def test_recorded_expense_is_obligation_not_settlement():
    state = apply_event(baseline(), event("EXPENSE_RECORDED", obligation={
        "id": "repair", "label": "Repair", "amount_paise": 1000000,
        "due_date": "2026-10-17", "mandatory": True,
    }))
    assert state.cash_paise == 10000000
    assert state.obligations["repair"].outstanding_paise == 1000000


def test_delay_changes_expectation_not_money():
    state = apply_event(baseline(), event("RECEIVABLE_DELAYED", receivable_id="customer", expected_date="2026-10-22"))
    assert state.cash_paise == 10000000
    assert state.receivables["customer"].expected_date.isoformat() == "2026-10-22"


@pytest.mark.parametrize("amount", [0, -1, 1.5, True, "100", 100000000000000])
def test_strict_amount_validation(amount):
    with pytest.raises(ValidationError):
        event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=amount)


@pytest.mark.parametrize("timestamp", ["2026-10-17T08:00:00", "not-a-date"])
def test_timestamp_requires_timezone(timestamp):
    with pytest.raises(ValidationError):
        EventAdapter.validate_python(dict(event_id="x", business_id="demo", type="PAYMENT_CONFIRMED",
                                         obligation_id="supplier", amount_paise=1, timestamp=timestamp))


def test_unaffordable_and_unknown_and_extra_fields():
    state = baseline()
    state.cash_paise = 1
    with pytest.raises(ValueError, match="cash"):
        apply_event(state, event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=2))
    with pytest.raises(ValueError, match="Unknown"):
        apply_event(state, event("RECEIVABLE_RECEIVED", receivable_id="absent", amount_paise=2))
    with pytest.raises(ValidationError):
        event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=2, bypass=True)


def test_event_copy_and_business_and_date_invariants():
    state = baseline()
    changed = apply_event(state, event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=100))
    assert state.cash_paise == 10000000
    assert changed.cash_paise == 9999900
    bad = event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=100)
    bad.business_id = "other"
    with pytest.raises(ValueError, match="business"):
        apply_event(state, bad)
    bad.business_id = "demo"
    bad.timestamp = datetime(2020, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="baseline"):
        apply_event(state, bad)


def test_obligation_update_cannot_erase_paid_amount():
    state = apply_event(baseline(), event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=3000000))
    with pytest.raises(ValueError, match="paid"):
        apply_event(state, event("OBLIGATION_UPDATED", obligation_id="supplier", amount_paise=2000000))


def test_replay_deduplicates_and_detects_conflicting_identity():
    item = event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=100)
    result = replay(baseline(), [item, item])
    assert result.version == 1
    assert result.cash_paise == 9999900
    conflicting = item.model_copy(update={"amount_paise": 200})
    with pytest.raises(ValueError, match="conflict"):
        replay(baseline(), [item, conflicting])


def test_business_midnight_is_indian_time_not_utc_midnight():
    item = event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=100)
    item.timestamp = datetime(2026, 10, 16, 20, tzinfo=timezone.utc)
    assert apply_event(baseline(), item).cash_paise == 9999900


def test_settlements_reduce_pending_proposal_and_close_it_when_paid():
    paid = apply_event(baseline(), event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=3000000))
    assert paid.proposals["proposal"].amount_paise == 3000000
    paid = apply_event(paid, event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=3000000))
    assert paid.proposals == {}
