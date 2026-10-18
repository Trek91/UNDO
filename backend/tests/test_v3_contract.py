from datetime import timedelta

import pytest

from app.domain import Obligation, baseline
from app.engine import EvaluationRequest, candidates, simulate


def test_real_quantiles_intervals_and_all_remaining_liabilities():
    state = baseline()
    state.obligations['later'] = Obligation(id='later', label='Later rent', amount_paise=2000000,
        due_date=state.base_date+timedelta(days=10))
    result = simulate(state, candidates(state, EvaluationRequest())[0], [{'customer': None}, {'customer': 0}], 1)
    assert result.cash_outcomes.sampled_worst_minimum_paise == -1000000
    assert result.cash_outcomes.daily_p05_paise == [4000000, -1000000]
    assert result.cash_outcomes.daily_p95_paise == [8000000, 3000000]
    interval = result.probability_intervals['shortfall_probability']
    assert interval.successes == 1 and interval.trials == 2
    assert interval.lower == pytest.approx(0.0945312, abs=1e-6)
    assert interval.upper == pytest.approx(0.9054688, abs=1e-6)
    assert result.expected_total_remaining_liabilities_paise == 2500000
    assert state.cash_paise == 10000000


def test_zero_observed_misses_are_not_certainty():
    result = simulate(baseline(), candidates(baseline(), EvaluationRequest())[1], [{'customer': 0}], 7)
    assert result.probability_intervals['shortfall_probability'].upper > 0
    assert result.probability_intervals['shortfall_probability'].lower == 0
