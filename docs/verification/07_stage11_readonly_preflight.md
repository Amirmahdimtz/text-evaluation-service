# Stage 11 — Non-invasive Simorgh Host Inventory Preflight

**State:** `SCRIPT_TESTED_OFF_HOST / NOT_EXECUTED_ON_SIMORGH` (2026-10-28). This is metadata reconnaissance, **not** execution or acceptance of any of the 56 Stage11 organization-only test IDs. `BLOCKED` remains the Stage11 Gate status.

## Scope and restrictions

The script at `scripts/verification/stage11_readonly_preflight.py` uses the Python standard library and *only* nonprivileged local reads of OS/CPU/RAM/root filesystem plus installed Python package metadata. By default, when present, it runs a single read-only `nvidia-smi --query-gpu=...` metadata command with an eight-second timeout; it does **not** query process owners, serial/UUID, run model inference, mutate GPU state, or allocate vLLM. `--no-gpu` omits even this command. There is no Docker daemon access, network request, authentication test, database connection, secret lookup, model download, container/driver inspection, or file output. No `sudo` is used. Output is JSON on stdout; Python bytecode writes are disabled in the operator command.

**Read-only authorization boundary:** obtain local operator permission to read host/GPU metadata. This preflight does not authorize any privileged host process, shared container/network access, or model load. If the host is production/shared, use the permitted scope only; stop if any approval is missing. Running `nvidia-smi` queries shared GPU counters but is not a capacity or safe-headroom test.

## Operator commands (on Simorgh, not from GitHub CI)

```bash
cd /srv/projects/text-evaluation-service
# Confirm the expected reviewed commit before invoking the script.
git rev-parse --short HEAD
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verification/stage11_readonly_preflight.py
```

For strict no-GPU-query mode:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verification/stage11_readonly_preflight.py --no-gpu
```

Do **not** redirect full output into the public GitHub repository or send unsanitized internal service topology, model identifiers, user/hostnames, IPs, keys, URLs or real dataset records to chat. If operator policies permit sharing, communicate only approved nonsecret summarized inventory: CPU architecture/count, aggregate RAM, GPU model/total/used VRAM (or `UNVERIFIED`), reported driver, and version status. Never treat current free VRAM as permission to load a second model.

The `installed_vllm_distribution` and `installed_torch_distribution` values are Python package metadata **of the current `.venv` interpreter**, not proof of the separately deployed vLLM container version. The script does not establish the actual running model, container digest, CUDA runtime compatibility, no-egress, security posture, artifact provenance or SLO. Any missing sensor is `UNVERIFIED`/`TOOL_NOT_FOUND`; no fake zeros.

## Local reproducible safety checks

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_readonly_preflight.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m py_compile scripts/verification/stage11_readonly_preflight.py
```

The compile command may write `.pyc` files (ignored by Git); omit the second command on any environment where **no filesystem writes** are permitted. The preflight itself does not write files. The test suite uses temporary synthetic fixture files only on an explicitly authorized development/CI host, not as part of the production preflight.

## Evidence and gate interpretation

Before any additional work, an authorized owner must verify signed Infrastructure/Security/Data approval, isolated staging, permitted egress tests, scoped service accounts, authorized artifact and dataset, GPU resource and abort limits. Inventory output merely resolves a subset of `S11-AI-01` prerequisites, without executing its capacity probe. All 56 deferred IDs stay `PENDING_SERVER`; model `Qwen2.5-7B-Instruct` and `Qwen3-14B` remain **candidates**, not approved or selected.

Keep detailed sensitive inventory/evidence in approved private storage, and put only redacted status and approval-reference summaries into GitHub. See [traceability](01_test_strategy_and_traceability.md) and [blockers](06_release_blockers.md).
