# Stage 04 — Local Security Validation and Acceptance Evidence

Date: 2026-10-24. GitHub baseline: `4e14c2db36dcd7ac771c3ee554367fd9e3a34b88`, `main`, public repository, verified using GitHub connector. Environment: isolated Python 3.13.5 sandbox, no access to corporate network, no real data or credentials. Direct package versions: FastAPI 0.128.2, Pydantic 2.13.5, PyYAML 6.0.3, Uvicorn 0.48.0; test: pytest 9.0.2, httpx 0.28.1. Python >=3.10 should be verified in supported corporate environment; actual interpreter target not organization-approved (`OD-13 OPEN`).

## Implemented local controls

- Real FastAPI startup/application factory; default only static liveness and readiness; discovery/wiring for future controllers, no real business route or DB/model/worker. Router is convention-discovered and DI scans `infrastructure`, `core`, `application`, except excluded directories, with fail-closed import errors and a bootstrap guard. DI singleton locking and cycle detection.
- Fail-closed YAML configuration, development/staging/production separation, strict schema, no external-allowed flag or non-loopback bind; env-only fake secret references. Actual Vault service is **not invented** while `OD-08 OPEN`.
- Metadata-only log formatter (untrusted free-text and exception ignored), correlation IDs, error status normalization, disabled docs and programmatic access logs (`python -m src.host.app` only); clean lifespan shutdown.
- Local role/scope/assignment authorization primitive, private-literal endpoint validation, no runtime HTTP/LLM client or model auto-download.

## Executed checks (observed)

| Check | Command | Result | Scope |
|---|---|---|---|
| Stage 04 unit/security/integration smoke | `PYTHONPATH=. python -m pytest -q tests/test_foundation.py` | `26 PASSED, 0 FAILED, 0 SKIPPED` | local synthetic only |
| Real Uvicorn loopback smoke | `PYTHONPATH=. python -m src.host.app`, local Python urllib GET `/health/live` and `/health/ready`, then SIGTERM | PASS: both HTTP 200; APP_START/APP_STOP observed | isolated local only |
| Python syntax | `PYTHONPATH=. python -m compileall -q src tests scripts` | `PASS` | local Python 3.13.5 |
| Static safety/source constraints | `python scripts/verification/check_stage04_safety.py` | `PASS: 9 runtime source files; dependency pins; credential patterns; ignored secrets` | AST/runtime source; not whole-repo DLP |
| Installed pinned versions | `importlib.metadata.version(...)` | `MATCH direct pins` | current sandbox, not clean dependency resolution |
| Environment-wide dependency check | `python -m pip check` | `FAIL (unrelated environment package moviepy requires pillow<12; installed pillow 12.3)` | shared host packages; no Stage04 package shown at fault |
| Original Stage 02/03 regression scripts | `NOT_RUN` | `NOT_RUN: GitHub files were inspected remotely but not present in sandbox runtime` | repeat in a real full clone; not PASS |
| Full transitive SBOM, vulnerability and license approval | `NOT_RUN` | `NOT_RUN: offline vulnerability database, approved wheelhouse and lock/hash manifest unavailable` | **local supply-chain gate outstanding** |
| Corporate SSO/Vault/mTLS/firewall/no-egress/model/restore/load | `DEFERRED_TO_STAGE_11` | not run | see ledger |

The earlier DI test initially failed due to inherited `object.__init__(*args, **kwargs)` being treated as injection parameters. The resolver now skips variadic arguments; tests rerun 26/26 PASS. A local cyclic self-annotation issue was fixed by supplying the decorated class to localns; rerun PASS. No tests are claimed successful before rerun.

## Gate evaluation

| Acceptance item | Local verdict | Evidence / remaining risk |
|---|---|---|
| Threat modeling and trust boundaries | PASS_DOCUMENTED | `docs/security/01_threat_model.md` |
| Candidate access matrix + local denial policy | PASS_LOCAL / ORG_APPROVAL_OPEN | Policy tests in 26-test suite, `OD-07` not decided |
| Config, DI, bootstrap, discoverable WebService | PASS_LOCAL | Discovery, singleton, config and startup tests; **only synthetic discovery fixture; no actual product controller** until Stage 10 |
| Import/startup/shutdown/health/error sanitization | PASS_LOCAL | TestClient smoke, static liveness/readiness and all sanitized errors |
| Sensitive logging/secret handling local | PASS_LOCAL | Synthetic marker and redacted config/exception tests; external gateway logs unverified |
| Network/topology/secrets deployment design | PASS_DOCUMENTED / NOT_DEPLOYED | proposed topology and port matrix, OD-08/13 OPEN |
| Outbound endpoint and auto-download prevention | PASS_LOCAL_STATIC | no external runtime client; future Stage 07 re-evaluation; real firewall `DEFERRED_TO_STAGE_11` |
| Dependency and supply-chain review | **PARTIAL / NOT_RUN full SCA** | versions pinned and source scanned; no complete SBOM/license/vulnerability scan or offline wheelhouse |
| Original regression verification | **NOT_RUN** | complete checkout unavailable in runner; must rerun |
| Real internal-server-only tests | `DEFERRED_TO_STAGE_11` | detailed test ledger |
| No unmitigated Critical/High local security defect | NOT_PROVEN_AS_ABSOLUTE | No evident local exploit, but full dependency security check outstanding |

**Stage status until missing local gates are closed: `IN_PROGRESS`**, not `DONE`. The absence of organizational server alone is *not* a blocker (D-017); unresolved **local** regression and supply-chain checks are not misclassified as server-dependent. Never treat this foundation as a production deployment approval. Stage 05 is not authorized by this document.
