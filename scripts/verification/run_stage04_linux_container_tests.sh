#!/usr/bin/env bash
# Execute Stage 04 Python tests in an isolated, offline Linux container.
set -Eeuo pipefail
umask 077

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [[ "$(git branch --show-current)" != "main" ]] || [[ -n "$(git status --porcelain)" ]]; then
  echo 'STOP: Stage 04 Linux tests require a clean main checkout.' >&2
  exit 1
fi

SOURCE_COMMIT='07f47f10fc0c'
BASE_IMAGE="text-evaluation-service:stage04-nonrootfix-${SOURCE_COMMIT}"

# The existing corrected image was built from SOURCE_COMMIT. Refuse to test stale source.
if ! git cat-file -e "${SOURCE_COMMIT}^{commit}" 2>/dev/null || \
   ! git diff --quiet "$SOURCE_COMMIT" HEAD -- requirements.txt src; then
  echo 'STOP: Runtime source differs from the prebuilt Stage 04 image.' >&2
  exit 1
fi

if ! sudo docker image inspect "$BASE_IMAGE" >/dev/null 2>&1; then
  echo "STOP: Required local candidate image not found: $BASE_IMAGE" >&2
  exit 1
fi

TAG="text-evaluation-service:stage04-pytest-$(git rev-parse --short=12 HEAD)"
if sudo docker image inspect "$TAG" >/dev/null 2>&1; then
  echo "STOP: Test image tag already exists: $TAG" >&2
  exit 1
fi

CTX="$(mktemp -d /tmp/tes-stage04-pytest.XXXXXXXX)"
cleanup() {
  if [[ "$CTX" == /tmp/tes-stage04-pytest.* && -d "$CTX" ]]; then
    rm -r -- "$CTX"
  fi
}
trap cleanup EXIT

# Archive tracked test tooling and manifests only; the source is already in BASE_IMAGE.
git archive HEAD requirements.txt requirements-dev.txt scripts tests | \
  tar -xf - -C "$CTX"

cat > "$CTX/Dockerfile" <<'DOCKERFILE'
FROM text-evaluation-service:stage04-nonrootfix-07f47f10fc0c
WORKDIR /app
USER root
COPY requirements.txt requirements-dev.txt ./
COPY tests/ ./tests/
COPY scripts/ ./scripts/
RUN python -m pip install --disable-pip-version-check --root-user-action=ignore \
      --no-cache-dir --only-binary=:all: --timeout 30 --retries 2 \
      --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
      -r requirements-dev.txt \
    && python -m pip check \
    && chgrp -R 65532 /app/tests /app/scripts \
    && chmod -R g-w,o-rwx /app/tests /app/scripts \
    && chmod -R g+rX /app/tests /app/scripts
ENV PYTHONPATH=/app PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
USER 65532:65532
DOCKERFILE

# Network access is needed only during the dedicated test image build for public packages.
sudo docker build --pull=false --network default --progress plain --tag "$TAG" "$CTX"

# Run all checks offline as the non-root user, without app ports, mounts or shared networks.
sudo docker run --rm \
  --network none \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --pids-limit 128 \
  --memory 1g \
  --cpus 2 \
  --user 65532:65532 \
  --entrypoint /bin/sh \
  "$TAG" -ec '
    python -m pytest -q -p no:cacheprovider tests
    python -m unittest discover -s scripts/benchmark -p "test_*.py" -q
    python -m unittest discover -s scripts/verification -p "test_check_stage02_docs.py" -q
    python scripts/verification/check_stage04_safety.py
    python -m pip check
    python -c "import os; from src.host.app import app; assert os.getuid()==65532; assert app.title==\"text-evaluation-service\"; print(\"NON_ROOT_IMPORT_PASS\")"
  '

sudo docker image inspect \
  --format 'TestImage={{.Id}} User={{.Config.User}} Architecture={{.Architecture}}' \
  "$TAG"
printf 'STAGE04_LINUX_CONTAINER_TESTS_PASS image=%s\n' "$TAG"
