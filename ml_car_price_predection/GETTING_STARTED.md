# 🚀 Getting Started Guide

## For Complete Beginners

If you're new to this project, follow this step-by-step guide.

### Prerequisites Checklist

Before starting, make sure you have:

- ✅ **Windows 10/11 or Mac or Linux**
- ✅ **Docker installed** ([Download](https://www.docker.com/products/docker-desktop))
- ✅ **Git installed** ([Download](https://git-scm.com))
- ✅ **4GB RAM minimum** (8GB recommended)
- ✅ **2GB free disk space**

### Installation (First Time Only)

#### Step 1: Download the Project

```powershell
# Open PowerShell or Terminal

# Navigate to where you want the project
cd "C:\Users\YourName\Documents"

# Clone the repository
git clone <repository-url>
cd ml_car_price_predection
```

#### Step 2: Start Docker

1. Open **Docker Desktop** application
2. Wait for it to show "Docker is running"

#### Step 3: Start All Services

```powershell
# This command starts everything needed
docker-compose -f deployment/dev/docker-compose.dev.yml up -d

# Wait 2-3 minutes for startup
# You'll see lots of progress messages
```

**What you should see:**
```
✔ Network dev_ml-network  Created
✔ Container postgres-dev  Started
✔ Container mlflow-dev    Started
✔ Container car-api-dev   Started
✔ Container car-ui-dev    Started
```

### First-Time Access

Once services are running, open these in your browser:

1. **Streamlit Dashboard** (Main UI):
   - URL: http://localhost:8501
   - No login needed

2. **MLflow Tracking** (Experiment metrics):
   - URL: http://localhost:5000
   - No login needed

3. **FastAPI Documentation** (API specs):
   - URL: http://localhost:8000/docs
   - No login needed

### Your First Prediction

1. Open http://localhost:8501 in your browser
2. You'll see the Car Price Prediction dashboard
3. Adjust the sliders:
   - Age: Move to 5 years
   - Mileage: Move to 75,000 km
   - Engine Size: Move to 2.0 L
   - Brand: Select "Toyota"
4. Click the **"🔮 Predict Price"** button
5. See the predicted price appear below!

**Expected Result:**
```
💰 Estimated Price: $18,500
Confidence: 85% (±$1,200)
```

### Stopping Services (When Done)

```powershell
# Stop all services
docker-compose -f deployment/dev/docker-compose.dev.yml down

# Fully remove (including data)
docker-compose -f deployment/dev/docker-compose.dev.yml down -v
```

---

## For Experienced Developers

### Docker Setup (Advanced)

```powershell
# Build from scratch
docker-compose -f deployment/dev/docker-compose.dev.yml build --no-cache

# Start with specific services only
docker-compose -f deployment/dev/docker-compose.dev.yml up -d postgres mlflow

# View live logs
docker-compose -f deployment/dev/docker-compose.dev.yml logs -f

# Check container health
docker-compose -f deployment/dev/docker-compose.dev.yml ps
```

### Python Virtual Environment Setup

```powershell
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\Activate.ps1

# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run services individually
python -m uvicorn predict_api:app --host 0.0.0.0 --port 8000
streamlit run streamlit_app.py
python train.py --n-samples 5000
```

### Airflow Orchestration

```powershell
# Install Astronomer CLI (if not already installed)
winget install Astronomer.astro

# Start Airflow
astro dev start

# Access at http://localhost:8080 (admin/admin)

# View logs
astro dev logs

# Stop Airflow
astro dev stop
```

---

## Troubleshooting Quick Fixes

### "Port already in use"

```powershell
# Find what's using port 8501
netstat -ano | findstr :8501

# Kill it (replace PID with actual number)
taskkill /PID 12345 /F

# Or use different port
streamlit run streamlit_app.py --server.port 8502
```

### "Cannot connect to Docker daemon"

1. Open Docker Desktop application
2. Wait for "Docker is running"
3. Try again

### "Streamlit can't connect to API"

```powershell
# Check if API is running
curl http://localhost:8000/health

# If not running, start it
python -m uvicorn predict_api:app --host 0.0.0.0 --port 8000
```

### "Database connection refused"

```powershell
# Restart PostgreSQL
docker-compose -f deployment/dev/docker-compose.dev.yml restart postgres-dev

# Wait 15 seconds
Start-Sleep -Seconds 15

# Check health
docker-compose -f deployment/dev/docker-compose.dev.yml ps
```

---

## Next Steps

1. **Explore the Dashboard**: Try different car features on Streamlit
2. **Check Metrics**: Visit MLflow to see model performance
3. **Train New Model**: Run `python train.py --n-samples 10000`
4. **Setup Airflow**: Follow Airflow guide in main README
5. **Customize**: Modify data and models for your use case

---

## Need Help?

1. Check the [main README.md](README.md) for detailed documentation
2. See [Troubleshooting section](README.md#troubleshooting) for common issues
3. Review [API Documentation](README.md#api-documentation) for API details
4. Check service logs: `docker-compose logs <service-name>`

---

**Congratulations! Your ML pipeline is running! 🎉**
