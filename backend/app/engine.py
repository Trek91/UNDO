"""Counterfactual trajectories, distinct risk metrics and transparent risk-first selection."""
import hashlib
import json
import random
from typing import Literal
from uuid import uuid4

from pydantic import Field

from app.domain import Contract, State
from app.analysis_types import SensitivityReport
from app.evidence_types import DecisionEvidence
from app.prediction import HazardModel, load_model
from app.results import CashOutcomes, Metrics, quantile, wilson

ActionId = Literal["full", "partial", "defer", "hold"]
ENGINE_VERSION = 'counterfactual-v3'


def default_actions() -> list[ActionId]:
    return ["full", "partial", "defer", "hold"]


class EvaluationRequest(Contract):
    proposal_id: str = Field(default="proposal", min_length=1, max_length=80)
    horizon_days: int = Field(default=7, ge=1, le=30, strict=True)
    paths: int = Field(default=1000, ge=1, le=5000, strict=True)
    seed: int = Field(default=20261017, ge=0, le=2**32-1, strict=True)
    action_ids: list[ActionId] = Field(default_factory=default_actions,
                                     min_length=1, max_length=4)
    include_robustness: bool = False


class Candidate(Contract):
    id: ActionId
    label: str
    description: str
    valid: bool = True
    invalid_reason: str | None = None
    payments: list[tuple[int, int]] = Field(default_factory=list)
    penalty_paise: int = 0
    penalty_day: int = 1
    late_fee_paise: int = 0
    contractual_due_day: int = 0
    contractual_late: bool = False
    reconsider_day: int | None = None
    delay_paise_days: int = 0


class ActionResult(Contract):
    action: Candidate
    valid: bool
    metrics: Metrics | None = None
    rank: int | None = None


class Metadata(Contract):
    engine_version: str = 'legacy-unversioned'
    horizon_days: int
    paths: int
    seed: int
    model_version: str | None
    scenario_digest: str | None
    model_metrics: dict[str, float]
    dataset_seed: int | None
    scenario_basis: str = 'legacy-unspecified'
    source_state_digest: str | None = None
    ordering: str = "Mandatory deadlines, supplier commitments, then uncertain receipts; intraday risk retained."
    assumptions: list[str] = Field(default_factory=lambda: [
        "Synthetic data and synthetic-data model evaluation; no real-world accuracy claim.",
        "Shared arrival scenarios across every action; independent customer arrival draws.",
        "Hold assumes full settlement at day-1 review; no speculative value of information.",
        "Negative projected cash is a funding requirement, never actual settled cash.",
        "Future funding shortfalls are risks; only affordable confirmed events alter the ledger.",
    ])


class Explanation(Contract):
    reason: str
    principal_metric: str | None = None
    downside: str
    alternative_id: str | None = None
    comparison: str
    sensitive_to_receivables: bool
    sensitivity_note: str
    limitations: list[str]


class TimelineItem(Contract):
    kind: Literal['mandatory', 'supplier', 'uncertain_receipt']
    label: str
    day: int
    amount_paise: int


class Evaluation(Contract):
    id: str
    generation: int
    state_version: int
    status: Literal["ready", "infeasible", "unavailable"]
    recommendation: ActionId | None
    actions: list[ActionResult]
    snapshot: State
    request: EvaluationRequest
    metadata: Metadata
    explanation: Explanation
    scope: Literal['live', 'experiment'] = 'live'
    decision_evidence: DecisionEvidence | None = None
    robustness: SensitivityReport | None = None
    experiment_changes: dict[str, int | float | bool] = Field(default_factory=dict)
    timeline: list[TimelineItem] = Field(default_factory=list)


def candidates(state: State, request: EvaluationRequest) -> list[Candidate]:
    proposal = state.proposals.get(request.proposal_id)
    if proposal is None:
        raise ValueError("Unknown payment proposal")
    obligation = state.obligations[proposal.obligation_id]
    outstanding = obligation.outstanding_paise
    amount = proposal.amount_paise
    terms = obligation.terms
    due = (obligation.due_date-state.base_date).days
    partial = max(terms.minimum_partial_paise if terms else 0, (amount+1)//2)
    partial_day = due+(terms.partial_days if terms else 3)
    defer_day = due+(terms.defer_days if terms else 3)
    fee = terms.late_penalty_paise if terms else 0
    late_day = max(0, due+1)
    full = Candidate(id="full", label="Pay in full", description="Settle the proposed payment immediately.",
                     payments=[(0, amount)], contractual_late=due < 0,
                     penalty_paise=fee if due < 0 else 0, penalty_day=late_day)
    part = Candidate(id="partial", label="Split payment", description=f"Pay the permitted portion now; remainder on day {partial_day}.",
                     payments=[(0, partial), (partial_day, outstanding-partial)],
                     contractual_late=due < 0,
                     delay_paise_days=max(0, outstanding-partial)*partial_day)
    defer = Candidate(id="defer", label="Defer payment", description=f"Schedule settlement on day {defer_day}; contractual late fee applies.",
                      payments=[(defer_day, outstanding)], penalty_paise=fee if defer_day > due else 0,
                      penalty_day=late_day, contractual_late=defer_day > due,
                      delay_paise_days=outstanding*defer_day)
    hold = Candidate(id="hold", label="Hold for review", description="Review tomorrow; original due date remains in force.",
                     payments=[(1, outstanding)], penalty_paise=fee if 1 > due else 0,
                     penalty_day=late_day, contractual_late=1 > due, reconsider_day=1,
                     delay_paise_days=outstanding)
    result = []
    for candidate in [full, part, defer, hold]:
        candidate.late_fee_paise = fee
        candidate.contractual_due_day = partial_day if candidate.id == "partial" else due
        candidate.penalty_day = max(0, candidate.contractual_due_day+1)
        if due < 0:
            candidate.penalty_day = 0
        reason = None
        if not outstanding:
            reason = "The obligation is already settled."
        elif amount != outstanding:
            reason = "Proposal must match the remaining obligation; update the proposal before comparing settlement plans."
        elif candidate.id == "partial" and (not terms or not terms.allow_partial or partial >= outstanding):
            reason = "The contract does not permit this partial-payment arrangement."
        elif candidate.id == "defer" and (not terms or not terms.allow_deferral):
            reason = "The contract does not permit scheduled deferral."
        elif any(day < 0 for day, _ in candidate.payments):
            reason = "The contractual extension has already elapsed; refresh the settlement terms."
        elif any(day > request.horizon_days for day, _ in candidate.payments):
            reason = "Committed settlement falls outside the evaluation horizon."
        elif sum(value for day, value in candidate.payments if day == 0) > max(0, state.cash_paise-sum(
                item.outstanding_paise for item in state.obligations.values()
                if item.id != obligation.id and item.mandatory and item.due_date <= state.base_date)):
            reason = "Immediate payment exceeds settled cash after prior mandatory deadlines."
        if reason:
            candidate.valid = False
            candidate.invalid_reason = reason
        if candidate.id in request.action_ids:
            result.append(candidate)
    return result


def draw_scenarios(state: State, request: EvaluationRequest, model: HazardModel) -> list[dict[str, int | None]]:
    model.validate()
    rng = random.Random(request.seed)
    distributions: dict[str, list[float]] = {}
    for identifier, receivable in sorted(state.receivables.items()):
        if receivable.status == "settled":
            continue
        survival = 1.0
        cumulative = []
        for day in range(request.horizon_days+1):
            survival *= 1-model.hazard(receivable, state.base_date, day)
            cumulative.append(1-survival)
        distributions[identifier] = cumulative
    return [{identifier: next((day for day, p in enumerate(cdf) if draw <= p), None)
             for identifier, cdf in distributions.items() for draw in [rng.random()]}
            for _ in range(request.paths)]


def simulate(state: State, candidate: Candidate, scenarios: list[dict[str, int | None]], horizon: int,
             proposal_id: str = "proposal") -> Metrics:
    if not candidate.valid or not scenarios:
        raise ValueError("Valid action and nonempty scenarios required")
    target = state.proposals[proposal_id].obligation_id
    closing = [0]*(horizon+1)
    shortfall_paths = deficit_paths = reserve_paths = late_paths = 0
    shortfall_total = gap_total = minimum_total = reserve_gap_total = remaining_total = 0
    penalty_total = 0
    all_remaining = fee_remaining = 0
    minimum_samples: list[int] = []
    daily_samples: list[list[int]] = [[] for _ in range(horizon+1)]
    for arrivals in scenarios:
        # Cash is simulated available money; debt is unpaid due commitments. Their difference is net funding.
        cash = state.cash_paise
        debt: dict[str, int] = {}
        mandatory_due: dict[str, int] = {}
        measured: set[str] = set()
        minimum = cash
        shortfall = 0
        target_paid = 0
        late = candidate.contractual_late
        accrued: set[str] = set()
        payable: dict[str, int] = {}
        scheduled: dict[int, int] = {}
        for day, amount in candidate.payments:
            scheduled[day] = scheduled.get(day, 0)+amount
        other = sorted((o for o in state.obligations.values() if o.id != target and o.outstanding_paise),
                       key=lambda obligation: (not obligation.mandatory, obligation.due_date, obligation.id))
        for day in range(horizon+1):
            # Bring each external obligation due once; no repeated charging of overdue balances.
            for obligation in other:
                due = max(0, (obligation.due_date-state.base_date).days)
                if due == day:
                    debt[obligation.id] = obligation.outstanding_paise
                    if obligation.mandatory:
                        mandatory_due[obligation.id] = day
            if day in scheduled:
                debt[target] = debt.get(target, 0)+scheduled[day]
            if state.obligations[target].mandatory and day == max(0, candidate.contractual_due_day):
                mandatory_due[target] = day
            # Mandatory debts settle first; then the chosen supplier schedule, then other commitments.
            for identifier in sorted(debt, key=lambda key: (key not in mandatory_due, key != target, key)):
                if day < payable.get(identifier, 0):
                    continue
                due_amount = debt[identifier]
                payment = min(cash, due_amount)
                cash -= payment
                debt[identifier] -= payment
                if identifier == target:
                    target_paid += payment
                if identifier != target and identifier in mandatory_due and identifier not in measured:
                    shortfall += due_amount-payment
                    measured.add(identifier)
            target_outstanding = state.obligations[target].outstanding_paise-target_paid
            deadline = max(0, candidate.contractual_due_day)
            if target in mandatory_due and target not in measured and day >= deadline:
                shortfall += target_outstanding
                measured.add(target)
            if target_outstanding and day >= deadline:
                late = True
            # Latch fees at the missed deadline before receipts. Fees remain liabilities
            # even when their next-day payment falls beyond the chosen horizon.
            charges: list[tuple[str, int, int]] = []
            if late and (day >= deadline or candidate.penalty_day == 0):
                charges.append(("$target-penalty", candidate.late_fee_paise, candidate.penalty_day))
            for obligation in other:
                original_due = (obligation.due_date-state.base_date).days
                if obligation.terms and day >= max(0, original_due) and (
                        debt.get(obligation.id, 0) or original_due < 0):
                    charges.append((f"$penalty-{obligation.id}", obligation.terms.late_penalty_paise,
                                    max(0, original_due+1)))
            for identifier, fee, payment_day in charges:
                if identifier not in accrued:
                    debt[identifier] = fee
                    payable[identifier] = payment_day
                    penalty_total += fee
                    accrued.add(identifier)
            unscheduled_due = max(0, target_outstanding-debt.get(target, 0)) if day >= deadline else 0
            minimum = min(minimum, cash-sum(debt.values())-unscheduled_due)
            for identifier, arrival in arrivals.items():
                if arrival == day:
                    receivable = state.receivables[identifier]
                    cash += receivable.amount_paise-receivable.received_paise
            # Receipts can cure earlier funding gaps, but cannot erase a missed deadline.
            for identifier in sorted(debt, key=lambda key: (key not in mandatory_due, key != target, key)):
                if day < payable.get(identifier, 0):
                    continue
                payment = min(cash, debt[identifier])
                cash -= payment
                debt[identifier] -= payment
                if identifier == target:
                    target_paid += payment
            unscheduled_due = max(0, state.obligations[target].outstanding_paise-target_paid-debt.get(target, 0)) if day >= deadline else 0
            close = cash-sum(debt.values())-unscheduled_due
            closing[day] += close
            daily_samples[day].append(close)
        shortfall_paths += shortfall > 0
        deficit_paths += minimum < 0
        reserve_paths += minimum < state.reserve_paise
        late_paths += late
        shortfall_total += shortfall
        gap_total += max(0, -minimum)
        minimum_total += minimum
        reserve_gap_total += max(0, state.reserve_paise-minimum)
        remaining_total += max(0, state.obligations[target].outstanding_paise-target_paid)
        minimum_samples.append(minimum)
        fees = sum(value for identifier, value in debt.items() if identifier.startswith('$'))
        fee_remaining += fees
        all_remaining += max(0, state.obligations[target].outstanding_paise-target_paid)+fees+sum(
            debt.get(item.id, 0) if (item.due_date-state.base_date).days <= horizon else item.outstanding_paise
            for item in other)
    paths = len(scenarios)
    return Metrics(daily_paise=[mean_paise(value, paths) for value in closing],
        shortfall_probability=shortfall_paths/paths, expected_shortfall_paise=mean_paise(shortfall_total, paths),
        cash_deficit_probability=deficit_paths/paths, expected_peak_cash_deficit_paise=mean_paise(gap_total, paths),
        expected_minimum_paise=mean_paise(minimum_total, paths), reserve_breach_probability=reserve_paths/paths,
        expected_peak_reserve_deficit_paise=mean_paise(reserve_gap_total, paths),
        reserve_maintained_probability=1-reserve_paths/paths, expected_penalty_paise=mean_paise(penalty_total, paths),
        late_payment_probability=late_paths/paths, expected_remaining_paise=mean_paise(remaining_total, paths),
        expected_total_remaining_liabilities_paise=mean_paise(all_remaining, paths),
        expected_remaining_fees_paise=mean_paise(fee_remaining, paths),
        probability_intervals={name: wilson(count, paths) for name, count in [
            ('shortfall_probability', shortfall_paths), ('reserve_breach_probability', reserve_paths),
            ('cash_deficit_probability', deficit_paths), ('late_payment_probability', late_paths)]},
        cash_outcomes=CashOutcomes(sampled_worst_minimum_paise=min(minimum_samples),
            minimum_p05_paise=quantile(minimum_samples, .05), minimum_p50_paise=quantile(minimum_samples, .5),
            minimum_p95_paise=quantile(minimum_samples, .95),
            daily_p05_paise=[quantile(values, .05) for values in daily_samples],
            daily_p50_paise=[quantile(values, .5) for values in daily_samples],
            daily_p95_paise=[quantile(values, .95) for values in daily_samples]))


def mean_paise(total: int, count: int) -> int:
    """Exact half-even integer mean, including signed funding requirements."""
    quotient, remainder = divmod(total, count)
    return quotient+int(2*remainder > count or (2*remainder == count and quotient % 2 != 0))


RANK_FIELDS = ("shortfall_probability", "expected_shortfall_paise", "expected_penalty_paise",
               "reserve_breach_probability")


def objective_key(result: ActionResult) -> tuple[float | int | str, ...]:
    if result.metrics is None:
        raise ValueError('Calculated metrics required for ranking')
    return tuple(getattr(result.metrics, name) for name in RANK_FIELDS)+(
        result.action.delay_paise_days, result.metrics.expected_remaining_paise, result.action.id)
_DEFAULT_MODEL = object()


def evaluate(state: State, request: EvaluationRequest,
             model: HazardModel | None | object = _DEFAULT_MODEL, *,
             scenarios_override: list[dict[str, int | None]] | None = None,
             scenario_basis: str = 'ml_hazard') -> Evaluation:
    active_model = load_model() if model is _DEFAULT_MODEL else model
    action_list = candidates(state, request)
    scenarios: list[dict[str, int | None]] | None
    try:
        if scenarios_override is not None:
            if len(scenarios_override) != request.paths or any(identifier not in state.receivables or
                    (day is not None and (isinstance(day, bool) or not isinstance(day, int) or not 0 <= day <= request.horizon_days))
                    for path in scenarios_override for identifier, day in path.items()):
                raise ValueError('Invalid prescribed scenario paths')
            scenarios = scenarios_override
        else:
            scenarios = draw_scenarios(state, request, active_model) if isinstance(active_model, HazardModel) else None
    except ValueError:
        scenarios = None
    results = [ActionResult(action=action, valid=action.valid,
               metrics=simulate(state, action, scenarios, request.horizon_days, request.proposal_id)
               if action.valid and scenarios else None) for action in action_list]

    ranked = sorted((result for result in results if result.metrics is not None), key=objective_key)
    for index, result in enumerate(ranked):
        result.rank = index+1
    best = ranked[0] if ranked else None
    alternative = ranked[1] if len(ranked) > 1 else None
    principal = None
    if best and alternative:
        principal = next((name for name in RANK_FIELDS if getattr(best.metrics, name) != getattr(alternative.metrics, name)),
                         "payment_delay")
    reason = (f"{best.action.label} ranks first under the documented risk-first objective."
              if best else "No valid action can be ranked." if scenarios else "Predictive model unavailable; evaluation cannot be ranked.")
    downside = ("This action can still miss mandatory obligations or breach the desired reserve."
                if best and best.metrics and (best.metrics.shortfall_probability or best.metrics.reserve_breach_probability)
                else "Results remain conditional on synthetic payment-arrival assumptions.")
    sensitive = any(result.metrics and result.metrics.shortfall_probability not in (0, 1) for result in results)
    explanation = Explanation(reason=reason, principal_metric=principal, downside=downside,
        alternative_id=alternative.action.id if alternative else None,
        comparison=f"Compared with {alternative.action.label}, the first ranking distinction is {principal}."
                   if alternative else "No second valid alternative is available.",
        sensitive_to_receivables=bool(sensitive),
        sensitivity_note="At least one action has both successful and missed-obligation paths."
                         if sensitive else "No mixed mandatory-shortfall outcomes were observed in this sample; other metrics can remain uncertain.",
        limitations=["Synthetic training and test data do not establish real-world predictive accuracy.",
                     "Improved outcomes over a transparent obligation-aware rule have not been established.",
                     "Hold continuation is an explicit assumption, not a promise of renegotiation.",
                     "Finite simulation paths introduce sampling error; customer shocks are not correlated."])
    metadata = Metadata(horizon_days=request.horizon_days, paths=request.paths, seed=request.seed,
        scenario_basis=scenario_basis,
        engine_version=ENGINE_VERSION,
        model_version=active_model.version if isinstance(active_model, HazardModel) else None,
        scenario_digest=hashlib.sha256(json.dumps(scenarios, sort_keys=True).encode()).hexdigest()[:16] if scenarios else None,
        model_metrics=active_model.metrics if isinstance(active_model, HazardModel) else {},
        dataset_seed=active_model.seed if isinstance(active_model, HazardModel) else None)
    return Evaluation(id=str(uuid4()), generation=state.generation, state_version=state.version,
                      status="ready" if best else "infeasible" if scenarios else "unavailable",
                      recommendation=best.action.id if best else None, actions=results,
                      snapshot=state.model_copy(deep=True), request=request, metadata=metadata, explanation=explanation)
