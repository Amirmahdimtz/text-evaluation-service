# Stage11 — Owner-approved serving-artifact provenance and reason CPU diagnostic

**Status:** PREPARED/OFFLINE_ONLY; operator/owner verification PENDING_SERVER;
Stage11 BLOCKED; Stage12 NOT_STARTED.

## Purpose and scope

This is not a model deployment, not a request-level backend determination,
not a security No-Egress audit and not a GPU inference/quality benchmark.
The existing vLLM container is shared. No service restarts, configuration
changes, model downloads, weight reads, GPU reservations, process/environment
dumps, raw service logs, credential inspection or private text export are
authorized by this document.

The last actual Simorgh two-trace CPU profile, with the fixed synthetic
CriterionInference JSON and cached tokenizer, found mask-fill steps
15–19 >100ms twice. Structural labels aligned steps 15–18 with
the **VALUE of the third sorted JSON field (`reason`)** and step 19
with CROSS_REGION. Live serving identity and effective guided-decoding
backend remain UNVERIFIED.

## Gate A: live serving identity — owner-only, no assertions from cache alone

The owner must privately establish the active **served** model and
tokenizer from the deployment record/runtime ownership boundary:
model ID/revision and approved artifact storage, file checksum manifest,
license, quantization/config, chat template, actual serving tokenizer and
vLLM version. Record provenance and checksums **only in an authorized
internal evidence store**. A cached snapshot candidate by itself is not
proof of the model loaded by the serving process. Do not paste IDs,
file paths, hashes, prompts, logs or configurations into GitHub/chat.

The existing `stage11_guided_backend_inspect.py --container`
read-only Docker Entrypoint/Cmd check on Simorgh showed the
guided-decoding backend flag was ABSENT, so the documented default is
AUTO. This is launch metadata, **not evidence that any individual
request used XGrammar**. Before a request-level conclusion, the owner
must identify the effective decoder using approved runtime
observability/deployment instrumentation; approved evidence must
distinguish requested mode, selected backend and any fallback.
Do not infer it from package installation or offline XGrammar
compilation. No new network request is implied by this document.

### Optional owner-approved local artifact byte comparison

The command-line utility
`scripts/verification/stage11_serving_artifact_match.py`
defaults to a no-access plan. In explicit emitted-runtime mode it
compares only these fixed tokenizer/config files under two
**owner-supplied, authorized** absolute directories: tokenizer.json,
tokenizer.model, tokenizer_config.json, special_tokens_map.json,
added_tokens.json, vocab.json, merges.txt, chat_template.jinja and
config.json. It reads no weights, hashes locally without emitting
hashes, and returns booleans/counts only. It has per-file (64MiB),
total (192MiB), CPU (15s) and wall-clock (30s) budgets, no model
loads or inference, and denies Python socket egress. Local equality
is NOT proof of serving provenance. Identical realpaths fail closed
because they offer no independent filesystem comparison.

The **owner**, not this tool, must establish that the second
directory corresponds to the serving artifact using an authoritative
trusted deployment record. A different path obtained from inference,
a guessed cache directory, or the same directory is not attestation.
If the server path is not verified or authorization is absent, skip
the emitted child and keep all status fields UNVERIFIED.

Offline preflight on an authorized checkout:

~~~bash
cd /srv/projects/text-evaluation-service
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m scripts.verification.stage11_serving_artifact_match
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_stage11_serving_artifact_match.py
~~~

With explicit authorization, the owner can privately set
`STAGE11_LOCAL_TOKENIZER_DIR` and
`STAGE11_OWNER_SERVED_ARTIFACT_DIR` to previously verified
absolute locations **inside the existing container** and pipe
`--emit-runtime-script` to a one-off child in
`ai-inference-vllm-1`, passing only these two variables with
`docker exec -i -e`. Neither path is to be printed in reports.
Do not change shared runtime state to force a match.

## Gate B: controlled reason sensitivity, CPU-only

`scripts/verification/stage11_xgrammar_tokenizer_profile.py`
keeps the default 2 x 24 token CPU probe unchanged. The new
`--emit-runtime-script --reason-sensitivity` option additionally
tests two fixed synthetic valid reason variants using fresh matchers:
REASON_SHORT (1-character value) and REASON_SAME_LENGTH (same
character count as the original but different fixed content).
Both preserve the exact original CriterionInference schema
and its compiled grammar. The maximum is 4 x 24 synthetic
mask-fill steps (96), with the original one-thread, 32MiB
compiler cache, CPU 25s and wall 45s budgets. The diagnostic
prints only named variant, total times, >100ms step indices,
structural alignment and aggregate mask-fill cost within
fully aligned synthetic reason-value tokens; it never prints
token IDs, text, offsets, decoded strings, model weights,
private paths or runtime serving state. If offsets are invalid,
reason-region statistics are UNVERIFIED (null), not estimated.

This experiment changes the *synthetic token sequence* and
thus cannot isolate all factors: string length, tokenization,
grammar state and CPU scheduling can interact. It is an
exploratory hypothesis test, NOT a validated XGrammar fix,
model throughput measurement or production SLO. The new
96-step workload requires **separate explicit shared-container
owner approval** and must not be auto-executed by CI or on a
shared GPU.

### Evidence expected and decision rubric

Record only the two fixture labels, total fill duration,
slow-step positions, structural map status and reason-region
aggregate values. Compare with the baseline/repeated matcher
observations. If reason-related spikes persist in both variants,
record a supported *association*, not a proven grammar backend
bug. If only one variant spikes, consider tokenization/value-
dependent work and repeat with a deliberate, controlled design
before changing production. If the two variants differ in
which tokens reach the 24-step cut, comparisons are not
like-for-like; explicitly mark INCONCLUSIVE.

**Never close Stage11 on this data alone.** The separate
real vLLM inference/quality benchmark, three domains,
effective backend proof, model provenance, actual no-egress,
GPU performance/capacity and service E2E acceptance gates
remain PENDING_SERVER.

## Offline CI evidence

[GitHub Actions run 41827513749](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/41827513749)
completed SUCCESS for `5aabc7e`: 59 Stage11 offline safety
tests and 213 focused Provider/probe/diagnostic tests
passed. This does **not** include any shared-container
artifact comparison, on-host reason sensitivity probe,
live backend selection or GPU model calls. All those
runtime checks remain PENDING_SERVER.
