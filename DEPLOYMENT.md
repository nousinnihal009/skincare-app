# 🚀 DermAI Deployment Guide

## Quick Start (Local Development)

### Backend API
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Dev Server
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

---

## 🐳 Docker Deployment

### Build & Run with Docker Compose
```bash
# From project root
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Access:**
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Individual Docker Builds
```bash
# Backend only
cd backend
docker build -t dermai-backend .
docker run -p 8000:8000 -v ./checkpoints:/app/checkpoints:ro dermai-backend

# Frontend only
cd frontend
docker build -t dermai-frontend .
docker run -p 80:80 dermai-frontend
```

---

## ☁️ AWS Deployment

### Option 1: EC2 Instance
```bash
# 1. Launch an EC2 instance (t3.medium minimum, GPU for fast inference)
# 2. SSH into the instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# 3. Install Docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# 4. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. Clone and deploy
git clone <your-repo-url> dermai
cd dermai
docker-compose up --build -d
```

### Option 2: AWS ECS (Fargate)
1. Push Docker images to Amazon ECR
2. Create ECS task definitions for frontend and backend
3. Create ECS service with Application Load Balancer
4. Configure security groups for ports 80 and 8000

### Option 3: AWS App Runner
```bash
# Push backend image to ECR, then:
aws apprunner create-service \
  --service-name dermai-backend \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "<account>.dkr.ecr.<region>.amazonaws.com/dermai-backend:latest",
      "ImageRepositoryType": "ECR"
    }
  }'
```

---

## ☁️ GCP Deployment

### Option 1: Google Cloud Run
```bash
# Backend
cd backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT/dermai-backend
gcloud run deploy dermai-backend \
  --image gcr.io/YOUR_PROJECT/dermai-backend \
  --port 8000 \
  --memory 2Gi \
  --allow-unauthenticated

# Frontend
cd frontend
gcloud builds submit --tag gcr.io/YOUR_PROJECT/dermai-frontend
gcloud run deploy dermai-frontend \
  --image gcr.io/YOUR_PROJECT/dermai-frontend \
  --port 80 \
  --allow-unauthenticated
```

### Option 2: GKE (Kubernetes)
```bash
# Create cluster
gcloud container clusters create dermai-cluster --num-nodes=2

# Apply k8s manifests
kubectl apply -f k8s/
```

---

## 🔒 Production Security Checklist

- [ ] Change `JWT_SECRET` to a strong random value
- [ ] Set up HTTPS with SSL certificates (Let's Encrypt)
- [ ] Configure CORS to only allow your domain
- [ ] Set up rate limiting (nginx or API gateway)
- [ ] Enable database backups
- [ ] Configure logging and monitoring
- [ ] Set up WAF (Web Application Firewall)
- [ ] Review and restrict API access
- [ ] Enable HIPAA-compliant data encryption at rest

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET` | Secret key for JWT token signing | `dermai-dev-secret-key-change-in-production` |
| `PYTHONUNBUFFERED` | Disable Python output buffering | `1` |

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│   ML Model   │
│  React/Vite  │     │   FastAPI    │     │  ResNet50    │
│   Port 80    │     │  Port 8000   │     │  PyTorch     │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────▼───────┐
                     │   SQLite DB  │
                     │  (Users/Auth)│
                     └──────────────┘
```
