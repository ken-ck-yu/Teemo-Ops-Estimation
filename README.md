# ML Training Resource Estimation API

AI-powered estimation of ML training resources, costs, and carbon emissions using Google Gemini. Runs on Google Cloud Run.

## Features

- Gemini AI for intelligent resource estimation
- Serverless deployment on Google Cloud Run
- Support for local files and Google Cloud Storage
- Estimates: GPU, CPU, RAM, training time, costs, and carbon emissionsing Resource Estimation API

AI-powered estimation of ML training resources, costs, and carbon emissions using Google Gemini. Runs on Google Cloud Run.

## Features

- 🤖 Gemini AI for intelligent resource estimation
- ☁️ Serverless deployment on Google Cloud Run
- 📦 Support for local files and Google Cloud Storage
- � Estimates: GPU, CPU, RAM, training time, costs, and carbon emissions

---

## Quick Deploy

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Deploy to Cloud Run
```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# Deploy from GitHub (Cloud Run builds automatically)
gcloud run deploy ml-training-estimator \
  --source https://github.com/YOUR_USERNAME/YOUR_REPO@main \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY="your-gemini-api-key"
```

### 3. Test
```bash
SERVICE_URL=$(gcloud run services describe ml-training-estimator \
  --region us-central1 --format 'value(status.url)')

curl $SERVICE_URL/health
```

---

## API Usage

### Python Example
```python
import requests

url = "https://your-service.run.app/estimate"
response = requests.post(url, json={
    "params_content": "model_params = {'layers': 12, 'hidden_size': 768}",
    "output_path": "gs://my-bucket/result.json"
})
print(response.json())
```

### cURL Example
```bash
curl -X POST https://your-service.run.app/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "params_content": "model = GPT2(layers=12)",
    "output_path": "gs://bucket/output.json"
  }'
```

### Request Format
```json
{
  "params_content": "Your model configuration as string",
  "output_path": "gs://bucket/output.json or /local/path.json",
  "params_path": "gs://bucket/input.txt (optional, alternative to params_content)",
  "api_key": "optional-override-gemini-key",
  "debug": false
}
```

### Response
```json
{
  "status": "success",
  "message": "Estimation completed successfully",
  "output_path": "gs://bucket/output.json"
}
```

---

## API Endpoints

- `POST /estimate` - Run estimation
- `GET /health` - Health check
- `GET /` - API documentation

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
export GEMINI_API_KEY="your-key"

# Run locally
python main.py

# Test
curl http://localhost:8080/health
```

---

## Storage Options

The API supports reading input and writing output to:
- **Local files**: `/path/to/file.txt`
- **Google Cloud Storage**: `gs://bucket-name/path/to/file.json`

Example with GCS:
```python
response = requests.post(url, json={
    "params_path": "gs://my-bucket/input/model_config.txt",
    "output_path": "gs://my-bucket/output/estimation.json"
})
```

---

## Project Structure

```
├── main.py                 # Flask API (entry point)
├── gemini_estimation.py    # Core estimation logic
├── file_reader.py          # File reading (local/GCS)
├── file_writer.py          # File writing (local/GCS)
├── requirements.txt        # Dependencies
└── README.md              # This file
```

---

## Requirements

- Python 3.11+
- Google Gemini API key ([Get one here](https://ai.google.dev/))
- Google Cloud Project (for Cloud Run deployment)

---

## Cost

Cloud Run is serverless - you only pay for request processing time. Scales to zero when idle.

**Estimated cost: ~$0.001 per estimation**

---

## Update Your Deployment

```bash
# Make changes, commit, and push
git add .
git commit -m "Update"
git push origin main

# Redeploy (same command as initial deploy)
gcloud run deploy ml-training-estimator \
  --source https://github.com/YOUR_USERNAME/YOUR_REPO@main \
  --region us-central1
```

---

## Troubleshooting

### View logs
```bash
gcloud run services logs tail ml-training-estimator --region us-central1
```

### Test locally first
```bash
python main.py
curl http://localhost:8080/health
```

### Check service status
```bash
gcloud run services describe ml-training-estimator --region us-central1
```

---

## License

MIT

