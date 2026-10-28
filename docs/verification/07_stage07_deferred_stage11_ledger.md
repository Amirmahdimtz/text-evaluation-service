# Stage07 — Organization-Only LLM Test Ledger

Every item below is **PENDING_SERVER / DEFERRED_TO_STAGE_11**, not PASSED. No enterprise model, GPU, SSO or confidential-data tests were executed for Stage07. The local Stub tests and no-external-client guards have already PASS in [CI 40644059782](https://github.com/Amirmahdimtz/text-evaluation-service/actions/runs/40643712715).

| ID | Responsible Stage11 owner | Why real organizational server is needed | Prerequisites and pass oracle |
|---|---|---|---|
| S07-S11-01 | MLOps + AI Lead | Real pinned vLLM and candidate model unavailable in local CI | Authorized model/tokenizer hashes and vLLM version; actual health, models, structured schema, chat template, finish_reason and revision inventory PASS on approved internal GPU |
| S07-S11-02 | IAM + Security + Network SRE | TLS/mTLS and corporate network policies absent | Approved identity/certificates and permitted routes; deny unauthenticated calls, all unauthorized paths, DNS and external egress with packet evidence |
| S07-S11-03 | SecOps + Data Steward | Model/trace/logging stack only runs in enterprise | Synthetic private-text canary with authorization; no prompt, response, auth token or evidence leaked to logs, metrics, telemetry or external sinks |
| S07-S11-04 | AI Quality + MLOps | Tokenizer budget and model-specific decoding/thinking are not verifiable by MockTransport | Pinned tokenizer, prompt, schema, model artifacts, approved synthetic Persian edge dataset; verify real input+output token budget, version negotiation, strict JSON, quote and abstention behavior |
| S07-S11-05 | SRE + GPU MLOps | Real OOM, concurrency, failover and latency cannot be measured locally | Approved bounded load, stop thresholds and performance policy; retry/circuit/cancellation/latency/VRAM/backpressure satisfy agreed acceptance |
| S07-S11-06 | Security + Legal + Release | Actual supply-chain model/OS attestation and legal authorization require enterprise import | Approved model, tokenizer, vLLM runtime/license, verified SHA manifest, vulnerability/SBOM scans, no auto-download and written signoff before artifact promotion |

**vLLM server security warning:** Official vLLM documentation cautions that built-in API-key protection does not cover all endpoints, including /invocations. Secure the *entire* inference listener by verified network gateway rules; API key alone is insufficient. Do not assume /health or /models are authorization boundaries.

No model was downloaded, selected, deployed or benchmarked in this stage. D-017 separates mandatory local tests from genuine Stage11 enterprise tests; D-015 final external business acceptance remains Stage12. No actual private text may be sent to outside services.

See docs/deployment/07_stage07_internal_llm_runbook.md.
