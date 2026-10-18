"""A small trained logistic hazard model; no external ML runtime or heuristic fallback."""
import hashlib
import math
import random
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache

from app.domain import Receivable

DATASET_SEED = 20261017
FEATURES = ("intercept", "log_amount", "age", "relative_due", "historical_late_rate", "mean_delay")


def sigmoid(value: float) -> float:
    if value >= 0:
        return 1 / (1 + math.exp(-value))
    exponential = math.exp(value)
    return exponential / (1 + exponential)


def features(receivable: Receivable, reference: date, day: int) -> tuple[float, ...]:
    if not 0 <= day <= 60:
        raise ValueError("Prediction day outside supported range")
    return (1.0, math.log1p(receivable.amount_paise / 100) / 12,
            ((reference - receivable.created_date).days + day) / 30,
            (day - (receivable.expected_date - reference).days) / 7,
            receivable.historical_late_rate, receivable.historical_delay_days / 10)


@dataclass(frozen=True)
class InvoiceRecord:
    id: int
    receivable: Receivable
    arrival_day: int | None


def generate_dataset(seed: int = DATASET_SEED, count: int = 600) -> list[InvoiceRecord]:
    rng = random.Random(seed)
    reference = date(2026, 1, 1)
    records = []
    for identifier in range(count):
        age = rng.randint(2, 28)
        due_in = rng.randint(-4, 12)
        receivable = Receivable(id=f"synthetic-{identifier}", label="Synthetic invoice",
            amount_paise=rng.randint(10000, 12000000), created_date=reference-timedelta(days=age),
            expected_date=reference+timedelta(days=max(due_in, -age)),
            historical_late_rate=rng.random(), historical_delay_days=rng.uniform(0, 12))
        latent = rng.gauss(0, 0.65)
        no_arrival = rng.random() < 0.06
        arrival = None
        for day in range(15):
            x = features(receivable, reference, day)
            true_logit = -2.3 + 0.15*x[1] + 0.55*x[2] + 1.3*x[3] - 1.6*x[4] - 0.7*x[5] + latent
            if not no_arrival and rng.random() < sigmoid(true_logit):
                arrival = day
                break
        records.append(InvoiceRecord(identifier, receivable, arrival))
    return records


def probability_metrics(labels: list[int], probabilities: list[float]) -> dict[str, float]:
    if not labels or len(labels) != len(probabilities):
        raise ValueError("Nonempty paired observations required")
    if any(label not in (0, 1) for label in labels) or any(
            not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("Invalid labels or probabilities")
    predicted = [p >= 0.5 for p in probabilities]
    tp = sum(label == 1 and prediction for label, prediction in zip(labels, predicted))
    fp = sum(label == 0 and prediction for label, prediction in zip(labels, predicted))
    fn = sum(label == 1 and not prediction for label, prediction in zip(labels, predicted))
    precision = tp / (tp+fp) if tp+fp else 0
    recall = tp / (tp+fn) if tp+fn else 0
    return dict(precision=precision, recall=recall,
                f1=2*precision*recall/(precision+recall) if precision+recall else 0,
                brier=sum((p-label)**2 for p, label in zip(probabilities, labels))/len(labels),
                threshold=0.5, observations=len(labels), positive_labels=sum(labels),
                predicted_positives=tp+fp, true_positives=tp,
                true_negatives=len(labels)-tp-fp-fn, false_positives=fp, false_negatives=fn,
                precision_defined=int(tp+fp > 0), recall_defined=int(tp+fn > 0))


@dataclass(frozen=True)
class HazardModel:
    weights: tuple[float, ...]
    version: str
    train_ids: tuple[int, ...]
    test_ids: tuple[int, ...]
    metrics: dict[str, float]
    seed: int

    def validate(self) -> None:
        if len(self.weights) != len(FEATURES) or not all(math.isfinite(weight) for weight in self.weights):
            raise ValueError("Invalid model coefficients")

    def hazard(self, receivable: Receivable, reference: date, day: int) -> float:
        self.validate()
        probability = sigmoid(sum(weight*x for weight, x in zip(self.weights, features(receivable, reference, day))))
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("Invalid model probability")
        return probability


def train(seed: int = DATASET_SEED, count: int = 600, epochs: int = 240) -> HazardModel:
    if count < 20 or epochs < 1:
        raise ValueError("Insufficient training configuration")
    records = generate_dataset(seed, count)
    random.Random(seed+1).shuffle(records)
    train_records, test_records = records[:int(count*0.8)], records[int(count*0.8):]
    reference = date(2026, 1, 1)

    def expand(items: list[InvoiceRecord]) -> list[tuple[tuple[float, ...], int]]:
        return [(features(item.receivable, reference, day), int(item.arrival_day == day))
                for item in items for day in range((item.arrival_day+1) if item.arrival_day is not None else 15)]

    observations = expand(train_records)
    weights = [-2.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    for _ in range(epochs):
        gradient = [0.0]*6
        for x, label in observations:
            error = sigmoid(sum(w*v for w, v in zip(weights, x))) - label
            for index in range(6):
                gradient[index] += error*x[index]
        weights = [w-0.7*(g/len(observations)+(0.002*w if i else 0))
                   for i, (w, g) in enumerate(zip(weights, gradient))]
    # Canonical coefficient precision makes provenance hashes stable across libm implementations.
    weights = [round(weight, 12) for weight in weights]
    test_observations = expand(test_records)
    probabilities = [sigmoid(sum(w*v for w, v in zip(weights, x))) for x, _ in test_observations]
    metrics = probability_metrics([label for _, label in test_observations], probabilities)
    metrics.update(heldout_invoices=len(test_records), training_invoices=len(train_records),
                   heldout_daily_observations=len(test_observations))
    horizon_probabilities = []
    for item in test_records:
        survival = 1.0
        for day in range(8):
            survival *= 1-sigmoid(sum(w*v for w, v in zip(weights, features(item.receivable, reference, day))))
        horizon_probabilities.append(1-survival)
    metrics["horizon_brier"] = probability_metrics(
        [int(item.arrival_day is not None and item.arrival_day <= 7) for item in test_records],
        horizon_probabilities)["brier"]
    digest = hashlib.sha256(repr((seed, count, epochs, weights, FEATURES)).encode()).hexdigest()[:12]
    return HazardModel(tuple(weights), f"synthetic-logistic-hazard-v1-{digest}",
                       tuple(item.id for item in train_records), tuple(item.id for item in test_records), metrics, seed)


@lru_cache(maxsize=1)
def load_model() -> HazardModel:
    return train()
