"""
Helper utilities for ML pipeline
"""
import joblib
from pathlib import Path
from typing import Any, Dict
import json


def save_pickle(obj: Any, filepath: Path):
    """Save object to pickle file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(obj, filepath)


def load_pickle(filepath: Path) -> Any:
    """Load object from pickle file"""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    return joblib.load(filepath)


def save_json(data: Dict, filepath: Path):
    """Save dictionary to JSON file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def load_json(filepath: Path) -> Dict:
    """Load dictionary from JSON file"""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)
