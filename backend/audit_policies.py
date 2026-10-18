"""Three fixed policies evaluated against identical untouched held-out invoice futures."""
import json
from collections import Counter
from datetime import date
from pathlib import Path

from app.domain import baseline
from app.engine import RANK_FIELDS, EvaluationRequest, candidates, evaluate, mean_paise, simulate
from app.prediction import generate_dataset, load_model


def run() -> None:
    model = load_model()
    by_id = {record.id: record for record in generate_dataset(model.seed, 600)}
    reports: dict[str, list[dict]] = {name: [] for name in ('balance_only', 'obligation_rule', 'worst_case_rule', 'ml_simulation')}
    selections: dict[str, Counter] = {name: Counter() for name in reports}
    details = []
    request = EvaluationRequest(paths=1000)
    for identifier in model.test_ids:
        record = by_id[identifier]
        state = baseline()
        shift = state.base_date-date(2026, 1, 1)
        state.receivables['customer'] = record.receivable.model_copy(update={
            'id': 'customer', 'created_date': record.receivable.created_date+shift,
            'expected_date': record.receivable.expected_date+shift})
        actions = {action.id: action for action in candidates(state, request) if action.valid}
        # Rule assumes no uncertain incoming cash; same explicit objective as production.
        worst = {key: simulate(state, action, [{'customer': None}], 7) for key, action in actions.items()}
        worst_case_rule = min(actions, key=lambda key: tuple(getattr(worst[key], field) for field in RANK_FIELDS)+(
            actions[key].delay_paise_days, worst[key].expected_remaining_paise, key))
        required = state.reserve_paise+sum(item.outstanding_paise for item in state.obligations.values()
            if item.mandatory and item.id != 'supplier' and (item.due_date-state.base_date).days <= 7)
        rule = next((key for key in ('full', 'partial', 'hold', 'defer') if key in actions and
            sum(amount for day, amount in actions[key].payments if day == 0)+required <= state.cash_paise), 'hold')
        prediction = evaluate(state, request, model)
        chosen = {'balance_only': 'full' if 'full' in actions else 'hold',
                  'obligation_rule': rule, 'worst_case_rule': worst_case_rule, 'ml_simulation': prediction.recommendation}
        realized = {'customer': record.arrival_day if record.arrival_day is not None and record.arrival_day <= 7 else None}
        row = {'invoice_id': identifier, 'arrival_day': realized['customer'], 'choices': chosen, 'outcomes': {}}
        for name, action_id in chosen.items():
            assert action_id is not None
            outcome = simulate(state, actions[action_id], [realized], 7).model_dump()
            reports[name].append(outcome)
            selections[name][action_id] += 1
            row['outcomes'][name] = outcome
        details.append(row)
    summary = {}
    for name, rows in reports.items():
        summary[name] = {'choices': dict(selections[name]), 'scenarios': len(rows),
            **{field: sum(row[field] for row in rows)/len(rows) for field in (
                'shortfall_probability', 'cash_deficit_probability', 'reserve_breach_probability', 'late_payment_probability')},
            **{field: mean_paise(sum(row[field] for row in rows), len(rows)) for field in (
                'expected_shortfall_paise', 'expected_penalty_paise', 'expected_peak_reserve_deficit_paise', 'expected_remaining_paise')}}
    output = dict(model_version=model.version, seed=model.seed, paths_per_ml_evaluation=1000,
        heldout_invoices=120, protocol='Original held-out invoice inputs and realized arrival days; dates translated without changing relative features. Same baseline obligations/cash and same future for all policies. No retraining or tuning.',
        summary=summary, records=details)
    Path('../docs/audit/policy-comparison.json').write_text(json.dumps(output, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    run()
