# SIT Environment (System Integration Testing)

Docker configuration for integration testing with realistic data volumes and external service connections.

## Services

- **MLflow** - Model tracking server
- **API** - FastAPI service (load balanced)
- **UI** - Streamlit dashboard
- **PostgreSQL** - Database with test data
- **Redis** - Caching layer

## Usage

```bash
# Start all services
docker-compose -f docker-compose.sit.yml up --build -d

# Run integration tests
docker-compose -f docker-compose.sit.yml exec api pytest tests/integration/

# View logs
docker-compose -f docker-compose.sit.yml logs -f api

# Stop services
docker-compose -f docker-compose.sit.yml down
```

## Configuration

- Test data pre-loaded
- External API mocking
- Performance monitoring enabled
- Automated testing on startup
