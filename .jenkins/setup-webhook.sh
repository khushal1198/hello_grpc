#!/bin/bash

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable is not set"
    echo "Please set it with: export GITHUB_TOKEN=your_github_token"
    exit 1
fi

# Generate a secure webhook secret
WEBHOOK_SECRET=$(openssl rand -hex 20)

# Get Jenkins URL
JENKINS_URL=$(kubectl get svc -n jenkins jenkins -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
JENKINS_PORT=$(kubectl get svc -n jenkins jenkins -o jsonpath='{.spec.ports[0].nodePort}')
WEBHOOK_URL="http://$JENKINS_URL:$JENKINS_PORT/github-webhook/"

# Create GitHub webhook using GitHub API
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/khushal1198/hello_grpc/hooks \
  -d "{
    \"name\": \"web\",
    \"active\": true,
    \"events\": [\"push\", \"pull_request\"],
    \"config\": {
      \"url\": \"$WEBHOOK_URL\",
      \"content_type\": \"json\",
      \"secret\": \"$WEBHOOK_SECRET\"
    }
  }"

echo "Jenkins webhook has been set up!"
echo "Webhook URL: $WEBHOOK_URL"
echo "Webhook Secret: $WEBHOOK_SECRET"
echo "Please configure this secret in your Jenkins job configuration" 