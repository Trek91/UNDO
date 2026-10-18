# Architecture

React/TypeScript/Vite renders FastAPI contracts; no financial ranking occurs in the browser. API → validated domain events → SQLite transaction → rebuildable financial state. Immutable evaluation snapshots feed prediction, shared scenario simulation, lexicographic selection and structured explanations. A durable work queue and notification log support recalculation and SSE recovery. One Uvicorn process owns a bounded evaluation worker. The production process serves compiled frontend assets and the API.

SQLite is appropriate for a local, single-business synthetic demonstration. Public multi-user hosting requires authentication, authorization, business isolation, TLS, backups, rate limits and operational monitoring. No external financial integration or LLM is required.

## Persistence and real-time flow

Schema version 1 stores demo generations, accepted events, immutable evaluations, a coalesced pending-job table, notifications and material-change audit records. Unknown schema versions are rejected without modification. Reset/scenario creation starts a new generation; older financial history is retained.

Events commit under BEGIN IMMEDIATE. Replay starts from the generation's immutable initial state, sorts by effective UTC time with insertion sequence ties, validates every transition and writes the rebuilt state atomically. Retries compare canonical typed payloads. An event-ID conflict, invalid historical replay or database failure rolls back all effects and notifications.

Logical event identity now spans generations; legacy duplicate rows remain intact. An
identical retry returns its original generation/acceptance version without reapplying cash.
All mutation endpoints support atomic expected_generation/expected_version guards, supplied
by the UI. Overview state/decision/pending/cursor facts share one SQLite read transaction.
New evaluations record engine counterfactual-v2; older calculations retain unversioned
provenance and are marked stale. Client refreshes reject regressing state, scope history to
the selected generation, retain overlapping pages and preserve a recoverable cursor across gaps.

An event affecting an active proposal queues recalculation in that transaction. A single bounded process worker reads a consistent snapshot, computes outside the write transaction and stores a versioned result. Completing an older result cannot remove newer queued work or become the current recommendation. SSE publishes only durable notifications; reconnecting clients replay cursors and refresh authoritative snapshots. Dashboard refreshes read results and never train or simulate unnecessarily.

The frontend uses generated OpenAPI request/response types, request sequence guards, stale labels, an error boundary and explicit user feedback. Native local testing, native Linux container testing, emulated s390x container testing and real IBM host deployment remain separate evidence categories. The model and simulator require no heavyweight ML runtime. A required OpenTelemetry API dependency of FastAPI is installed, but no telemetry SDK/exporter or external service is configured.


## V3 additions

The same FastAPI process orchestrates evidence-gated decisions. `results.py` defines
quantiles/intervals; `scenarios.py` clones hypothetical state; `robustness.py` runs bounded
one-factor cases; `policies.py` separates policy selection from common-future scoring;
`model_evidence.py` validates actual diagnostics and the source-bound held-out artifact;
`decisions.py` selects the disclosed primary policy. The offline validation and benchmark
scripts write actual evidence files; core decisions require no external AI provider.

`/api/lab/evaluate` is ephemeral. `/api/lab/save` archives `scope=experiment`, guarded by
source digest and generation/version, and cannot change generations.request, event tables,
settled cash, pending live jobs, or the overview's live result. Recalculate queues the
original request verbatim. Existing SQLite schema1 is unchanged; JSON fields are additive.
Strict V2 readers cannot parse new V3 fields: rollback uses the verified pre-release
backup plus preserved baseline image, tested on a separate volume. Never delete live data.

SSE/audit event records link affected evaluations and new state versions; completion
records identify the immutable calculation snapshot and policy. The React application
formats backend results, with current/live and hypothetical/history labels kept distinct.
