# Environment-Specific Deployment Summary

All Docker-related files have been organized into environment-specific folders in the `deployment/` directory.

## 📁 Structure Overview

```
deployment/
├── README.md                    # Main deployment guide
├── dev/                         # Development environment
│   ├── docker-compose.dev.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.ui
│   ├── .env.dev
│   └── README.md
├── sit/                         # System Integration Testing
│   ├── docker-compose.sit.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.ui
│   ├── .env.sit
│   └── README.md
├── uat/                         # User Acceptance Testing
│   ├── docker-compose.uat.yml
│   ├── Dockerfile.api
│   ├── Dockerfile.ui
│   ├── nginx.conf
│   ├── .env.uat
│   └── README.md
└── prod/                        # Production
    ├── docker-compose.prod.yml
    ├── Dockerfile.api
    ├── Dockerfile.ui
    ├── nginx-prod.conf
    ├── prometheus.yml
    ├── postgres-prod.conf
    ├── .env.prod
    └── README.md
```

## 🚀 Quick Start Commands

### Using deployment scripts:

**Windows PowerShell:**
```powershell
# Development
.\deploy.ps1 -Env dev -Action up

# SIT
.\deploy.ps1 -Env sit -Action up

# UAT
.\deploy.ps1 -Env uat -Action up

# Production (requires secrets)
$env:PROD_DB_PASSWORD = "secure_password"
$env:REDIS_PASSWORD = "secure_password"
$env:JWT_SECRET = "secure_secret"
.\deploy.ps1 -Env prod -Action up

# Scale production API
.\deploy.ps1 -Env prod -Action scale -Replicas 5

# View logs
.\deploy.ps1 -Env dev -Action logs -Service api

# Backup database
.\deploy.ps1 -Env prod -Action backup
```

**Linux/Mac:**
```bash
# Development
./deploy.sh dev up

# SIT
./deploy.sh sit up

# UAT
./deploy.sh uat up

# Production
export PROD_DB_PASSWORD="secure_password"
export REDIS_PASSWORD="secure_password"
export JWT_SECRET="secure_secret"
./deploy.sh prod up

# Scale production API
./deploy.sh prod scale 5

# View logs
./deploy.sh dev logs api

# Backup database
./deploy.sh prod backup
```

### Manual docker-compose commands:

```bash
# Development
cd deployment/dev
docker-compose -f docker-compose.dev.yml up --build

# SIT
cd deployment/sit
docker-compose -f docker-compose.sit.yml up --build

# UAT
cd deployment/uat
docker-compose -f docker-compose.uat.yml up --build -d

# Production
cd deployment/prod
docker-compose -f docker-compose.prod.yml up --build -d
```

## 🔧 Environment Features

| Environment | Purpose | Key Features | Ports |
|-------------|---------|--------------|-------|
| **DEV** | Local development | Hot reload, debug mode, direct access | 5000, 8000, 8501, 5433 |
| **SIT** | Integration testing | Redis cache, health checks, test data | 5001, 8001, 8502, 5434, 6380 |
| **UAT** | Pre-production | Nginx proxy, rate limiting, security | 80, 5002, 8002, 8503, 5435, 6381 |
| **PROD** | Production | SSL, monitoring, HA, backups | 443, 5003, 8003-8005, 5436, 6382, 9090, 3000 |

## 📊 Database Configuration

Each environment uses a separate PostgreSQL instance:

```
DEV:  localhost:5433  → ml_evaluation (ml_user)
SIT:  localhost:5434  → ml_evaluation (ml_user_sit)
UAT:  localhost:5435  → ml_evaluation (ml_user_uat)
PROD: localhost:5436  → ml_evaluation (ml_user_prod)
```

## 🔒 Security Checklist (Production)

- [ ] Generate proper SSL certificates (not self-signed)
- [ ] Update all passwords in `.env.prod`
- [ ] Configure firewall rules (allow only 80/443)
- [ ] Set up database backups (automated)
- [ ] Configure Grafana alerts
- [ ] Enable audit logging
- [ ] Review Nginx security headers
- [ ] Test rate limiting
- [ ] Implement secrets management (Vault, AWS Secrets Manager)
- [ ] Set up log aggregation (ELK, Splunk)

## 📈 Production Monitoring

### Grafana (http://localhost:3000)
- API performance metrics
- Database connection pool
- Redis cache hit rate
- System resource usage

### Prometheus (http://localhost:9090)
- Collect metrics from all services
- Alert on anomalies
- Query historical data

### Available Metrics:
- `api_requests_total` - Total API requests
- `api_request_duration_seconds` - Request latency
- `api_errors_total` - Error count
- `db_connections_active` - Active DB connections
- `redis_cache_hits_total` - Cache performance

## 🛠️ Common Operations

### View service status:
```bash
.\deploy.ps1 -Env prod -Action status
```

### Tail logs:
```bash
.\deploy.ps1 -Env prod -Action logs -Service api
```

### Restart services:
```bash
.\deploy.ps1 -Env prod -Action restart
```

### Stop services:
```bash
.\deploy.ps1 -Env prod -Action down
```

### Database backup:
```bash
.\deploy.ps1 -Env prod -Action backup
```

### Database restore:
```bash
Get-Content backup_prod_20240115.sql | docker-compose -f deployment\prod\docker-compose.prod.yml exec -T postgres psql -U ml_user_prod ml_evaluation
```

## 🧪 Testing Workflow

1. **DEV**: Develop and debug locally
2. **SIT**: Run integration tests, validate caching
3. **UAT**: Performance testing, security validation
4. **PROD**: Deploy with monitoring

## 📝 Migration Notes

### Old → New File Locations:

| Old Location | New Location | Notes |
|--------------|--------------|-------|
| `docker-compose.yml` | `deployment/dev/docker-compose.dev.yml` | Development config |
| `Dockerfile.api` | `deployment/{env}/Dockerfile.api` | Environment-specific |
| `Dockerfile.ui` | `deployment/{env}/Dockerfile.ui` | Environment-specific |
| `Dockerfile.prod` | `deployment/prod/Dockerfile.api` | Production optimized |
| Root Docker files | `deployment/` folders | Organized by environment |

### What Stays in Root:
- `Dockerfile.train` - Used by Airflow DAG
- `train.py` - Training script
- `predict_api.py` - API source code
- `streamlit_app.py` - UI source code

## 🔍 Troubleshooting

### Port conflicts:
```powershell
# Check what's using a port
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <pid> /F
```

### Volume cleanup:
```bash
# Clean specific environment
docker-compose -f deployment\dev\docker-compose.dev.yml down -v

# Clean all volumes (WARNING: deletes data!)
docker volume prune -f
```

### Database connection test:
```bash
docker-compose -f deployment\dev\docker-compose.dev.yml exec postgres psql -U ml_user -d ml_evaluation -c "SELECT 1;"
```

### Network issues:
```bash
# Restart Docker daemon
Restart-Service Docker

# Recreate networks
docker network prune -f
```

## 📚 Additional Resources

- [Deployment Guide](deployment/README.md) - Comprehensive deployment documentation
- [Production Setup](PRODUCTION_SETUP.md) - Production architecture details
- [Database Integration](docs/DATABASE_INTEGRATION.md) - Database schema and queries

## ⚡ Performance Tips

1. **DEV**: Use volume mounts for hot reload
2. **SIT**: Enable Redis caching to test performance
3. **UAT**: Test with production-like data volumes
4. **PROD**: 
   - Scale API workers based on load
   - Configure PostgreSQL connection pooling
   - Enable Nginx caching for static assets
   - Monitor resource usage via Grafana

## 🎯 Next Steps

1. ✅ All environment configs created
2. Test each environment independently
3. Configure production secrets
4. Set up SSL certificates
5. Deploy to cloud (AWS ECS, Azure AKS, GCP GKE)
6. Configure CI/CD pipeline
7. Set up monitoring alerts
8. Implement automated backups

---

**Created**: January 2024  
**Last Updated**: January 2024  
**Maintainer**: ML Team
