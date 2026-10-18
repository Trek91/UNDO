"""Actual probabilistic diagnostics and a version-checked held-out decision gate."""
import hashlib
import math
import statistics
from datetime import date
from functools import lru_cache
from pathlib import Path

from app.evidence_types import BinaryEvidence, CalibrationBin, ModelEvidence, ModelGate, ValidationBenchmark
from app.prediction import HazardModel, generate_dataset
from app.metric_reporting import classification_report

BENCHMARK_PATH = Path(__file__).parent/'evidence'/'validation.json'
LIMITS = [
    'Synthetic diagnostics and held-out outcomes do not establish real-world accuracy or causal financial benefit.',
    'Daily threshold 0.5 is diagnostic, not an operating rule; zero predicted positives makes precision undefined.',
    'Daily hazards combine as 1 minus the product of survival from day 0 through H inclusive.',
    'Calibration bins with few observations are unreliable; customers and macroeconomic shocks are not jointly modeled.',
    'Training follows days 0–14; horizons 15–30 extrapolate.',
]


def source_hashes() -> dict[str, str]:
    return {name: hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
            for name in ('engine.py', 'prediction.py', 'policies.py')}


def weights_digest(model: HazardModel) -> str:
    return hashlib.sha256(repr(model.weights).encode()).hexdigest()


def binary_metrics(labels: list[int], probabilities: list[float]) -> BinaryEvidence:
    if not labels or len(labels) != len(probabilities) or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError('Valid paired labels/probabilities required')
    predicted = [p >= .5 for p in probabilities]
    tp = sum(y == 1 and p for y, p in zip(labels, predicted))
    fp = sum(y == 0 and p for y, p in zip(labels, predicted))
    fn = sum(y == 1 and not p for y, p in zip(labels, predicted))
    classification = classification_report(dict(true_positives=tp, false_positives=fp, false_negatives=fn))
    loss = None if any((y and p == 0) or (not y and p == 1) for y, p in zip(labels, probabilities)) else statistics.mean(
        -math.log(p) if y else -math.log1p(-p) for y, p in zip(labels, probabilities))
    return BinaryEvidence(observations=len(labels), positives=sum(labels), negatives=len(labels)-sum(labels),
        predicted_positives=tp+fp, true_positives=tp, true_negatives=len(labels)-tp-fp-fn,
        false_positives=fp, false_negatives=fn, prevalence=sum(labels)/len(labels),
        precision=classification.precision.value, recall=classification.recall.value,
        f1=classification.f1.value, classification=classification,
        brier=statistics.mean((p-y)**2 for y, p in zip(labels, probabilities)), log_loss=loss)


@lru_cache(maxsize=4)
def diagnostics(weights: tuple[float, ...], version: str, seed: int,
                train_ids: tuple[int, ...], test_ids: tuple[int, ...]) -> dict:
    if not train_ids or not test_ids or max((*train_ids, *test_ids)) >= 5000:
        raise ValueError('Missing or oversized invoice validation split')
    model = HazardModel(weights, version, train_ids, test_ids, {}, seed)
    model.validate()
    records = {item.id: item for item in generate_dataset(seed, max((*train_ids, *test_ids))+1)}
    train, test = [records[key] for key in train_ids], [records[key] for key in test_ids]
    reference = date(2026, 1, 1)
    train_labels = [int(item.arrival_day == day) for item in train
        for day in range(item.arrival_day+1 if item.arrival_day is not None else 15)]
    labels = [int(item.arrival_day == day) for item in test
        for day in range(item.arrival_day+1 if item.arrival_day is not None else 15)]
    scores = [model.hazard(item.receivable, reference, day) for item in test
        for day in range(item.arrival_day+1 if item.arrival_day is not None else 15)]
    prevalence = sum(train_labels)/len(train_labels)
    h_labels = [int(item.arrival_day is not None and item.arrival_day <= 7) for item in test]
    h_scores = [1-math.prod(1-model.hazard(item.receivable, reference, day) for day in range(8)) for item in test]
    h_prevalence = sum(item.arrival_day is not None and item.arrival_day <= 7 for item in train)/len(train)
    bins = []
    for i in range(10):
        selected = [(y, p) for y, p in zip(labels, scores) if i/10 <= p < (i+1)/10 or (i == 9 and p == 1)]
        bins.append(CalibrationBin(lower=i/10, upper=(i+1)/10, count=len(selected),
            predicted=statistics.mean(p for _, p in selected) if selected else None,
            observed=statistics.mean(y for y, _ in selected) if selected else None))
    return dict(dataset_seed=seed, training_invoices=len(train), heldout_invoices=len(test),
        train_daily_observations=len(train_labels), train_daily_prevalence=prevalence,
        invoice_overlap=len(set(train_ids)&set(test_ids)), daily=binary_metrics(labels, scores),
        daily_baseline=binary_metrics(labels, [prevalence]*len(labels)), horizon=binary_metrics(h_labels, h_scores),
        horizon_baseline=binary_metrics(h_labels, [h_prevalence]*len(h_labels)),
        probability_min=min(scores), probability_max=max(scores), probability_mean=statistics.mean(scores),
        calibration=bins, calibration_error=sum(item.count*abs(item.predicted-item.observed)
            for item in bins if item.predicted is not None and item.observed is not None)/len(labels))


def model_evidence(model: HazardModel | None) -> ModelEvidence:
    try:
        if model is None:
            raise ValueError('Model missing')
        data = diagnostics(model.weights, model.version, model.seed, model.train_ids, model.test_ids)
    except (ValueError, KeyError):
        gate = ModelGate(eligible=False, status='UNAVAILABLE', primary_basis='obligation_rule',
            criteria={'valid_model_and_validation_split': False}, reason='The predictive model is missing or invalid. The validated obligation-aware rule remains primary; forecasts use explicitly prescribed stress only.')
        return ModelEvidence(status='UNAVAILABLE', version=None, benchmark_status='unavailable', gate=gate, limitations=LIMITS)
    benchmark = None
    benchmark_status = 'missing or stale validation artifact'
    try:
        artifact = ValidationBenchmark.model_validate_json(BENCHMARK_PATH.read_text())
        if (artifact.model_version == model.version and artifact.weights_digest == weights_digest(model)
                and artifact.source_hashes == source_hashes() and artifact.dataset_seed == model.seed):
            benchmark, benchmark_status = artifact, 'verified source/model provenance'
    except (OSError, ValueError):
        pass
    criteria = dict(valid_model_and_validation_split=data['invoice_overlap'] == 0,
        probability_beats_training_prevalence=data['daily'].brier < data['daily_baseline'].brier,
        heldout_decision_benefit=bool(benchmark and benchmark.decision_advantage),
        multi_seed_paired_validation=bool(benchmark and len(benchmark.seed_results) >= 3 and benchmark.heldout_invoices >= 120))
    eligible = all(criteria.values())
    status = 'ELIGIBLE_SYNTHETIC_ONLY' if eligible else 'EXPERIMENTAL'
    gate = ModelGate(eligible=eligible, status=status, primary_basis='ml_informed' if eligible else 'obligation_rule', criteria=criteria,
        reason='The prescribed synthetic validation gate passed; real-world validity remains unverified.' if eligible else
        'Reliable held-out decision improvement over the obligation-aware rule has not been established. ML is an experimental comparator; known obligations and reserve rules determine the primary action.')
    return ModelEvidence.model_validate(dict(status=status, version=model.version, **data,
        benchmark=benchmark, benchmark_status=benchmark_status, gate=gate, limitations=LIMITS))
