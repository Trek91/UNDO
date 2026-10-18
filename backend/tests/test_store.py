import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.store import Conflict, Store
from test_domain import event


def test_seed_restart_and_idempotency(tmp_path):
    path = tmp_path / "ledger.db"
    store = Store(path)
    item = event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=100)
    result = store.accept(item)
    assert not result["duplicate"]
    assert store.accept(item)["duplicate"]
    reopened = Store(path)
    assert reopened.state().cash_paise == 9999900
    assert len(reopened.events()) == 1
    assert reopened.state().version == 1
    with pytest.raises(Conflict):
        store.accept(item.model_copy(update={"amount_paise": 200}))


def test_invalid_event_rolls_back_and_version_conflicts(tmp_path):
    store = Store(tmp_path / "ledger.db")
    item = event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=7000000)
    with pytest.raises(ValueError):
        store.accept(item)
    assert store.state().version == 0
    assert not store.events()
    with pytest.raises(Conflict):
        store.accept(event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=100), expected_version=2)


def test_database_failure_is_atomic(tmp_path):
    path = tmp_path / "ledger.db"
    store = Store(path)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TRIGGER fail_update BEFORE UPDATE ON generations BEGIN SELECT RAISE(ABORT, 'disk simulation'); END")
    with pytest.raises(sqlite3.DatabaseError):
        store.accept(event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=100))
    assert not store.events()
    assert not store.notifications()
    assert store.state().cash_paise == 10000000


def test_historical_replay_rejects_invalid_earlier_dependency(tmp_path):
    store = Store(tmp_path / "ledger.db")
    # Payment of 110k is valid only after this actual incoming settlement.
    store.accept(event("RECEIVABLE_RECEIVED", receivable_id="customer", amount_paise=4000000))
    store.accept(event("OBLIGATION_UPDATED", obligation_id="supplier", amount_paise=12000000).model_copy(
        update={"event_id": "increase"}))
    store.accept(event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=11000000).model_copy(
        update={"event_id": "payment"}))
    previous = store.state().model_dump()
    # Same receipt moved to an earlier time is safe and recomputes all accepted events.
    delay = event("RECEIVABLE_DELAYED", receivable_id="customer", expected_date="2026-10-23")
    delay.timestamp = delay.timestamp.replace(hour=7)
    store.accept(delay.model_copy(update={"event_id": "historical"}))
    assert store.state().cash_paise == previous["cash_paise"]
    invalid = event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=10000000)
    invalid.timestamp = invalid.timestamp.replace(hour=6)
    with pytest.raises(ValueError):
        store.accept(invalid.model_copy(update={"event_id": "invalid-history"}))
    assert store.state().version == 4


def test_concurrency_and_reset_preserves_history(tmp_path):
    store = Store(tmp_path / "ledger.db")
    item = event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=100)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: store.accept(item), range(8)))
    assert sum(not result["duplicate"] for result in results) == 1
    assert store.state().cash_paise == 9999900
    state = store.reset()
    assert state.generation == 2 and state.cash_paise == 10000000
    assert store.events() == []
    assert len(store.events(generation=1)) == 1
    assert any(row["kind"] == "DEMO_RESET" for row in store.audit())


def test_concurrent_distinct_cash_events_do_not_lose_updates(tmp_path):
    store = Store(tmp_path / "ledger.db")
    events = [event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=100).model_copy(
        update={"event_id": f"unique-{index}"}) for index in range(12)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(store.accept, events))
    assert store.state().cash_paise == 10000000-1200
    assert store.state().version == 12


def test_stale_evaluation_cannot_delete_newer_pending_work(tmp_path):
    from app.engine import EvaluationRequest, evaluate
    store = Store(tmp_path / "ledger.db")
    request = EvaluationRequest(paths=10)
    snapshot = store.schedule(request.model_dump(mode="json"))
    store.accept(event("RECEIVABLE_DELAYED", receivable_id="customer", expected_date="2026-10-25"))
    older = evaluate(snapshot, request)
    store.save_evaluation(older.model_dump(mode="json"), request.model_dump(mode="json"))
    assert store.pending()[0].version == 1
    assert store.decision(older.id)["state_version"] == 0


def test_settled_proposal_does_not_leave_an_invalid_recalculation_job(tmp_path):
    store = Store(tmp_path / "ledger.db")
    store.schedule({"proposal_id": "proposal", "paths": 10})
    store.accept(event("PAYMENT_CONFIRMED", obligation_id="supplier", amount_paise=6000000))
    assert store.pending() is None
    assert store.state().proposals == {}


def test_unknown_schema_is_preserved_not_downgraded(tmp_path):
    path = tmp_path / "future.db"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version=2")
    with pytest.raises(ValueError, match="schema version"):
        Store(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2
