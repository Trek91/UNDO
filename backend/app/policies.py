"""Explicit policy choices separated from their common-future outcome scoring."""
from app.analysis_types import Action, PolicyComparison, PolicyResult
from app.domain import State
from app.engine import Evaluation, EvaluationRequest, evaluate
from app.prediction import HazardModel
from app.scenarios import scenario_evaluation

POLICY_VERSION = 'obligation-reserve-rule-v1'
OUTCOME_FIELDS = ('shortfall_probability', 'expected_shortfall_paise', 'expected_penalty_paise',
                 'reserve_breach_probability', 'expected_peak_cash_deficit_paise',
                 'expected_peak_reserve_deficit_paise', 'expected_remaining_paise')


def obligation_choice(state: State, evaluation: Evaluation) -> Action | None:
    valid = {item.action.id: item.action for item in evaluation.actions if item.valid}
    target = state.proposals[evaluation.request.proposal_id].obligation_id
    required = state.reserve_paise+sum(item.outstanding_paise for item in state.obligations.values()
        if item.mandatory and item.id != target and (item.due_date-state.base_date).days <= evaluation.request.horizon_days)
    order: list[Action] = ['full', 'partial', 'hold', 'defer']
    for key in order:
        if key in valid and sum(amount for day, amount in valid[key].payments if day == 0)+required <= state.cash_paise:
            return key
    if 'hold' in valid:
        return 'hold'
    return list(valid)[0] if valid else None


def compare_policies(state: State, request: EvaluationRequest, model: HazardModel | None, *,
                     paths: list[dict[str, int | None]] | None = None,
                     planning: Evaluation | None = None) -> PolicyComparison:
    planning = planning or scenario_evaluation(state, request, model)
    if paths is not None and not 1 <= len(paths) <= 5000:
        raise ValueError('One to 5000 scoring paths required')
    outcome_request = request.model_copy(update={'paths': len(paths)}) if paths is not None else request
    outcomes = evaluate(state, outcome_request, model, scenarios_override=paths,
                        scenario_basis='heldout_realized') if paths is not None else planning
    valid = {item.action.id for item in planning.actions if item.valid}
    stress = evaluate(state, request.model_copy(update={'paths': 1, 'include_robustness': False}), None,
        scenarios_override=[{key: None for key in state.receivables}], scenario_basis='prescribed_stress')
    picks: list[tuple[str, str, Action | None, str]] = [
        ('balance_only', 'Balance-only', 'full' if 'full' in valid else 'hold' if 'hold' in valid else None,
         'Pay full if immediately affordable and contract-feasible; otherwise hold. Ignores future mandatory budget.'),
        ('obligation_rule', 'Obligation-aware rule', obligation_choice(state, planning),
         'Reserve known mandatory principal through the horizon plus desired reserve; try full, permitted split, then hold/defer. If no plan preserves the soft reserve, hold if feasible.'),
        ('ml_informed', 'Experimental ML', planning.recommendation if planning.metadata.model_version else None,
         'Select by the documented lexicographic objective using forecast paths only; no access to held-out realized futures.'),
        ('stress', 'No-receipt stress', stress.recommendation,
         'Choose under a prescribed no-receipt path; score below on the same futures as every other policy. Not optimal or risk-free.'),
    ]
    rows = []
    for identifier, label, action, reason in picks:
        result = next((item for item in outcomes.actions if item.action.id == action), None)
        rows.append(PolicyResult.model_validate(dict(id=identifier, label=label, action_id=action,
            status='unavailable' if identifier == 'ml_informed' and not planning.metadata.model_version else 'ready' if result else 'infeasible',
            reason=reason, metrics=result.metrics if result else None,
            scenario_digest=outcomes.metadata.scenario_digest or 'unavailable', contractual_feasibility_rate=float(result is not None and result.valid))))
    rule, ml = rows[1].metrics, rows[2].metrics
    differences = {field: getattr(ml, field)-getattr(rule, field) for field in OUTCOME_FIELDS} if ml and rule else {}
    values = list(differences.values())
    conclusion = ('insufficient_evidence' if not values else 'no_difference' if all(value == 0 for value in values)
        else 'ml_better' if all(value <= 0 for value in values) else 'ml_worse' if all(value >= 0 for value in values)
        else 'mixed_tradeoffs')
    return PolicyComparison.model_validate(dict(policies=rows, scenario_digest=outcomes.metadata.scenario_digest or 'unavailable',
        outcome_basis=outcomes.metadata.scenario_basis, conclusion=conclusion, differences=differences,
        interpretation='Paired financial outcomes, ML minus rule; negative risk/cost differences favor ML. Mixed directions are tradeoffs, not a fabricated composite score.',
        limitations=['Current planning simulations are conditional on assumptions and do not establish held-out or real-world decision improvement.',
                     'Contractual feasibility is at decision time, not a guarantee of future funding.',
                     'Policy choices never receive the realized future paths used for scoring in a held-out comparison.']))
