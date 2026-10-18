import pytest
from fastapi.testclient import TestClient

from app.decisions import assess
from app.engine import EvaluationRequest
from app.lab import LabRequest, run_lab
from app.main import create_app
from app.prediction import load_model
from app.store import Conflict, Store
from test_domain import event


def test_event_provenance_links_affected_live_results(tmp_path):
    store = Store(tmp_path/'trace.db')
    request = EvaluationRequest(paths=10)
    state = store.schedule(request.model_dump())
    old = assess(state, request, load_model())
    store.save_evaluation(old.model_dump(mode='json'), request.model_dump())
    store.accept(event('RECEIVABLE_DELAYED', receivable_id='customer', expected_date='2026-10-26'))
    detail = store.notifications()[-1]['detail']
    assert detail['affected_evaluation_ids'] == [old.id]
    assert detail['recalculation_scheduled'] is True
    assert detail['state_version'] == 1


def test_experiment_cannot_complete_live_job_or_replace_current_and_stale_save_rejected(tmp_path):
    store = Store(tmp_path/'jobs.db')
    model = load_model()
    request = EvaluationRequest(paths=10)
    original = store.state()
    live = assess(original, request, model)
    store.save_evaluation(live.model_dump(mode='json'), request.model_dump())
    store.schedule(request.model_dump())
    experiment = run_lab(original, LabRequest(simulation=request), model).modified
    store.save_experiment(experiment.model_dump(mode='json'), request.model_dump())
    assert store.pending() is not None
    assert store.overview_snapshot()[1]['id'] == live.id
    store.accept(event('RECEIVABLE_DELAYED', receivable_id='customer', expected_date='2026-10-26'))
    with pytest.raises(Conflict):
        store.save_experiment(experiment.model_dump(mode='json'), request.model_dump())
    newer = assess(store.state(), request, model)
    store.save_evaluation(newer.model_dump(mode='json'), request.model_dump())
    older = assess(original, request, model)
    store.save_evaluation(older.model_dump(mode='json'), request.model_dump())
    assert store.overview_snapshot()[1]['id'] == newer.id
    assert store.decision(older.id)['state_version'] == 0


def test_stale_lab_anchor_conflict_and_missing_model_rule_remains_available(tmp_path):
    with TestClient(create_app(str(tmp_path/'api.db'))) as client:
        client.app.state.model = None
        body = {'simulation': {'paths': 10}}
        lab = client.post('/api/lab/evaluate?expected_generation=1&expected_version=0', json=body).json()
        assert lab['modified']['decision_evidence']['model_gate']['status'] == 'UNAVAILABLE'
        assert lab['modified']['recommendation'] == 'partial'
        assert lab['modified']['metadata']['scenario_basis'] == 'prescribed_stress'
        change = event('RECEIVABLE_DELAYED', receivable_id='customer', expected_date='2026-10-26').model_dump(mode='json')
        assert client.post('/api/events', json=change).status_code == 201
        body['source_state_digest'] = lab['source_state_digest']
        assert client.post('/api/lab/save?expected_generation=1&expected_version=1', json=body).status_code == 409
        assert client.get('/api/decisions').json()['items'] == []
