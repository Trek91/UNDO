"""HTTP contracts and durable real-time integration. No endpoint executes a real payment."""
import asyncio
import json
import logging
import os
import sqlite3
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.domain import Amount, Contract, Event, Nonnegative, Obligation, Receivable, State, Terms, baseline
from app.engine import ENGINE_VERSION, Evaluation, EvaluationRequest
from app.decisions import assess as evaluate
from app.lab import LabRequest, LabResult, run_lab
from app.evidence_types import ModelEvidence
from app.model_evidence import model_evidence
from app.prediction import load_model
from app.store import Conflict, Store
from app.metric_reporting import ClassificationReport, classification_report

logger = logging.getLogger("undo")


class DecisionRecord(Contract):
    evaluation: Evaluation
    stale: bool
    model_statistics: ClassificationReport | None = None


class Overview(Contract):
    state: State
    outstanding_obligations_paise: int
    outstanding_receivables_paise: int
    latest_decision: DecisionRecord | None
    recalculating: bool
    worker_error: str | None
    notification_cursor: int
    near_term_mandatory_paise: int = 0
    near_term_horizon_days: int = 7


class Acceptance(Contract):
    duplicate: bool
    event_id: str
    generation: int
    state_version: int


class EventRecord(Contract):
    seq: int
    event: Event


class EventPage(Contract):
    items: list[EventRecord]
    next_before: int | None


class DecisionPage(Contract):
    items: list[DecisionRecord]
    next_before: str | None


class AuditRecord(Contract):
    seq: int
    generation: int
    kind: str
    detail: dict[str, Any]
    created_at: str


class AuditPage(Contract):
    items: list[AuditRecord]
    next_before: int | None


class FeedResult(Contract):
    completed: bool
    accepted: Acceptance | None


class Health(Contract):
    status: str
    database: str
    model_version: str | None
    synthetic: bool = True


class ScenarioRequest(Contract):
    cash_paise: Nonnegative = 10000000
    reserve_paise: Nonnegative = 1000000
    supplier_paise: Amount = 6000000
    expense_paise: Amount = 5000000
    receivable_paise: Amount = 4000000
    supplier_due_days: int = Query(0, ge=0, le=30)
    expense_due_days: int = Query(1, ge=0, le=30)
    receivable_due_days: int = Query(1, ge=0, le=30)
    terms: Terms = Terms()


def create_app(database: str | None = None) -> FastAPI:
    lock = asyncio.Lock()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.store = Store(database or os.environ.get("UNDO_DB") or "data/undo.db")
        try:
            app.state.model = await asyncio.to_thread(load_model)
        except Exception:
            logger.exception("Predictive model failed to initialize")
            app.state.model = None
        app.state.worker_error = None

        async def worker() -> None:
            while True:
                try:
                    async with lock:
                        pending = await asyncio.to_thread(app.state.store.pending)
                        if pending:
                            snapshot, raw = pending
                            request = EvaluationRequest.model_validate(raw)
                            result = await asyncio.to_thread(evaluate, snapshot, request, app.state.model)
                            await asyncio.to_thread(app.state.store.save_evaluation, result.model_dump(mode="json"), raw)
                            app.state.worker_error = None
                    await asyncio.sleep(0.15)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Durable recalculation failed; will retry")
                    app.state.worker_error = "Recalculation failed; stored work will be retried."
                    await asyncio.sleep(5)

        task = asyncio.create_task(worker())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    app = FastAPI(title="UNDO V3", version="3.0.0", description="Synthetic financial decision intelligence. No real payments.",
                  lifespan=lifespan)
    origins = os.environ.get("UNDO_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
                       allow_headers=["Content-Type", "If-Match", "Last-Event-ID"])

    @app.middleware("http")
    async def boundary(request: Request, call_next: Any) -> Response:
        if request.method in ("POST", "PUT", "PATCH"):
            origin = request.headers.get("origin")
            if origin and origin not in origins and origin != str(request.base_url).rstrip("/"):
                return JSONResponse({"error": {"code": "origin_denied", "message": "Origin is not allowed."}}, 403)
            size = 0
            chunks = []
            async for chunk in request.stream():
                size += len(chunk)
                if size > 65536:
                    return JSONResponse({"error": {"code": "body_too_large", "message": "Request exceeds 64 KiB."}}, 413)
                chunks.append(chunk)
            request._body = b"".join(chunks)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        issues = [{"field": ".".join(str(part) for part in issue["loc"]), "message": issue["msg"]}
                  for issue in exc.errors()]
        return JSONResponse({"error": {"code": "validation_error", "message": "Check the submitted fields.",
                                       "issues": issues}}, 422)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse({"error": {"code": f"http_{exc.status_code}", "message": str(exc.detail)}}, exc.status_code)

    @app.exception_handler(Conflict)
    async def conflict_error(request: Request, exc: Conflict) -> JSONResponse:
        return JSONResponse({"error": {"code": "conflict", "message": str(exc)}}, 409)

    @app.exception_handler(ValueError)
    async def domain_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse({"error": {"code": "domain_error", "message": str(exc)}}, 422)

    @app.exception_handler(sqlite3.DatabaseError)
    async def database_error(request: Request, exc: sqlite3.DatabaseError) -> JSONResponse:
        logger.error("Database operation failed: %s", type(exc).__name__)
        return JSONResponse({"error": {"code": "database_unavailable", "message": "Storage is unavailable. Retry shortly."}}, 503)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unexpected application failure")
        return JSONResponse({"error": {"code": "internal_error", "message": "The request could not be completed."}}, 500)

    def store() -> Store:
        return app.state.store

    def decision_record(raw: dict[str, Any], state: State | None = None) -> DecisionRecord:
        state = state or store().state()
        return DecisionRecord(evaluation=Evaluation.model_validate(raw),
                              model_statistics=classification_report(raw['metadata'].get('model_metrics', {})),
                              stale=(raw.get('scope') == 'experiment' or (raw["generation"], raw["state_version"]) != (state.generation, state.version) or
                                     raw['metadata'].get('engine_version') != ENGINE_VERSION))

    @app.get("/api/health", response_model=Health)
    def health() -> Health:
        store().state()
        model = app.state.model
        return Health(status="ok" if model and not app.state.worker_error else "degraded", database="ok",
                      model_version=model.version if model else None)

    @app.get("/api/overview", response_model=Overview)
    def overview() -> Overview:
        state, latest, pending, cursor = store().overview_snapshot()
        return Overview(state=state,
            outstanding_obligations_paise=sum(item.outstanding_paise for item in state.obligations.values()),
            outstanding_receivables_paise=sum(item.amount_paise-item.received_paise for item in state.receivables.values()),
            latest_decision=decision_record(latest, state) if latest else None,
            recalculating=pending, worker_error=app.state.worker_error, notification_cursor=cursor,
            near_term_horizon_days=latest['request']['horizon_days'] if latest else 7,
            near_term_mandatory_paise=sum(item.outstanding_paise for item in state.obligations.values()
                if item.mandatory and item.due_date <= state.base_date+timedelta(days=latest['request']['horizon_days'] if latest else 7)))

    @app.get('/api/model/evidence', response_model=ModelEvidence)
    def evidence_center() -> ModelEvidence:
        return model_evidence(app.state.model)

    @app.post('/api/lab/evaluate', response_model=LabResult)
    async def lab_evaluate(request: LabRequest, expected_generation: int = Query(..., ge=1),
                           expected_version: int = Query(..., ge=0)) -> LabResult:
        async with lock:
            snapshot = await asyncio.to_thread(store().analysis_snapshot, expected_version, expected_generation)
            result = await asyncio.to_thread(run_lab, snapshot, request, app.state.model)
            current = store().state()
            result.stale = (current.generation, current.version) != (snapshot.generation, snapshot.version)
            return result

    @app.post('/api/lab/save', response_model=DecisionRecord)
    async def lab_save(request: LabRequest, expected_generation: int = Query(..., ge=1),
                       expected_version: int = Query(..., ge=0)) -> DecisionRecord:
        if request.source_state_digest is None:
            raise HTTPException(422, 'Evaluate and supply the exact source digest before saving an experiment.')
        async with lock:
            snapshot = await asyncio.to_thread(store().analysis_snapshot, expected_version, expected_generation)
            result = await asyncio.to_thread(run_lab, snapshot, request, app.state.model)
            await asyncio.to_thread(store().save_experiment, result.modified.model_dump(mode='json'), request.simulation.model_dump(mode='json'))
            return decision_record(result.modified.model_dump(mode='json'))

    @app.post('/api/decisions/recalculate', response_model=State)
    def recalculate(expected_generation: int = Query(..., ge=1), expected_version: int = Query(..., ge=0)) -> State:
        return store().recalculate(expected_version, expected_generation)

    @app.get("/api/obligations", response_model=list[Obligation])
    def obligations() -> list[Obligation]:
        return list(store().state().obligations.values())

    @app.get("/api/receivables", response_model=list[Receivable])
    def receivables() -> list[Receivable]:
        return list(store().state().receivables.values())

    @app.get("/api/events", response_model=EventPage)
    def events(limit: int = Query(50, ge=1, le=100), before: int | None = Query(None, ge=1),
               generation: int | None = Query(None, ge=1)) -> EventPage:
        items = store().events(limit, before, generation)
        return EventPage(items=[EventRecord.model_validate(item) for item in items],
                         next_before=items[-1]["seq"] if len(items) == limit else None)

    @app.post("/api/events", response_model=Acceptance, status_code=201)
    def accept_event(event: Event, response: Response,
                     expected_version: int | None = Query(None, ge=0),
                     expected_generation: int | None = Query(None, ge=1)) -> Acceptance:
        # Python 3.12's Windows wall clock can lag a browser timestamp by one
        # 15.625ms tick. Wait for the clock; never relax the reducer's future guard.
        resolution = min(time.get_clock_info('time').resolution, 0.05)
        ahead = (event.timestamp-datetime.now(timezone.utc)).total_seconds()
        if 0 < ahead <= resolution:
            time.sleep(resolution)
        result = Acceptance.model_validate(store().accept(event, expected_version, expected_generation))
        if result.duplicate:
            response.status_code = 200
        return result

    @app.get("/api/decisions", response_model=DecisionPage)
    def decisions(limit: int = Query(30, ge=1, le=100), before: str | None = Query(None, max_length=80),
                  generation: int | None = Query(None, ge=1)) -> DecisionPage:
        state = store().state()
        rows = store().decisions(limit, before, generation)
        cursor = store().decision_cursor(rows[-1]['id']) if rows else None
        return DecisionPage(items=[decision_record(row, state) for row in rows],
                            next_before=cursor if len(rows) == limit else None)

    @app.post("/api/decisions/evaluate", response_model=DecisionRecord)
    async def evaluate_payment(request: EvaluationRequest, expected_version: int | None = Query(None, ge=0),
                               expected_generation: int | None = Query(None, ge=1)) -> DecisionRecord:
        if request.proposal_id not in store().state().proposals:
            raise HTTPException(404, "Payment proposal not found.")
        async with lock:
            snapshot = await asyncio.to_thread(store().schedule, request.model_dump(mode="json"), expected_version, expected_generation)
            result = await asyncio.to_thread(evaluate, snapshot, request, app.state.model)
            await asyncio.to_thread(store().save_evaluation, result.model_dump(mode="json"), request.model_dump(mode="json"))
            return decision_record(result.model_dump(mode="json"))

    @app.get("/api/decisions/{identifier}", response_model=DecisionRecord)
    def decision(identifier: str) -> DecisionRecord:
        raw = store().decision(identifier)
        if raw is None:
            raise HTTPException(404, "Decision evaluation not found.")
        return decision_record(raw)

    @app.get("/api/audit", response_model=AuditPage)
    def audit(limit: int = Query(50, ge=1, le=100), before: int | None = Query(None, ge=1)) -> AuditPage:
        items = store().audit(limit, before)
        return AuditPage(items=[AuditRecord.model_validate(item) for item in items],
                         next_before=items[-1]["seq"] if len(items) == limit else None)

    @app.post("/api/demo/events/next", response_model=FeedResult)
    def next_demo(expected_version: int | None = Query(None, ge=0),
                  expected_generation: int | None = Query(None, ge=1)) -> FeedResult:
        return FeedResult.model_validate(store().next_demo(expected_version, expected_generation))

    @app.post("/api/demo/reset", response_model=State)
    def reset(expected_version: int | None = Query(None, ge=0),
              expected_generation: int | None = Query(None, ge=1)) -> State:
        return store().reset(expected_version, expected_generation)

    @app.post("/api/demo/scenario", response_model=State)
    def scenario(request: ScenarioRequest, expected_version: int | None = Query(None, ge=0),
                 expected_generation: int | None = Query(None, ge=1)) -> State:
        from datetime import timedelta
        state = baseline()
        state.cash_paise = request.cash_paise
        state.reserve_paise = request.reserve_paise
        state.obligations["supplier"].amount_paise = request.supplier_paise
        state.obligations["supplier"].due_date = state.base_date+timedelta(days=request.supplier_due_days)
        state.obligations["supplier"].terms = request.terms
        state.proposals["proposal"].amount_paise = request.supplier_paise
        state.obligations["operations"].amount_paise = request.expense_paise
        state.obligations["operations"].due_date = state.base_date+timedelta(days=request.expense_due_days)
        state.receivables["customer"].amount_paise = request.receivable_paise
        state.receivables["customer"].expected_date = state.base_date+timedelta(days=request.receivable_due_days)
        return store().scenario(state, expected_version, expected_generation)

    @app.get("/api/events/stream")
    async def stream(request: Request, after: int | None = Query(None, ge=0, le=2**63-1),
                     last_event_id: str | None = Header(None), once: bool = False) -> StreamingResponse:
        if last_event_id is not None:
            try:
                after = int(last_event_id)
                if not 0 <= after <= 2**63-1:
                    raise ValueError
            except ValueError as exc:
                raise HTTPException(422, "Invalid event cursor.") from exc
        with store().connection() as conn:
            latest_cursor = conn.execute("SELECT COALESCE(MAX(seq),0) FROM notifications").fetchone()[0]
        cursor = latest_cursor if after is None else after

        async def messages() -> AsyncIterator[str]:
            nonlocal cursor
            state = store().state()
            yield f"event: snapshot\ndata: {json.dumps({'generation': state.generation, 'state_version': state.version})}\n\n"
            if cursor > latest_cursor:
                cursor = latest_cursor
                yield f"event: reset\nid: {cursor}\ndata: {{\"refresh\": true}}\n\n"
            heartbeat = time.monotonic()
            while True:
                rows = await asyncio.to_thread(store().notifications, cursor)
                for row in rows:
                    cursor = row["seq"]
                    yield f"id: {cursor}\nevent: update\ndata: {json.dumps(row)}\n\n"
                if once or await request.is_disconnected():
                    break
                if time.monotonic()-heartbeat > 15:
                    yield ": heartbeat\n\n"
                    heartbeat = time.monotonic()
                await asyncio.sleep(0.25)

        return StreamingResponse(messages(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    static = Path(os.environ.get("UNDO_STATIC", "../frontend/dist"))
    if static.is_dir():
        app.mount("/assets", StaticFiles(directory=static / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            if path.startswith("api/"):
                raise HTTPException(404, "Endpoint not found.")
            return FileResponse(static / "index.html")

    return app


app = create_app()
