#!/usr/bin/env bash
# Collect Stage 04 Linux package evidence from the exact tested, non-root Docker image.
# This is an opt-in PUBLIC-PACKAGE network operation; it never starts the API.
set -Eeuo pipefail
umask 077

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
if [[ "$(git branch --show-current)" != main || -n "$(git status --porcelain)" ]]; then
  echo 'STOP: clean main checkout required.' >&2
  exit 1
fi

BASE_COMMIT=d39e5f21c3c37a8fbeb03a599c0c3f6b8d407e73
BASE_IMAGE=text-evaluation-service:stage04-pytest-d39e5f21c3c3
BASE_ID=sha256:7b3c7532a3e31f002ec1f8211c28d22148602b74ff1bfc51dd8edb4df5239785
if ! git cat-file -e "${BASE_COMMIT}^{commit}" 2>/dev/null || \
   ! git diff --quiet "$BASE_COMMIT" HEAD -- requirements.txt requirements-dev.txt src; then
  echo 'STOP: installed application/dependency pins differ from reviewed Linux image.' >&2
  exit 1
fi
image_info="$(sudo docker image inspect --format '{{.Id}} {{.Config.User}} {{.Architecture}}' "$BASE_IMAGE")" || {
  echo 'STOP: reviewed Linux test image unavailable.' >&2
  exit 1
}
if [[ "$image_info" != "$BASE_ID 65532:65532 amd64" ]]; then
  echo 'STOP: test image ID, runtime user or architecture mismatch.' >&2
  exit 1
fi

EVIDENCE="${1:-.stage04-evidence-linux-$(git rev-parse --short=12 HEAD)}"
if [[ "$EVIDENCE" != .stage04-evidence-linux-* || "$EVIDENCE" == */* || -e "$EVIDENCE" ]]; then
  echo 'STOP: supply a NEW project-local .stage04-evidence-linux-* directory.' >&2
  exit 1
fi
AUDITOR_IMAGE="text-evaluation-service:stage04-linux-audit-$(git rev-parse --short=12 HEAD)"
if sudo docker image inspect "$AUDITOR_IMAGE" >/dev/null 2>&1; then
  echo 'STOP: auditor image tag already exists; no overwrite.' >&2
  exit 1
fi
CTX="$(mktemp -d /tmp/tes-stage04-audit.XXXXXXXX)"
cleanup() {
  if [[ "$CTX" == /tmp/tes-stage04-audit.* && -d "$CTX" ]]; then
    rm -r -- "$CTX"
  fi
}
trap cleanup EXIT

git archive HEAD requirements-audit.txt scripts/verification/audit_stage04_dependencies.py \
  scripts/verification/review_stage04_supply_chain.py | tar -xf - -C "$CTX"
cat > "$CTX/Dockerfile" <<'DOCKERFILE'
FROM text-evaluation-service:stage04-pytest-d39e5f21c3c3
USER root
COPY requirements-audit.txt /opt/stage04/requirements-audit.txt
COPY scripts/verification/audit_stage04_dependencies.py scripts/verification/review_stage04_supply_chain.py /app/scripts/verification/
RUN python -m venv /opt/stage04-audit \
 && /opt/stage04-audit/bin/python -m pip install --disable-pip-version-check --no-cache-dir --only-binary=:all: --timeout 120 --retries 4 --index-url https://pypi.tuna.tsinghua.edu.cn/simple pip==26.2.2 \
 && /opt/stage04-audit/bin/python -m pip install --disable-pip-version-check --no-cache-dir --only-binary=:all: --timeout 120 --retries 4 --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r /opt/stage04/requirements-audit.txt \
 && /opt/stage04-audit/bin/python -m pip check \
 && chgrp 65532 /app/scripts/verification/audit_stage04_dependencies.py /app/scripts/verification/review_stage04_supply_chain.py \
 && chmod 0640 /app/scripts/verification/audit_stage04_dependencies.py /app/scripts/verification/review_stage04_supply_chain.py
ENV HOME=/tmp XDG_CACHE_HOME=/tmp/cache PYTHONPATH=/app PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
USER 65532:65532
WORKDIR /app
DOCKERFILE

# The known local base image is never pulled or overwritten. Build tools are isolated
# in /opt/stage04-audit, outside the audited system site-packages.
sudo docker build --pull=false --network default --progress plain --tag "$AUDITOR_IMAGE" "$CTX"
# This new output directory contains public package metadata only; UID 65532 owns it.
sudo install -d -o 65532 -g 65532 -m 0700 "$EVIDENCE" "$EVIDENCE/wheelhouse"
MOUNT="$ROOT/$EVIDENCE:/evidence:rw"
COMMON=(--rm --read-only --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  --cap-drop ALL --security-opt no-new-privileges --pids-limit 128 \
  --memory 1g --cpus 2 --user 65532:65532 --volume "$MOUNT" --entrypoint /bin/sh)

# Snapshot installed metadata and RECORD hashes without any network.
sudo docker run --network none "${COMMON[@]}" "$AUDITOR_IMAGE" -ec '
  python scripts/verification/review_stage04_supply_chain.py bootstrap-check
  /opt/stage04-audit/bin/python scripts/verification/review_stage04_supply_chain.py bootstrap-check
  python -m pip check
  python scripts/verification/audit_stage04_dependencies.py --output /evidence/inventory.json
  python scripts/verification/review_stage04_supply_chain.py freeze --inventory /evidence/inventory.json --output /evidence/pinned-closure.txt
  python scripts/verification/review_stage04_supply_chain.py license-template --inventory /evidence/inventory.json --output /evidence/license-review.json
'

# Only PUBLIC names/versions and public wheels/advisories are exchanged externally.
# No host directories, customer data, credentials, app ports or internal networks.
sudo docker run --network bridge "${COMMON[@]}" "$AUDITOR_IMAGE" -ec '
  set -eu
  scan_rc=0
  /opt/stage04-audit/bin/python -m pip_audit --strict --path /usr/local/lib/python3.12/site-packages \
    --vulnerability-service osv --timeout 120 --progress-spinner off \
    --format json --output /evidence/vulnerabilities.osv.json || scan_rc=$?
  audit_status="$(python scripts/verification/review_stage04_supply_chain.py audit-status \
    --inventory /evidence/inventory.json --audit /evidence/vulnerabilities.osv.json)"
  case "$audit_status:$scan_rc" in
    AUDIT_COMPLETE_NO_REPORTED_FINDINGS:0) ;;
    AUDIT_COMPLETE_WITH_FINDINGS:1) echo "SECURITY_FINDINGS_PRESENT; evidence preserved" >&2 ;;
    *) echo "STOP: incomplete or contradictory OSV result" >&2; exit 1 ;;
  esac
  /opt/stage04-audit/bin/python -m cyclonedx_py environment /usr/local/bin/python \
    --spec-version 1.6 --output-format JSON --output-file /evidence/sbom.cdx.json
  python -m pip download --disable-pip-version-check --no-cache-dir --timeout 120 --retries 4 \
    --only-binary=:all: --no-deps --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    -r /evidence/pinned-closure.txt -d /evidence/wheelhouse
  python scripts/verification/review_stage04_supply_chain.py hash-wheels \
    --inventory /evidence/inventory.json --wheelhouse /evidence/wheelhouse --output /evidence/wheel-hashes.json
  python scripts/verification/review_stage04_supply_chain.py verify-pypi \
    --hashes /evidence/wheel-hashes.json --output /evidence/pypi-digests.json
  if [ "$audit_status" != AUDIT_COMPLETE_NO_REPORTED_FINDINGS ]; then
    echo "STOP: verified OSV findings remain; Stage 04 gate OPEN" >&2
    exit 2
  fi
  echo "LINUX_PACKAGE_EVIDENCE_COLLECTED_NOT_LEGALLY_APPROVED"
'

printf 'Evidence saved as %s (owned by UID 65532); license approval, image OS CVEs and provenance remain separate.\n' "$EVIDENCE"
