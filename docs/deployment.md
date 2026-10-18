> Historical / superseded release instructions and verification snapshot.
> Use [the current V3 handoff](UNDO_V3_HANDOFF.md) and [final repair report](FINAL_REPAIR_REPORT.md)
> for the submitted build. Prior findings and measurements below are preserved.

# Packaging and LinuxONE deployment

Current audited target tag: `undo:audit-final-s390x`; native `undo:native` points to
`undo:audit-final-native`. Original tags/images are retained. Current indexes, verification,
backup/restore evidence and blockers are in [AUDIT_HANDOFF.md](AUDIT_HANDOFF.md).
No real LinuxONE host execution has occurred.

## Architecture

Runtime target: Linux `s390x` (Linux on IBM Z/LinuxONE, not z/OS). Development here is Windows x64 with a Linux amd64 Docker engine. Buildx advertises s390x emulation. Emulated container execution does not prove real LinuxONE deployment.

Base Python tag: `python:3.12.12-slim-bookworm`, pinned multi-platform index digest `sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c`. s390x manifest: `sha256:1f4da44a940d41c7cc5929a37921b2e0425533735f5efbf616c2f6a46633848e`.

Frontend builder: `node:24.12.0-bookworm-slim`, index digest `sha256:7326fb2dbdce998edd72140946851be64ef4a643e8715e138ca467e8e9d92c99`. It runs on BUILDPLATFORM and produces architecture-independent browser assets. Runtime pip installs execute on TARGETPLATFORM. Pydantic/Pydantic Core pins are in backend/requirements.txt; exact target imports are printed by each build. See BUILD_LOG for actual results and later security-driven dependency updates.

## Native image

From the root:

```text
docker version
docker info
docker buildx version
docker buildx inspect --bootstrap
docker compose config --quiet
docker buildx build --platform linux/amd64 -f deploy/Dockerfile -t undo:native --load --progress plain .
docker compose up -d --no-build
```

Open http://127.0.0.1:8080/. `docker compose ps` reports health. Compose binds loopback, runs UID/GID 10001, drops capabilities, sets no-new-privileges, uses a read-only root filesystem and stores SQLite in `undo_data`. `docker compose stop` preserves the volume and history. Back up the volume using SQLite's backup API or after stopping the process; copying an actively written WAL database without its WAL is unsafe.

## Target image

```text
docker buildx build --platform linux/s390x -f deploy/Dockerfile -t undo:s390x --load --progress plain .
docker image inspect undo:s390x
docker run --rm --platform linux/s390x undo:s390x python -c "import platform,pydantic,pydantic_core; print(platform.machine(),pydantic.__version__,pydantic_core.__version__)"
```

Actual build and execution results belong in BUILD_LOG. If no native builder or emulator exists, record the error and use an authorized s390x builder; do not silently substitute an amd64 image. Docker itself is optional for local development.

## On an authorized LinuxONE host

No host access is currently configured. Remaining deployment work:

1. Verify host architecture with `uname -m`, supported Linux distribution, Docker/Podman and storage.
2. Transfer the approved target image (for example via `docker save`/`docker load`); no registry publishing is performed automatically.
3. Provision a local persistent volume writable by UID 10001. Choose a supported backup and restore procedure.
4. Start one runtime process, initially on loopback. Example:

```text
docker volume create undo_data
docker run -d --name undo --restart unless-stopped --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges --mount source=undo_data,target=/app/data -p 127.0.0.1:8080:8000 -e UNDO_ORIGINS=http://127.0.0.1:8080 undo:s390x
```

5. Verify `/api/health`, static frontend/assets, evaluation, a persisted financial event, SSE reconnection, restart persistence, reset and preserved audit history. Run the backend suite on the actual host if its supported development dependencies are available.
6. Record host identity, architecture, runtime versions, image ID/digest, exact commands and observed results. Only then claim LinuxONE execution.

Public network access requires a separately authorized TLS proxy, authentication, authorization, business isolation, request limits, backups and monitoring. Keep one worker; SQLite and the process-local evaluation lock are not a multi-node architecture.


## V3 packaging and recovery

V3 tags: `undo:v3-native` (linux/amd64), `undo:v3-s390x` (linux/s390x). The preserved
pre-V3 image is `undo:v3-baseline-native`; exact current identities are recorded in
`v3/container-runtime-v3-verified.json`. The pinned Python3.12.12 slim-bookworm manifest
supports both targets; Pydantic2.11.7/Core2.33.2 are verified by actual imports and tests.
Frontend compilation uses BUILDPLATFORM, then copies architecture-independent static assets.

Native Windows3.12.13 development, native Linux3.12.12 runtime and emulated s390x runtime
are separate checks. Emulation is not real LinuxONE execution. No LinuxONE host was
available; Docker Scout requires login. Exact outputs are under v3/.

Authoritative live volume is `undo-demo_undo_data`, DB `/app/data/undo.db`. Online backups
are under `.runtime/v3/`; pre-release.db was restored to a fresh recovery volume and
served under the preserved V2 and new V3 images. V3 recalculation/restart on the restored
clone preserved financial state. No table schema migration is required. V3 old JSON
loads with defaults; old V2 strict models cannot read new V3 JSON, so rollback restores
the verified pre-release backup into an isolated location with the baseline image first.
Keep the current live DB for investigation; never replace/delete it blindly or remove
volumes. Recovered old backups omit subsequent appended evaluations.

Container test tools can be installed offline from verified pure-Python wheels under
`.runtime/v3/test-wheels` using `scripts/v3_container_tests.py`; production dependencies
are used directly from each image and are not replaced. This avoids interrupted network
downloads during tests. No payment rails, external AI or additional service was added.
