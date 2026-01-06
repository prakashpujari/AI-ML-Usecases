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
        
        -- Model artifacts (serialized models stored in database)
        CREATE TABLE IF NOT EXISTS model_artifacts (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(255) NOT NULL,
            model_version VARCHAR(50) NOT NULL,
            model_type VARCHAR(100) NOT NULL,  -- e.g., RandomForest, XGBoost
            model_binary BYTEA NOT NULL,  -- serialized model (pickle/joblib)
            model_size_bytes INTEGER,
            accuracy_score FLOAT,
            rmse_score FLOAT,
            r2_score FLOAT,
            is_production BOOLEAN DEFAULT FALSE,
            deployment_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (run_id) REFERENCES model_runs(run_id) ON DELETE CASCADE,
            UNIQUE(run_id, model_version)
        );
        
        -- Model predictions history (for monitoring)
        CREATE TABLE IF NOT EXISTS model_predictions (
            id SERIAL PRIMARY KEY,
            model_version VARCHAR(50) NOT NULL,
            input_features JSONB NOT NULL,
            predicted_value FLOAT NOT NULL,
            actual_value FLOAT,
            confidence_score FLOAT,
            prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Model degradation analysis and rollback history
        CREATE TABLE IF NOT EXISTS model_degradation_analysis (
            id SERIAL PRIMARY KEY,
            degraded_model_version VARCHAR(50) NOT NULL,
            previous_stable_version VARCHAR(50) NOT NULL,
            degradation_type VARCHAR(100) NOT NULL,  -- R2_DEGRADATION, RMSE_INCREASE, etc.
            severity VARCHAR(20) NOT NULL,  -- LOW, MEDIUM, HIGH, CRITICAL
            r2_degraded FLOAT,
            r2_stable FLOAT,
            r2_change_percent FLOAT NOT NULL,
            rmse_degraded FLOAT,
            rmse_stable FLOAT,
            rmse_change_percent FLOAT NOT NULL,
            accuracy_degraded FLOAT,
            accuracy_stable FLOAT,
            accuracy_change_percent FLOAT,
            threshold_percent FLOAT NOT NULL,
            degradation_triggered BOOLEAN DEFAULT TRUE,
            rollback_executed BOOLEAN DEFAULT FALSE,
            rollback_timestamp TIMESTAMP,
            explanation TEXT NOT NULL,
            root_cause_hypothesis TEXT,
            recommended_action VARCHAR(255),
            detected_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_model_runs_trained_at ON model_runs(trained_at DESC);
        CREATE INDEX IF NOT EXISTS idx_model_runs_model_name ON model_runs(model_name);
        CREATE INDEX IF NOT EXISTS idx_model_metrics_run_id ON model_metrics(run_id);
        CREATE INDEX IF NOT EXISTS idx_model_alerts_severity ON model_alerts(severity, resolved);
        CREATE INDEX IF NOT EXISTS idx_feature_importance_run_id ON feature_importance(run_id);
        CREATE INDEX IF NOT EXISTS idx_model_artifacts_run_id ON model_artifacts(run_id);
        CREATE INDEX IF NOT EXISTS idx_model_artifacts_is_production ON model_artifacts(is_production);
        CREATE INDEX IF NOT EXISTS idx_model_predictions_model_version ON model_predictions(model_version);
        CREATE INDEX IF NOT EXISTS idx_degradation_analysis_degraded_model ON model_degradation_analysis(degraded_model_version);
        CREATE INDEX IF NOT EXISTS idx_degradation_analysis_severity ON model_degradation_analysis(severity);
        CREATE INDEX IF NOT EXISTS idx_degradation_analysis_detected_at ON model_degradation_analysis(detected_at DESC);
        CREATE INDEX IF NOT EXISTS idx_degradation_analysis_rollback_executed ON model_degradation_analysis(rollback_executed);
        
        -- Model retraining events
        CREATE TABLE IF NOT EXISTS model_retraining_events (
            id SERIAL PRIMARY KEY,
            trigger_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            drift_type VARCHAR(50),
            trigger_reason TEXT,
            trigger_metrics JSONB,
            execution_attempted BOOLEAN DEFAULT FALSE,
            execution_successful BOOLEAN DEFAULT FALSE,
            execution_metrics JSONB,
            retraining_model_version VARCHAR(50),
            retraining_r2 FLOAT,
            retraining_rmse FLOAT,
            retraining_accuracy FLOAT,
            comparison_previous_r2 FLOAT,
            comparison_previous_rmse FLOAT,
            comparison_previous_accuracy FLOAT,
            improvement_r2_percent FLOAT,
            improvement_rmse_percent FLOAT,
            improvement_accuracy_percent FLOAT,
            triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            execution_completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Retraining indexes
        CREATE INDEX IF NOT EXISTS idx_retraining_severity ON model_retraining_events(severity);
        CREATE INDEX IF NOT EXISTS idx_retraining_trigger_type ON model_retraining_events(trigger_type);
        CREATE INDEX IF NOT EXISTS idx_retraining_triggered_at ON model_retraining_events(triggered_at DESC);
        CREATE INDEX IF NOT EXISTS idx_retraining_execution_successful ON model_retraining_events(execution_successful);
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
    
    def store_model(
        self,
        run_id: str,
        model_version: str,
        model_type: str,
        model_binary: bytes,
        accuracy: Optional[float] = None,
        rmse: Optional[float] = None,
        r2: Optional[float] = None,
        is_production: bool = False
    ) -> int:
        """
        Store serialized model in database
        
        Args:
            run_id: MLflow run ID
            model_version: Version string (e.g., "1.0.0")
            model_type: Type of model (e.g., "RandomForest")
            model_binary: Serialized model bytes (from joblib.dump)
            accuracy: Accuracy score
            rmse: RMSE score
            r2: R² score
            is_production: Whether this is production model
            
        Returns:
            Database ID of inserted model artifact
        """
        sql = """
        INSERT INTO model_artifacts (
            run_id, model_version, model_type, model_binary, 
            model_size_bytes, accuracy_score, rmse_score, r2_score, is_production
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_id, model_version) 
        DO UPDATE SET
            model_binary = EXCLUDED.model_binary,
            model_size_bytes = EXCLUDED.model_size_bytes,
            accuracy_score = EXCLUDED.accuracy_score,
            rmse_score = EXCLUDED.rmse_score,
            r2_score = EXCLUDED.r2_score,
            is_production = EXCLUDED.is_production,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id
        """
        
        try:
            model_size = len(model_binary)
            with self.conn.cursor() as cur:
                cur.execute(sql, (
                    run_id, model_version, model_type, model_binary,
                    model_size, accuracy, rmse, r2, is_production
                ))
                result = cur.fetchone()
                self.conn.commit()
                logging.info(f"Stored model {model_version} for run {run_id} (size: {model_size} bytes)")
                return result[0]
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to store model: {e}")
            raise
    
    def get_model(self, model_version: str) -> Optional[bytes]:
        """
        Retrieve serialized model from database
        
        Args:
            model_version: Version string to retrieve
            
        Returns:
            Model binary data or None if not found
        """
        sql = "SELECT model_binary FROM model_artifacts WHERE model_version = %s LIMIT 1"
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (model_version,))
                result = cur.fetchone()
                if result:
                    logging.info(f"Retrieved model {model_version} from database")
                    return result[0]
                else:
                    logging.warning(f"Model {model_version} not found in database")
                    return None
        except Exception as e:
            logging.error(f"Failed to retrieve model: {e}")
            raise
    
    def get_production_model(self) -> Optional[bytes]:
        """
        Retrieve the current production model from database
        
        Returns:
            Model binary data or None if no production model exists
        """
        sql = """
        SELECT model_binary FROM model_artifacts 
        WHERE is_production = TRUE 
        ORDER BY updated_at DESC 
        LIMIT 1
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql)
                result = cur.fetchone()
                if result:
                    logging.info("Retrieved production model from database")
                    return result[0]
                else:
                    logging.warning("No production model found in database")
                    return None
        except Exception as e:
            logging.error(f"Failed to retrieve production model: {e}")
            raise
    
    def set_production_model(self, model_version: str) -> bool:
        """
        Mark a model version as production model
        
        Args:
            model_version: Version to promote to production
            
        Returns:
            True if successful, False otherwise
        """
        sql_unset = "UPDATE model_artifacts SET is_production = FALSE WHERE is_production = TRUE"
        sql_set = "UPDATE model_artifacts SET is_production = TRUE, deployment_date = CURRENT_TIMESTAMP WHERE model_version = %s"
        
        try:
            with self.conn.cursor() as cur:
                # Unset current production model
                cur.execute(sql_unset)
                # Set new production model
                cur.execute(sql_set, (model_version,))
                self.conn.commit()
                logging.info(f"Model {model_version} promoted to production")
                return True
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to promote model to production: {e}")
            raise
    
    def list_models(self, limit: int = 10) -> List[Dict]:
        """
        List available models in database
        
        Args:
            limit: Maximum number of models to return
            
        Returns:
            List of model metadata dictionaries
        """
        sql = """
        SELECT id, run_id, model_version, model_type, model_size_bytes,
               accuracy_score, rmse_score, r2_score, is_production, 
               created_at, updated_at
        FROM model_artifacts 
        ORDER BY updated_at DESC 
        LIMIT %s
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (limit,))
                results = cur.fetchall()
                logging.info(f"Retrieved {len(results)} models from database")
                return [dict(row) for row in results]
        except Exception as e:
            logging.error(f"Failed to list models: {e}")
            raise
    
    def store_prediction(
        self,
        model_version: str,
        input_features: Dict,
        predicted_value: float,
        actual_value: Optional[float] = None,
        confidence_score: Optional[float] = None
    ) -> int:
        """
        Store prediction in database for monitoring
        
        Args:
            model_version: Model version used for prediction
            input_features: Dictionary of input features
            predicted_value: The predicted value
            actual_value: Actual value (if available for validation)
            confidence_score: Confidence score of prediction
            
        Returns:
            Database ID of inserted prediction
        """
        sql = """
        INSERT INTO model_predictions 
        (model_version, input_features, predicted_value, actual_value, confidence_score)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (
                    model_version,
                    json.dumps(input_features),
                    predicted_value,
                    actual_value,
                    confidence_score
                ))
                result = cur.fetchone()
                self.conn.commit()
                logging.info(f"Stored prediction for model {model_version}")
                return result[0]
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to store prediction: {e}")
            raise
    
    def compare_models(self, version1: str, version2: str) -> Dict:
        """
        Compare performance metrics between two model versions
        
        Args:
            version1: First model version
            version2: Second model version
            
        Returns:
            Dictionary with comparison results
        """
        sql = """
        SELECT 
            model_version,
            accuracy_score,
            rmse_score,
            r2_score,
            created_at
        FROM model_artifacts
        WHERE model_version IN (%s, %s)
        ORDER BY created_at DESC
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (version1, version2))
                results = cur.fetchall()
                
                if len(results) != 2:
                    logging.warning(f"Could not find both models: {version1}, {version2}")
                    return {}
                
                v1 = results[1]  # Older version
                v2 = results[0]  # Newer version
                
                comparison = {
                    'current_version': v2['model_version'],
                    'previous_version': v1['model_version'],
                    'r2_current': v2['r2_score'],
                    'r2_previous': v1['r2_score'],
                    'r2_change': (v2['r2_score'] or 0) - (v1['r2_score'] or 0),
                    'rmse_current': v2['rmse_score'],
                    'rmse_previous': v1['rmse_score'],
                    'rmse_change': (v2['rmse_score'] or 0) - (v1['rmse_score'] or 0),
                    'accuracy_current': v2['accuracy_score'],
                    'accuracy_previous': v1['accuracy_score'],
                    'accuracy_change': (v2['accuracy_score'] or 0) - (v1['accuracy_score'] or 0),
                    'degraded': (v2['r2_score'] or 0) < (v1['r2_score'] or 0),
                }
                
                logging.info(f"Model comparison: {comparison}")
                return comparison
        except Exception as e:
            logging.error(f"Failed to compare models: {e}")
            return {}
    
    def check_performance_degradation(
        self,
        threshold_percent: float = 5.0
    ) -> Dict:
        """
        Check if current production model has degraded compared to previous version
        
        Args:
            threshold_percent: Degradation threshold in percentage (default 5%)
            
        Returns:
            Dictionary with degradation check results
        """
        sql = """
        SELECT 
            model_version,
            r2_score,
            rmse_score,
            accuracy_score,
            is_production,
            created_at
        FROM model_artifacts
        ORDER BY created_at DESC
        LIMIT 2
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)
                models = cur.fetchall()
                
                if len(models) < 2:
                    logging.info("Not enough model versions to check degradation")
                    return {'degraded': False, 'reason': 'Only one model version exists'}
                
                current = models[0]  # Most recent
                previous = models[1]  # Previous
                
                # Calculate percentage change in R² score
                if previous['r2_score'] and current['r2_score']:
                    r2_change_percent = (
                        (current['r2_score'] - previous['r2_score']) / 
                        abs(previous['r2_score']) * 100
                    )
                else:
                    r2_change_percent = 0
                
                # Calculate percentage change in RMSE
                if previous['rmse_score'] and current['rmse_score']:
                    rmse_change_percent = (
                        (current['rmse_score'] - previous['rmse_score']) / 
                        abs(previous['rmse_score']) * 100
                    )
                else:
                    rmse_change_percent = 0
                
                # Determine if degraded
                degraded = (
                    r2_change_percent < -threshold_percent or  # R² decreased
                    rmse_change_percent > threshold_percent     # RMSE increased
                )
                
                result = {
                    'degraded': degraded,
                    'current_version': current['model_version'],
                    'previous_version': previous['model_version'],
                    'r2_change_percent': round(r2_change_percent, 2),
                    'rmse_change_percent': round(rmse_change_percent, 2),
                    'threshold_percent': threshold_percent,
                    'current_r2': current['r2_score'],
                    'previous_r2': previous['r2_score'],
                    'current_rmse': current['rmse_score'],
                    'previous_rmse': previous['rmse_score'],
                }
                
                if degraded:
                    logging.warning(f"⚠️  Performance degradation detected: {result}")
                else:
                    logging.info(f"✓ No performance degradation detected")
                
                return result
        except Exception as e:
            logging.error(f"Failed to check degradation: {e}")
            return {'degraded': False, 'error': str(e)}
    
    def rollback_production_model(self, target_version: Optional[str] = None) -> bool:
        """
        Rollback to a previous model version
        
        Args:
            target_version: Specific version to rollback to. 
                          If None, rolls back to the previous version.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if target_version:
                    # Rollback to specific version
                    sql_check = "SELECT id FROM model_artifacts WHERE model_version = %s"
                    cur.execute(sql_check, (target_version,))
                    if not cur.fetchone():
                        logging.error(f"Target version not found: {target_version}")
                        return False
                    
                    version_to_use = target_version
                else:
                    # Find previous version
                    sql_prev = """
                    SELECT model_version FROM model_artifacts
                    WHERE is_production = TRUE
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """
                    cur.execute(sql_prev)
                    current = cur.fetchone()
                    
                    if not current:
                        logging.error("No current production model found")
                        return False
                    
                    # Get the version before this one
                    sql_prev2 = """
                    SELECT model_version FROM model_artifacts
                    WHERE model_version != %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """
                    cur.execute(sql_prev2, (current['model_version'],))
                    prev = cur.fetchone()
                    
                    if not prev:
                        logging.error("No previous version to rollback to")
                        return False
                    
                    version_to_use = prev['model_version']
                
                # Unset current production
                sql_unset = "UPDATE model_artifacts SET is_production = FALSE WHERE is_production = TRUE"
                cur.execute(sql_unset)
                
                # Set target as production
                sql_set = """
                UPDATE model_artifacts 
                SET is_production = TRUE, deployment_date = CURRENT_TIMESTAMP 
                WHERE model_version = %s
                """
                cur.execute(sql_set, (version_to_use,))
                
                self.conn.commit()
                
                # Log the rollback
                self.insert_alert(
                    alert_type='MODEL_ROLLBACK',
                    severity='HIGH',
                    message=f'Model rolled back to version {version_to_use}'
                )
                
                logging.info(f"✓ Successfully rolled back to model v{version_to_use}")
                return True
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to rollback model: {e}")
            return False
    
    def get_model_history(self, limit: int = 10) -> List[Dict]:
        """
        Get model version history with metrics
        
        Args:
            limit: Maximum number of versions to return
            
        Returns:
            List of model versions with their metrics
        """
        sql = """
        SELECT 
            id,
            model_version,
            model_type,
            r2_score,
            rmse_score,
            accuracy_score,
            is_production,
            created_at,
            updated_at,
            ROUND(model_size_bytes::numeric / 1024 / 1024, 2) as size_mb
        FROM model_artifacts
        ORDER BY created_at DESC
        LIMIT %s
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (limit,))
                return cur.fetchall()
        except Exception as e:
            logging.error(f"Failed to get model history: {e}")
            return []
    def store_degradation_analysis(
        self,
        degraded_model_version: str,
        previous_stable_version: str,
        degradation_type: str,
        severity: str,
        r2_degraded: Optional[float],
        r2_stable: Optional[float],
        r2_change_percent: float,
        rmse_degraded: Optional[float],
        rmse_stable: Optional[float],
        rmse_change_percent: float,
        accuracy_degraded: Optional[float] = None,
        accuracy_stable: Optional[float] = None,
        accuracy_change_percent: Optional[float] = None,
        threshold_percent: float = 5.0,
        rollback_executed: bool = False,
        explanation: str = "",
        root_cause_hypothesis: Optional[str] = None,
        recommended_action: Optional[str] = None
    ) -> int:
        """
        Store detailed model degradation analysis
        
        Args:
            degraded_model_version: Version with degraded performance
            previous_stable_version: Previous stable version
            degradation_type: Type of degradation (R2_DEGRADATION, RMSE_INCREASE, etc.)
            severity: LOW, MEDIUM, HIGH, CRITICAL
            r2_degraded: R² score of degraded model
            r2_stable: R² score of stable model
            r2_change_percent: Percentage change in R²
            rmse_degraded: RMSE of degraded model
            rmse_stable: RMSE of stable model
            rmse_change_percent: Percentage change in RMSE
            accuracy_degraded: Accuracy of degraded model (if applicable)
            accuracy_stable: Accuracy of stable model (if applicable)
            accuracy_change_percent: Percentage change in accuracy
            threshold_percent: Degradation threshold used
            rollback_executed: Whether rollback was executed
            explanation: Detailed explanation of degradation
            root_cause_hypothesis: Suspected root cause
            recommended_action: Recommended next action
            
        Returns:
            Database ID of inserted record
        """
        sql = """
        INSERT INTO model_degradation_analysis (
            degraded_model_version, previous_stable_version, degradation_type,
            severity, r2_degraded, r2_stable, r2_change_percent,
            rmse_degraded, rmse_stable, rmse_change_percent,
            accuracy_degraded, accuracy_stable, accuracy_change_percent,
            threshold_percent, degradation_triggered, rollback_executed,
            explanation, root_cause_hypothesis, recommended_action, detected_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        RETURNING id
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (
                    degraded_model_version, previous_stable_version, degradation_type,
                    severity, r2_degraded, r2_stable, r2_change_percent,
                    rmse_degraded, rmse_stable, rmse_change_percent,
                    accuracy_degraded, accuracy_stable, accuracy_change_percent,
                    threshold_percent, True, rollback_executed,
                    explanation, root_cause_hypothesis, recommended_action
                ))
                result = cur.fetchone()
                self.conn.commit()
                logging.info(f"Stored degradation analysis for v{degraded_model_version}")
                return result[0]
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to store degradation analysis: {e}")
            raise
    
    def get_degradation_history(
        self,
        limit: int = 20,
        severity: Optional[str] = None,
        rollback_executed: Optional[bool] = None
    ) -> List[Dict]:
        """
        Retrieve degradation analysis history
        
        Args:
            limit: Maximum number of records to return
            severity: Filter by severity (HIGH, MEDIUM, LOW, CRITICAL)
            rollback_executed: Filter by rollback status (True/False)
            
        Returns:
            List of degradation analysis records
        """
        sql = """
        SELECT 
            id, degraded_model_version, previous_stable_version,
            degradation_type, severity, r2_degraded, r2_stable, r2_change_percent,
            rmse_degraded, rmse_stable, rmse_change_percent,
            accuracy_degraded, accuracy_stable, accuracy_change_percent,
            threshold_percent, rollback_executed, rollback_timestamp,
            explanation, root_cause_hypothesis, recommended_action,
            detected_at, created_at
        FROM model_degradation_analysis
        WHERE 1=1
        """
        
        params = []
        
        if severity:
            sql += " AND severity = %s"
            params.append(severity)
        
        if rollback_executed is not None:
            sql += " AND rollback_executed = %s"
            params.append(rollback_executed)
        
        sql += " ORDER BY detected_at DESC LIMIT %s"
        params.append(limit)
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                return cur.fetchall()
        except Exception as e:
            logging.error(f"Failed to retrieve degradation history: {e}")
            return []
    
    def get_latest_degradation(self) -> Optional[Dict]:
        """
        Get the most recent degradation event
        
        Returns:
            Latest degradation record or None
        """
        sql = """
        SELECT 
            id, degraded_model_version, previous_stable_version,
            degradation_type, severity, r2_degraded, r2_stable, r2_change_percent,
            rmse_degraded, rmse_stable, rmse_change_percent,
            accuracy_degraded, accuracy_stable, accuracy_change_percent,
            threshold_percent, rollback_executed, explanation,
            root_cause_hypothesis, recommended_action, detected_at
        FROM model_degradation_analysis
        ORDER BY detected_at DESC
        LIMIT 1
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)
                result = cur.fetchone()
                if result:
                    logging.info("Retrieved latest degradation event")
                    return dict(result)
                return None
        except Exception as e:
            logging.error(f"Failed to retrieve latest degradation: {e}")
            return None
    
    def update_degradation_with_rollback(
        self,
        degradation_id: int,
        rollback_executed: bool = True
    ) -> bool:
        """
        Update degradation record after rollback execution
        
        Args:
            degradation_id: ID of degradation record
            rollback_executed: Whether rollback was executed
            
        Returns:
            True if successful, False otherwise
        """
        sql = """
        UPDATE model_degradation_analysis
        SET rollback_executed = %s,
            rollback_timestamp = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (rollback_executed, degradation_id))
                self.conn.commit()
                logging.info(f"Updated degradation record {degradation_id}")
                return True
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to update degradation record: {e}")
            return False
    
    def get_degradation_summary(self) -> Dict:
        """
        Get summary statistics of degradation events
        
        Returns:
            Dictionary with summary statistics
        """
        sql = """
        SELECT 
            COUNT(*) as total_events,
            SUM(CASE WHEN rollback_executed THEN 1 ELSE 0 END) as rollbacks_executed,
            SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high_count,
            SUM(CASE WHEN severity = 'MEDIUM' THEN 1 ELSE 0 END) as medium_count,
            SUM(CASE WHEN severity = 'LOW' THEN 1 ELSE 0 END) as low_count,
            AVG(r2_change_percent) as avg_r2_change,
            AVG(rmse_change_percent) as avg_rmse_change,
            MAX(detected_at) as latest_event
        FROM model_degradation_analysis
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)
                result = cur.fetchone()
                if result:
                    logging.info("Retrieved degradation summary statistics")
                    return dict(result)
                return {}
        except Exception as e:
            logging.error(f"Failed to retrieve degradation summary: {e}")
            return {}
    
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
