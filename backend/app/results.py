"""Calculated evidence contracts; missing legacy evidence stays missing, never backfilled."""
import math

from pydantic import Field

from app.domain import Contract


class ProbabilityInterval(Contract):
    lower: float = Field(ge=0, le=1, allow_inf_nan=False)
    upper: float = Field(ge=0, le=1, allow_inf_nan=False)
    successes: int
    trials: int
    method: str = 'Wilson 95%; Monte Carlo sampling only, conditional on the scenario assumptions.'


class CashOutcomes(Contract):
    sampled_worst_minimum_paise: int
    minimum_p05_paise: int
    minimum_p50_paise: int
    minimum_p95_paise: int
    daily_p05_paise: list[int]
    daily_p50_paise: list[int]
    daily_p95_paise: list[int]
    method: str = 'Nearest-rank empirical quantiles of simulated net funding; not guaranteed future cash.'


class Metrics(Contract):
    daily_paise: list[int]
    shortfall_probability: float
    expected_shortfall_paise: int
    cash_deficit_probability: float
    expected_peak_cash_deficit_paise: int
    expected_minimum_paise: int
    reserve_breach_probability: float
    expected_peak_reserve_deficit_paise: int
    reserve_maintained_probability: float
    expected_penalty_paise: int
    late_payment_probability: float
    expected_remaining_paise: int
    expected_total_remaining_liabilities_paise: int | None = None
    expected_remaining_fees_paise: int | None = None
    probability_intervals: dict[str, ProbabilityInterval] = Field(default_factory=dict)
    cash_outcomes: CashOutcomes | None = None


def wilson(successes: int, trials: int) -> ProbabilityInterval:
    if not trials or not 0 <= successes <= trials:
        raise ValueError('Valid binomial counts required')
    z = 1.959963984540054
    proportion = successes/trials
    denominator = 1+z*z/trials
    center = (proportion+z*z/(2*trials))/denominator
    half = z*math.sqrt(proportion*(1-proportion)/trials+z*z/(4*trials*trials))/denominator
    return ProbabilityInterval(lower=max(0, center-half), upper=min(1, center+half),
                               successes=successes, trials=trials)


def quantile(values: list[int], probability: float) -> int:
    if not values or not 0 <= probability <= 1:
        raise ValueError('Nonempty sample and unit probability required')
    return sorted(values)[max(0, math.ceil(probability*len(values))-1)]
