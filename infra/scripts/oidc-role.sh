#!/usr/bin/env bash
# oidc-role.sh — creates the IAM OIDC role for GitHub Actions
# Run once from your local machine with AWS credentials.
# After this, no long-lived AWS keys are ever stored in GitHub.

set -euo pipefail

GITHUB_ORG="signed-data"
GITHUB_REPO="cds"
ROLE_NAME="signeddata-github-actions"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="${AWS_DEFAULT_REGION:-us-east-1}"

echo "==> Account: $ACCOUNT_ID  Region: $REGION"

# 1. OIDC provider (once per account)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1" \
  2>/dev/null && echo "✅ OIDC provider created" || echo "ℹ️  OIDC provider already exists"

OIDC_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"

# 2. Trust policy — only this repo
TRUST=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "${OIDC_ARN}" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:${GITHUB_ORG}/${GITHUB_REPO}:*"
      }
    }
  }]
}
EOF
)

aws iam create-role \
  --role-name "$ROLE_NAME" \
  --assume-role-policy-document "$TRUST" \
  --description "GitHub Actions deploy role for ${GITHUB_ORG}/${GITHUB_REPO}"

# 3. Permissions
POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CDKDeploy",
      "Effect": "Allow",
      "Action": [
        "cloudformation:*", "lambda:*", "s3:*", "sqs:*",
        "events:*", "apigateway:*", "secretsmanager:*",
        "bedrock:InvokeModel", "logs:*", "ecr:*",
        "cloudfront:*", "route53:*", "acm:*",
        "iam:PassRole", "iam:GetRole", "iam:CreateRole",
        "iam:DeleteRole", "iam:AttachRolePolicy", "iam:DetachRolePolicy",
        "iam:PutRolePolicy", "iam:DeleteRolePolicy", "iam:TagRole",
        "ssm:GetParameter", "ssm:PutParameter"
      ],
      "Resource": "*"
    }
  ]
}
EOF
)

aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "signeddata-deploy-policy" \
  --policy-document "$POLICY"

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"
echo ""
echo "✅ Role created: $ROLE_ARN"
echo ""
echo "Add to GitHub Secrets (Settings → Secrets → Actions):"
echo "  AWS_DEPLOY_ROLE_ARN = $ROLE_ARN"
echo ""
echo "After first 'cdk deploy', also add:"
echo "  SITE_BUCKET         — from CDK output SiteBucketName"
echo "  CF_DISTRIBUTION_ID  — from CDK output CfDistributionId"
