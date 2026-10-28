# Stage 11 — Non-invasive Simorgh Host Inventory Preflight

**State:** `PASS_USER_SIMORGH_READONLY_PREFLIGHT / ENTERPRISE_GATE_BLOCKED` (2026-10-28). This is metadata reconnaissance, **not** execution or acceptance of any of the 56 Stage11 organization-only test IDs. `BLOCKED` remains the Stage11 Gate status.

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

## Verified operator-reported Simorgh run — 2026-10-28

This section records **operator-provided terminal output** from the main checkout fast-forwarded to commit `e29537b3db9ec12579f9ec55bf4b41f8d8b86e70`; it is not an assistant SSH session, independent infrastructure audit or live-inference test.

- `git pull --ff-only origin main`: `1e07ad2..e29537b` fast-forward successful.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_readonly_preflight.py`: **13 passed in 0.04s**. These are offline safety/contract tests, not 13 out of 56 Stage11 organization acceptance tests.
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/verification/stage11_readonly_preflight.py`: completed; schema `stage11-readonly-inventory-v1`, GPU `OBSERVED_READ_ONLY`.
- Host aggregate, approved nonsecret summary from supplied output: Linux x86_64, 24 logical CPUs, **96,513 MiB RAM total / 79,782 MiB available** at probe, **359.03 GiB available on root filesystem** at probe (not model artifact storage).
- One detected **NVIDIA GeForce RTX 3090**: **24,576 MiB VRAM total / 18,847 MiB VRAM used** at probe, NVIDIA reported driver `570.124.06`. The arithmetic difference **5,729 MiB** is *apparent free VRAM at one instant*, NOT safe model-serving headroom, reserved GPU capacity, load-test result or proof another 7B/14B model can load; the GPU appears in use and shared workload impact is unknown.
- Project virtualenv Python `3.12.3`; `torch` and `vllm` **not installed in this Python virtualenv**, which does **not** determine versions in existing separate model-serving containers. Docker CLI detected only, **no daemon/container inspection**.
- Not examined: deployed model ID/version, tokenizer/model hashes and license, CUDA/vLLM container runtime, actual GPU headroom under workload, NIC/egress/firewall, SSO/KMS, DB, isolation, staging authorization or AI Quality benchmark. No generation, inference/API probing, privileged command, network packet test or model import was performed.
- `S11-AI-01` has **partial hardware inventory evidence only**; its pinned runtime and capacity probe acceptance oracle is **not met**, so it remains `PENDING_SERVER`. **All 56 Stage11 deferred test IDs remain `PENDING_SERVER`**, Stage11 `BLOCKED`; no Production or Stage12 authorization.

Use these figures as a time-local observation only. Future private evidence requires a separately approved isolated environment and authorized owner. No full raw host output or secrets have been committed.
