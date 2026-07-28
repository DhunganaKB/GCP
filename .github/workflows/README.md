# GitHub Actions Workflows

This directory contains automated CI/CD workflows for the Support Triage application.

## Workflows

### 🔨 build.yml
**Reusable build workflow** - Can be called by other workflows

**Purpose:** Build and test the application

**Steps:**
1. Checkout code
2. Set up Python 3.12
3. Install dependencies from `requirements.txt`
4. Verify app imports correctly

**Usage:**
```yaml
jobs:
  test:
    uses: ./.github/workflows/build.yml
```

---

### 🚀 deploy.yml
**Build and Deploy to Cloud Run**

**Triggers:**
- Push to `main` branch (when `app/`, `Dockerfile`, or `requirements.txt` changes)
- Manual workflow dispatch

**What it does:**
1. **Test Job:** Calls the reusable build workflow to run tests
2. **Deploy Job (only if tests pass):**
   - Builds Docker image tagged with git SHA + `latest`
   - Pushes to Artifact Registry (`youtube-analyst` repository)
   - Deploys to Cloud Run as `support-triage` service
   - Prints the live service URL

**Configuration:**
- **Service Name:** `support-triage`
- **Memory:** 2Gi
- **CPU:** 2 cores
- **Instances:** 0-10 (autoscaling)
- **Timeout:** 300 seconds
- **Service Account:** `youtube-analyst-sa`
- **Public Access:** Enabled (unauthenticated)

**Required Secrets:**
- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GCP_SA_KEY`

See [SECRETS_SETUP.md](../SECRETS_SETUP.md) for configuration details.

---

## Shared Infrastructure

These workflows use the **same GCP resources** as the [Google_ADK_Youtube](https://github.com/DhunganaKB/Google_ADK_Youtube) project:

- ✅ Artifact Registry: `youtube-analyst`
- ✅ Service Account: `youtube-analyst-sa`
- ✅ Secret Manager: `GOOGLE_API_KEY`

Only the **Cloud Run service name** is different: `support-triage`

## Manual Deployment

To trigger a deployment manually:

1. Go to **Actions** tab
2. Select **Build and Deploy to Cloud Run**
3. Click **Run workflow**
4. Select `main` branch
5. Click **Run workflow**

## Monitoring Deployments

View workflow runs:
- GitHub: **Actions** tab in this repository
- Cloud Run: `gcloud run services describe support-triage --region=us-central1`

## Local Testing

Test before pushing:

```bash
# Build locally
docker build -t support-triage:local .

# Run locally
docker run -p 8080:8080 -e GOOGLE_API_KEY="your-key" support-triage:local

# Test
curl http://localhost:8080/
```
