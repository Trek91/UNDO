"""Executed, version-bound validation artifact; never tunes the production model or uses live data."""
import json
import random
from collections import Counter
from datetime import date
from pathlib import Path

from app.domain import baseline
from app.engine import EvaluationRequest, mean_paise
from app.evidence_types import SeedBenchmark, ValidationBenchmark
from app.model_evidence import BENCHMARK_PATH, model_evidence, source_hashes, weights_digest
from app.policies import OUTCOME_FIELDS, compare_policies
from app.prediction import generate_dataset, load_model
from app.results import quantile


def main() -> None:
    model = load_model()
    by_id = {row.id: row for row in generate_dataset(model.seed, 600)}
    seeds = [20261017, 20261034, 20261048]
    results = []
    benefit_sums = {identifier: 0 for identifier in model.test_ids}
    records = []
    for seed in seeds:
        rows: dict[str, list[dict]] = {}
        choices: dict[str, Counter] = {}
        for identifier in model.test_ids:
            invoice = by_id[identifier]
            state = baseline()
            shift = state.base_date-date(2026, 1, 1)
            state.receivables['customer'] = invoice.receivable.model_copy(update={
                'id': 'customer', 'created_date': invoice.receivable.created_date+shift,
                'expected_date': invoice.receivable.expected_date+shift})
            realized = {'customer': invoice.arrival_day if invoice.arrival_day is not None and invoice.arrival_day <= 7 else None}
            comparison = compare_policies(state, EvaluationRequest(paths=100, seed=seed), model, paths=[realized])
            row_by_id = {policy.id: policy for policy in comparison.policies}
            rule, ml = row_by_id['obligation_rule'].metrics, row_by_id['ml_informed'].metrics
            assert rule is not None and ml is not None
            benefit_sums[identifier] += rule.expected_penalty_paise-ml.expected_penalty_paise
            for policy in comparison.policies:
                assert policy.metrics is not None and policy.action_id is not None
                rows.setdefault(policy.id, []).append(policy.metrics.model_dump())
                choices.setdefault(policy.id, Counter())[policy.action_id] += 1
            records.append(dict(seed=seed, invoice_id=identifier, realized=realized,
                choices={key: value.action_id for key, value in row_by_id.items()},
                outcomes={key: {field: getattr(value.metrics, field) for field in OUTCOME_FIELDS} for key, value in row_by_id.items()}))
        summaries = {key: {field: mean_paise(sum(row[field] for row in values), len(values)) if field.endswith('paise')
                    else sum(row[field] for row in values)/len(values) for field in OUTCOME_FIELDS} for key, values in rows.items()}
        results.append(SeedBenchmark(seed=seed, policies=summaries, choices={key: dict(value) for key, value in choices.items()}))
    benefits = list(benefit_sums.values())
    rng = random.Random(20261017)
    boot = [mean_paise(sum(rng.choice(benefits) for _ in benefits), len(benefits)*len(seeds)) for _ in range(1000)]
    ci = [quantile(boot, .025), quantile(boot, .975)]
    advantage = ci[0] > 0 and all(
        row.policies['ml_informed']['shortfall_probability'] <= row.policies['obligation_rule']['shortfall_probability'] and
        row.policies['ml_informed']['reserve_breach_probability'] <= row.policies['obligation_rule']['reserve_breach_probability']
        for row in results)
    artifact = ValidationBenchmark(protocol='v3-heldout-paired-120x3-seeds-100-paths; 1000 invoice-cluster bootstrap replicates',
        model_version=model.version, weights_digest=weights_digest(model), source_hashes=source_hashes(),
        dataset_seed=model.seed, heldout_invoices=len(model.test_ids), paths_per_decision=100, seed_results=results,
        paired_penalty_benefit_paise=mean_paise(sum(benefits), len(benefits)*len(seeds)),
        paired_penalty_benefit_ci95=ci, decision_advantage=advantage,
        conclusion='Synthetic protocol shows positive paired fee improvement with no observed mandatory/reserve risk worsening.' if advantage else
            'No reliable incremental benefit over the obligation-aware rule established on this held-out protocol.',
        assumptions=['Original untouched held-out invoices and actual synthetic future per invoice; original fixed model.',
            'Policies choose using prediction/known facts only; realized futures are supplied for scoring afterward.',
            'Invoice-cluster resampling preserves dependence among repeated seed choices; monetary means round half-even.',
            'Synthetic evidence only. Three Monte Carlo seeds are not three independent real-world cohorts.'])
    BENCHMARK_PATH.parent.mkdir(exist_ok=True)
    BENCHMARK_PATH.write_text(artifact.model_dump_json(indent=2))
    out = Path('../docs/v3')
    (out/'heldout-policy-records.json').write_text(json.dumps(records, indent=2))
    evidence = model_evidence(model)
    (out/'model-evidence.json').write_text(evidence.model_dump_json(indent=2))
    assert evidence.benchmark is not None
    print(json.dumps(dict(status=evidence.status, gate=evidence.gate.model_dump(), benchmark=artifact.model_dump()), indent=2))


if __name__ == '__main__':
    main()
