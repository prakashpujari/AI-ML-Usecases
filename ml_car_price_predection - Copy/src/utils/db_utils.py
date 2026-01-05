"""
Database utilities for storing model evaluation results
Moved from scripts/db_utils.py
"""
import psycopg2
from psycopg2.extras import Json, execute_values
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional
import os

from .logger import setup_logger

logger = setup_logger(__name__)


class ModelEvaluationDB:
    """Database manager for ML model evaluation results"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@localhost:5433/ml_evaluation'
        )
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(self.connection_string)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def initialize_schema(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Model runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_runs (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(255) UNIQUE NOT NULL,
                    model_name VARCHAR(255) NOT NULL,
                    model_version VARCHAR(50),
                    model_stage VARCHAR(50),
                    trained_at TIMESTAMP NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_run_id ON model_runs(run_id);
                CREATE INDEX IF NOT EXISTS idx_model_name ON model_runs(model_name);
            """)
            
            # Model metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_metrics (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(255) REFERENCES model_runs(run_id),
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value FLOAT NOT NULL,
                    metric_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_metrics_run_id ON model_metrics(run_id);
            """)
            
            # Hyperparameters table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_hyperparameters (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(255) REFERENCES model_runs(run_id),
                    param_name VARCHAR(100) NOT NULL,
                    param_value VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Data quality table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(255) REFERENCES model_runs(run_id),
                    dataset_type VARCHAR(50),
                    total_rows INTEGER,
                    total_columns INTEGER,
                    missing_values JSONB,
                    duplicate_rows INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_alerts (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(255) REFERENCES model_runs(run_id),
                    alert_type VARCHAR(100) NOT NULL,
                    severity VARCHAR(20),
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Feature importance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feature_importance (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(255) REFERENCES model_runs(run_id),
                    feature_name VARCHAR(255) NOT NULL,
                    importance_score FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            logger.info("Database schema initialized successfully")
    
    def insert_model_run(self, run_id: str, model_name: str, trained_at: datetime,
                        model_version: str = None, model_stage: str = None,
                        metadata: Dict = None):
        """Insert or update model run information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO model_runs (run_id, model_name, model_version, model_stage, trained_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id) DO UPDATE SET
                    model_version = EXCLUDED.model_version,
                    model_stage = EXCLUDED.model_stage,
                    metadata = EXCLUDED.metadata
            """, (run_id, model_name, model_version, model_stage, trained_at, Json(metadata or {})))
    
    def insert_metrics(self, run_id: str, metrics: Dict[str, float], metric_type: str = 'train'):
        """Insert model metrics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            values = [(run_id, name, value, metric_type) for name, value in metrics.items()]
            execute_values(cursor, """
                INSERT INTO model_metrics (run_id, metric_name, metric_value, metric_type)
                VALUES %s
            """, values)
    
    def insert_hyperparameters(self, run_id: str, params: Dict[str, any]):
        """Insert model hyperparameters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            values = [(run_id, name, str(value)) for name, value in params.items()]
            execute_values(cursor, """
                INSERT INTO model_hyperparameters (run_id, param_name, param_value)
                VALUES %s
            """, values)
    
    def insert_data_quality(self, run_id: str, dataset_type: str, total_rows: int,
                           total_columns: int, missing_values: Dict, duplicate_rows: int):
        """Insert data quality metrics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO data_quality (run_id, dataset_type, total_rows, total_columns, missing_values, duplicate_rows)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (run_id, dataset_type, total_rows, total_columns, Json(missing_values), duplicate_rows))
    
    def insert_alert(self, run_id: str, alert_type: str, severity: str, message: str):
        """Insert model alert"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO model_alerts (run_id, alert_type, severity, message)
                VALUES (%s, %s, %s, %s)
            """, (run_id, alert_type, severity, message))
    
    def insert_feature_importance(self, run_id: str, features: Dict[str, float]):
        """Insert feature importance scores"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            values = [(run_id, name, score) for name, score in features.items()]
            execute_values(cursor, """
                INSERT INTO feature_importance (run_id, feature_name, importance_score)
                VALUES %s
            """, values)


@contextmanager
def get_db_connection():
    """Convenience function to get database connection"""
    db = ModelEvaluationDB()
    db.initialize_schema()
    yield db
