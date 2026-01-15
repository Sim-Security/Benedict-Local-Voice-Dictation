# Deployment Guide

This document covers deploying Benedict Voice Dictation to Google Cloud Run.

## Architecture Overview

```
+------------------+     +------------------+     +------------------+
|   GitHub Repo    | --> |   Cloud Build    | --> |    Cloud Run     |
|  (push to main)  |     |  (build image)   |     | (Streamlit app)  |
+------------------+     +------------------+     +------------------+
                                                          |
                                                          v
                                              +------------------+
                                              |  External Ollama |
                                              |    (LLM API)     |
                                              +------------------+
```

**Important**: This deployment runs the **Streamlit web UI only**. The CLI voice dictation (`main.py`) requires local audio hardware and cannot run in Cloud Run.

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Required APIs enabled**:
   - Cloud Run API
   - Cloud Build API
   - Container Registry API

Enable APIs:
```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com
```

4. **External Ollama endpoint** (optional but recommended for text processing)
   - Self-hosted on Compute Engine
   - Or a compatible LLM API endpoint

## Deployment Options

### Option 1: GitHub Actions (Recommended)

Automated deployment on every push to `main`.

#### Setup

1. **Create a GCP Service Account**:
```bash
# Create service account
gcloud iam service-accounts create github-actions-deploy \
  --display-name="GitHub Actions Deploy"

# Grant required permissions
export PROJECT_ID=$(gcloud config get-value project)

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-deploy@$PROJECT_ID.iam.gserviceaccount.com
```

2. **Add GitHub Secrets** (Settings > Secrets and variables > Actions > Secrets):

| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `GCP_SA_KEY` | Contents of `github-actions-key.json` |
| `OLLAMA_BASE_URL` | (Optional) External Ollama endpoint URL |

3. **Add GitHub Variables** (Settings > Secrets and variables > Actions > Variables):

| Variable | Default | Description |
|----------|---------|-------------|
| `GCP_REGION` | `us-central1` | Cloud Run region |
| `SERVICE_NAME` | `benedict-voice` | Cloud Run service name |

4. **Push to main** to trigger deployment:
```bash
git push origin main
```

### Option 2: Cloud Build (GCP Console)

Use Cloud Build triggers for deployment.

#### Setup

1. **Connect repository** in Cloud Build (Console > Cloud Build > Triggers)

2. **Create trigger**:
   - Name: `benedict-deploy`
   - Event: Push to branch `^main$`
   - Configuration: Cloud Build config file (`cloudbuild.yaml`)
   - Substitution variables:
     - `_REGION`: `us-central1`
     - `_SERVICE_NAME`: `benedict-voice`
     - `_OLLAMA_BASE_URL`: Your Ollama endpoint

3. **Manual trigger**:
```bash
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=_REGION=us-central1,_SERVICE_NAME=benedict-voice,_OLLAMA_BASE_URL=https://your-ollama-endpoint
```

### Option 3: Manual Deployment

Direct deployment without CI/CD.

```bash
# Set variables
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1
export SERVICE_NAME=benedict-voice

# Build image
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
  --region $REGION \
  --platform managed \
  --port 8080 \
  --memory 1Gi \
  --allow-unauthenticated \
  --set-env-vars "OLLAMA_BASE_URL=https://your-ollama-endpoint"
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | No | `llama3.2` | LLM model to use |
| `SESSIONS_DIR` | No | `/app/sessions` | Session storage path |

## Cloud Run Configuration

The default configuration:

| Setting | Value | Notes |
|---------|-------|-------|
| Port | 8080 | Required by Cloud Run |
| Memory | 1 GiB | Sufficient for Streamlit |
| CPU | 1 | Single vCPU |
| Min instances | 0 | Scale to zero when idle |
| Max instances | 10 | Adjust based on traffic |
| Timeout | 300s | 5 minutes for LLM processing |
| Concurrency | 80 | Requests per instance |

## Ollama Setup for Cloud Run

Since Cloud Run is stateless, Ollama must run externally.

### Option A: Compute Engine (Recommended)

1. Create a GPU-enabled VM:
```bash
gcloud compute instances create ollama-server \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=100GB \
  --maintenance-policy=TERMINATE
```

2. Install Ollama and expose API:
```bash
# SSH into VM
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2

# Start Ollama with external access
OLLAMA_HOST=0.0.0.0 ollama serve
```

3. Set up firewall:
```bash
gcloud compute firewall-rules create allow-ollama \
  --allow tcp:11434 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=ollama-server
```

### Option B: Cloud Run Jobs

For batch processing without a persistent Ollama server.

### Option C: External LLM API

Use OpenAI, Anthropic, or other LLM APIs by modifying `src/text_processor.py`.

## Monitoring

### Cloud Run Console

View logs, metrics, and revisions at:
```
https://console.cloud.google.com/run/detail/{REGION}/{SERVICE_NAME}
```

### Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=benedict-voice" --limit 100
```

### Health Check

```bash
curl https://your-service-url/_stcore/health
```

## Troubleshooting

### Issue: Text processing not working

**Cause**: Ollama endpoint not reachable from Cloud Run.

**Solution**: Verify `OLLAMA_BASE_URL` is set and accessible:
```bash
curl -X POST https://your-ollama-endpoint/api/generate \
  -d '{"model": "llama3.2", "prompt": "Hello"}'
```

### Issue: Cold start latency

**Cause**: Scale-to-zero means first request initializes container.

**Solution**: Set `--min-instances=1` for always-warm instances (incurs cost).

### Issue: Session data lost on restart

**Cause**: Cloud Run is stateless; `/app/sessions` is ephemeral.

**Solution**: Mount Cloud Storage bucket or use Firestore for persistence.

## Cost Optimization

1. **Scale to zero**: Keep `--min-instances=0` for dev/staging
2. **Right-size memory**: Start with 1Gi, monitor and adjust
3. **Use committed use discounts**: For production workloads
4. **Regional deployment**: Deploy in regions with lower pricing

## Security Best Practices

1. **Remove `--allow-unauthenticated`** for private deployments
2. **Use Secret Manager** for sensitive environment variables
3. **Enable VPC connector** if Ollama is on private network
4. **Set up Cloud Armor** for DDoS protection

## Local Development

```bash
# Run locally with Docker
docker build -t benedict:local .
docker run -p 8080:8080 -e OLLAMA_BASE_URL=http://host.docker.internal:11434 benedict:local

# Or run directly
streamlit run app.py --server.port 8080
```
