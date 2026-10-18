"""Independent diagnostics of the existing fixed model/data; no threshold or fitting changes."""
import csv
import json
import math
import statistics
from datetime import date
from pathlib import Path

from app.prediction import FEATURES, generate_dataset, load_model, sigmoid


def metrics(labels: list[int], probabilities: list[float]) -> dict[str, object]:
    predictions = [probability >= 0.5 for probability in probabilities]
    tp = sum(label == 1 and prediction for label, prediction in zip(labels, predictions))
    tn = sum(label == 0 and not prediction for label, prediction in zip(labels, predictions))
    fp = sum(label == 0 and prediction for label, prediction in zip(labels, predictions))
    fn = sum(label == 1 and not prediction for label, prediction in zip(labels, predictions))
    return dict(n=len(labels), positives=sum(labels), prevalence=statistics.mean(labels),
                tp=tp, tn=tn, fp=fp, fn=fn, predicted_positives=sum(predictions), threshold=0.5,
                precision=tp/(tp+fp) if tp+fp else None, recall=tp/(tp+fn) if tp+fn else None,
                f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
                brier=statistics.mean((probability-label)**2 for label, probability in zip(labels, probabilities)))


def run() -> dict[str, object]:
    model = load_model()
    records = generate_dataset(model.seed, len(model.train_ids)+len(model.test_ids))
    by_id = {record.id: record for record in records}
    training = [by_id[identifier] for identifier in model.train_ids]
    heldout = [by_id[identifier] for identifier in model.test_ids]
    reference = date(2026, 1, 1)
    observations = [(record.id, day, int(record.arrival_day == day)) for record in heldout
                    for day in range(record.arrival_day+1 if record.arrival_day is not None else 15)]
    train_labels = [int(record.arrival_day == day) for record in training
                    for day in range(record.arrival_day+1 if record.arrival_day is not None else 15)]
    labels = [label for _, _, label in observations]
    probabilities = [model.hazard(by_id[identifier].receivable, reference, day) for identifier, day, _ in observations]
    prevalence = sum(train_labels)/len(train_labels)
    training_probabilities = [model.hazard(record.receivable, reference, day) for record in training
        for day in range(record.arrival_day+1 if record.arrival_day is not None else 15)]

    def log_loss(targets, scores):
        return statistics.mean(-math.log(p) if y else -math.log1p(-p) for y, p in zip(targets, scores))

    training_loss = dict(initial_log_loss=log_loss(train_labels, [sigmoid(-2)]*len(train_labels)),
        final_log_loss=log_loss(train_labels, training_probabilities),
        training_prevalence_log_loss=log_loss(train_labels, [prevalence]*len(train_labels)))
    assert training_loss['final_log_loss'] < training_loss['initial_log_loss']
    bins = []
    for index in range(10):
        selected = [(label, p) for label, p in zip(labels, probabilities)
                    if index/10 <= p < (index+1)/10 or (index == 9 and p == 1)]
        bins.append(dict(lower=index/10, upper=(index+1)/10, count=len(selected),
            predicted=statistics.mean(p for _, p in selected) if selected else None,
            observed=statistics.mean(label for label, _ in selected) if selected else None))
    ece = sum(item["count"]*abs(item["predicted"]-item["observed"]) for item in bins if item["count"])/len(labels)
    horizon_labels = [int(record.arrival_day is not None and record.arrival_day <= 7) for record in heldout]
    horizon_probabilities = [1-math.prod(1-model.hazard(record.receivable, reference, day) for day in range(8)) for record in heldout]
    train_horizon_prevalence = sum(record.arrival_day is not None and record.arrival_day <= 7 for record in training)/len(training)
    report = dict(version=model.version, seed=model.seed, features=FEATURES, weights=model.weights,
        data="Existing fixed synthetic generator; no changes to seed, split, epochs, data or threshold",
        training_invoices=len(training), heldout_invoices=len(heldout), training_daily_observations=len(train_labels),
        training_positive_days=sum(train_labels), training_daily_prevalence=prevalence,
        training_loss=training_loss,
        daily_model=metrics(labels, probabilities), daily_training_prevalence_baseline=metrics(labels, [prevalence]*len(labels)),
        daily_probability_distribution=dict(min=min(probabilities), max=max(probabilities), mean=statistics.mean(probabilities), median=statistics.median(probabilities)),
        calibration_bins=bins, expected_calibration_error=ece,
        horizon_model=metrics(horizon_labels, horizon_probabilities),
        horizon_training_prevalence_baseline=metrics(horizon_labels, [train_horizon_prevalence]*len(horizon_labels)),
        train_test_invoice_overlap=sorted(set(model.train_ids)&set(model.test_ids)),
        original_metrics=model.metrics,
        undefined_metric_convention="The original helper replaces undefined precision with zero; this report uses null and publishes counts.")
    output = Path("../docs/audit")
    output.mkdir(parents=True, exist_ok=True)
    (output/"ml-diagnostics.json").write_text(json.dumps(report, indent=2))
    with (output/"heldout-predictions.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["invoice_id", "day", "label", "probability", "predicted_at_0_5", "training_prevalence_baseline"])
        for (identifier, day, label), probability in zip(observations, probabilities):
            writer.writerow([identifier, day, label, probability, int(probability >= 0.5), prevalence])
    print(json.dumps({key: value for key, value in report.items() if key not in ("calibration_bins", "original_metrics")}, indent=2))
    return report


if __name__ == "__main__":
    run()
