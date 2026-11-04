# Stage11 — Owner-gated single synthetic media request on existing vLLM

**2026-11-04 | Stage11 only | NOT EXECUTED by assistant**

## Authorization and boundaries

The project requester explicitly approved progressing to bounded GPU/model
testing in this conversation. This is **requester consent only**, not
independent approval of the shared vLLM runtime owner, organization
security/network controls, or any resource ceiling not yet confirmed.
The operator must have both a valid serving-owner approval to use
the shared GPU at the specified time and a written allowed stop/resource
window before issuing the actual POST. Record the approval reference
privately. The requester cannot confer missing server or organization
privileges through a chat message.

No external model service, real confidential data, production
database, extra model loading, server restart, port exposure,
container settings, secrets, model download, or GPU stress is
part of this task. Do **not** execute the full three-domain
probe or structured/unconstrained A/B, which would send more requests.

## Reuse existing source, no new inference tool

Use the existing reviewed
`scripts/verification/stage11_real_model_criterion_probe.py` and
`scripts/verification/stage11_container_metadata.py`. Both use
fixed, synthetic inputs; the criterion probe emits sanitized
contract/failure/timing categories, not prompts, raw responses,
source quotes, model identifiers or private paths. Before
live execution, note that `--domain media` selects exactly
one criterion, `media_message_clarity`, not all domains.

**Conditions that must be true in the approved runtime window:**

- The running container is still the existing shared vLLM
  instance and is responsive on operator-approved local
  port 8000. An offline package version or redacted model
  list **does not prove** model revision or tokenizer identity.
- Shared-runtime owner approves **exactly one** synthetic
  single-domain GPU model POST, at most 512 completion
  tokens, one in-flight request, no retry, 45-second
  provider request timeout, and any authorized RAM/VRAM
  stop policy. Record observed resource baseline privately
  without exposing other tenants or workloads.
- No concurrent stress, uncontrolled background operations,
  CPU profiler, database migrations, model downloads,
  or live user content enters this diagnostic.
- Private owner attestation of actual served model/tokenizer,
  runtime revision/license, and effective per-request
  guided-decoding backend is a **separate required gate**.
  Prior Docker launch flags were absent, so the documented
  backend `auto` remains an intention, not an effective
  request-level XGrammar proof. The optional local
  artifact comparison has not been executed; do not
  claim a file match.

## Commands on the existing Simorgh checkout

First perform the harmless GitHub source update and the
*default no-request plans*:

~~~bash
cd /srv/projects/text-evaluation-service
git pull --ff-only origin main
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_real_model_criterion_probe.py tests/test_stage11_container_metadata.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_real_model_criterion_probe --domain media --disable-thinking --diagnostics --max-output-tokens 512
~~~

Once the shared service owner's permitted window and resource
budget are confirmed, the following read-only metadata
check requests **one local /v1/models GET** (not inference)
and reads bounded container metadata:

~~~bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_container_metadata --container ai-inference-vllm-1 --port 8000
~~~

If the Container or endpoint check is unavailable, private
owner metadata conflicts with the observed candidate, or
the shared GPU is not available, **STOP without a model
POST**. If clear and explicitly approved, make **one**
fixed synthetic media criterion request:

~~~bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_real_model_criterion_probe --execute-live --domain media --disable-thinking --diagnostics --max-output-tokens 512
~~~

The above command uses the existing private loopback
`http://127.0.0.1:8000/v1` provider only, fixed
in-repository synthetic Persian media text, max_input
2048 characters, max_context 8192 tokens, temperature
0, disabled thinking request, max_concurrency 1,
max_attempts 1, timeout 45s, circuit_failures 1,
and max_output_tokens 512. This is one criterion
evaluation at most, not one approved E2E application
or a 56-ID gate. Do not increase token budgets or
auto-retry if it fails.

**STOP** on any non-successful/incomplete contract,
HTTP/transport failure, timeout, 429, OOM/resource
alarm, unexpected model/backend, unauthorized
requests, or data/log safety concerns. No second
POST may be attempted on this authorization. No
automatic restart, new model, backend/config switch,
wider domain probe or larger token budget follows.

## What counts as evidence

Share only the redacted JSON of the two commands,
test result counts and a nonsecret owner approval
reference if policy permits. Never paste hidden
model IDs, model paths, prompts, raw outputs,
GPU process lists, secrets, logs or local hashes.

A model contract result `valid` requires a
schema-valid grounded response with exact source
quote/offsets or a valid abstention, but **does not
prove the quality of the model's judgment**.
The diagnostics may report `finish_reason`,
`reported_usage`, request duration and shared
service-wide metric delta, which is explicitly
`SHARED_SERVICE_UNATTRIBUTED` and cannot be
causally assigned to this request.

If the probe fails, report the exact sanitized
error category rather than changing XGrammar,
Schema, timeout or output limits. The earlier
single 29.118s versus 2.327s comparison produced
incomplete responses and has no valid causal
attribution. Release acceptance needs an
owner-verified actual model/Tokenizer/backend,
strict contract validity, tri-domain expert
quality/golden labels, No-Egress/security,
full signed API/Worker/DB/model E2E and
controlled capacity/recovery evidence.

**State**: User consent OBSERVED; operational
shared-GPU owner authorization, identity and
resource limits PENDING_SERVER; actual new
one-shot media inference NOT_RUN; Stage11
BLOCKED; Stage12 NOT_STARTED.
