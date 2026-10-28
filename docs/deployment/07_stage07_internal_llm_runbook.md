# Stage07 — Approved-only Internal vLLM Stage11 Runbook

**Status: DOCUMENTED_ONLY, NOT_EXECUTED, 2026-10-28.** No real company model, credentials, endpoint, GPU or vLLM configuration has been approved for this integration.

## Prerequisites and acceptance procedure

1. Obtain written AI Lead, Infrastructure, IAM and Security approval before any network, Docker, model, credential or Production change. Do not modify shared Simorgh or access real confidential text during Stage07.
2. Preserve immutable model SHA/registry digest, tokenizer/chat template/config hashes, quantization variant, published license and approved legal obligations for both benchmark candidates Qwen2.5-7B-Instruct and Qwen3-14B. Use an approved offline, signed internal import path, not automatic internet download. Neither model is officially selected.
3. Pin exact deployed vLLM image/version and verify API compatibility, response_format json_schema, constrained decoding behavior and schema features against that version. The candidate contract uses /v1/chat/completions, /v1/models and root /health; legacy guided_json is not used. The JSON schema from pinned Pydantic must be validated independently after inference even when constrained decoding is enabled.
4. Require a real trusted corporate gateway, TLS/mTLS where approved, least-privilege service identity, network segmentation and allowlisted egress. vLLM built-in --api-key does NOT protect all endpoints (notably /invocations); enforce perimeter controls for the entire server, not only /v1 routes. No public egress or unapproved telemetry.
5. Keep LLM disabled in both committed YAML files until an explicitly approved private literal-IP endpoint, concrete model ID, immutable revision, secret reference, and measured values for max_input_characters, max_context_tokens, max_output_tokens, timeout_seconds, max_concurrency, max_attempts, retry_backoff_seconds, circuit_failures, circuit_reset_seconds, temperature and thinking_mode are available. Actual tokenizer-informed input/output budget and thinking-mode behavior must be tested: config values alone are not token proof.
6. Use approved synthetic-only probes and fault-injection: timeouts, 429/5xx, malformed JSON, duplicate envelope keys, stale/missing model identity, partial generations, giant responses, circuit recovery, cancellation, permissions and TLS failures. Test prompt injection and Persian ZWNJ/Unicode offset matching. Verify no confidential data or secrets in upstream/downstream logs, stack traces or metrics.
7. Freeze reproducible evidence: model/tokenizer SHA256, container digest, runtime and driver versions, settings, prompt/schema checksum, deployment identity, packet/no-egress audit, structured-output validity, model-generated token counts, GPU throughput/VRAM, error handling, data retention and named Security/AI signoffs. Mark each ledger S07-S11 test PASS only after actual executed proof and qualified review.

## Existing local evidence and safe testing

Local HTTPX MockTransport contract test [CI run 40644059782](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40644059782): 52 focused PASS, 159 total non-DB PASS; zero inference. No actual model revision verification, GPU startup, TLS handshake, external network test or Production approvals have been performed.

Official vLLM public documentation (public technical metadata only):
- https://docs.vllm.ai/en/stable/serving/online_serving/openai_compatible_server/
- https://docs.vllm.ai/en/latest/features/structured_outputs/

All secret references and endpoint/memory/capacity values are organization-private and MUST NOT be copied into a public repository or this runbook. Stage11 tests remain PENDING_SERVER; this runbook is not an authorization to operate on Simorgh.
