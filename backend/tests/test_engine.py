import math
from datetime import timedelta

import pytest

from app.domain import baseline
from app.engine import EvaluationRequest, candidates, evaluate, simulate
from app.prediction import generate_dataset, load_model, probability_metrics, sigmoid, train


def test_dataset_training_split_and_metrics():
    assert generate_dataset(42, 30) == generate_dataset(42, 30)
    model = train(seed=42, count=120, epochs=40)
    assert not set(model.train_ids) & set(model.test_ids)
    assert model.metrics["heldout_invoices"] == 24
    assert 0 <= model.metrics["brier"] <= 1
    assert all(math.isfinite(weight) for weight in model.weights)
    assert sigmoid(-10000) == 0 and sigmoid(10000) == 1
    metric = probability_metrics([0, 1, 1, 0], [0.1, 0.9, 0.2, 0.8])
    assert metric["precision"] == metric["recall"] == metric["f1"] == 0.5
    assert metric["brier"] == pytest.approx(0.325)


def test_model_reproducibility_probability_and_input_validation():
    assert train(42, 120, 40).weights == train(42, 120, 40).weights
    model = load_model()
    receivable = baseline().receivables["customer"]
    assert 0 < model.hazard(receivable, baseline().base_date, 1) < 1
    with pytest.raises(ValueError):
        model.hazard(receivable, baseline().base_date, -1)
    with pytest.raises(ValueError):
        probability_metrics([0], [float("nan")])


def test_reproducible_shared_scenarios_and_changed_facts():
    state = baseline()
    request = EvaluationRequest(paths=100, seed=7)
    first = evaluate(state, request)
    second = evaluate(state, request)
    assert [a.model_dump() for a in first.actions] == [a.model_dump() for a in second.actions]
    assert first.recommendation == second.recommendation
    assert first.snapshot.cash_paise == state.cash_paise == 10000000
    state.receivables["customer"].expected_date += timedelta(days=12)
    changed = evaluate(state, request)
    assert changed.actions != first.actions
    assert first.metadata.scenario_digest == second.metadata.scenario_digest


def test_deterministic_no_receipt_full_payment_hand_calculation():
    state = baseline()
    action = candidates(state, EvaluationRequest())[0]
    metrics = simulate(state, action, [{"customer": None}], 7)
    assert metrics.daily_paise[:2] == [4000000, -1000000]
    assert metrics.shortfall_probability == 1
    assert metrics.expected_shortfall_paise == 1000000
    assert metrics.cash_deficit_probability == 1
    assert metrics.expected_peak_cash_deficit_paise == 1000000
    assert metrics.expected_minimum_paise == -1000000
    assert metrics.reserve_breach_probability == 1
    assert metrics.expected_penalty_paise == 0
    assert metrics.late_payment_probability == 0


def test_reserve_breach_distinct_from_deficit_and_missed_obligation():
    state = baseline()
    state.cash_paise = 11500000
    action = candidates(state, EvaluationRequest())[0]
    metrics = simulate(state, action, [{"customer": None}], 7)
    assert metrics.shortfall_probability == 0
    assert metrics.cash_deficit_probability == 0
    assert metrics.reserve_breach_probability == 1
    assert metrics.expected_peak_reserve_deficit_paise == 500000


def test_late_contract_distinct_from_liquidity_and_no_receivable_double_count():
    state = baseline()
    state.cash_paise = 20000000
    action = candidates(state, EvaluationRequest())[2]
    metrics = simulate(state, action, [{"customer": 1}], 7)
    assert metrics.late_payment_probability == 1
    assert metrics.expected_penalty_paise == 200000
    assert metrics.shortfall_probability == 0
    assert metrics.daily_paise[-1] == 12800000
    assert metrics.expected_remaining_paise == 0


def test_same_day_receipt_does_not_hide_missed_deadline():
    state = baseline()
    metrics = simulate(state, candidates(state, EvaluationRequest())[0], [{"customer": 1}], 7)
    assert metrics.daily_paise[1] == 3000000
    assert metrics.shortfall_probability == 1
    assert metrics.expected_shortfall_paise == 1000000
    assert metrics.reserve_breach_probability == 1


def test_invalid_terms_no_feasible_action_and_horizon():
    state = baseline()
    terms = state.obligations["supplier"].terms
    terms.allow_partial = False
    terms.allow_deferral = False
    result = evaluate(state, EvaluationRequest(paths=10, horizon_days=1))
    assert result.actions[1].valid is False
    assert result.actions[2].valid is False
    state.cash_paise = 0
    result = evaluate(state, EvaluationRequest(paths=10, action_ids=["full"]))
    assert result.status == "infeasible" and result.recommendation is None
    result = evaluate(baseline(), EvaluationRequest(paths=10, horizon_days=1))
    assert not result.actions[1].valid and not result.actions[2].valid


def test_hold_has_continuation_and_unchanged_contract():
    state = baseline()
    hold = candidates(state, EvaluationRequest())[3]
    assert hold.payments == [(1, 6000000)]
    metrics = simulate(state, hold, [{"customer": None}], 7)
    assert metrics.expected_penalty_paise == 200000
    assert metrics.expected_remaining_paise > 0
    assert metrics.late_payment_probability == 1


def test_model_unavailable_does_not_invent_probability():
    result = evaluate(baseline(), EvaluationRequest(paths=10), model=None)
    assert result.status == "unavailable" and result.recommendation is None
    assert all(action.metrics is None for action in result.actions)


def test_missed_split_remainder_accrues_late_fee():
    state = baseline()
    split = candidates(state, EvaluationRequest())[1]
    result = simulate(state, split, [{"customer": None}], 7)
    assert result.shortfall_probability == 0
    assert result.late_payment_probability == 1
    assert result.expected_penalty_paise == 200000
    assert result.expected_peak_cash_deficit_paise == 1200000
    on_time = simulate(state, split, [{"customer": 2}], 7)
    assert on_time.expected_penalty_paise == 0
    assert on_time.late_payment_probability == 0


def test_invalid_trained_model_is_unavailable():
    from dataclasses import replace
    broken = replace(load_model(), weights=(float("nan"),)*6)
    result = evaluate(baseline(), EvaluationRequest(paths=10), model=broken)
    assert result.status == "unavailable"
    assert result.recommendation is None


def test_multiple_mandatory_shortfalls_count_once_and_high_cash_changes_choice():
    from app.domain import Obligation
    state = baseline()
    state.obligations["other"] = Obligation(id="other", label="Tax", amount_paise=1000000,
        due_date=state.base_date+timedelta(days=1))
    result = simulate(state, candidates(state, EvaluationRequest())[0], [{"customer": None}], 7)
    assert result.expected_shortfall_paise == 2000000
    assert result.expected_peak_cash_deficit_paise == 2000000
    state.cash_paise = 30000000
    assert evaluate(state, EvaluationRequest(paths=10)).recommendation == "full"
