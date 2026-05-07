#!/usr/bin/env bash
# post-deploy.sh — reads CDK outputs and sets GitHub secrets automatically
# Run after the first 'cdk deploy'.
# Requires: gh CLI authenticated, jq installed.

set -euo pipefail

GITHUB_ORG="signed-data"
GITHUB_REPO="cds"
OUTPUTS_FILE="${1:-cdk-outputs.json}"

if [[ ! -f "$OUTPUTS_FILE" ]]; then
  echo "❌ $OUTPUTS_FILE not found. Run: cdk deploy --outputs-file cdk-outputs.json"
  exit 1
fi

STACK=$(jq -r 'keys[0]' "$OUTPUTS_FILE")
echo "==> Reading outputs from stack: $STACK"

SITE_BUCKET=$(jq -r ".\"$STACK\".SiteBucketName"  "$OUTPUTS_FILE")
CF_DIST_ID=$(jq  -r ".\"$STACK\".CfDistributionId" "$OUTPUTS_FILE")

echo "  SiteBucket:        $SITE_BUCKET"
echo "  CF Distribution:   $CF_DIST_ID"

gh secret set SITE_BUCKET        --body "$SITE_BUCKET" --repo "$GITHUB_ORG/$GITHUB_REPO"
gh secret set CF_DISTRIBUTION_ID --body "$CF_DIST_ID"  --repo "$GITHUB_ORG/$GITHUB_REPO"

echo "✅ GitHub secrets updated"
