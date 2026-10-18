# UNDO engineering rules

Preserve the financial ledger: projections never change settled cash. Use integer paise, explicit currency, timezone-aware timestamps, validated typed events, atomic writes and logical idempotency. Do not execute real payments.

Complete phases 0–7 in order. Each phase requires RED, GREEN, REFACTOR and VERIFY; record executed commands, counts, failures, fixes and blockers in docs/BUILD_LOG.md. Never invent evidence or weaken tests for a green result. Preserve user changes. No commits, pushes or external deployment without authorization.

React renders backend calculations. Reuse random scenarios across alternatives. Preserve immutable evaluation snapshots and audit history. Synthetic model metrics do not establish real-world accuracy. Native testing, s390x packaging and real LinuxONE execution are separate claims.

Run backend checks from backend with ../.venv/Scripts/python.exe on Windows (../.venv/bin/python on Linux). Frontend scripts run from frontend. Keep dependency pins and documentation synchronized. Do not add infrastructure without a demonstrated requirement.
