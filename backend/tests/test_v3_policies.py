from app.domain import baseline
from app.engine import EvaluationRequest
from app.policies import compare_policies
from app.prediction import load_model


def test_policies_use_same_realized_futures_and_stronger_rule():
    state = baseline()
    request = EvaluationRequest(paths=2)
    report = compare_policies(state, request, load_model(), paths=[{'customer': None}, {'customer': 0}])
    policies = {row.id: row for row in report.policies}
    assert policies['balance_only'].action_id == 'full'
    assert policies['obligation_rule'].action_id == 'partial'
    assert policies['stress'].action_id == 'hold'
    assert policies['balance_only'].metrics.expected_shortfall_paise == 500000
    assert policies['obligation_rule'].metrics.expected_shortfall_paise == 0
    assert all(row.scenario_digest == report.scenario_digest for row in report.policies)
    assert state.cash_paise == 10000000


def test_rule_and_ml_tie_at_high_cash_without_manufactured_uplift():
    state = baseline()
    state.cash_paise = 30000000
    report = compare_policies(state, EvaluationRequest(paths=20), load_model())
    assert report.conclusion == 'no_difference'
    assert {row.action_id for row in report.policies} == {'full'}


def test_missing_model_is_explicit_but_deterministic_policy_remains_available():
    report = compare_policies(baseline(), EvaluationRequest(paths=10), None)
    policies = {row.id: row for row in report.policies}
    assert policies['ml_informed'].status == 'unavailable'
    assert policies['obligation_rule'].status == 'ready'
    assert report.conclusion == 'insufficient_evidence'
