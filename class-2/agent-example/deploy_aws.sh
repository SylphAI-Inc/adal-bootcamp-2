#!/usr/bin/env bash
#
# Deploy the Lumen Audio demo to AWS App Runner.
#
# The demo is a server-side BFF proxy (proxy/server.py) that serves the
# storefront (site/) and proxies /api/* to AdaL Cloud with the Clerk JWT
# injected server-side. App Runner gives it a public HTTPS URL with the least
# infra: build image -> push to ECR -> create/update an App Runner service.
#
# The JWT is passed as a runtime env var (RuntimeEnvironmentVariables) — it is
# NEVER baked into the image. For production, promote it to a Secrets Manager
# secret and reference it via RuntimeEnvironmentSecrets instead.
#
# Prereqs: AWS CLI authenticated, Docker running, an ADAL_JWT to run under.
#
# Usage:
#   ADAL_JWT="eyJ..." ./deploy.sh
#   AWS_REGION=us-west-2 SERVICE=lumen-demo ADAL_JWT="eyJ..." ./deploy.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

: "${AWS_REGION:=us-west-2}"
: "${SERVICE:=lumen-audio-demo}"
: "${ADAL_APP_URL:=https://cloud.adal.sylph.ai}"
: "${ADAL_MODEL:=google-gemini-3-flash-preview}"

if [[ -z "${ADAL_JWT:-}" ]]; then
  echo "ERROR: ADAL_JWT is required (a Clerk session JWT the demo runs under)." >&2
  echo "  ADAL_JWT=\"eyJ...\" ./deploy.sh" >&2
  exit 1
fi

command -v aws >/dev/null || { echo "ERROR: aws CLI is required." >&2; exit 1; }
command -v docker >/dev/null || { echo "ERROR: docker is required." >&2; exit 1; }

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ECR_REPO="${SERVICE}"
IMAGE_TAG="$(git -C "$SCRIPT_DIR" rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"
IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:${IMAGE_TAG}"

echo "→ Deploying Lumen demo"
echo "  region:  ${AWS_REGION}"
echo "  service: ${SERVICE}"
echo "  image:   ${IMAGE_URI}"
echo "  upstream:${ADAL_APP_URL}"
echo ""

# ── 1. Build + push the proxy image ─────────────────────────────────────────
aws ecr describe-repositories --repository-names "${ECR_REPO}" --region "${AWS_REGION}" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "${ECR_REPO}" \
       --image-scanning-configuration scanOnPush=true --region "${AWS_REGION}" >/dev/null

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "→ Building image (context = example root, Dockerfile = proxy/Dockerfile)…"
docker build --platform linux/amd64 -f proxy/Dockerfile -t "${IMAGE_URI}" .
docker push "${IMAGE_URI}"

# ── 2. IAM role letting App Runner pull from ECR (idempotent) ────────────────
ACCESS_ROLE="${SERVICE}-ecr-access"
if ! aws iam get-role --role-name "${ACCESS_ROLE}" >/dev/null 2>&1; then
  echo "→ Creating App Runner ECR access role ${ACCESS_ROLE}…"
  aws iam create-role --role-name "${ACCESS_ROLE}" \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"build.apprunner.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
  aws iam attach-role-policy --role-name "${ACCESS_ROLE}" \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess >/dev/null
  echo "  waiting for role propagation…"; sleep 10
fi
ACCESS_ROLE_ARN="$(aws iam get-role --role-name "${ACCESS_ROLE}" --query Role.Arn --output text)"

# ── 3. Create or update the App Runner service ───────────────────────────────
SOURCE_CONFIG="$(cat <<JSON
{
  "ImageRepository": {
    "ImageIdentifier": "${IMAGE_URI}",
    "ImageRepositoryType": "ECR",
    "ImageConfiguration": {
      "Port": "8080",
      "RuntimeEnvironmentVariables": {
        "ADAL_APP_URL": "${ADAL_APP_URL}",
        "ADAL_MODEL": "${ADAL_MODEL}",
        "ADAL_JWT": "${ADAL_JWT}"
      }
    }
  },
  "AutoDeploymentsEnabled": false,
  "AuthenticationConfiguration": { "AccessRoleArn": "${ACCESS_ROLE_ARN}" }
}
JSON
)"

SERVICE_ARN="$(aws apprunner list-services --region "${AWS_REGION}" \
  --query "ServiceSummaryList[?ServiceName=='${SERVICE}'].ServiceArn | [0]" --output text 2>/dev/null || true)"

if [[ -z "${SERVICE_ARN}" || "${SERVICE_ARN}" == "None" ]]; then
  echo "→ Creating App Runner service ${SERVICE}…"
  SERVICE_ARN="$(aws apprunner create-service --region "${AWS_REGION}" \
    --service-name "${SERVICE}" \
    --source-configuration "${SOURCE_CONFIG}" \
    --instance-configuration '{"Cpu":"1024","Memory":"2048"}' \
    --query "Service.ServiceArn" --output text)"
else
  echo "→ Updating existing App Runner service ${SERVICE}…"
  aws apprunner update-service --region "${AWS_REGION}" \
    --service-arn "${SERVICE_ARN}" \
    --source-configuration "${SOURCE_CONFIG}" >/dev/null
fi

echo "→ Waiting for the service to be RUNNING…"
for _ in $(seq 1 40); do
  STATUS="$(aws apprunner describe-service --region "${AWS_REGION}" --service-arn "${SERVICE_ARN}" \
    --query "Service.Status" --output text)"
  [[ "${STATUS}" == "RUNNING" ]] && break
  [[ "${STATUS}" == *FAILED* ]] && { echo "ERROR: service is ${STATUS}"; exit 1; }
  sleep 15
done

URL="$(aws apprunner describe-service --region "${AWS_REGION}" --service-arn "${SERVICE_ARN}" \
  --query "Service.ServiceUrl" --output text)"
echo ""
echo "✓ Deployed. Live at:"
echo "  https://${URL}/"
