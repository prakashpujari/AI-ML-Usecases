# UAT Environment (User Acceptance Testing)

Docker configuration for user acceptance testing with production-like setup and real user testing scenarios.

## Services

- **MLflow** - Model tracking (readonly for users)
- **API** - FastAPI service (high availability)
- **UI** - Streamlit dashboard (user-friendly)
- **PostgreSQL** - Production-grade database
- **Nginx** - Reverse proxy and load balancer

## Usage

```bash
# Start all services
docker-compose -f docker-compose.uat.yml up --build -d

# Check service health
docker-compose -f docker-compose.uat.yml ps

# View application logs
docker-compose -f docker-compose.uat.yml logs -f api ui

# Stop services
docker-compose -f docker-compose.uat.yml down
```

## Configuration

- Production-like environment
- User authentication enabled
- Rate limiting configured
- SSL/TLS ready
- Backup and monitoring
