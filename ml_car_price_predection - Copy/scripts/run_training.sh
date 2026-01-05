#!/bin/bash
# Run training script

set -e

echo "Starting training pipeline..."

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run training
python -m src.pipelines.training_pipeline \
    --model-type random_forest \
    --n-estimators "${N_ESTIMATORS:-100}" \
    --max-depth "${MAX_DEPTH:-None}" \
    --cv-folds "${CV_FOLDS:-5}"

echo "Training complete!"
