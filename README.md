# UNDO V3

See the consequences before you commit. Local synthetic cash-flow decision support,
with real backend counterfactual calculations and immutable audit history.

**Start here: [Current V3 handoff](docs/UNDO_V3_HANDOFF.md)** — setup, run commands,
capabilities, architecture, tests, packaging and limitations.

[Verified test results](docs/SUBMISSION_VERIFICATION.md) · [Final repair report](docs/FINAL_REPAIR_REPORT.md) · [Executed build log](docs/BUILD_LOG.md)
· [Financial model](docs/financial-model.md) · [Decision contract](docs/DECISION_CONTRACT.md)

The submission is built from explicitly curated current files using
`submission-manifest.json`, including essential V3 files that were previously
untracked. Run `python scripts/package_submission.py` after following the handoff's
Python setup. The ZIP, SHA-256, listing and integrity report appear in `dist/`.
The [portable verification record](docs/SUBMISSION_VERIFICATION.json) records independent verification of the tested submission ZIP. The source checkout keeps generated archives out of Git.

The obligation-aware rule is primary; synthetic experiments have not established
incremental ML decision benefit or real-world accuracy. No workflow executes real
payments. Native tests, emulated s390x and real LinuxONE execution are separate
claims. No real LinuxONE deployment is claimed. Older handoffs/audits are retained
as labelled history; their counts are not current verification results.
