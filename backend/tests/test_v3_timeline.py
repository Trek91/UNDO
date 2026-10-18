from app.decisions import assess
from app.domain import baseline
from app.engine import EvaluationRequest
from app.prediction import load_model


def test_timeline_is_snapshot_evidence_and_primary_downside_is_chosen_action():
    state = baseline()
    result = assess(state, EvaluationRequest(paths=10), load_model())
    assert any(item.kind == 'mandatory' and item.amount_paise == 5000000 for item in result.timeline)
    assert any(item.kind == 'uncertain_receipt' for item in result.timeline)
    assert state.cash_paise == 10000000
    assert 'conditional' in result.explanation.downside.lower()
    assert result.explanation.alternative_id != result.recommendation
    assert 'leading experimental alternative' in result.explanation.reason
    assert 'rule order' in result.explanation.reason


def test_primary_explains_why_unbudgeted_full_alternative_is_lower():
    result = assess(baseline(), EvaluationRequest(paths=10, action_ids=['full', 'partial']), load_model())
    assert result.recommendation == 'partial'
    assert result.explanation.alternative_id == 'full'
    assert 'reserved for known mandatory' in result.explanation.reason
