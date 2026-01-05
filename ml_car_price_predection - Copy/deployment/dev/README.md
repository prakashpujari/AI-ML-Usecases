# Development Environment

Docker configuration for local development with hot reload and debugging enabled.

## Services

- **MLflow** - Model tracking server (port 5000)
- **API** - FastAPI service with auto-reload (port 8000)
- **UI** - Streamlit dashboard (port 8501)
- **PostgreSQL** - Database for evaluation storage (port 5433)

## Usage

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up --build

# Start specific service
docker-compose -f docker-compose.dev.yml up mlflow api

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

## Configuration

- Hot reload enabled
- Debug mode on
- Volume mounts for live code changes
- Local data persistence
