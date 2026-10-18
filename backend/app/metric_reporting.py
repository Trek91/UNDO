"""Denominator-aware presentation only. Never rewrite stored model metadata or weights."""
import math
from typing import Literal, Mapping

from app.domain import Contract


class ReportedMetric(Contract):
    value: float | None
    defined: bool
    numerator: int | None
    denominator: int | None
    status: Literal['defined', 'undefined', 'unverified']
    reason: str | None


class ClassificationReport(Contract):
    precision: ReportedMetric
    recall: ReportedMetric
    f1: ReportedMetric
    counts: dict[str, int] | None
    provenance: str = 'Confusion-count presentation; original raw metrics retained separately.'


def classification_report(metrics: Mapping[str, float]) -> ClassificationReport:
    names = ('true_positives', 'false_positives', 'false_negatives')
    if any(name not in metrics or isinstance(metrics[name], bool) or not math.isfinite(metrics[name])
           or metrics[name] < 0 or int(metrics[name]) != metrics[name] for name in names):
        unavailable = ReportedMetric(value=None, defined=False, numerator=None, denominator=None,
            status='unverified', reason='stored denominator counts unavailable or invalid')
        return ClassificationReport(precision=unavailable, recall=unavailable, f1=unavailable, counts=None)
    counts = {name: int(metrics[name]) for name in names}
    tp, fp, fn = (counts[name] for name in names)

    def metric(numerator: int, denominator: int, reason: str) -> ReportedMetric:
        return ReportedMetric(value=numerator/denominator if denominator else None, defined=denominator > 0,
            numerator=numerator, denominator=denominator, status='defined' if denominator else 'undefined',
            reason=None if denominator else reason)

    return ClassificationReport(counts=counts,
        precision=metric(tp, tp+fp, 'no positive predictions (0 predicted positives)'),
        recall=metric(tp, tp+fn, 'no actual positive cases (0 actual positives)'),
        f1=metric(2*tp, 2*tp+fp+fn, 'no actual or predicted positives (F1 denominator is 0)'))
