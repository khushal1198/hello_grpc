#!/bin/bash

# Check if required environment variables are set
if [ -z "$GITHUB_TOKEN" ] || [ -z "$KUBECONFIG_PATH" ]; then
    echo "Error: Required environment variables are not set"
    echo "Please set:"
    echo "  GITHUB_TOKEN - Your GitHub personal access token"
    echo "  KUBECONFIG_PATH - Path to your kubeconfig file"
    exit 1
fi

# Get Jenkins URL and admin password
JENKINS_URL=$(kubectl get svc -n jenkins jenkins -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
JENKINS_PORT=$(kubectl get svc -n jenkins jenkins -o jsonpath='{.spec.ports[0].nodePort}')
JENKINS_PASSWORD=$(kubectl exec -n jenkins jenkins-0 -- cat /run/secrets/additional/chart-admin-password)

# Create GitHub credentials
curl -X POST "http://$JENKINS_URL:$JENKINS_PORT/credentials/store/system/domain/_/createCredentials" \
    --user "admin:$JENKINS_PASSWORD" \
    --data-urlencode "json={
        \"\": \"0\",
        \"credentials\": {
            \"scope\": \"GLOBAL\",
            \"id\": \"github-credentials\",
            \"username\": \"khushal1198\",
            \"password\": \"$GITHUB_TOKEN\",
            \"description\": \"GitHub Container Registry credentials\",
            \"$class\": \"com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl\"
        }
    }"

# Create kubeconfig credentials
curl -X POST "http://$JENKINS_URL:$JENKINS_PORT/credentials/store/system/domain/_/createCredentials" \
    --user "admin:$JENKINS_PASSWORD" \
    --data-urlencode "json={
        \"\": \"0\",
        \"credentials\": {
            \"scope\": \"GLOBAL\",
            \"id\": \"kubeconfig\",
            \"description\": \"Kubernetes cluster credentials\",
            \"file\": \"$KUBECONFIG_PATH\",
            \"$class\": \"org.jenkinsci.plugins.plaincredentials.impl.FileCredentialsImpl\"
        }
    }"

echo "Credentials have been set up in Jenkins!" 