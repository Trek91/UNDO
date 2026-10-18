from typing import Literal

from pydantic import Field

from app.analysis_types import PolicyComparison
from app.domain import Contract
from app.metric_reporting import ClassificationReport


class BinaryEvidence(Contract):
    observations: int
    positives: int
    negatives: int
    predicted_positives: int
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    prevalence: float
    threshold: float = .5
    precision: float | None
    recall: float | None
    f1: float | None
    brier: float
    log_loss: float | None
    classification: ClassificationReport


class CalibrationBin(Contract):
    lower: float
    upper: float
    count: int
    predicted: float | None
    observed: float | None


class SeedBenchmark(Contract):
    seed: int
    policies: dict[str, dict[str, float | int]]
    choices: dict[str, dict[str, int]]


class ValidationBenchmark(Contract):
    protocol: str
    model_version: str
    weights_digest: str
    source_hashes: dict[str, str]
    dataset_seed: int
    heldout_invoices: int
    paths_per_decision: int
    seed_results: list[SeedBenchmark]
    paired_penalty_benefit_paise: int
    paired_penalty_benefit_ci95: list[int] = Field(min_length=2, max_length=2)
    decision_advantage: bool
    conclusion: str
    assumptions: list[str]


class ModelGate(Contract):
    eligible: bool
    status: Literal['EXPERIMENTAL', 'UNAVAILABLE', 'ELIGIBLE_SYNTHETIC_ONLY']
    primary_basis: Literal['obligation_rule', 'ml_informed']
    criteria: dict[str, bool]
    reason: str
    policy_version: str = 'evidence-gate-v3-1'


class ModelEvidence(Contract):
    status: Literal['EXPERIMENTAL', 'UNAVAILABLE', 'ELIGIBLE_SYNTHETIC_ONLY']
    version: str | None
    target: str = 'conditional_daily_arrival_hazard'
    provenance: str = 'Deterministic synthetic invoices; invoice split before at-risk daily expansion, no real customer validation.'
    dataset_seed: int | None = None
    training_invoices: int | None = None
    heldout_invoices: int | None = None
    train_daily_observations: int | None = None
    train_daily_prevalence: float | None = None
    invoice_overlap: int | None = None
    daily: BinaryEvidence | None = None
    daily_baseline: BinaryEvidence | None = None
    horizon: BinaryEvidence | None = None
    horizon_baseline: BinaryEvidence | None = None
    horizon_days: int = 7
    probability_min: float | None = None
    probability_max: float | None = None
    probability_mean: float | None = None
    calibration: list[CalibrationBin] = Field(default_factory=list)
    calibration_error: float | None = None
    benchmark: ValidationBenchmark | None = None
    benchmark_status: str
    gate: ModelGate
    real_world_claims_supported: bool = False
    limitations: list[str]


class DecisionEvidence(Contract):
    primary_policy: Literal['obligation_rule', 'ml_informed']
    policy_version: str
    model_gate: ModelGate
    policy_comparison: PolicyComparison
    known_mandatory_budget_paise: int
    desired_reserve_paise: int
    primary_reason: str
    forecast_basis: str
    reevaluate_when: list[str]
    important_dimensions: list[str] = Field(default_factory=list)
