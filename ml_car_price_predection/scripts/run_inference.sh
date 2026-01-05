#!/bin/bash
# Run inference script

set -e

echo "Starting inference pipeline..."

# Check arguments
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <input_file> <output_file>"
    exit 1
fi

INPUT_FILE=$1
OUTPUT_FILE=$2

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run inference
python -m src.pipelines.inference_pipeline \
    --input "$INPUT_FILE" \
    --output "$OUTPUT_FILE" \
    --model-stage "${MODEL_STAGE:-production}"

echo "Inference complete! Results saved to $OUTPUT_FILE"
