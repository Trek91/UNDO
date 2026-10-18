"""Pure, bounded hypothetical changes. No event, ledger settlement or persistence here."""
import random
from datetime import timedelta

from pydantic import Field

from app.domain import Amount, Contract, Nonnegative, Obligation, State
from app.engine import Evaluation, EvaluationRequest, draw_scenarios, evaluate
from app.prediction import HazardModel


class ScenarioChanges(Contract):
    receipt_delay_days: int | None = Field(default=None, ge=0, le=14, strict=True)
    receipt_probability: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    unexpected_expense_paise: Nonnegative | None = None
    mandatory_due_days: int | None = Field(default=None, ge=0, le=30, strict=True)
    proposed_amount_paise: Amount | None = None
    supplier_due_days: int | None = Field(default=None, ge=-7, le=30, strict=True)
    partial_days: int | None = Field(default=None, ge=1, le=30, strict=True)
    minimum_partial_paise: Amount | None = None
    allow_partial: bool | None = None
    penalty_paise: Nonnegative | None = None
    reserve_paise: Nonnegative | None = None


def receipt_id(state: State) -> str | None:
    return next((key for key, item in sorted(state.receivables.items()) if item.status != 'settled'), None)


def mandatory_id(state: State, proposal_id: str) -> str | None:
    target = state.proposals[proposal_id].obligation_id
    return next((key for key, item in sorted(state.obligations.items()) if item.mandatory and key != target), None)


def changed_state(state: State, changes: ScenarioChanges, proposal_id: str = 'proposal') -> State:
    result = state.model_copy(deep=True)
    proposal = result.proposals.get(proposal_id)
    if proposal is None:
        raise ValueError('Unknown payment proposal')
    target = result.obligations[proposal.obligation_id]
    customer = receipt_id(result)
    if changes.receipt_delay_days is not None:
        if customer is None:
            raise ValueError('No unpaid receivable to change')
        result.receivables[customer].expected_date += timedelta(days=changes.receipt_delay_days)
    if changes.proposed_amount_paise is not None:
        target.amount_paise = target.paid_paise+changes.proposed_amount_paise
        proposal.amount_paise = changes.proposed_amount_paise
    if changes.supplier_due_days is not None:
        target.due_date = result.base_date+timedelta(days=changes.supplier_due_days)
    for name, term in [('partial_days', 'partial_days'), ('minimum_partial_paise', 'minimum_partial_paise'),
                       ('allow_partial', 'allow_partial'), ('penalty_paise', 'late_penalty_paise')]:
        value = getattr(changes, name)
        if value is not None:
            if target.terms is None:
                raise ValueError('No supplier terms support this change')
            setattr(target.terms, term, value)
    if changes.reserve_paise is not None:
        result.reserve_paise = changes.reserve_paise
    mandatory = mandatory_id(result, proposal_id)
    if changes.mandatory_due_days is not None:
        if mandatory is None:
            raise ValueError('No separate mandatory obligation to reschedule')
        result.obligations[mandatory].due_date = result.base_date+timedelta(days=changes.mandatory_due_days)
    if changes.unexpected_expense_paise:
        identifier = next(f'v3-lab-unexpected-{i}' for i in range(len(result.obligations)+1)
                          if f'v3-lab-unexpected-{i}' not in result.obligations)
        result.obligations[identifier] = Obligation(id=identifier, label='Hypothetical unexpected expense',
            amount_paise=changes.unexpected_expense_paise, due_date=result.base_date+timedelta(days=1), mandatory=True)
    return State.model_validate(result.model_dump())


def scenario_evaluation(state: State, request: EvaluationRequest, model: HazardModel | None,
                        probability: float | None = None) -> Evaluation:
    if probability is None and model is not None:
        result = evaluate(state, request, model)
        if result.status != 'unavailable':
            return result
    try:
        paths = draw_scenarios(state, request, model) if model else [{} for _ in range(request.paths)]
    except ValueError:
        paths = [{} for _ in range(request.paths)]
        model = None
    for path in paths:
        for key in state.receivables:
            path.setdefault(key, None)
    basis = 'prescribed_stress'
    customer = receipt_id(state)
    if probability is not None:
        if customer is None:
            raise ValueError('No unpaid receivable for prescribed arrival probability')
        day = min(request.horizon_days, max(0, (state.receivables[customer].expected_date-state.base_date).days))
        rng = random.Random(request.seed)
        identifiers = [key for key, item in sorted(state.receivables.items()) if item.status != 'settled']
        for path in paths:
            for key in identifiers:
                draw = rng.random()
                if key == customer:
                    path[key] = day if draw < probability else None
        basis = 'prescribed_receipt'
    result = evaluate(state, request, model, scenarios_override=paths, scenario_basis=basis)
    if basis == 'prescribed_stress':
        for action in result.actions:
            if action.metrics:
                action.metrics.probability_intervals = {}
    result.metadata.assumptions.append('Prescribed stress uses no uncertain receipts; prescribed probability uses one receipt at the expected day clipped to this horizon. Neither is a learned probability.')
    return result
