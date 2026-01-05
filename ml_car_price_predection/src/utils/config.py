"""
Configuration management for ML pipeline
"""
import os
from pathlib import Path
from typing import Dict, Any
import yaml

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Environment
ENV = os.getenv('ENV', 'development')

# Paths
DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = PROJECT_ROOT / 'models'
MLRUNS_DIR = PROJECT_ROOT / 'mlruns'
CONFIGS_DIR = PROJECT_ROOT / 'configs'

# MLflow
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
MLFLOW_EXPERIMENT_NAME = os.getenv('MLFLOW_EXPERIMENT_NAME', 'car_price_prediction')

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/ml_evaluation')

# Model
MODEL_NAME = 'car_price_predictor'
TARGET_COLUMN = 'price'


def load_config(config_name: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    config_path = CONFIGS_DIR / f'{config_name}.yaml'
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_model_path(stage: str = 'production') -> Path:
    """Get model path for specific stage"""
    return MODELS_DIR / stage / 'model.pkl'
