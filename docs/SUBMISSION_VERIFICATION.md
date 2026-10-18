# UNDO V3 — exact final artifact verification

Status: PASS for achievable checks; ready with documented limitations.
Verified UTC: 2026-10-18T01:48:12.326161+00:00.

Artifact: UNDO-V3-SUBMISSION.zip (299069 bytes).
SHA-256: `ba53b3879d4db24c7fd5e327d244b30a73a7d79db7215e304e49778561b53187`.

| Gate | Actual result |
|---|---|
| Manifest / CRC / content hashes | PASS115 archive members /114 indexed files |
| Fresh independent installation | PASS Python3.12 declared pins / npm lockfile |
| Backend / frontend / browser | PASS97 /27 /21 |
| Typecheck / Ruff / mypy / ESLint / production build | PASS |
| npm / runtime pip audit | PASS0 reported advisories |
| Package failure/integrity regressions | PASS3 |
| Native amd64 build/tests/runtime/restart | PASS97 backend tests |
| Emulated s390x build/tests/runtime/restart | PASS97 backend tests |
| Deterministic rebuild from extracted files | PASS exact same ZIP SHA-256 |
| Live financial state/settings/all raw history | PASS exactly unchanged |
| Existing Git index / selective missing files | PASS76 preserved /57 explicit additions; no commits/pushes |

The local8080 app serves the same backend and production asset bytes as this ZIP.
All temporary runtime checks used separate databases, containers, ports and fresh
volumes; volumes and images were retained. No real payments or external deployment.

BLOCKED: real LinuxONE host execution (no host/access) and Docker Scout image-layer
scan (login required). ML remains experimental, without demonstrated decision uplift
or real-world accuracy. These are separate from the passing native/emulated checks.

Full commands, working directories, exit codes, source/asset hashes and runtime
records are in [SUBMISSION_VERIFICATION.json](SUBMISSION_VERIFICATION.json). The ZIP contains docs/FINAL_REPAIR_REPORT.md,
docs/UNDO_V3_HANDOFF.md and docs/BUILD_LOG.md with all earlier failures and repairs.
This external checksum record preserves the bytes of the tested final archive.

Public documentation copy: local profile names are redacted in the accompanying JSON.
The reported checksum belongs to the independently tested submission ZIP; repository
publication adds documentation without changing the application source.
