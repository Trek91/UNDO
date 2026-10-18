"""Bounded one-factor sensitivity over the existing engine; no hidden optimizer."""
import hashlib
from collections.abc import Callable

from app.analysis_types import Action, Dimension, SensitivityCase, SensitivityReport, TippingPoint
from app.domain import MAX_MONEY, State
from app.engine import Evaluation, EvaluationRequest
from app.prediction import HazardModel
from app.scenarios import ScenarioChanges, changed_state, mandatory_id, receipt_id, scenario_evaluation

Selector = Callable[[State, Evaluation], Action | None]


def default_grids(state: State, request: EvaluationRequest) -> dict[Dimension, list[int | float]]:
    target = state.obligations[state.proposals[request.proposal_id].obligation_id]
    known = sum(item.outstanding_paise for item in state.obligations.values()
                if item.mandatory and item.id != target.id and (item.due_date-state.base_date).days <= request.horizon_days)
    budget = max(1, state.cash_paise-known-state.reserve_paise)
    amount_values = sorted({max(1, target.outstanding_paise//2), target.outstanding_paise, budget,
                            min(MAX_MONEY, budget+1), max(1, state.cash_paise), min(MAX_MONEY, state.cash_paise+1)})
    grids: dict[Dimension, list[int | float]] = {
        'receipt_delay_days': [0, 2, 5, 10], 'receipt_probability': [0, .25, .5, .75, 1],
        'unexpected_expense_paise': [0, 1000000, 1000001, 2000000],
        'mandatory_due_days': [0, 1, 3, 7], 'proposed_amount_paise': list(amount_values),
        'supplier_due_days': [-1, 0, 1, 3], 'reserve_paise': [0, 1000000, 2000000, 3000000, 5000000],
    }
    if target.terms:
        grids['partial_days'] = sorted({1, target.terms.partial_days, 5, 7})
        grids['penalty_paise'] = sorted({0, target.terms.late_penalty_paise, 500000})
    return grids


def sensitivity(state: State, request: EvaluationRequest, model: HazardModel | None, *,
                grids: dict[Dimension, list[int | float]] | None = None,
                selector: Selector | None = None, base_evaluation: Evaluation | None = None,
                probability: float | None = None) -> SensitivityReport:
    configured = grids if grids is not None else default_grids(state, request)
    if len(configured) > 9 or sum(len(values) for values in configured.values()) > 60:
        raise ValueError('Sensitivity is limited to nine dimensions and sixty cases')
    quick = request.model_copy(update={'paths': min(request.paths, 200), 'include_robustness': False})
    base = base_evaluation or scenario_evaluation(state, quick, model, probability)
    choose = selector or (lambda snapshot, result: result.recommendation)
    primary = choose(state, base)
    baseline_metrics = next((item.metrics for item in base.actions if item.action.id == primary), None)
    cases: list[SensitivityCase] = []
    skipped = []
    points: list[TippingPoint] = []
    for dimension, values in configured.items():
        if dimension.startswith('receipt_') and receipt_id(state) is None:
            skipped.append(dimension+': no unpaid invoice')
            continue
        if dimension == 'mandatory_due_days' and mandatory_id(state, request.proposal_id) is None:
            skipped.append(dimension+': no separate mandatory obligation')
            continue
        series: list[SensitivityCase] = []
        unit = 'paise' if dimension.endswith('paise') else 'probability' if dimension == 'receipt_probability' else 'days'
        for value in sorted(set(values)):
            changes = ScenarioChanges.model_validate({dimension: value})
            modified = changed_state(state, changes, request.proposal_id)
            case_probability = changes.receipt_probability if dimension == 'receipt_probability' else probability
            result = scenario_evaluation(modified, quick, model, case_probability)
            action = choose(modified, result)
            chosen = next((item for item in result.actions if item.action.id == action), None)
            previous = next((item for item in result.actions if item.action.id == primary), None)
            metrics = chosen.metrics if chosen else None
            case = SensitivityCase(dimension=dimension, value=value, unit=unit, recommendation=action,
                experimental_recommendation=result.recommendation if result.metadata.model_version else None,
                changed=action != primary, previous_action_infeasible=bool(previous and not previous.valid),
                new_mandatory_shortfall=bool(metrics and baseline_metrics and
                    metrics.shortfall_probability > baseline_metrics.shortfall_probability),
                shortfall_probability=metrics.shortfall_probability if metrics else None,
                expected_penalty_paise=metrics.expected_penalty_paise if metrics else None,
                constraints=[item.action.label+': '+str(item.action.invalid_reason) for item in result.actions if not item.valid],
                status='infeasible' if action is None else 'changed' if action != primary else 'unchanged')
            cases.append(case)
            series.append(case)
        for left, right in zip(series, series[1:]):
            if left.recommendation != right.recommendation:
                points.append(TippingPoint(dimension=dimension, lower_value=left.value, upper_value=right.value,
                    before_action=left.recommendation, after_action=right.recommendation, unit=unit))
    seeds = [(request.seed+i) % 2**32 for i in range(3)]
    replicates = [scenario_evaluation(state, quick.model_copy(update={'seed': seed}), model, probability).recommendation
                  if model is not None else None for seed in seeds]
    ranked = sorted((item for item in base.actions if item.rank is not None), key=lambda item: item.rank or 100)
    overlap = False
    if len(ranked) >= 2 and ranked[0].metrics and ranked[1].metrics:
        a = ranked[0].metrics.probability_intervals.get('shortfall_probability')
        b = ranked[1].metrics.probability_intervals.get('shortfall_probability')
        overlap = bool(a and b and max(a.lower, b.lower) <= min(a.upper, b.upper))
    stable = sum(case.recommendation == primary for case in cases)
    return SensitivityReport(source_state_digest=hashlib.sha256(state.model_dump_json().encode()).hexdigest(),
        model_version=base.metadata.model_version, seed=request.seed, horizon_days=request.horizon_days,
        grid_paths=quick.paths, baseline_paths=request.paths, base_recommendation=primary,
        evaluated_cases=len(cases), stable_cases=stable, stability_share=stable/len(cases) if cases else None,
        cases=cases, tipping_points=points, skipped_dimensions=skipped,
        experimental_seed_recommendations=replicates, sampling_seeds=seeds,
        sampling_status='unavailable' if model is None else 'unstable' if len(set(replicates)) > 1 else 'consistent-limited-check',
        ranking_intervals_overlap=overlap)
