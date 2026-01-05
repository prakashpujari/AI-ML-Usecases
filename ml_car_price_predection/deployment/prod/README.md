# Production Environment

Docker configuration for production deployment with high availability, security, and monitoring.

## Services

- **MLflow** - Model tracking (HA setup)
- **API** - FastAPI service (multi-instance with load balancing)
- **UI** - Streamlit dashboard (optimized)
- **PostgreSQL** - Production database with replication
- **Redis** - Caching with persistence
- **Nginx** - Load balancer with SSL
- **Prometheus** - Metrics collection
- **Grafana** - Monitoring dashboards

## Prerequisites

```bash
# Set production secrets
export PROD_DB_PASSWORD="<secure_password>"
export REDIS_PASSWORD="<secure_password>"
export JWT_SECRET="<secure_secret>"

# Generate SSL certificates
./scripts/generate_ssl_certs.sh
```

## Usage

```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up --build -d

# Scale API instances
docker-compose -f docker-compose.prod.yml up --scale api=3 -d

# View production logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Backup database
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U ml_user_prod ml_evaluation > backup.sql

# Stop production (graceful shutdown)
docker-compose -f docker-compose.prod.yml down --timeout 30
```

## Configuration

- SSL/TLS encryption
- Multi-instance deployment
- Automatic backups
- Health checks and auto-restart
- Resource limits enforced
- Security hardening applied
- Full monitoring stack

## Security Checklist

- [ ] Update all default passwords
- [ ] Configure SSL certificates
- [ ] Set up firewall rules
- [ ] Enable audit logging
- [ ] Configure backup strategy
- [ ] Set up monitoring alerts
- [ ] Review and apply security patches
