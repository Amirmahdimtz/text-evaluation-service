# Stage 11 — Reuse of existing shared on-prem vLLM (non-disruptive candidate plan)

**State:** `SHARED_REUSE_FEASIBLE_IN_PRINCIPLE / NON_INTERFERENCE_NOT_VERIFIED / NO_NEW_LIVE_REQUESTS` · 2026-10-31. Stage 11 only.

## Decision and existing evidence

The user requested preference for **models already running for other projects** rather than deploying/download/loading additional models. Reuse is technically compatible with the existing `LocalLlmProvider`: its endpoint, model ID, revision, max concurrency, attempts, input/output/context limits and timeout are configuration-driven. The successful on-prem `PASS_SYNTHETIC_CRITERION_CONTRACT` already demonstrated **one** currently served model/endpoint at loopback port 8000 can return a correctly grounded synthetic `CriterionInference`; it did **not** demonstrate resource isolation or non-interference with the other projects.

A prior host-local one-time GPU snapshot reported an RTX 3090 with 24576 MiB VRAM total and 18847 MiB used (snapshot from 2026-10-28). This is **not current free capacity** or proof of safe extra model loading. Do not start a second model or alter another project's running container based on this observation.

## Explicit safety contract before using a shared service

- Obtain the shared vLLM owner's approval of the **specific endpoint, model artifact, test time window, workload limit, isolation and stop criteria**; keep private model IDs, host configuration, logs and artifact hashes in approved private storage only. User preference is not authority to alter or monopolize a production/shared runtime.
- **Reuse already loaded weights only**. Do not launch, download, reload or replace models, restart containers, change inference flags, authentication, GPU allocation or another project's deployment.
- Never assume zero impact from shared-GPU requests. vLLM scheduler, KV cache, model decode and queue slots are shared; even concurrency 1 can increase other applications' tail latency. A zero-interference requirement may require a **reserved low-traffic window, enforced per-client quota, separate instance/GPU, or deferral**, if the owner cannot establish acceptable headroom.
- Conservative initial integration settings **if approved, not enabled by this document**: one client request in flight (`llm.max_concurrency=1`, `worker.max_inflight=1`), `llm.max_attempts=1` (no model retries), short synthetic inputs, explicit context/output limits, bounded timeout and durable queue backpressure. These are proposed client-side safeguards, **not** server-side quota or guaranteed isolation.
- Use only existing configured private endpoints and trusted credentials; do not scan ports or enumerate unrelated projects, bypass IAM, expose model IDs in chat/public GitHub or send confidential text until identity, No-Egress and data-handling controls have actually passed.
- Collect shared service owner's baseline on other tenants' latency/error/queue/GPU/VRAM before any load. Abort immediately if approved limits, competing-project latency or reliability degrade. Single successful inference latency is not p95 or non-interference evidence.
- Both comparison candidates must be identified and pinned with provenance/license; they may already be served at separate **approved** endpoints, but do not assume this from one `/v1/models` response. Do not start both on the same constrained GPU; compare sequentially during authorized windows.

## Zero-inference preflight for the Simorgh operator

The following **read-only** commands must be run only by the authorized host operator; they do not restart services or submit inference. The metadata query checks **only the previously used approved loopback 8000 port** and prints neither model IDs nor raw metadata:

```bash
cd /srv/projects/text-evaluation-service

nvidia-smi --query-gpu=index,memory.total,memory.used,utilization.gpu \
  --format=csv,noheader,nounits

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import http.client
import json
connection = http.client.HTTPConnection("127.0.0.1", 8000, timeout=4)
try:
    connection.request("GET", "/v1/models", headers={"Accept": "application/json"})
    response = connection.getresponse()
    payload = response.read(16385)
    count = None
    if response.status == 200 and 0 < len(payload) <= 16384:
        value = json.loads(payload)
        models = value.get("data") if isinstance(value, dict) else None
        if isinstance(models, list):
            count = len(models)
    print(json.dumps({
        "http_status": response.status,
        "advertised_model_count": count,
        "model_ids_redacted": True,
        "inference_requests": 0,
    }))
finally:
    connection.close()
PY
```

**Meaning:** the GET reports only what is advertised at **one** endpoint; it neither identifies every loaded model on Simorgh nor proves spare capacity, acceptable sharing or approved artifact provenance. The operator must confirm privately whether other existing models/endpoints are intentionally available for this project, their usage rights and the shared service's monitoring/quotas. Do not infer or probe undisclosed ports.

## Continuation and gates

1. Record sanitized GPU aggregate and the explicit endpoint's model count without private identities.
2. Obtain the serving owner/SRE's permission and non-interference criteria for each intended existing model and its approved access identity.
3. Privately bind model IDs and immutable revisions to `LocalLlmProvider` configuration without changing the shared service; prepare a **separate** approved single-request/benchmark budget and model-order plan.
4. Only then measure controlled sequential candidate quality and competing-project latency/error/queue impact, stop on any violation, and preserve evidence per mandatory Stage11 test oracle.

**No new live model request or server operation was performed by drafting this document.** The previously granted one-request synthetic permission has been consumed. Existing defaults remain fail-closed. All 56 enterprise Stage11 test IDs remain `PENDING_SERVER`, `Stage11=BLOCKED`, `Stage12=NOT_STARTED`.

## Simorgh approved read-only shared-runtime observation — 2026-10-31

The operator ran the documented non-invasive commands on Simorgh and supplied these **aggregate, redacted results**:

| Check | Observed | Interpretation |
|---|---|---|
| `nvidia-smi --query-gpu=index,memory.total,memory.used,utilization.gpu` | GPU index 0; total **24576 MiB**; used **18847 MiB**; instantaneous utilization **0%** | Simple arithmetic difference **5729 MiB** of unallocated reported VRAM at that snapshot, **not** sustained headroom, spare safe VRAM or cross-project reservation |
| Previously approved `127.0.0.1:8000/v1/models` GET | HTTP **200**, **1 advertised model**, redacted ID | Exactly one model advertised **at this one endpoint**; not proof that other projects have no additional model servers elsewhere |
| Inference submitted by this inspection | **0** | No prompt inference, Docker/GPU reconfiguration, model loading, GPU pressure test, endpoint discovery, or port scanning |

**Engineering disposition:** reuse this already-running endpoint as the **first candidate for a later authorized bounded benchmark**, because its one-shot real synthetic CriterionInference smoke previously succeeded. Non-interference remains `UNVERIFIED`: zero instantaneous GPU activity does not preclude a busy queue or other projects' latency spikes; the previously recorded 18847 MiB VRAM allocation still occupies much of the 24576 MiB GPU. Do not add a second loaded model, raise concurrency, submit protected data or bypass authentication. For any other existing model candidate, require its owner's already-authorized endpoint and verified identity **privately**; do not discover it via probing/scanning.

**Next external prerequisite:** shared serving owner's confirmation of which clients/models may be reused, current serving artifact revision/license, off-peak/test window, acceptable latency/error impact, request budget, fair-share quotas and immediate abort criteria; then separately approved, synthetic-only, sequential benchmarks with `max_inflight=1` and `max_attempts=1` on our side, subject to actual enforceable controls. No such approval or measured competing-workload baseline is present in this transcript.

**No actual source or runtime configuration was changed by this observation; no new inference was sent.** All 56 original Stage11 enterprise test IDs remain `PENDING_SERVER`, Stage11 `BLOCKED`, Stage12 `NOT_STARTED`.
