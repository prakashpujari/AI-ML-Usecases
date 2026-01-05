# Environment Testing Guide

This guide helps you test each environment (DEV, SIT, UAT, PROD) to ensure proper functionality.

## Prerequisites

- Docker and Docker Compose installed
- PowerShell (Windows) or Bash (Linux/Mac)
- At least 8GB RAM available
- Ports available: 5000-5003, 8000-8005, 8501-8504, 5433-5436, 6380-6382

## 1. Development (DEV) Testing

### Start Environment
```powershell
.\deploy.ps1 -Env dev -Action up
```

### Test Services

#### 1.1 MLflow
```powershell
# Check MLflow UI
curl http://localhost:5000

# Verify it loads in browser
Start-Process http://localhost:5000
```

#### 1.2 PostgreSQL
```powershell
# Test connection
docker exec postgres-dev pg_isready -U ml_user

# Connect and verify tables
docker exec -it postgres-dev psql -U ml_user -d ml_evaluation -c "\dt"
```

#### 1.3 API
```powershell
# Health check
curl http://localhost:8000/health

# Info endpoint
curl http://localhost:8000/info

# Test prediction
curl -X POST http://localhost:8000/predict `
  -H "Content-Type: application/json" `
  -d '{
    "year": 2020,
    "km": 50000,
    "fuel_type": "Petrol",
    "seller_type": "Dealer",
    "transmission": "Manual"
  }'
```

#### 1.4 UI
```powershell
# Open Streamlit UI
Start-Process http://localhost:8501

# Test prediction manually in UI
# Enter values and click Predict
```

### Test Hot Reload (DEV Only)
```powershell
# Edit predict_api.py (add a comment)
# API should automatically reload
# Check logs: docker logs api-dev
```

### Expected Results
- ✅ All services start without errors
- ✅ API responds to health check
- ✅ Database connection successful
- ✅ Prediction returns valid price
- ✅ Streamlit UI loads and makes predictions
- ✅ Hot reload works for code changes

### Cleanup
```powershell
.\deploy.ps1 -Env dev -Action down
```

---

## 2. System Integration Testing (SIT)

### Start Environment
```powershell
.\deploy.ps1 -Env sit -Action up
```

### Test Services

#### 2.1 Redis Caching
```powershell
# Connect to Redis
docker exec -it redis-sit redis-cli -a sit_redis_password

# Test cache
SET test_key "test_value"
GET test_key
DEL test_key
EXIT
```

#### 2.2 API with Caching
```powershell
# First request (cache miss)
Measure-Command {
  curl -X POST http://localhost:8001/predict `
    -H "Content-Type: application/json" `
    -d '{"year": 2020, "km": 50000, "fuel_type": "Petrol", "seller_type": "Dealer", "transmission": "Manual"}'
}

# Second request (cache hit - should be faster)
Measure-Command {
  curl -X POST http://localhost:8001/predict `
    -H "Content-Type: application/json" `
    -d '{"year": 2020, "km": 50000, "fuel_type": "Petrol", "seller_type": "Dealer", "transmission": "Manual"}'
}
```

#### 2.3 Health Checks
```powershell
# API health
curl http://localhost:8001/health

# Database health
docker exec postgres-sit pg_isready -U ml_user_sit

# Redis health
docker exec redis-sit redis-cli -a sit_redis_password PING
```

#### 2.4 Integration Test
```powershell
# Run complete workflow
# 1. Train model
python train.py --n-samples 1000 --experiment-name sit_test

# 2. Query database
python query_results.py runs

# 3. Make prediction
curl -X POST http://localhost:8001/predict `
  -H "Content-Type: application/json" `
  -d '{"year": 2021, "km": 30000, "fuel_type": "Diesel", "seller_type": "Individual", "transmission": "Automatic"}'

# 4. Check cache hit in Redis
docker exec redis-sit redis-cli -a sit_redis_password KEYS "*"
```

### Expected Results
- ✅ Redis caching works (second request faster)
- ✅ Health checks pass for all services
- ✅ Integration workflow completes successfully
- ✅ 2 API workers running
- ✅ Resource monitoring available

### Cleanup
```powershell
.\deploy.ps1 -Env sit -Action down
```

---

## 3. User Acceptance Testing (UAT)

### Start Environment
```powershell
.\deploy.ps1 -Env uat -Action up
```

### Test Services

#### 3.1 Nginx Reverse Proxy
```powershell
# Access API through Nginx
curl http://localhost/api/health

# Access UI through Nginx
Start-Process http://localhost/

# Test rate limiting (should succeed)
for ($i=1; $i -le 10; $i++) {
  curl http://localhost/api/health
  Start-Sleep -Milliseconds 1000
}

# Test rate limiting (should fail after 60 requests/min)
for ($i=1; $i -le 70; $i++) {
  Write-Host "Request $i"
  curl http://localhost/api/health
  Start-Sleep -Milliseconds 500
}
```

#### 3.2 Production-like Configuration
```powershell
# Check 4 API workers
docker exec api-uat ps aux | grep uvicorn

# Verify resource limits
docker stats --no-stream api-uat

# Check security headers
curl -I http://localhost/api/health
```

#### 3.3 Performance Testing
```powershell
# Install Apache Bench (if not installed)
# choco install apache-httpd

# Load test API (100 requests, 10 concurrent)
ab -n 100 -c 10 -p test_data.json -T "application/json" http://localhost/api/predict
```

Create `test_data.json`:
```json
{"year": 2020, "km": 50000, "fuel_type": "Petrol", "seller_type": "Dealer", "transmission": "Manual"}
```

#### 3.4 Backup Test
```powershell
# Create backup
.\deploy.ps1 -Env uat -Action backup

# Verify backup file exists
Get-ChildItem backup_uat_*.sql
```

### Expected Results
- ✅ Nginx serves API and UI correctly
- ✅ Rate limiting kicks in after threshold
- ✅ Security headers present in responses
- ✅ 4 API workers running
- ✅ Resource limits enforced (2 CPU, 2GB RAM)
- ✅ Load test completes successfully
- ✅ Backup created successfully

### Cleanup
```powershell
.\deploy.ps1 -Env uat -Action down
```

---

## 4. Production (PROD) Testing

### Prerequisites
```powershell
# Set production secrets
$env:PROD_DB_PASSWORD = "secure_prod_password_123"
$env:REDIS_PASSWORD = "secure_redis_password_123"
$env:JWT_SECRET = "secure_jwt_secret_key_123"
$env:GRAFANA_PASSWORD = "secure_grafana_password_123"

# Generate SSL certificates
.\scripts\generate_ssl_certs.ps1
```

### Start Environment
```powershell
.\deploy.ps1 -Env prod -Action up
```

### Test Services

#### 4.1 SSL/HTTPS
```powershell
# Test HTTPS (accept self-signed cert)
curl -k https://localhost/

# Verify SSL certificate
openssl s_client -connect localhost:443 -showcerts
```

#### 4.2 Monitoring Stack

**Prometheus:**
```powershell
# Open Prometheus
Start-Process http://localhost:9090

# Test query
curl "http://localhost:9090/api/v1/query?query=up"
```

**Grafana:**
```powershell
# Open Grafana
Start-Process http://localhost:3000

# Login with admin / <GRAFANA_PASSWORD>
# Navigate to dashboards
```

#### 4.3 Multi-Instance API
```powershell
# Check 3 API replicas
docker ps | grep car-api-prod

# Scale to 5 instances
.\deploy.ps1 -Env prod -Action scale -Replicas 5

# Verify 5 instances running
docker ps | grep car-api-prod
```

#### 4.4 High Availability Test
```powershell
# Make requests and monitor load distribution
for ($i=1; $i -le 50; $i++) {
  curl -k https://localhost/api/health
  Start-Sleep -Milliseconds 100
}

# Kill one API instance
$container = docker ps | grep car-api-prod | Select-Object -First 1 | ForEach-Object { $_.Split()[0] }
docker stop $container

# Verify other instances still serve requests
curl -k https://localhost/api/health
```

#### 4.5 Database Backups
```powershell
# Create manual backup
.\deploy.ps1 -Env prod -Action backup

# Verify backup volume
docker volume ls | grep postgres-prod-backup

# List backup files
docker exec postgres-prod ls -lh /backups/
```

#### 4.6 Security Test
```powershell
# Check security headers
curl -k -I https://localhost/

# Expected headers:
# - X-Frame-Options: SAMEORIGIN
# - X-Content-Type-Options: nosniff
# - X-XSS-Protection: 1; mode=block
# - Strict-Transport-Security: max-age=31536000

# Test rate limiting
for ($i=1; $i -le 150; $i++) {
  Write-Host "Request $i"
  curl -k https://localhost/api/health
}
# Should hit rate limit around request 100-120
```

#### 4.7 Metrics Verification
```powershell
# Check API metrics endpoint (restrict access)
curl http://localhost:8003/metrics

# Expected metrics:
# - api_requests_total
# - api_request_duration_seconds
# - api_errors_total
```

### Expected Results
- ✅ HTTPS/SSL works (even with self-signed cert)
- ✅ Prometheus collects metrics
- ✅ Grafana dashboards load
- ✅ Multiple API instances running
- ✅ Load balanced across instances
- ✅ Automatic failover works
- ✅ Database backups created
- ✅ Security headers present
- ✅ Rate limiting enforced
- ✅ Monitoring metrics available

### Cleanup
```powershell
.\deploy.ps1 -Env prod -Action down

# Clean up secrets
Remove-Item Env:\PROD_DB_PASSWORD
Remove-Item Env:\REDIS_PASSWORD
Remove-Item Env:\JWT_SECRET
Remove-Item Env:\GRAFANA_PASSWORD
```

---

## 5. End-to-End Integration Test

Test complete ML pipeline across environments:

### Step 1: Train in DEV
```powershell
# Start DEV
.\deploy.ps1 -Env dev -Action up

# Train model
python train.py --n-samples 5000 --experiment-name e2e_test

# Verify model saved
python query_results.py runs
```

### Step 2: Test in SIT
```powershell
# Stop DEV, start SIT
.\deploy.ps1 -Env dev -Action down
.\deploy.ps1 -Env sit -Action up

# Copy model to SIT
# (In production, this would be via MLflow registry)

# Test API with caching
curl -X POST http://localhost:8001/predict `
  -H "Content-Type: application/json" `
  -d '{"year": 2020, "km": 50000, "fuel_type": "Petrol", "seller_type": "Dealer", "transmission": "Manual"}'
```

### Step 3: Validate in UAT
```powershell
# Stop SIT, start UAT
.\deploy.ps1 -Env sit -Action down
.\deploy.ps1 -Env uat -Action up

# Run load test
ab -n 1000 -c 50 -p test_data.json -T "application/json" http://localhost/api/predict

# Check metrics
python query_results.py trend 10
```

### Step 4: Deploy to PROD
```powershell
# Set production secrets
$env:PROD_DB_PASSWORD = "secure_password"
$env:REDIS_PASSWORD = "secure_password"
$env:JWT_SECRET = "secure_secret"

# Stop UAT, start PROD
.\deploy.ps1 -Env uat -Action down
.\deploy.ps1 -Env prod -Action up

# Monitor via Grafana
Start-Process http://localhost:3000

# Make production requests
for ($i=1; $i -le 100; $i++) {
  curl -k https://localhost/api/predict `
    -H "Content-Type: application/json" `
    -d '{"year": 2020, "km": 50000, "fuel_type": "Petrol", "seller_type": "Dealer", "transmission": "Manual"}'
}
```

---

## 6. Airflow Testing

### Start Airflow
```powershell
astro dev start
```

### Test DAG
```powershell
# Access Airflow UI
Start-Process http://localhost:8080

# Trigger DAG manually
astro dev run dags trigger train_model_dag

# Monitor execution
astro dev logs scheduler

# Check DAG run in database
python query_results.py runs
```

### Expected Results
- ✅ DAG appears in Airflow UI
- ✅ All 7 tasks execute successfully
- ✅ Model metrics stored in database
- ✅ MLflow experiment logged
- ✅ Model registered in MLflow

---

## 7. Troubleshooting Tests

### Port Conflict Test
```powershell
# Start DEV and SIT simultaneously (should work - different ports)
.\deploy.ps1 -Env dev -Action up
.\deploy.ps1 -Env sit -Action up

# Verify both running
curl http://localhost:8000/health  # DEV
curl http://localhost:8001/health  # SIT
```

### Database Recovery Test
```powershell
# Create data
python train.py --n-samples 1000

# Backup
.\deploy.ps1 -Env dev -Action backup

# Simulate data loss
.\deploy.ps1 -Env dev -Action down
docker volume rm ml_car_price_predection_postgres-dev-data

# Restore
.\deploy.ps1 -Env dev -Action up
Get-Content backup_dev_*.sql | docker exec -i postgres-dev psql -U ml_user ml_evaluation

# Verify data restored
python query_results.py runs
```

### Failover Test (PROD)
```powershell
# Start PROD with 3 API instances
.\deploy.ps1 -Env prod -Action up

# Kill 2 instances
docker ps | grep car-api-prod | Select-Object -First 2 | ForEach-Object {
  $container = $_.Split()[0]
  docker stop $container
}

# Verify remaining instance still works
for ($i=1; $i -le 10; $i++) {
  curl -k https://localhost/api/health
}
```

---

## 8. Performance Benchmarks

### DEV Environment
- Startup time: ~30 seconds
- API response time: <100ms
- Memory usage: ~1GB total

### SIT Environment
- Startup time: ~45 seconds
- API response time (cache miss): <150ms
- API response time (cache hit): <10ms
- Memory usage: ~2GB total

### UAT Environment
- Startup time: ~60 seconds
- API response time: <100ms (through Nginx)
- Concurrent requests: 100 req/s
- Memory usage: ~4GB total

### PROD Environment
- Startup time: ~90 seconds (includes Prometheus/Grafana)
- API response time: <80ms
- Concurrent requests: 500 req/s (with 3 replicas)
- Memory usage: ~8GB total

---

## Summary Checklist

### DEV
- [ ] All services start
- [ ] Hot reload works
- [ ] API predictions work
- [ ] UI loads and functions
- [ ] Database stores metrics

### SIT
- [ ] Redis caching works
- [ ] Cache hit faster than miss
- [ ] Health checks pass
- [ ] Integration test passes

### UAT
- [ ] Nginx reverse proxy works
- [ ] Rate limiting enforces limits
- [ ] Security headers present
- [ ] Load test passes
- [ ] Backup succeeds

### PROD
- [ ] SSL/HTTPS works
- [ ] Multiple API instances run
- [ ] Load balancing works
- [ ] Monitoring stack operational
- [ ] Failover works
- [ ] Automated backups configured
- [ ] Security hardened

---

## Next Steps

After successful testing:
1. Configure real SSL certificates (Let's Encrypt)
2. Set up CI/CD pipeline
3. Configure monitoring alerts
4. Implement automated backups
5. Set up log aggregation
6. Document runbooks
7. Train operations team
