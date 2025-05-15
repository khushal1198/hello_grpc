#!/bin/bash

# Generate a secure webhook secret
WEBHOOK_SECRET=$(openssl rand -hex 20)

# Replace placeholders in the manifests
sed -i '' "s/\${GITHUB_TOKEN}/$GITHUB_TOKEN/g" github-credentials.yaml
sed -i '' "s/\${WEBHOOK_SECRET}/$WEBHOOK_SECRET/g" jenkins-webhook.yaml

# Apply the configurations
kubectl apply -f github-credentials.yaml
kubectl apply -f jenkins-pipeline.yaml
kubectl apply -f jenkins-webhook.yaml

# Get the Jenkins URL
JENKINS_URL=$(kubectl get svc -n jenkins jenkins -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
JENKINS_PORT=$(kubectl get svc -n jenkins jenkins -o jsonpath='{.spec.ports[0].nodePort}')

echo "Jenkins pipeline has been set up!"
echo "Jenkins URL: http://$JENKINS_URL:$JENKINS_PORT"
echo "Webhook URL: http://$JENKINS_URL:$JENKINS_PORT/github-webhook/"
echo "Webhook Secret: $WEBHOOK_SECRET" 