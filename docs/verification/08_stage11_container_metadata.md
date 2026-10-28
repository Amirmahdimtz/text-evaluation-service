# Stage 11 — Bounded Container vLLM Metadata Inspection

**Status:** `LOCAL_SCRIPT_TESTED / SIMORGH_NOT_RUN / ENTERPRISE_GATE_BLOCKED` (2026-10-28). An explicit request for read-only inspection authorizes preparing this bounded probe, **not** modifying any shared running container, using internal model artifacts or running inference, network scanning, stress tests or altering production/enterprise secrets.

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
