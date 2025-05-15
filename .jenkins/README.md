# Jenkins Setup

This directory contains scripts for one-time setup of Jenkins and its integrations. These scripts only need to be run once during initial setup, unless you need to:
- Change GitHub credentials
- Update webhook configuration
- Reconfigure Jenkins after a cluster reset

## Webhook Setup

The `setup-webhook.sh` script sets up GitHub webhook integration with Jenkins. This is a one-time setup that:
1. Generates a secure webhook secret
2. Configures Jenkins to accept webhooks
3. Creates a GitHub webhook to trigger Jenkins builds

You only need to run this script again if:
- The Jenkins URL changes
- The webhook secret needs to be rotated
- The webhook configuration needs to be updated

### Prerequisites

1. **GitHub Personal Access Token (PAT)**
   - Go to GitHub → Settings → Developer settings → Personal access tokens
   - Create a new token with these permissions:
     - `repo` (Full control of private repositories)
     - `admin:repo_hook` (Full control of repository hooks)

### Usage

1. Make the script executable:
   ```bash
   chmod +x setup-webhook.sh
   ```

2. Set required environment variables:
   ```bash
   export GITHUB_TOKEN="your_github_token"
   ```

3. Run the script:
   ```bash
   ./setup-webhook.sh
   ```

## Credentials Setup

The `setup-credentials.sh` script sets up two essential credentials in Jenkins. This is a one-time setup unless:
- GitHub token needs to be rotated
- Kubernetes cluster credentials change
- Jenkins is reinstalled

1. **GitHub Container Registry Credentials** (`github-credentials`)
   - Used for pushing Docker images to GitHub Container Registry
   - Requires a GitHub Personal Access Token (PAT)

2. **Kubernetes Cluster Credentials** (`kubeconfig`)
   - Used for deploying to Kubernetes cluster
   - Requires a kubeconfig file

### Prerequisites

1. **GitHub Personal Access Token (PAT)**
   - Go to GitHub → Settings → Developer settings → Personal access tokens
   - Create a new token with these permissions:
     - `read:packages`
     - `write:packages`
     - `delete:packages`

2. **Kubernetes Config File**
   - Typically located at `~/.kube/config`
   - Ensure it has correct permissions: `chmod 600 ~/.kube/config`

### Usage

1. Make the script executable:
   ```bash
   chmod +x setup-credentials.sh
   ```

2. Set required environment variables:
   ```bash
   export GITHUB_TOKEN="your_github_token"
   export KUBECONFIG_PATH="/path/to/your/kubeconfig"
   ```

3. Run the script:
   ```bash
   ./setup-credentials.sh
   ```

## What the Script Does

1. Verifies required environment variables are set
2. Retrieves Jenkins URL and admin password from Kubernetes
3. Creates GitHub credentials in Jenkins using the PAT
4. Creates Kubernetes credentials in Jenkins using the kubeconfig file

## Troubleshooting

If you encounter issues:

1. **Jenkins URL not accessible**
   - Verify Jenkins service is running: `kubectl get svc -n jenkins`
   - Check if the LoadBalancer IP is assigned

2. **Authentication failures**
   - Verify the GitHub token is valid
   - Ensure kubeconfig has correct permissions
   - Check Jenkins admin password is accessible

3. **Webhook not triggering**
   - Check GitHub webhook settings in repository
   - Verify webhook URL is accessible
   - Check Jenkins logs: `kubectl logs -n jenkins jenkins-0` 