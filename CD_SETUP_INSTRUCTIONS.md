# Connectivity Layer CD Pipeline Setup Instructions

## 🎯 Overview
This guide will help you set up the Continuous Deployment (CD) pipeline for the Connectivity Layer repository.

## 📋 Prerequisites
- Azure CLI installed and configured
- kubectl installed
- Access to your Azure subscription and AKS cluster
- GitHub repository with admin access

## 🔧 Step 1: Create Azure Service Principal

```bash
# Create service principal for GitHub Actions
az ad sp create-for-rbac --name "connectivity-cd-pipeline" \
  --role contributor \
  --scopes /subscriptions/{your-subscription-id}/resourceGroups/service-web \
  --sdk-auth

# Grant ACR push permissions
az role assignment create \
  --assignee {service-principal-id} \
  --role AcrPush \
  --scope /subscriptions/{your-subscription-id}/resourceGroups/service-web/providers/Microsoft.ContainerRegistry/registries/iotflow
```

## 🔐 Step 2: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

### Required Secrets:
```bash
# Azure Authentication (copy the entire JSON output from service principal creation)
AZURE_CREDENTIALS='{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "..."
}'

# Azure Container Registry
ACR_USERNAME=iotflow
ACR_PASSWORD=<your-acr-password>
```

### Optional Variables (for notifications):
```bash
# Slack webhook URL (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## 🏗️ Step 3: Set Up GitHub Environments

1. Go to your repository → Settings → Environments
2. Create two environments:
   - `staging` (no protection rules)
   - `production` (with required reviewers)

## 🚀 Step 4: Deploy Kubernetes Resources

```bash
# Connect to your AKS cluster
az aks get-credentials --resource-group service-web --name iotflow-cluster

# Create namespace if it doesn't exist
kubectl create namespace iotflow --dry-run=client -o yaml | kubectl apply -f -

# Apply the connectivity layer deployment
kubectl apply -f k8s/connectivity.yml
```

## 🧪 Step 5: Test the Pipeline

### Manual Test:
1. Go to Actions tab in your GitHub repository
2. Select "CD - Connectivity Layer" workflow
3. Click "Run workflow"
4. Choose environment (staging recommended for first test)
5. Check "Force deployment" if needed
6. Click "Run workflow"

### Automatic Test:
1. Make a small change to your code (e.g., update a comment in `app.py`)
2. Commit and push to `develop` branch (triggers staging deployment)
3. Or push to `main` branch (triggers production deployment)

## 📊 Step 6: Monitor Deployment

### Check GitHub Actions:
- Go to Actions tab to see workflow progress
- Each step shows detailed logs
- Summary shows deployment status

### Check AKS Deployment:
```bash
# Check pod status
kubectl get pods -n iotflow -l app=connectivity-layer

# Check deployment status
kubectl get deployment connectivity-layer -n iotflow

# Check service
kubectl get service connectivity-layer -n iotflow

# View logs
kubectl logs -n iotflow -l app=connectivity-layer --tail=50
```

### Health Check:
```bash
# If using gateway (external access)
curl http://4.233.23.8:5000/health

# Or port-forward for testing
kubectl port-forward service/connectivity-layer 5000:5000 -n iotflow
curl http://localhost:5000/health
```

## 🔄 Step 7: Rollback (if needed)

### Via kubectl:
```bash
# Rollback to previous version
kubectl rollout undo deployment/connectivity-layer -n iotflow

# Check rollout status
kubectl rollout status deployment/connectivity-layer -n iotflow
```

### Via GitHub Actions:
1. Go to Actions tab
2. Find the last successful deployment
3. Click "Re-run all jobs"

## 🎛️ Pipeline Features

### Automatic Triggers:
- **Push to `develop`** → Deploys to staging
- **Push to `main`** → Deploys to production (with approval)
- **Manual trigger** → Choose environment and options

### Smart Deployment:
- Only deploys if source code changes detected
- Can force deployment with manual trigger
- Caches Docker layers for faster builds

### Health Checks:
- Kubernetes readiness/liveness probes
- External health endpoint verification
- Automatic rollback on failure

### Notifications:
- Slack notifications (if configured)
- GitHub Actions summary
- Deployment status in PR comments

## 🐛 Troubleshooting

### Common Issues:

1. **Authentication Failed**
   ```bash
   # Check service principal permissions
   az role assignment list --assignee {service-principal-id}
   ```

2. **Image Pull Failed**
   ```bash
   # Check ACR permissions
   az acr check-health --name iotflow
   ```

3. **Deployment Timeout**
   ```bash
   # Check pod events
   kubectl describe pod -n iotflow -l app=connectivity-layer
   ```

4. **Health Check Failed**
   ```bash
   # Check application logs
   kubectl logs -n iotflow -l app=connectivity-layer
   ```

### Debug Commands:
```bash
# Get all resources
kubectl get all -n iotflow

# Describe deployment
kubectl describe deployment connectivity-layer -n iotflow

# Check events
kubectl get events -n iotflow --sort-by='.lastTimestamp'

# Check secrets
kubectl get secrets -n iotflow
```

## 📈 Next Steps

1. **Test the pipeline** with a small code change
2. **Set up monitoring** (Prometheus/Grafana)
3. **Add integration tests** to the pipeline
4. **Configure alerts** for deployment failures
5. **Set up dashboard repository** CD pipeline

## 🎉 Success Criteria

✅ Pipeline runs without errors  
✅ Pods are running and healthy  
✅ Health endpoint responds correctly  
✅ Notifications work (if configured)  
✅ Rollback works when needed  

Your Connectivity Layer CD pipeline is now ready! 🚀