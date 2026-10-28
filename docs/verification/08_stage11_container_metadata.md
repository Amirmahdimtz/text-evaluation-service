# Stage 11 — Bounded Container vLLM Metadata Inspection

**Status:** `OPERATOR_SIMORGH_METADATA_OBSERVED_PARTIAL / ENTERPRISE_GATE_BLOCKED` (2026-10-28). An explicit request for read-only inspection authorizes preparing this bounded probe, **not** modifying any shared running container, using internal model artifacts or running inference, network scanning, stress tests or altering production/enterprise secrets.

## Scope and data minimization

`scripts/verification/stage11_container_metadata.py` runs only these explicitly requested metadata operations:

1. `docker inspect --type container --format '{{.State.Running}}' <container>` to check a Boolean running state. It does **not** inspect or print `.Config.Env`, `.Config.Cmd`, mounts, image registry URL/digest, container network endpoints, process state or logs.
2. If running, `docker exec --env PYTHONDONTWRITEBYTECODE=1 <container> python3 -B -c 'from importlib.metadata import version; print(version("vllm"))'` to inspect the **installed** Python distribution version in that running container. This starts a small short-lived Python metadata process, not an inference process; no file modification, GPU command, network call or model import is intended. It requires separate operator approval for `docker exec` on a shared service. Any failure remains `UNVERIFIED` without exposing stderr.
3. **Only if `--port` is supplied**, a bounded 4-second HTTP `GET /v1/models` to the literal IPv4 loopback `127.0.0.1:<port>`. This requests **metadata only, not generation**, sends **no authentication token or business text**, uses no proxy or internet, does not retry, does not enumerate ports or execute a load test. The parser discards all returned fields except IDs, and discloses only exact publicly known candidate names (`Qwen/Qwen3-14B`, `Qwen/Qwen2.5-7B-Instruct`); other IDs and original paths are redacted. HTTP 401/403 must remain `UNVERIFIED`; do **not** bypass a gateway or add credentials.

The tool never writes output to files or sends data to GitHub. It returns a sanitized JSON summary to stdout, with no raw model identifiers, secrets, Docker image name, hostnames or network addresses. `--sudo-docker` is opt-in and uses only noninteractive `sudo -n docker`; it neither requests passwords nor alters sudo configuration. **All stdout should still be reviewed for internal sharing clearance.** The script cannot prove that a listed served name matches the weights/tokenizer SHA, currently deployed artifact, signed image or approved runtime.

## Operator commands — only after authorization for Docker metadata/exec and local model listing

```bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_container_metadata.py

# Replace placeholders with authorized locally verified metadata.
# Do not put private runtime identifiers or port values in GitHub.
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verification/stage11_container_metadata.py \
  --container APPROVED_CONTAINER_NAME \
  --port APPROVED_LOOPBACK_PORT \
  --sudo-docker
```

The container name is operator-supplied and **never echoed by the tool**. If you have direct Docker read access, omit `--sudo-docker`. If Docker exec is not allowed, **do not run the command**; obtain a qualified owner to perform/package-inspect it. If the loopback API is not approved, omit the `--port` argument; the model identity will remain unknown. No alternative elevated socket, password prompt, privileged container operation, inference, or shell inspection is attempted by the script.

## Interpretation

- `installed_vllm_version` from `importlib.metadata` is container package **version evidence only**. `UNVERIFIED` may mean missing Python, missing `vllm` distribution, Docker socket denial, Python environment mismatch, timeout or service stopped; it is not a failure of the product, and **never implies a synthetic version**.
- `known_public_candidate_ids` represents advertised labels from **loopback model metadata** only. Other names stay redacted; a known public model string is **not** immutable revision/license/weight verification, and a model not among the two candidates cannot be automatically rejected without authorized private review.
- No GPU workload, throughput, No-Egress, TLS, KMS, IAM, private artifact hash, model load, inference or validation of external requests took place. The Stage 11 test `S07-S11-01`, `S11-AI-01..04`, supply chain and all other 56 enterprise test IDs remain `PENDING_SERVER` pending separate approved evidence and owners.

The accepted output format is `stage11-container-metadata-v1`; test the parser and commands offline before any authorized metadata probe. [Host inventory](07_stage11_readonly_preflight.md), [complete traceability](01_test_strategy_and_traceability.md), [release blockers](06_release_blockers.md).

## Simorgh operator result — 2026-10-28 (partial, not enterprise PASS)

- Fast-forwarded to commit `095f318`; `tests/test_stage11_container_metadata.py` **30 passed in 0.06 s**. This is a test suite for the metadata tool only.
- Authorized metadata probe returned `container_running: UNVERIFIED`, `installed_vllm_version: UNVERIFIED`, `version_evidence: NOT_OBSERVED`. These values do **not** mean the container is stopped or that vLLM is absent. The implementation suppresses stderr and does not expose the inspect failure cause; it also cannot confirm an `exec` call took place.
- The host-local loopback `GET /v1/models` returned `OBSERVED_LOOPBACK_METADATA`: **one** model advertised; it matched neither of the two exact known public candidate IDs, so **one ID remained redacted**. Exact name mismatch may be a serving alias; there is no proof of underlying model revision, loaded weights, license or successful generation. The response is not bound by this probe to any specific Docker container.
- No network egress, SSO/KMS, TLS, GPU inference, service health, load, artifact checksums, or real end-to-end tests were performed. All 56 organization gates remain `PENDING_SERVER`; Stage11 remains `BLOCKED`.

### Minimal local diagnostic (only with Docker metadata permission)

For the **approved exact container name**, run the following locally. This only queries `State.Running` and shows a shell exit code. Docker errors are suppressed to avoid copying daemon details into shared/public logs:

```bash
sudo -n docker inspect --type container --format '{{.State.Running}}' APPROVED_CONTAINER_NAME 2>/dev/null
printf 'docker_inspect_exit=%s\n' "$?"
```

A successful command reports `true` or `false`, followed by `docker_inspect_exit=0`. A nonzero exit indicates the query did not succeed, **not why**; likely causes include a wrong container identifier, missing Docker daemon access or a `sudo -n` permission/prompt requirement. The operator must resolve failures privately with their authorized SRE/Platform owner, without changing sudoers, Docker group permissions, disabling gateway controls or pasting sensitive stderr into public reports. Do not attempt Docker exec or alternate privilege routes if not explicitly authorized.

## Simorgh focused Docker-inspect diagnostic — 2026-10-28

- The operator successfully fast-forwarded local `main` to commit `3aa8755`.
- The exact approved-name Docker-state query `sudo -n docker inspect --type container --format '{{.State.Running}}' <approved-container>` produced **no stdout** and the shell reported `docker_inspect_exit=1` (stderr intentionally discarded).
- Interpretation: **`UNVERIFIED / QUERY_FAILED`**, not evidence that the container is stopped or absent, that vLLM is not installed, or that a security control passed/failed. The exit code alone cannot distinguish noninteractive sudo authorization, Docker daemon availability, or name mismatch.
- **Next low-exposure triage:** where authorized, separately run `sudo -n true` and `sudo -n docker version --format '{{.Server.Version}}'` with stdout+stderr suppressed and record **only exit codes**. If both succeed, run a minimal exact-name filtered `docker ps -a` query without exposing the full container list. Do not change sudoers, Docker group, service/network settings or inspect environment/logs. Share only sanitized exit codes.
- Real runtime version and model artifact metadata remain `UNVERIFIED`; all 56 enterprise Stage11 tests stay `PENDING_SERVER`; Stage11 `BLOCKED`.

## Simorgh noninteractive sudo and Docker status-only triage — 2026-10-28

Operator-provided shell results: `sudo_noninteractive_exit=1` for `sudo -n true`; `docker_daemon_exit=1` for `sudo -n docker version --format '{{.Server.Version}}'`; and `container_match_exit=1` for a filtered `sudo -n docker ps -a` piped into exact-name `grep -Fxq`.

**Interpretation:** `sudo -n` was not usable in the current shell context. Because the generic noninteractive sudo prerequisite already failed, the Docker version result is **not independent evidence** that the daemon is unavailable. With an ordinary shell pipeline lacking `pipefail`, `container_match_exit=1` denotes a negative exact-name grep match; it does **not** establish that Docker successfully returned a list, nor that the container is stopped or nonexistent. The reason for sudo failure (password/cached-ticket required, sudoers policy, or another permission issue) is still `UNVERIFIED` with diagnostic stderr intentionally suppressed.

**Permitted next action:** an authorized operator may authenticate interactively using `sudo -v` *on the local terminal only* (never share password), then run a minimal read-only `sudo -n docker inspect --type container --format '{{.State.Running}}' <approved-container>`, capturing only state and exit code. If interactive sudo authentication is not permitted or fails, stop, involve the designated Infra/SRE administrator and request a sanitized container state/version attestation instead. Do not modify sudoers, Docker group, services, networking or production identities.

The local loopback one-model metadata observation remains separate from Docker. No container runtime version, deployed artifact revision, running state, GPU inference or No-Egress acceptance is verified. All **56 Stage11 enterprise tests remain `PENDING_SERVER`**, overall Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.
