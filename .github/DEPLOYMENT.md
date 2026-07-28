# Deployment Guide

This guide explains how to deploy the Support Triage application to Google Cloud Run using GitHub Actions.

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **GitHub repository** with this code
3. **gcloud CLI** installed locally (for initial setup)

## GCP Setup

### 1. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com
```

### 2. Create Artifact Registry Repository

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"

# Create the Docker repository
gcloud artifacts repositories create support-triage \
  --repository-format=docker \
  --location=$REGION \
  --project=$PROJECT_ID \
  --description="Support triage application images"
```

### 3. Create Service Account

```bash
# Create service account for Cloud Run
gcloud iam service-accounts create support-triage-sa \
  --display-name="Support Triage Service Account" \
  --project=$PROJECT_ID

# Grant necessary permissions to the service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:support-triage-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### 4. Create Deployment Service Account (for GitHub Actions)

```bash
# Create service account for GitHub Actions
gcloud iam service-accounts create github-actions-deploy \
  --display-name="GitHub Actions Deployment" \
  --project=$PROJECT_ID

# Grant permissions to deploy
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com

# Display the key (you'll copy this to GitHub Secrets)
cat github-actions-key.json
```

### 5. Create Secrets in Google Secret Manager

```bash
# Create secret for Google API Key
echo -n "your-google-api-key" | gcloud secrets create GOOGLE_API_KEY \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID

# Grant the Cloud Run service account access to the secret
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
  --member="serviceAccount:support-triage-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID
```

## GitHub Secrets Setup

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**, then add these secrets:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `GCP_PROJECT_ID` | Your GCP project ID | `my-project-123456` |
| `GCP_REGION` | Cloud Run deployment region | `us-central1` |
| `GCP_SA_KEY` | Service account JSON key | Contents of `github-actions-key.json` |

## Customization

### Change Service Name

If you want to use a different service name, update these files:

1. `.github/workflows/deploy.yml`:
   - Change `SERVICE_NAME` environment variable
   - Update the `IMAGE` path to match

2. Update the service account name in the deploy command

### Change Region

To deploy to a different region:

1. Update Artifact Registry location in GCP setup
2. Change `GCP_REGION` secret in GitHub
3. Update Docker registry URL in `deploy.yml` if not using `us-central1`

### Add More Environment Variables

Edit the `Deploy to Cloud Run` step in `deploy.yml` and add more `--set-env-vars` flags:

```yaml
--set-env-vars "MY_VAR=value" \
```

### Add More Secrets

1. Create the secret in Google Secret Manager
2. Grant access to the service account
3. Add `--set-secrets` flag in the deploy step:

```yaml
--set-secrets "MY_SECRET=MY_SECRET:latest" \
```

## Deployment

### Automatic Deployment

The workflow automatically deploys when you push changes to the `main` branch that affect:
- `app/**` files
- `Dockerfile`
- `requirements.txt`

### Manual Deployment

1. Go to **Actions** tab in your GitHub repository
2. Select **Build and Deploy to Cloud Run** workflow
3. Click **Run workflow** → **Run workflow**

## Monitoring

After deployment, monitor your service:

```bash
# View service details
gcloud run services describe support-triage \
  --region=$REGION \
  --project=$PROJECT_ID

# View logs
gcloud logs tail --service=support-triage \
  --project=$PROJECT_ID

# Get service URL
gcloud run services describe support-triage \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(status.url)"
```

## Troubleshooting

### Build Fails

- Check that all dependencies in `requirements.txt` are installable
- Verify Dockerfile syntax
- Check GitHub Actions logs for specific errors

### Deployment Fails

- Verify service account permissions
- Check that Artifact Registry repository exists
- Ensure secrets are properly created and accessible

### Application Errors

- Check Cloud Run logs: `gcloud logs tail --service=support-triage`
- Verify environment variables and secrets are set correctly
- Test the Docker image locally before deploying

## Local Testing

Test the Docker image locally before deploying:

```bash
# Build the image
docker build -t support-triage:local .

# Run locally
docker run -p 8080:8080 \
  -e GOOGLE_API_KEY="your-api-key" \
  support-triage:local

# Test the endpoint
curl http://localhost:8080/
```

## Clean Up

To delete all resources:

```bash
# Delete Cloud Run service
gcloud run services delete support-triage \
  --region=$REGION \
  --project=$PROJECT_ID

# Delete Artifact Registry repository
gcloud artifacts repositories delete support-triage \
  --location=$REGION \
  --project=$PROJECT_ID

# Delete service accounts
gcloud iam service-accounts delete support-triage-sa@$PROJECT_ID.iam.gserviceaccount.com
gcloud iam service-accounts delete github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com

# Delete secrets
gcloud secrets delete GOOGLE_API_KEY --project=$PROJECT_ID
```
