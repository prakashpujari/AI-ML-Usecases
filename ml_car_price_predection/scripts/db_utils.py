"""
Database utilities for storing ML model evaluation results
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
import json

logging.basicConfig(level=logging.INFO)


class ModelEvaluationDB:
    """Manages model evaluation results in PostgreSQL"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            connection_string: PostgreSQL connection string
                             If None, uses environment variables
        """
        if connection_string:
            self.conn_string = connection_string
        else:
            # Try to detect if running in Docker container
            # If in Docker (Airflow), use host.docker.internal; otherwise use localhost
            in_docker = os.path.exists('/.dockerenv')
            db_host = 'host.docker.internal' if in_docker else 'localhost'
            
            self.conn_string = os.getenv(
                'DATABASE_URL',
                f'postgresql://postgres:postgres@{db_host}:5433/postgres'
            )
        
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.conn_string)
            logging.info("Connected to PostgreSQL database")
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            raise
    
    def _create_tables(self):
        """Create tables for storing evaluation results"""
        create_tables_sql = """
        -- Model training runs
        CREATE TABLE IF NOT EXISTS model_runs (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(255) UNIQUE NOT NULL,
            model_name VARCHAR(255) NOT NULL,
            model_version VARCHAR(50),
            model_stage VARCHAR(50),
            trained_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB
        );
        
        -- Model evaluation metrics
        CREATE TABLE IF NOT EXISTS model_metrics (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(255) NOT NULL,
            metric_name VARCHAR(100) NOT NULL,
            metric_value FLOAT NOT NULL,
            metric_type VARCHAR(50) NOT NULL,  -- train, test, cv
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES model_runs(run_id) ON DELETE CASCADE,
            UNIQUE(run_id, metric_name, metric_type)
        );
        
        -- Model hyperparameters
        CREATE TABLE IF NOT EXISTS model_hyperparameters (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(255) NOT NULL,
            param_name VARCHAR(100) NOT NULL,
            param_value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES model_runs(run_id) ON DELETE CASCADE,
            UNIQUE(run_id, param_name)
        );
        
        -- Data quality metrics
        CREATE TABLE IF NOT EXISTS data_quality (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(255) NOT NULL,
            dataset_type VARCHAR(50) NOT NULL,  -- train, test
            total_rows INTEGER NOT NULL,
            total_columns INTEGER NOT NULL,
            missing_values JSONB,
            duplicate_rows INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES model_runs(run_id) ON DELETE CASCADE
        );
        
        -- Model alerts and warnings
        CREATE TABLE IF NOT EXISTS model_alerts (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(255),
            alert_type VARCHAR(100) NOT NULL,
            severity VARCHAR(20) NOT NULL,  -- HIGH, MEDIUM, LOW
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (run_id) REFERENCES model_runs(run_id) ON DELETE SET NULL
        );
        
        -- Feature importance
        CREATE TABLE IF NOT EXISTS feature_importance (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(255) NOT NULL,
            feature_name VARCHAR(255) NOT NULL,
            importance_score FLOAT NOT NULL,
            rank INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES model_runs(run_id) ON DELETE CASCADE
        );
        
        -- Create indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_model_runs_trained_at ON model_runs(trained_at DESC);
        CREATE INDEX IF NOT EXISTS idx_model_runs_model_name ON model_runs(model_name);
        CREATE INDEX IF NOT EXISTS idx_model_metrics_run_id ON model_metrics(run_id);
        CREATE INDEX IF NOT EXISTS idx_model_alerts_severity ON model_alerts(severity, resolved);
        CREATE INDEX IF NOT EXISTS idx_feature_importance_run_id ON feature_importance(run_id);
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(create_tables_sql)
                self.conn.commit()
                logging.info("Database tables created/verified successfully")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to create tables: {e}")
            raise
    
    def insert_model_run(
        self,
        run_id: str,
        model_name: str,
        model_version: Optional[str] = None,
        model_stage: Optional[str] = None,
        trained_at: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Insert a new model training run
        
        Returns:
            Database ID of inserted row
        """
        if trained_at is None:
            trained_at = datetime.now()
        
        sql = """
        INSERT INTO model_runs (run_id, model_name, model_version, model_stage, trained_at, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_id) DO UPDATE 
        SET model_version = EXCLUDED.model_version,
            model_stage = EXCLUDED.model_stage,
            metadata = EXCLUDED.metadata
        RETURNING id
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (
                    run_id, model_name, model_version, model_stage, 
                    trained_at, json.dumps(metadata) if metadata else None
                ))
                result = cur.fetchone()
                self.conn.commit()
                logging.info(f"Inserted model run: {run_id}")
                return result[0]
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to insert model run: {e}")
            raise
    
    def insert_metrics(self, run_id: str, metrics: Dict[str, float], metric_type: str = 'test'):
        """
        Insert model metrics
        
        Args:
            run_id: MLflow run ID
            metrics: Dictionary of metric_name -> value
            metric_type: train, test, or cv
        """
        sql = """
        INSERT INTO model_metrics (run_id, metric_name, metric_value, metric_type)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (run_id, metric_name, metric_type) 
        DO UPDATE SET metric_value = EXCLUDED.metric_value
        """
        
        try:
            with self.conn.cursor() as cur:
                for name, value in metrics.items():
                    cur.execute(sql, (run_id, name, float(value), metric_type))
                self.conn.commit()
                logging.info(f"Inserted {len(metrics)} metrics for run {run_id}")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to insert metrics: {e}")
            raise
    
    def insert_hyperparameters(self, run_id: str, hyperparameters: Dict):
        """Insert model hyperparameters"""
        sql = """
        INSERT INTO model_hyperparameters (run_id, param_name, param_value)
        VALUES (%s, %s, %s)
        ON CONFLICT (run_id, param_name) 
        DO UPDATE SET param_value = EXCLUDED.param_value
        """
        
        try:
            with self.conn.cursor() as cur:
                for name, value in hyperparameters.items():
                    cur.execute(sql, (run_id, name, str(value)))
                self.conn.commit()
                logging.info(f"Inserted {len(hyperparameters)} hyperparameters for run {run_id}")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to insert hyperparameters: {e}")
            raise
    
    def insert_data_quality(
        self,
        run_id: str,
        dataset_type: str,
        total_rows: int,
        total_columns: int,
        missing_values: Dict,
        duplicate_rows: int
    ):
        """Insert data quality metrics"""
        sql = """
        INSERT INTO data_quality (run_id, dataset_type, total_rows, total_columns, missing_values, duplicate_rows)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (
                    run_id, dataset_type, total_rows, total_columns,
                    json.dumps(missing_values), duplicate_rows
                ))
                self.conn.commit()
                logging.info(f"Inserted data quality metrics for {dataset_type} dataset")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to insert data quality: {e}")
            raise
    
    def insert_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        run_id: Optional[str] = None
    ):
        """Insert a model alert"""
        sql = """
        INSERT INTO model_alerts (run_id, alert_type, severity, message)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (run_id, alert_type, severity, message))
                result = cur.fetchone()
                self.conn.commit()
                logging.info(f"Inserted alert: {alert_type} ({severity})")
                return result[0]
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to insert alert: {e}")
            raise
    
    def insert_feature_importance(self, run_id: str, feature_importance: List[Dict]):
        """
        Insert feature importance scores
        
        Args:
            run_id: MLflow run ID
            feature_importance: List of dicts with 'feature' and 'importance' keys
        """
        sql = """
        INSERT INTO feature_importance (run_id, feature_name, importance_score, rank)
        VALUES (%s, %s, %s, %s)
        """
        
        try:
            with self.conn.cursor() as cur:
                for idx, item in enumerate(feature_importance, 1):
                    cur.execute(sql, (
                        run_id,
                        item.get('feature', item.get('feature_name')),
                        float(item.get('importance', item.get('importance_score'))),
                        idx
                    ))
                self.conn.commit()
                logging.info(f"Inserted {len(feature_importance)} feature importance scores")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to insert feature importance: {e}")
            raise
    
    def get_latest_metrics(self, model_name: str, limit: int = 10) -> List[Dict]:
        """Get latest metrics for a model"""
        sql = """
        SELECT 
            mr.run_id,
            mr.model_version,
            mr.trained_at,
            mm.metric_name,
            mm.metric_value,
            mm.metric_type
        FROM model_runs mr
        JOIN model_metrics mm ON mr.run_id = mm.run_id
        WHERE mr.model_name = %s
        ORDER BY mr.trained_at DESC
        LIMIT %s
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (model_name, limit))
                return cur.fetchall()
        except Exception as e:
            logging.error(f"Failed to fetch metrics: {e}")
            return []
    
    def get_model_performance_trend(self, model_name: str, metric_name: str = 'test_r2') -> List[Dict]:
        """Get performance trend over time"""
        sql = """
        SELECT 
            mr.trained_at,
            mr.model_version,
            mm.metric_value
        FROM model_runs mr
        JOIN model_metrics mm ON mr.run_id = mm.run_id
        WHERE mr.model_name = %s 
        AND mm.metric_name = %s
        ORDER BY mr.trained_at ASC
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (model_name, metric_name))
                return cur.fetchall()
        except Exception as e:
            logging.error(f"Failed to fetch performance trend: {e}")
            return []
    
    def get_unresolved_alerts(self, severity: Optional[str] = None) -> List[Dict]:
        """Get unresolved alerts, optionally filtered by severity"""
        sql = """
        SELECT 
            id, run_id, alert_type, severity, message, created_at
        FROM model_alerts
        WHERE resolved = FALSE
        """
        params = []
        
        if severity:
            sql += " AND severity = %s"
            params.append(severity)
        
        sql += " ORDER BY created_at DESC"
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                return cur.fetchall()
        except Exception as e:
            logging.error(f"Failed to fetch alerts: {e}")
            return []
    
    def resolve_alert(self, alert_id: int):
        """Mark an alert as resolved"""
        sql = "UPDATE model_alerts SET resolved = TRUE WHERE id = %s"
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (alert_id,))
                self.conn.commit()
                logging.info(f"Resolved alert {alert_id}")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to resolve alert: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_db_connection() -> ModelEvaluationDB:
    """Factory function to get database connection"""
    return ModelEvaluationDB()


if __name__ == "__main__":
    # Test database setup
    with get_db_connection() as db:
        print("✓ Database connection successful")
        print("✓ Tables created/verified")
        
        # Test queries
        alerts = db.get_unresolved_alerts()
        print(f"✓ Found {len(alerts)} unresolved alerts")
