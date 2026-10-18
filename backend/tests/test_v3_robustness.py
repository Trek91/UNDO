from datetime import timedelta

from app.domain import baseline
from app.engine import EvaluationRequest
from app.prediction import load_model
from app.robustness import sensitivity
from app.scenarios import ScenarioChanges, changed_state


def test_known_probability_switch_and_reproducible_grid():
    state = baseline()
    state.receivables['customer'].expected_date = state.base_date
    request = EvaluationRequest(paths=40, horizon_days=3)
    report = sensitivity(state, request, load_model(), grids={'receipt_probability': [0, 1]})
    assert [case.recommendation for case in report.cases] == ['hold', 'full']
    assert report.tipping_points[0].lower_value == 0
    assert report.tipping_points[0].upper_value == 1
    assert report.model_dump() == sensitivity(state, request, load_model(), grids={'receipt_probability': [0, 1]}).model_dump()
    assert state.cash_paise == 10000000


def test_no_switch_and_prior_action_infeasible_are_distinct():
    state = baseline()
    state.cash_paise = 30000000
    result = sensitivity(state, EvaluationRequest(paths=20), load_model(), grids={'receipt_delay_days': [0, 3, 7]})
    assert result.stability_share == 1 and not result.tipping_points
    result = sensitivity(state, EvaluationRequest(paths=20), load_model(), grids={'proposed_amount_paise': [6000000, 40000000]})
    assert result.cases[-1].previous_action_infeasible


def test_hypothetical_changes_never_change_settled_cash_or_original_contract():
    state = baseline()
    modified = changed_state(state, ScenarioChanges(receipt_delay_days=4, unexpected_expense_paise=1000000,
        proposed_amount_paise=5000000, reserve_paise=2000000, partial_days=5))
    assert modified.receivables['customer'].expected_date == state.receivables['customer'].expected_date+timedelta(days=4)
    assert modified.cash_paise == state.cash_paise
    assert state.proposals['proposal'].amount_paise == 6000000
    assert len(state.obligations) == 2 and len(modified.obligations) == 3
