"""V3 orchestration: evidence-gated primary policy, transparent forecasts and optional robustness."""
import hashlib
from collections import Counter

from app.domain import State
from app.engine import Evaluation, EvaluationRequest, TimelineItem
from app.evidence_types import DecisionEvidence
from app.model_evidence import model_evidence
from app.policies import POLICY_VERSION, compare_policies, obligation_choice
from app.prediction import HazardModel
from app.robustness import sensitivity
from app.scenarios import scenario_evaluation


def assess(state: State, request: EvaluationRequest, model: HazardModel | None,
           receipt_probability: float | None = None) -> Evaluation:
    evidence = model_evidence(model)
    active_model = model if evidence.status != 'UNAVAILABLE' else None
    result = scenario_evaluation(state, request, active_model, receipt_probability)
    comparison = compare_policies(state, request, active_model, planning=result)
    primary = result.recommendation if evidence.gate.eligible else obligation_choice(state, result)
    target = state.proposals[request.proposal_id].obligation_id
    known = sum(item.outstanding_paise for item in state.obligations.values() if item.mandatory
        and item.id != target and (item.due_date-state.base_date).days <= request.horizon_days)
    chosen = next((item for item in result.actions if item.action.id == primary), None)
    alternatives = sorted((item for item in result.actions if item.valid and item.action.id != primary),
                          key=lambda item: item.rank or 100)
    alternative = alternatives[0] if alternatives else None
    budget_explanation = ''
    if alternative and not evidence.gate.eligible:
        committed = sum(amount for day, amount in alternative.action.payments if day == 0)
        budget_explanation = (f' {alternative.action.label}, the leading experimental alternative, '
            + ('would consume cash reserved for known mandatory principal and the desired reserve.'
               if committed+known+state.reserve_paise > state.cash_paise
               else 'does not precede this action in the disclosed full/split/hold/defer rule order.'))
    reason = (f'{chosen.action.label} is the primary choice under the validated known-obligation and reserve rule. '
        'Experimental ML rankings remain visible and do not silently override this policy.'+budget_explanation if chosen and not evidence.gate.eligible
        else result.explanation.reason)
    triggers = ['A confirmed receipt, new expense, contractual change or reserve change requires reevaluation.']
    if request.include_robustness:
        selector = None if evidence.gate.eligible else obligation_choice
        result.robustness = sensitivity(state, request, active_model, selector=selector, base_evaluation=result, probability=receipt_probability)
        triggers += [f'Tested {point.dimension} switch between {point.lower_value} and {point.upper_value} {point.unit}.'
                     for point in result.robustness.tipping_points[:5]]
    important = Counter(case.dimension for case in result.robustness.cases if case.changed) if result.robustness else Counter()
    result.decision_evidence = DecisionEvidence(primary_policy=evidence.gate.primary_basis,
        policy_version=POLICY_VERSION, model_gate=evidence.gate, policy_comparison=comparison,
        known_mandatory_budget_paise=known, desired_reserve_paise=state.reserve_paise,
        primary_reason=reason, forecast_basis=result.metadata.scenario_basis, reevaluate_when=triggers,
        important_dimensions=[key for key, _ in important.most_common()])
    result.recommendation = primary
    result.status = 'ready' if chosen else 'infeasible'
    result.explanation.reason = reason
    result.explanation.alternative_id = alternative.action.id if alternative else None
    if chosen and chosen.metrics:
        metrics = chosen.metrics
        result.explanation.downside = (f'{chosen.action.label}: conditional mandatory-miss frequency '
            f'{metrics.shortfall_probability:.1%}, reserve-breach frequency {metrics.reserve_breach_probability:.1%}; '
            f'expected contractual penalties {metrics.expected_penalty_paise} paise and '
            f'remaining liabilities {metrics.expected_total_remaining_liabilities_paise} paise. '
            'These scenario outcomes are uncertain, not guaranteed future cash.')
    result.explanation.comparison = 'Experimental rank compares modeled outcomes; the primary action follows the separately disclosed eligibility gate and policy.'
    result.metadata.source_state_digest = hashlib.sha256(state.model_dump_json().encode()).hexdigest()
    result.timeline = [TimelineItem(kind='mandatory' if item.mandatory else 'supplier', label=item.label,
        day=(item.due_date-state.base_date).days, amount_paise=item.outstanding_paise)
        for item in state.obligations.values() if item.outstanding_paise]
    result.timeline += [TimelineItem(kind='uncertain_receipt', label=item.label,
        day=(item.expected_date-state.base_date).days, amount_paise=item.amount_paise-item.received_paise)
        for item in state.receivables.values() if item.amount_paise > item.received_paise]
    result.timeline.sort(key=lambda item: (item.day, item.kind, item.label))
    result.metadata.assumptions.append('Primary policy is separately disclosed. All forecast risks remain conditional; prescribed stress frequencies are not learned probabilities.')
    return result
