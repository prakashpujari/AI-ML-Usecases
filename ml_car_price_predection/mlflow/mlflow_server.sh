#!/bin/bash
# MLflow Server Startup Script

# Configuration
BACKEND_STORE_URI=${MLFLOW_BACKEND_STORE_URI:-"sqlite:///mlflow/tracking/mlflow.db"}
ARTIFACT_ROOT=${MLFLOW_ARTIFACT_ROOT:-"./mlflow/tracking/artifacts"}
HOST=${MLFLOW_HOST:-"0.0.0.0"}
PORT=${MLFLOW_PORT:-"5000"}

echo "Starting MLflow Server..."
echo "Backend Store: $BACKEND_STORE_URI"
echo "Artifact Root: $ARTIFACT_ROOT"
echo "Host: $HOST:$PORT"

# Create directories
mkdir -p mlflow/tracking/artifacts

# Start MLflow server
mlflow server \
    --backend-store-uri "$BACKEND_STORE_URI" \
    --default-artifact-root "$ARTIFACT_ROOT" \
    --host "$HOST" \
    --port "$PORT"
