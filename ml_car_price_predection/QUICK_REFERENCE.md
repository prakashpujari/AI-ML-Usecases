# Quick Reference Card

## 🚀 Quick Commands

### Deployment

| Action | Windows (PowerShell) | Linux/Mac |
|--------|---------------------|-----------|
| Start DEV | `.\deploy.ps1 -Env dev -Action up` | `./deploy.sh dev up` |
| Start SIT | `.\deploy.ps1 -Env sit -Action up` | `./deploy.sh sit up` |
| Start UAT | `.\deploy.ps1 -Env uat -Action up` | `./deploy.sh uat up` |
| Start PROD | `.\deploy.ps1 -Env prod -Action up` | `./deploy.sh prod up` |
| Stop | `.\deploy.ps1 -Env dev -Action down` | `./deploy.sh dev down` |
| Logs | `.\deploy.ps1 -Env dev -Action logs -Service api` | `./deploy.sh dev logs api` |
| Status | `.\deploy.ps1 -Env dev -Action status` | `./deploy.sh dev status` |
| Backup DB | `.\deploy.ps1 -Env prod -Action backup` | `./deploy.sh prod backup` |

### Airflow

```bash
# Start Airflow
astro dev start

# Stop Airflow
astro dev stop

# Restart Airflow
astro dev restart

# View logs
astro dev logs

# Trigger DAG
astro dev run dags trigger train_model_dag
```

### Database Queries

```bash
# List all runs
python query_results.py runs

# Show metrics for specific run
python query_results.py metrics 1

# Show trend (last 5 runs)
python query_results.py trend 5

# Compare two runs
python query_results.py compare 1 2

# Show alerts
python query_results.py alerts

# Export to CSV
python query_results.py export output.csv
```

### Training

```bash
# Local training
python train.py --n-samples 5000 --experiment-name car_price_dev

# With custom parameters
python train.py --n-estimators 200 --max-depth 15 --cv-folds 5
```

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# API info
curl http://localhost:8000/info

# Make prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"year": 2020, "km": 50000, "fuel_type": "Petrol", "seller_type": "Dealer"}'
```

## 📝 Environment URLs

### DEV
- API: http://localhost:8000
- UI: http://localhost:8501
- MLflow: http://localhost:5000
- PostgreSQL: localhost:5433

### SIT
- API: http://localhost:8001
- UI: http://localhost:8502
- MLflow: http://localhost:5001
- PostgreSQL: localhost:5434
- Redis: localhost:6380

### UAT
- API: http://localhost/api
- UI: http://localhost/
- MLflow: http://localhost:5002
- PostgreSQL: localhost:5435
- Redis: localhost:6381

### PROD
- HTTPS: https://localhost/
- MLflow: http://localhost:5003
- PostgreSQL: localhost:5436
- Redis: localhost:6382
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## 🔧 Docker Commands

```bash
# View running containers
docker ps

# View all containers
docker ps -a

# View logs
docker logs <container_name>

# Execute command in container
docker exec -it <container_name> bash

# Clean up
docker system prune -a --volumes

# Inspect container
docker inspect <container_name>

# View container stats
docker stats
```

## 🗄️ Database Commands

```bash
# Connect to PostgreSQL
docker exec -it postgres-dev psql -U ml_user -d ml_evaluation

# Backup database
docker exec postgres-dev pg_dump -U ml_user ml_evaluation > backup.sql

# Restore database
cat backup.sql | docker exec -i postgres-dev psql -U ml_user ml_evaluation

# List tables
docker exec postgres-dev psql -U ml_user -d ml_evaluation -c "\dt"

# View table schema
docker exec postgres-dev psql -U ml_user -d ml_evaluation -c "\d model_runs"
```

## 🔍 Troubleshooting

### Port Already in Use
```powershell
# Windows: Find process using port
netstat -ano | findstr :8000

# Windows: Kill process
taskkill /PID <pid> /F

# Linux/Mac: Find and kill
lsof -ti:8000 | xargs kill -9
```

### Docker Issues
```bash
# Restart Docker
# Windows: Restart-Service Docker
# Linux: sudo systemctl restart docker

# Clean volumes
docker volume prune -f

# Clean networks
docker network prune -f

# Full cleanup (WARNING: removes all data!)
docker system prune -a --volumes -f
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# View PostgreSQL logs
docker logs postgres-dev

# Test connection
docker exec postgres-dev pg_isready -U ml_user
```

### MLflow Issues
```bash
# Check MLflow service
curl http://localhost:5000/health

# View MLflow logs
docker logs mlflow-dev

# Clear MLflow database
rm -rf mlruns/
rm -rf mlflow_db/
```

## 📊 Monitoring (PROD)

### Grafana Dashboards
- URL: http://localhost:3000
- Default user: admin
- Password: (set in .env.prod)

### Prometheus Queries
```promql
# API request rate
rate(api_requests_total[5m])

# API error rate
rate(api_errors_total[5m])

# API latency (95th percentile)
histogram_quantile(0.95, api_request_duration_seconds)

# Database connections
db_connections_active
```

## 🔐 Security Checklist

- [ ] Change default passwords in .env files
- [ ] Generate SSL certificates for PROD
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Set up automated backups
- [ ] Review Nginx security headers
- [ ] Rotate secrets regularly
- [ ] Monitor security alerts

## 📚 Documentation

- [Deployment Guide](deployment/README.md)
- [Deployment Summary](DEPLOYMENT_SUMMARY.md)
- [Production Setup](PRODUCTION_SETUP.md)
- [Database Integration](docs/DATABASE_INTEGRATION.md)
- [Airflow DAG](airflow/dags/train_dag.py)

## 🆘 Support

For issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review environment logs: `.\deploy.ps1 -Env dev -Action logs`
3. Verify service status: `.\deploy.ps1 -Env dev -Action status`
4. Check documentation in `docs/` folder
