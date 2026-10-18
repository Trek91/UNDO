import math
from dataclasses import replace

from app.domain import baseline
from app.engine import EvaluationRequest
from app.model_evidence import model_evidence
from app.decisions import assess
from app.prediction import load_model


def test_daily_target_counts_baseline_scores_and_fail_closed_gate():
    report = model_evidence(load_model())
    assert report.target == 'conditional_daily_arrival_hazard'
    assert report.daily.observations == 1125
    assert report.daily.positives == 94 and report.daily.predicted_positives == 0
    assert report.daily.precision is None and report.daily.recall == 0
    assert math.isclose(report.daily.brier, .07397396463575107)
    assert report.daily.brier < report.daily_baseline.brier
    assert not report.gate.eligible
    assert not report.real_world_claims_supported


def test_primary_is_validated_rule_and_missing_model_is_explicit():
    result = assess(baseline(), EvaluationRequest(paths=20), None)
    assert result.status == 'ready' and result.recommendation == 'partial'
    assert result.decision_evidence.primary_policy == 'obligation_rule'
    assert result.decision_evidence.model_gate.status == 'UNAVAILABLE'
    assert result.metadata.scenario_basis == 'prescribed_stress'
    assert all(not item.metrics.probability_intervals for item in result.actions if item.metrics)
    report = model_evidence(replace(load_model(), weights=()))
    assert not report.gate.eligible and report.status == 'UNAVAILABLE'
