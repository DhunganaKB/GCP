# GitHub Secrets Setup

This repository uses the **same GCP infrastructure** as the [Google_ADK_Youtube](https://github.com/DhunganaKB/Google_ADK_Youtube) project. No new GCP resources need to be created.

## Required GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**, then add these secrets:

### 1. GCP_PROJECT_ID
Your Google Cloud Project ID (same as youtube-analyst project)

**Example:** `my-project-123456`

### 2. GCP_REGION
The Cloud Run deployment region (same as youtube-analyst)

**Example:** `us-central1`

### 3. GCP_SA_KEY
The service account JSON key for GitHub Actions deployment

**To get this key:**

```bash
# If you don't have it already, create/download the key:
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-deploy@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Then copy the entire contents of the file
cat github-actions-key.json
```

Paste the **entire JSON content** into the GitHub secret.

---

## Shared Resources Being Used

The workflow deploys to your existing infrastructure:

| Resource | Name | Purpose |
|----------|------|---------|
| **Artifact Registry** | `youtube-analyst` | Stores Docker images |
| **Service Account** | `youtube-analyst-sa` | Cloud Run runtime identity |
| **Secret Manager** | `GOOGLE_API_KEY` | API credentials |
| **Service Name** | `support-triage` | This app's Cloud Run service |

## Deployment

Once secrets are configured:

1. **Automatic:** Push to `main` branch → workflow runs automatically
2. **Manual:** Go to Actions tab → "Build and Deploy to Cloud Run" → "Run workflow"

## Verify Setup

After your first deployment, check that it worked:

```bash
# Get the service URL
gcloud run services describe support-triage \
  --region=us-central1 \
  --format="value(status.url)"

# Test the endpoint
curl https://YOUR_SERVICE_URL/
```

## Need to Create Resources?

If the shared infrastructure doesn't exist yet, you'll need to:

1. Run the Terraform from the [Google_ADK_Youtube repo](https://github.com/DhunganaKB/Google_ADK_Youtube/tree/main/terraform)
2. Or create resources manually following the [original DEPLOYMENT.md](.github/DEPLOYMENT.md)

## Service Account Permissions

The `youtube-analyst-sa` service account already has these permissions:
- Firestore read/write
- Secret Manager accessor
- Vertex AI user
- Cloud Logging writer
- Artifact Registry reader

No additional permissions needed for this deployment.
