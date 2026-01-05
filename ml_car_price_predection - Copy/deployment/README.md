# ML Car Price Prediction - Deployment Guide

This folder contains environment-specific deployment configurations for the ML Car Price Prediction application.

## Environment Structure

```
deployment/
├── dev/     # Development environment
├── sit/     # System Integration Testing
├── uat/     # User Acceptance Testing
└── prod/    # Production environment
```

## Environment Comparison

| Feature | DEV | SIT | UAT | PROD |
|---------|-----|-----|-----|------|
| **Purpose** | Local development | Integration testing | Pre-production testing | Production |
| **MLflow Port** | 5000 | 5001 | 5002 | 5003 |
| **API Port** | 8000 | 8001 | 8002 | 8003-8005 |
| **UI Port** | 8501 | 8502 | 8503 | 8504 |
| **PostgreSQL Port** | 5433 | 5434 | 5435 | 5436 |
| **Hot Reload** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Redis** | ❌ No | ✅ Yes (6380) | ✅ Yes (6381) | ✅ Yes (6382) |
| **Nginx** | ❌ No | ❌ No | ✅ Yes | ✅ Yes (SSL) |
| **API Workers** | 1 | 2 | 4 | 4 |
| **Rate Limiting** | ❌ No | ✅ Basic | ✅ Advanced | ✅ Advanced |
| **Resource Limits** | ❌ No | ✅ Moderate | ✅ Production-like | ✅ High |
| **Monitoring** | ❌ No | ❌ No | ❌ No | ✅ Yes (Prometheus/Grafana) |
| **SSL/TLS** | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Backups** | ❌ No | ❌ No | ✅ Yes | ✅ Yes (automated) |
| **Health Checks** | ⚠️ Basic | ✅ Full | ✅ Full | ✅ Full |
| **Logging** | Console | Console | File | File (retained) |

## Quick Start

### Development (DEV)
```bash
cd deployment/dev
docker-compose -f docker-compose.dev.yml up --build

# Access services:
# - MLflow: http://localhost:5000
# - API: http://localhost:8000
# - UI: http://localhost:8501
```

### System Integration Testing (SIT)
```bash
cd deployment/sit
docker-compose -f docker-compose.sit.yml up --build

# Access services:
# - MLflow: http://localhost:5001
# - API: http://localhost:8001
# - UI: http://localhost:8502
# - Redis: localhost:6380
```

### User Acceptance Testing (UAT)
```bash
cd deployment/uat
docker-compose -f docker-compose.uat.yml up --build -d

# Access services:
# - API: http://localhost/api
# - UI: http://localhost/
# - MLflow: http://localhost:5002
```

### Production (PROD)
```bash
cd deployment/prod

# Set production secrets
export PROD_DB_PASSWORD="<secure_password>"
export REDIS_PASSWORD="<secure_password>"
export JWT_SECRET="<secure_secret>"

# Deploy
docker-compose -f docker-compose.prod.yml up --build -d

# Access services:
# - HTTPS: https://localhost/
# - Monitoring: http://localhost:3000 (Grafana)
# - Metrics: http://localhost:9090 (Prometheus)
```

## Environment Details

### DEV (Development)
- **Use Case**: Local development and debugging
- **Features**:
  - Hot code reload with volume mounts
  - Debug mode enabled
  - No security restrictions
  - Direct service access
  - Fast iteration cycle

### SIT (System Integration Testing)
- **Use Case**: Testing integration between components
- **Features**:
  - Redis caching enabled
  - Health checks active
  - Integration test support
  - Test data pre-loaded
  - Resource monitoring

### UAT (User Acceptance Testing)
- **Use Case**: Final validation before production
- **Features**:
  - Nginx reverse proxy
  - Rate limiting (60 req/min)
  - Production-like configuration
  - Security hardening
  - Performance testing ready

### PROD (Production)
- **Use Case**: Live production environment
- **Features**:
  - SSL/TLS encryption
  - Multi-instance deployment (3 API replicas)
  - Full monitoring stack (Prometheus + Grafana)
  - Automated backups
  - Advanced security
  - High availability configuration
  - Resource limits enforced
  - Comprehensive logging

## Database Configuration

Each environment uses a separate PostgreSQL database:

| Environment | Port | Database | User |
|-------------|------|----------|------|
| DEV | 5433 | ml_evaluation | ml_user |
| SIT | 5434 | ml_evaluation | ml_user_sit |
| UAT | 5435 | ml_evaluation | ml_user_uat |
| PROD | 5436 | ml_evaluation | ml_user_prod |

## Migration from Root Docker Files

Old Docker files in the root directory have been replaced with environment-specific configurations:

| Old File | New Location |
|----------|--------------|
| `docker-compose.yml` | `deployment/dev/docker-compose.dev.yml` |
| `Dockerfile.api` | `deployment/{env}/Dockerfile.api` |
| `Dockerfile.ui` | `deployment/{env}/Dockerfile.ui` |
| `Dockerfile.train` | Still in root (used by Airflow) |
| `Dockerfile.prod` | `deployment/prod/Dockerfile.api` |

## Common Operations

### View Logs
```bash
# All services
docker-compose -f deployment/{env}/docker-compose.{env}.yml logs -f

# Specific service
docker-compose -f deployment/{env}/docker-compose.{env}.yml logs -f api
```

### Scale API Instances
```bash
# Production only
docker-compose -f deployment/prod/docker-compose.prod.yml up --scale api=5 -d
```

### Database Backup
```bash
# Backup
docker-compose -f deployment/{env}/docker-compose.{env}.yml exec postgres \
  pg_dump -U ml_user_{env} ml_evaluation > backup_$(date +%Y%m%d).sql

# Restore
cat backup.sql | docker-compose -f deployment/{env}/docker-compose.{env}.yml exec -T postgres \
  psql -U ml_user_{env} ml_evaluation
```

### Health Check
```bash
# API health
curl http://localhost:8000/health

# Database connection
docker-compose -f deployment/{env}/docker-compose.{env}.yml exec postgres \
  pg_isready -U ml_user_{env}
```

## Troubleshooting

### Port Conflicts
If you encounter port conflicts, update the port mappings in the respective `docker-compose.{env}.yml` file.

### Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose -f deployment/{env}/docker-compose.{env}.yml logs postgres

# Verify connection
docker-compose -f deployment/{env}/docker-compose.{env}.yml exec postgres \
  psql -U ml_user_{env} -d ml_evaluation -c "SELECT 1;"
```

### Volume Cleanup
```bash
# Clean specific environment volumes
docker-compose -f deployment/{env}/docker-compose.{env}.yml down -v

# Clean all Docker volumes (WARNING: removes all data)
docker volume prune -f
```

## Security Best Practices

1. **Never commit `.env` files with real secrets**
2. **Use environment variables** for all sensitive data
3. **Rotate passwords regularly** (especially PROD)
4. **Update SSL certificates** before expiry
5. **Review Nginx security headers** periodically
6. **Enable audit logging** in production
7. **Implement proper backup strategy**
8. **Monitor security alerts**

## Monitoring (PROD Only)

### Grafana Dashboards
- URL: http://localhost:3000
- Default credentials: admin / (see `.env.prod`)

### Prometheus Metrics
- URL: http://localhost:9090
- Metrics available: API requests, response times, error rates

## Next Steps

1. Test each environment independently
2. Configure production secrets
3. Set up SSL certificates for PROD
4. Configure monitoring alerts
5. Set up automated backups
6. Review and apply security patches
7. Load test UAT and PROD environments

## Support

For issues or questions, refer to:
- [Production Setup Guide](../PRODUCTION_SETUP.md)
- [Database Integration Guide](../docs/DATABASE_INTEGRATION.md)
