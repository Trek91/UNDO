"""Audit regressions: independent edge cases, always on isolated state/databases."""
from dataclasses import replace
from datetime import timedelta
from fractions import Fraction

import pytest

from app.domain import Obligation, apply_event, baseline
from app.engine import EvaluationRequest, candidates, evaluate, simulate
from app.prediction import load_model
from app.store import Conflict, Store
from test_domain import event


def test_immediate_plan_respects_prior_mandatory_deadlines():
    state = baseline()
    state.obligations['operations'].due_date = state.base_date
    full, partial, *_ = candidates(state, EvaluationRequest())
    assert not full.valid
    assert partial.valid


def test_overdue_contract_does_not_restart_extension_clock():
    state = baseline()
    state.obligations['supplier'].due_date -= timedelta(days=1)
    _, partial, defer, _ = candidates(state, EvaluationRequest())
    assert partial.payments[-1][0] == 2
    assert defer.payments[0][0] == 2
    state.cash_paise = 20000000
    assert simulate(state, partial, [{'customer': None}], 7).expected_penalty_paise == 200000


def test_overdue_extension_in_past_is_not_a_valid_schedule():
    state = baseline()
    state.obligations['supplier'].due_date -= timedelta(days=10)
    _, partial, defer, _ = candidates(state, EvaluationRequest())
    assert not partial.valid and not defer.valid


def test_late_mandatory_target_is_counted_even_with_available_cash():
    state = baseline()
    state.cash_paise = 20000000
    state.obligations['supplier'].mandatory = True
    hold = candidates(state, EvaluationRequest())[3]
    result = simulate(state, hold, [{'customer': None}], 7)
    assert result.expected_shortfall_paise == 6000000
    assert result.shortfall_probability == 1
    assert result.cash_deficit_probability == 0


def test_same_day_cure_does_not_erase_other_supplier_late_fee():
    state = baseline()
    state.obligations['operations'].due_date = state.base_date+timedelta(days=1)
    state.obligations['operations'].terms = state.obligations['supplier'].terms.model_copy()
    result = simulate(state, candidates(state, EvaluationRequest())[0], [{'customer': 1}], 7)
    assert result.expected_penalty_paise == 200000
    assert result.daily_paise[-1] == 2800000


def test_last_day_deadline_carries_incurred_fee_beyond_horizon():
    state = baseline()
    partial = candidates(state, EvaluationRequest(horizon_days=3))[1]
    result = simulate(state, partial, [{'customer': None}], 3)
    assert result.expected_penalty_paise == 200000
    assert result.daily_paise[-1] == -1200000


@pytest.mark.parametrize('weights', [(), (1.0,)*5, (float('inf'),)*6])
def test_malformed_model_cannot_rank(weights):
    result = evaluate(baseline(), EvaluationRequest(paths=2), replace(load_model(), weights=weights))
    assert result.status == 'unavailable'
    assert result.recommendation is None


def test_retry_after_reset_does_not_apply_to_new_generation(tmp_path):
    store = Store(tmp_path/'retry.db')
    item = event('PAYMENT_CONFIRMED', obligation_id='supplier', amount_paise=100)
    original = store.accept(item)
    store.reset()
    retried = store.accept(item)
    assert retried['duplicate']
    assert retried['generation'] == original['generation']
    assert store.state().cash_paise == 10000000
    assert not store.events()


def test_duplicate_returns_original_acceptance_version(tmp_path):
    store = Store(tmp_path/'receipt.db')
    first = event('PAYMENT_CONFIRMED', obligation_id='supplier', amount_paise=100)
    store.accept(first)
    store.accept(first.model_copy(update={'event_id': 'second'}))
    assert store.accept(first)['state_version'] == 1


def test_stale_generation_mutation_is_rejected(tmp_path):
    store = Store(tmp_path/'stale.db')
    store.reset()
    with pytest.raises(Conflict):
        store.accept(event('PAYMENT_CONFIRMED', obligation_id='supplier', amount_paise=100),
                     expected_version=0, expected_generation=1)
    assert store.state().version == 0
    with pytest.raises(Conflict):
        store.reset(expected_generation=1, expected_version=0)
    assert store.state().generation == 2


def test_future_invoice_cannot_be_recorded_before_creation():
    state = baseline()
    invoice = state.receivables['customer'].model_copy(update={
        'id': 'future', 'created_date': state.base_date+timedelta(days=1),
        'expected_date': state.base_date+timedelta(days=2)})
    with pytest.raises(ValueError, match='creation'):
        apply_event(state, event('RECEIVABLE_CREATED', receivable=invoice.model_dump(mode='json')))


def test_money_averages_do_not_round_through_binary_float():
    state = baseline()
    for i in range(100):
        state.obligations[f'large{i}'] = Obligation(id=f'large{i}', label='Large',
            amount_paise=100000000000, due_date=state.base_date+timedelta(days=1))
    state.receivables['customer'].amount_paise = 1
    action = candidates(state, EvaluationRequest())[0]
    none = simulate(state, action, [{'customer': None}], 1).daily_paise[-1]
    one = simulate(state, action, [{'customer': 1}], 1).daily_paise[-1]
    scenarios = [{'customer': 1}]*2501+[{'customer': None}]*2499
    result = simulate(state, action, scenarios, 1)
    assert result.daily_paise[-1] == round(Fraction(one*2501+none*2499, 5000))


def test_history_cursor_preserves_equal_timestamp_records(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import create_app
    monkeypatch.setattr('app.store.now', lambda: '2026-10-17T10:00:00+00:00')
    with TestClient(create_app(str(tmp_path/'history.db'))) as client:
        ids = {client.post('/api/decisions/evaluate', json={'paths': 1}).json()['evaluation']['id']
               for _ in range(3)}
        seen = set()
        cursor = None
        for _ in range(4):
            page = client.get('/api/decisions', params={'limit': 1, **({'before': cursor} if cursor else {})}).json()
            seen.update(row['evaluation']['id'] for row in page['items'])
            cursor = page['next_before']
            if not cursor:
                break
        assert seen == ids


def test_http_stale_generation_guards_all_mutations(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import create_app
    with TestClient(create_app(str(tmp_path/'guards.db'))) as client:
        client.post('/api/demo/reset')
        token = '?expected_generation=1&expected_version=0'
        for endpoint, body in [('/events', event('PAYMENT_CONFIRMED', obligation_id='supplier', amount_paise=100).model_dump(mode='json')),
                               ('/demo/reset', None), ('/demo/scenario', {}),
                               ('/decisions/evaluate', {'paths': 1}), ('/demo/events/next', None)]:
            assert client.post('/api'+endpoint+token, json=body).status_code == 409, endpoint
        assert client.get('/api/overview').json()['state']['version'] == 0
        assert client.get('/api/overview').json()['state']['generation'] == 2


def test_metrics_publish_class_counts_and_undefined_precision():
    from app.prediction import probability_metrics
    result = probability_metrics([0, 1, 0], [0.1, 0.2, 0.3])
    assert result['positive_labels'] == 1
    assert result['predicted_positives'] == 0
    assert result['precision_defined'] == 0
    assert result['true_negatives'] == 2
    assert result['false_negatives'] == 1


def test_invalid_model_is_unavailable_even_without_forecasts():
    state = baseline()
    state.receivables = {}
    result = evaluate(state, EvaluationRequest(paths=1), replace(load_model(), weights=()))
    assert result.status == 'unavailable'


def test_legacy_evaluation_keeps_honest_engine_provenance(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import create_app
    with TestClient(create_app(str(tmp_path/'legacy.db'))) as client:
        raw = evaluate(baseline(), EvaluationRequest(paths=1)).model_dump(mode='json')
        from app.engine import ENGINE_VERSION
        assert raw['metadata']['engine_version'] == ENGINE_VERSION
        raw['metadata'].pop('engine_version')
        client.app.state.store.save_evaluation(raw, raw['request'])
        record = client.get('/api/decisions/'+raw['id']).json()
        assert record['stale']
        assert record['evaluation']['metadata']['engine_version'] == 'legacy-unversioned'


def test_durable_worker_failure_is_visible_and_recovers(tmp_path, monkeypatch):
    import time
    from fastapi.testclient import TestClient
    from app.main import create_app
    actual = evaluate
    failures = []

    def fail_once(*args, **kwargs):
        if not failures:
            failures.append(True)
            raise RuntimeError('Isolated transient model failure')
        return actual(*args, **kwargs)

    monkeypatch.setattr('app.main.evaluate', fail_once)
    with TestClient(create_app(str(tmp_path/'worker-retry.db'))) as client:
        client.app.state.store.schedule({'paths': 1})
        deadline = time.monotonic()+3
        while not client.get('/api/overview').json()['worker_error'] and time.monotonic() < deadline:
            time.sleep(0.03)
        assert client.get('/api/overview').json()['worker_error']
        assert client.get('/api/health').json()['status'] == 'degraded'
        assert client.app.state.store.pending() is not None
        deadline = time.monotonic()+8
        while client.app.state.store.pending() is not None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert client.app.state.store.pending() is None
        assert client.get('/api/health').json()['status'] == 'ok'
        assert client.get('/api/overview').json()['state']['cash_paise'] == 10000000


def test_shared_scenarios_match_hazard_cumulative_probability():
    import math
    from app.engine import draw_scenarios
    state = baseline()
    model = load_model()
    request = EvaluationRequest(paths=5000)
    draws = draw_scenarios(state, request, model)
    probability = 1-math.prod(1-model.hazard(state.receivables['customer'], state.base_date, day) for day in range(8))
    observed = sum(row['customer'] is not None for row in draws)/len(draws)
    assert abs(observed-probability) < 5*math.sqrt(probability*(1-probability)/len(draws))
    assert draw_scenarios(state, request, model) == draws


def test_http_waits_for_one_coarse_clock_tick_without_accepting_future_settlements(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from fastapi.testclient import TestClient
    from app.main import create_app
    clock = [datetime.now(timezone.utc)]
    waited = []

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return clock[0]

    def sleep_tick(seconds):
        waited.append(seconds)
        clock[0] += timedelta(seconds=seconds)

    monkeypatch.setattr('app.domain.datetime', Clock)
    monkeypatch.setattr('app.main.datetime', Clock, raising=False)
    monkeypatch.setattr('app.main.time.get_clock_info', lambda _: SimpleNamespace(resolution=0.03))
    monkeypatch.setattr('app.main.time.sleep', sleep_tick)
    with TestClient(create_app(str(tmp_path/'clock.db'))) as client:
        item = event('PAYMENT_CONFIRMED', obligation_id='supplier', amount_paise=100).model_dump(mode='json')
        item['timestamp'] = (clock[0]+timedelta(milliseconds=10)).isoformat()
        response = client.post('/api/events', json=item)
        assert response.status_code == 201, response.text
        assert waited == [0.03]
        item.update(event_id='actual-future', timestamp=(clock[0]+timedelta(seconds=1)).isoformat())
        assert client.post('/api/events', json=item).status_code == 422
        assert waited == [0.03]
        assert client.app.state.store.state().cash_paise == 9999900
