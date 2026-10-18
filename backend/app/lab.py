"""Scenario Lab computes snapshots without financial events; saving archives an experiment."""
import hashlib

from pydantic import Field

from app.decisions import assess
from app.domain import Contract, State
from app.engine import Evaluation, EvaluationRequest
from app.prediction import HazardModel
from app.scenarios import ScenarioChanges, changed_state
from app.store import Conflict


class LabRequest(Contract):
    changes: ScenarioChanges = Field(default_factory=ScenarioChanges)
    simulation: EvaluationRequest = Field(default_factory=EvaluationRequest)
    source_state_digest: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')


class LabResult(Contract):
    baseline: Evaluation
    modified: Evaluation
    recommendation_changed: bool
    source_state_digest: str
    stale: bool = False
    semantics: str = 'Hypothetical snapshots only. Save archives an experiment; revert discards local inputs. Neither changes the live ledger.'


def run_lab(state: State, request: LabRequest, model: HazardModel | None) -> LabResult:
    digest = hashlib.sha256(state.model_dump_json().encode()).hexdigest()
    if request.source_state_digest is not None and request.source_state_digest != digest:
        raise Conflict('The source financial state changed; evaluate this experiment again before saving')
    original = assess(state, request.simulation.model_copy(update={'include_robustness': False}), model)
    changed = changed_state(state, request.changes, request.simulation.proposal_id)
    modified = assess(changed, request.simulation, model, request.changes.receipt_probability)
    modified.scope = 'experiment'
    modified.metadata.source_state_digest = digest
    modified.experiment_changes = request.changes.model_dump(exclude_none=True)
    return LabResult(baseline=original, modified=modified, source_state_digest=digest,
        recommendation_changed=original.recommendation != modified.recommendation)
