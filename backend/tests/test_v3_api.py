import json

from fastapi.testclient import TestClient

from app.main import create_app


def test_lab_is_ephemeral_and_saved_experiment_never_becomes_live(tmp_path):
    with TestClient(create_app(str(tmp_path/'v3.db'))) as client:
        initial = client.get('/api/overview').json()['state']
        token = '?expected_generation=1&expected_version=0'
        body = {'changes': {'receipt_delay_days': 5, 'unexpected_expense_paise': 1000001},
                'simulation': {'paths': 30, 'horizon_days': 7, 'include_robustness': True}}
        result = client.post('/api/lab/evaluate'+token, json=body)
        assert result.status_code == 200, result.text
        lab = result.json()
        assert lab['modified']['scope'] == 'experiment'
        assert lab['modified']['recommendation'] == 'hold'
        assert lab['baseline']['recommendation'] == 'partial'
        assert client.get('/api/overview').json()['state'] == initial
        body['source_state_digest'] = lab['source_state_digest']
        saved = client.post('/api/lab/save'+token, json=body)
        assert saved.status_code == 200, saved.text
        assert saved.json()['stale']
        assert client.get('/api/overview').json()['latest_decision'] is None
        assert client.get('/api/overview').json()['state'] == initial
        assert len(client.get('/api/decisions').json()['items']) == 1


def test_model_center_primary_policy_and_preserving_recalculation(tmp_path):
    with TestClient(create_app(str(tmp_path/'evidence.db'))) as client:
        report = client.get('/api/model/evidence')
        assert report.status_code == 200
        assert report.json()['benchmark_status'] == 'verified source/model provenance'
        assert not report.json()['gate']['eligible']
        decision = client.post('/api/decisions/evaluate', json={'paths': 20}).json()['evaluation']
        assert decision['decision_evidence']['primary_policy'] == 'obligation_rule'
        with client.app.state.store.connection() as connection:
            before = connection.execute('SELECT request FROM generations WHERE id=1').fetchone()[0]
        assert client.post('/api/decisions/recalculate?expected_generation=1&expected_version=0').status_code == 200
        with client.app.state.store.connection() as connection:
            assert connection.execute('SELECT request FROM generations WHERE id=1').fetchone()[0] == before
        assert json.loads(before)['paths'] == 20
