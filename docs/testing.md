> Historical / superseded release instructions and verification snapshot.
> Use [the current V3 handoff](UNDO_V3_HANDOFF.md) and [final repair report](FINAL_REPAIR_REPORT.md)
> for the submitted build. Prior findings and measurements below are preserved.

# Verification commands

From backend on Windows: `../.venv/Scripts/python.exe -m pytest -q` (Linux: `../.venv/bin/python -m pytest -q`). Use `-v` for named cases. Tests use temporary SQLite databases and deterministic independent fixtures.

Backend static checks: `../.venv/Scripts/python.exe -m ruff check app tests`; `../.venv/Scripts/python.exe -m mypy app`.

From frontend: `npm test`, `npm run typecheck`, `npm run lint`, `npm run build`, `npm run e2e`. E2E uses real backend and frontend servers and its own database; install Chromium using `npx playwright install chromium`. Browser QA must inspect actual screenshots in addition to automated assertions. No skipped test is a pass.

Phase coverage: 1 domain invariants; 2 restart/rollback/replay/idempotency; 3 model/simulation/metrics/ranking; 4 actual HTTP and SSE contracts; 5 rendering/component contracts/build; 6 UI journeys/resilience/a11y; 7 packaging, native and target smoke checks, measured performance and documentation.

Exact observed command results are recorded in BUILD_LOG.md. Commands listed here are instructions, not claims they have already passed.

Current audited results: 74 backend tests on Windows, 74 packaged amd64, 74 emulated s390x;
10 frontend tests and 13 browser journeys. See AUDIT_HANDOFF.md and docs/audit evidence
(from this document the evidence folder is `audit/`). Use current target tag
`undo:audit-final-s390x`; original target image/tag is retained as historical evidence.

## Architecture checks

Production Docker builds are separate: `docker buildx build --platform linux/amd64 -f deploy/Dockerfile -t undo:native --load --progress plain .` and the same command with `linux/s390x` / `undo:s390x`. Both print actual imported dependency versions. Native development never depends on Docker.

Container tests bind only backend/tests read-only into /verify/tests; packaged /app/backend/app remains the implementation under test. Ephemeral test containers install pytest/httpx, run `python -m pytest -q -p no:cacheprovider /verify/tests`, and remove themselves. Full command and results are in BUILD_LOG and container-tests logs. Non-root production runtime containers never install development tools.

`scripts/container_smoke.py` checks a running loopback deployment through real HTTP: static assets, health, evaluation, idempotent event, recalculation, original audit snapshot and SSE. `--probe` checks expected persisted records after a separate actual container restart. This deliberately uses independent demo volumes.

**Its default mode resets its target: never run it against the live 8080 demo during an
audit.** `scripts/audit_containers.py` creates isolated volumes/ports and refuses existing
volumes. `scripts/audit_baseline.py` takes a read-only online backup and refuses overwrites;
`scripts/audit_restore.py` verifies the matching original image/backup in a separate volume.

## Benchmark and security checks

From backend run `../.venv/Scripts/python.exe benchmark.py`. It uses temporary databases, 20 warm evaluations and 10 event/recalculation trials. It records machine/runtime/workload and nearest-rank P95 in benchmark.json. It is an in-process ASGI measurement and excludes network/browser latency.

Python environment audit: `python -m pip_audit --format json --output docs/python-audit-final.json` from root with the isolated interpreter. Pinned runtime graph audit: `python -m pip_audit -r backend/requirements.txt --no-deps --disable-pip --format json --output docs/python-runtime-audit.json`. Frontend: `npm audit`. Audits cover known dependency advisories, not the OS image, secrets review, access control certification or a complete security assessment. TestClient currently emits one upstream httpx deprecation warning; tests are executed and counted normally.
