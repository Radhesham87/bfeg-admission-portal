#!/usr/bin/env bash
# ---------------------------------------------------------------
#  Deploys backend/ to Google Cloud Run.
#  Fill in the five values below, then run:  bash deploy-backend.sh
# ---------------------------------------------------------------
set -e

SERVICE="bfeg-api"
REGION="asia-south1"

ADMIN_USERNAME="admin"
ADMIN_PASSWORD="CHANGE-ME-to-a-long-password"
JWT_SECRET="CHANGE-ME-run: python -c \"import secrets;print(secrets.token_hex(32))\""
DATABASE_URL="CHANGE-ME-postgresql://user:pass@host/db?sslmode=require"
ALLOWED_ORIGINS="https://CHANGE-ME.netlify.app"

# ---------------------------------------------------------------
for v in ADMIN_PASSWORD JWT_SECRET DATABASE_URL ALLOWED_ORIGINS; do
  case "${!v}" in
    CHANGE-ME*|*CHANGE-ME*)
      echo "ERROR: set $v at the top of this script first."; exit 1;;
  esac
done

cd "$(dirname "$0")/backend"

gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "ADMIN_USERNAME=${ADMIN_USERNAME}" \
  --set-env-vars "ADMIN_PASSWORD=${ADMIN_PASSWORD}" \
  --set-env-vars "JWT_SECRET=${JWT_SECRET}" \
  --set-env-vars "DATABASE_URL=${DATABASE_URL}" \
  --set-env-vars "ALLOWED_ORIGINS=${ALLOWED_ORIGINS}"

echo
echo "Deployed. Check it with:"
echo "  curl \$(gcloud run services describe $SERVICE --region $REGION --format='value(status.url)')/api/health"
