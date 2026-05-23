#!/usr/bin/env bash
# Deploy OCMS backend from ECR image
set -euo pipefail

: "${AWS_DEFAULT_REGION:?AWS_DEFAULT_REGION must be set}"
: "${ECR_REGISTRY:?ECR_REGISTRY must be set}"
: "${ECR_REPOSITORY:?ECR_REPOSITORY must be set}"
: "${IMAGE_TAG:=${GITHUB_SHA:-latest}}"

export ECR_IMAGE="${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"

echo "==> Logging into ECR"
aws ecr get-login-password --region "$AWS_DEFAULT_REGION" \
    | docker login --username AWS --password-stdin "$ECR_REGISTRY"

echo "==> Pulling image: $ECR_IMAGE"
docker pull "$ECR_IMAGE"

echo "==> Running Alembic migrations"
docker run --rm \
    --env OCMS_DATABASE_URL \
    --env OCMS_AWS_REGION="$AWS_DEFAULT_REGION" \
    "$ECR_IMAGE" \
    alembic upgrade head

echo "==> Restarting service"
docker compose -f docker-compose.prod.yml up -d --no-build

echo "==> Deploy complete: $ECR_IMAGE"
