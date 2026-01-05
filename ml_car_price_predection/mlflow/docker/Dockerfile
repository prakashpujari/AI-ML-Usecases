FROM python:3.11-slim

WORKDIR /mlflow

# Install MLflow
RUN pip install --no-cache-dir mlflow psycopg2-binary

# Expose port
EXPOSE 5000

# Create directories
RUN mkdir -p /mlflow/tracking/artifacts

# Default command
CMD ["mlflow", "server", \
     "--backend-store-uri", "sqlite:///mlflow/tracking/mlflow.db", \
     "--default-artifact-root", "/mlflow/tracking/artifacts", \
     "--host", "0.0.0.0", \
     "--port", "5000"]
