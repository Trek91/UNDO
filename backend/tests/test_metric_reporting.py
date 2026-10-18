import json

import pytest
from fastapi.testclient import TestClient

from app.decisions import assess
from app.engine import EvaluationRequest
from app.main import create_app
from app.prediction import load_model


@pytest.mark.parametrize('counts,values,status', [
    ({'true_positives': 0, 'false_positives': 0, 'false_negatives': 94}, [None, 0, 0], 'undefined'),
    ({'true_positives': 2, 'false_positives': 1, 'false_negatives': 3}, [2/3, 2/5, .5], 'defined'),
    ({'true_positives': 0, 'false_positives': 2, 'false_negatives': 0}, [0, None, 0], 'defined'),
    ({'true_positives': 0, 'false_positives': 0, 'false_negatives': 0}, [None, None, None], 'undefined'),
    ({}, [None, None, None], 'unverified'),
])
def test_historical_api_presentation_uses_denominators_and_preserves_raw_rows(tmp_path, counts, values, status):
    with TestClient(create_app(str(tmp_path/'metrics.db'))) as client:
        request = EvaluationRequest(paths=10)
        result = assess(client.app.state.store.state(), request, load_model()).model_dump(mode='json')
        result['metadata']['model_metrics'] = {'precision': 0, 'recall': 0, 'f1': 0, **counts}
        store = client.app.state.store
        store.save_evaluation(result, request.model_dump())
        with store.connection() as connection:
            before = connection.execute('SELECT result FROM evaluations WHERE id=?', (result['id'],)).fetchone()[0]
            audits = list(connection.execute('SELECT * FROM audit'))
        body = client.get('/api/decisions/'+result['id']).json()
        report = body['model_statistics']
        assert report['precision']['status'] == status
        for key, value in zip(['precision', 'recall', 'f1'], values):
            assert report[key]['value'] == value
            assert report[key]['defined'] == (value is not None)
        assert body['evaluation']['metadata']['model_metrics'] == json.loads(before)['metadata']['model_metrics']
        with store.connection() as connection:
            assert connection.execute('SELECT result FROM evaluations WHERE id=?', (result['id'],)).fetchone()[0] == before
            assert list(connection.execute('SELECT * FROM audit')) == audits


def test_model_center_and_evaluation_share_the_same_authoritative_representation(tmp_path):
    with TestClient(create_app(str(tmp_path/'shared.db'))) as client:
        current = client.post('/api/decisions/evaluate', json={'paths': 10}).json()
        center = client.get('/api/model/evidence').json()
        assert current['model_statistics'] == center['daily']['classification']
        assert center['daily']['classification']['precision']['reason'] == 'no positive predictions (0 predicted positives)'
