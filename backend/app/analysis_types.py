"""Versioned V3 evidence. Stability describes specified experiments, not confidence."""
from typing import Literal

from pydantic import Field

from app.domain import Contract
from app.results import Metrics

Action = Literal['full', 'partial', 'defer', 'hold']
Dimension = Literal['receipt_delay_days', 'receipt_probability', 'unexpected_expense_paise',
    'mandatory_due_days', 'proposed_amount_paise', 'supplier_due_days', 'partial_days', 'penalty_paise', 'reserve_paise']


class PolicyResult(Contract):
    id: Literal['balance_only', 'obligation_rule', 'ml_informed', 'stress']
    label: str
    action_id: Action | None
    status: Literal['ready', 'infeasible', 'unavailable']
    reason: str
    metrics: Metrics | None
    scenario_digest: str
    contractual_feasibility_rate: float


class PolicyComparison(Contract):
    policies: list[PolicyResult]
    scenario_digest: str
    outcome_basis: str
    conclusion: Literal['no_difference', 'ml_better', 'ml_worse', 'mixed_tradeoffs', 'insufficient_evidence']
    differences: dict[str, float | int]
    interpretation: str
    limitations: list[str]


class SensitivityCase(Contract):
    dimension: Dimension
    value: int | float
    unit: str
    recommendation: Action | None
    experimental_recommendation: Action | None
    changed: bool
    previous_action_infeasible: bool
    new_mandatory_shortfall: bool
    shortfall_probability: float | None
    expected_penalty_paise: int | None
    constraints: list[str]
    status: str


class TippingPoint(Contract):
    dimension: Dimension
    lower_value: int | float
    upper_value: int | float
    before_action: Action | None
    after_action: Action | None
    unit: str
    method: str = 'Adjacent tested grid points; boundary is bracketed, not an exact or guaranteed threshold.'


class SensitivityReport(Contract):
    source_state_digest: str
    model_version: str | None
    seed: int
    horizon_days: int
    grid_paths: int
    baseline_paths: int
    base_recommendation: Action | None
    evaluated_cases: int
    stable_cases: int
    stability_share: float | None
    cases: list[SensitivityCase]
    tipping_points: list[TippingPoint]
    skipped_dimensions: list[str]
    experimental_seed_recommendations: list[Action | None]
    sampling_seeds: list[int]
    sampling_status: str
    ranking_intervals_overlap: bool
    method: str = 'Bounded one-factor grid, common seed and customer uniforms; no monotonicity or joint likelihood assumed.'
    limitations: list[str] = Field(default_factory=lambda: [
        'An unweighted share of tested cases is sensitivity, not model confidence or a probability of being right.',
        'Three finite-path seed replicates can reveal instability but cannot prove a stable true ranking.',
        'Wilson intervals describe conditional Monte Carlo sampling, not model uncertainty or real-world calibration.',
        'Receipt-probability experiments prescribe a one-time arrival on the expected day clipped to the horizon.',
        'No switch means no crossing found in this grid; it does not establish global robustness.',
    ])
