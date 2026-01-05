"""
Model Monitoring and Performance Tracking
Monitors model performance, data drift, and system health
"""

import pandas as pd
import numpy as np
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import joblib
from dataclasses import dataclass, asdict
import mlflow
from mlflow.tracking import MlflowClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


@dataclass
class ModelPerformanceMetrics:
    """Model performance metrics snapshot"""
    timestamp: str
    model_version: str
    predictions_count: int
    mse: float
    mae: float
    r2_score: float
    mean_prediction: float
    std_prediction: float
    mean_actual: Optional[float] = None
    std_actual: Optional[float] = None


@dataclass
class DataDriftReport:
    """Data drift detection report"""
    timestamp: str
    features_checked: int
    drifted_features: List[str]
    drift_scores: Dict[str, float]
    has_drift: bool
    drift_threshold: float


@dataclass
class SystemHealthMetrics:
    """System health and performance metrics"""
    timestamp: str
    api_uptime_percent: float
    avg_response_time_ms: float
    error_rate_percent: float
    requests_per_hour: int
    memory_usage_mb: float
    cpu_usage_percent: float


class ModelMonitor:
    """Monitors ML model performance and system health"""
    
    def __init__(
        self,
        model_path: str,
        tracking_uri: str = 'http://localhost:5000',
        drift_threshold: float = 0.1
    ):
        self.model_path = model_path
        self.drift_threshold = drift_threshold
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient()
        self.alerts = []
        
        # Load model artifacts
        try:
            self.model_artifacts = joblib.load(model_path)
            logging.info(f"Loaded model from {model_path}")
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            self.model_artifacts = None
    
    def calculate_performance_metrics(
        self,
        predictions: np.ndarray,
        actuals: Optional[np.ndarray] = None,
        model_version: str = "unknown"
    ) -> ModelPerformanceMetrics:
        """
        Calculate current model performance metrics
        
        Args:
            predictions: Model predictions
            actuals: Actual values (optional)
            model_version: Model version identifier
            
        Returns:
            ModelPerformanceMetrics object
        """
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        metrics = ModelPerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            model_version=model_version,
            predictions_count=len(predictions),
            mse=0.0,
            mae=0.0,
            r2_score=0.0,
            mean_prediction=float(np.mean(predictions)),
            std_prediction=float(np.std(predictions))
        )
        
        if actuals is not None:
            metrics.mse = float(mean_squared_error(actuals, predictions))
            metrics.mae = float(mean_absolute_error(actuals, predictions))
            metrics.r2_score = float(r2_score(actuals, predictions))
            metrics.mean_actual = float(np.mean(actuals))
            metrics.std_actual = float(np.std(actuals))
            
            # Check for performance degradation
            if metrics.r2_score < 0.6:
                self.alerts.append({
                    'severity': 'HIGH',
                    'type': 'PERFORMANCE_DEGRADATION',
                    'message': f'R2 score dropped to {metrics.r2_score:.4f} (threshold: 0.6)',
                    'timestamp': metrics.timestamp
                })
        
        return metrics
    
    def detect_data_drift(
        self,
        reference_data: pd.DataFrame,
        current_data: pd.DataFrame,
        categorical_features: Optional[List[str]] = None
    ) -> DataDriftReport:
        """
        Detect data drift using statistical tests
        
        Args:
            reference_data: Training/reference dataset
            current_data: Current production data
            categorical_features: List of categorical feature names
            
        Returns:
            DataDriftReport object
        """
        from scipy.stats import ks_2samp, chi2_contingency
        
        drifted_features = []
        drift_scores = {}
        
        # Identify feature types
        if categorical_features is None:
            categorical_features = reference_data.select_dtypes(
                include=['object', 'category']
            ).columns.tolist()
        
        numeric_features = reference_data.select_dtypes(
            include=[np.number]
        ).columns.tolist()
        
        # Check numeric features using Kolmogorov-Smirnov test
        for feature in numeric_features:
            if feature in current_data.columns:
                ref_values = reference_data[feature].dropna()
                curr_values = current_data[feature].dropna()
                
                if len(ref_values) > 0 and len(curr_values) > 0:
                    statistic, p_value = ks_2samp(ref_values, curr_values)
                    drift_scores[feature] = float(statistic)
                    
                    if p_value < 0.05:  # Significant drift detected
                        drifted_features.append(feature)
                        logging.warning(f"Drift detected in {feature}: p-value={p_value:.4f}")
        
        # Check categorical features using chi-square test
        for feature in categorical_features:
            if feature in current_data.columns:
                try:
                    # Create contingency table
                    ref_counts = reference_data[feature].value_counts()
                    curr_counts = current_data[feature].value_counts()
                    
                    # Align categories
                    all_categories = set(ref_counts.index) | set(curr_counts.index)
                    ref_counts = ref_counts.reindex(all_categories, fill_value=0)
                    curr_counts = curr_counts.reindex(all_categories, fill_value=0)
                    
                    contingency_table = pd.DataFrame({
                        'reference': ref_counts,
                        'current': curr_counts
                    }).T
                    
                    chi2, p_value, _, _ = chi2_contingency(contingency_table)
                    drift_scores[feature] = float(chi2 / len(contingency_table))
                    
                    if p_value < 0.05:
                        drifted_features.append(feature)
                        logging.warning(f"Drift detected in {feature}: p-value={p_value:.4f}")
                        
                except Exception as e:
                    logging.warning(f"Could not check drift for {feature}: {e}")
        
        has_drift = len(drifted_features) > 0
        
        report = DataDriftReport(
            timestamp=datetime.now().isoformat(),
            features_checked=len(drift_scores),
            drifted_features=drifted_features,
            drift_scores=drift_scores,
            has_drift=has_drift,
            drift_threshold=self.drift_threshold
        )
        
        if has_drift:
            self.alerts.append({
                'severity': 'MEDIUM',
                'type': 'DATA_DRIFT',
                'message': f'Drift detected in {len(drifted_features)} features: {drifted_features}',
                'timestamp': report.timestamp
            })
        
        return report
    
    def check_prediction_distribution(
        self,
        predictions: np.ndarray,
        reference_predictions: np.ndarray,
        threshold: float = 0.2
    ) -> Dict:
        """
        Check if prediction distribution has shifted significantly
        
        Args:
            predictions: Current predictions
            reference_predictions: Reference predictions
            threshold: Threshold for detecting shift
            
        Returns:
            Dictionary with shift detection results
        """
        from scipy.stats import ks_2samp
        
        statistic, p_value = ks_2samp(reference_predictions, predictions)
        
        has_shifted = p_value < 0.05
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'ks_statistic': float(statistic),
            'p_value': float(p_value),
            'has_shifted': has_shifted,
            'current_mean': float(np.mean(predictions)),
            'reference_mean': float(np.mean(reference_predictions)),
            'mean_difference': float(np.mean(predictions) - np.mean(reference_predictions)),
            'current_std': float(np.std(predictions)),
            'reference_std': float(np.std(reference_predictions))
        }
        
        if has_shifted:
            self.alerts.append({
                'severity': 'MEDIUM',
                'type': 'PREDICTION_SHIFT',
                'message': f'Prediction distribution has shifted (p-value: {p_value:.4f})',
                'timestamp': result['timestamp']
            })
        
        return result
    
    def monitor_model_staleness(
        self,
        model_metadata: Dict,
        max_age_days: int = 30
    ) -> Dict:
        """
        Check if model is too old and needs retraining
        
        Args:
            model_metadata: Model metadata including training date
            max_age_days: Maximum acceptable model age in days
            
        Returns:
            Dictionary with staleness check results
        """
        trained_at = model_metadata.get('trained_at')
        
        if not trained_at:
            return {'is_stale': False, 'message': 'Training date unknown'}
        
        try:
            trained_date = datetime.fromisoformat(trained_at)
            age_days = (datetime.now() - trained_date).days
            is_stale = age_days > max_age_days
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'trained_at': trained_at,
                'age_days': age_days,
                'max_age_days': max_age_days,
                'is_stale': is_stale
            }
            
            if is_stale:
                self.alerts.append({
                    'severity': 'LOW',
                    'type': 'MODEL_STALE',
                    'message': f'Model is {age_days} days old (threshold: {max_age_days} days)',
                    'timestamp': result['timestamp']
                })
            
            return result
            
        except Exception as e:
            logging.error(f"Error checking model staleness: {e}")
            return {'is_stale': False, 'error': str(e)}
    
    def generate_monitoring_report(
        self,
        performance_metrics: ModelPerformanceMetrics,
        drift_report: Optional[DataDriftReport] = None,
        save_path: str = "metrics/monitoring_report.json"
    ) -> Dict:
        """
        Generate comprehensive monitoring report
        
        Args:
            performance_metrics: Model performance metrics
            drift_report: Optional data drift report
            save_path: Path to save report
            
        Returns:
            Complete monitoring report dictionary
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'performance_metrics': asdict(performance_metrics),
            'drift_report': asdict(drift_report) if drift_report else None,
            'alerts': self.alerts,
            'alert_summary': {
                'total_alerts': len(self.alerts),
                'high_severity': len([a for a in self.alerts if a['severity'] == 'HIGH']),
                'medium_severity': len([a for a in self.alerts if a['severity'] == 'MEDIUM']),
                'low_severity': len([a for a in self.alerts if a['severity'] == 'LOW'])
            },
            'recommendations': self._generate_recommendations()
        }
        
        # Save report
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logging.info(f"Monitoring report saved to {save_path}")
        
        # Log to MLflow
        try:
            with mlflow.start_run(run_name=f"monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
                mlflow.set_tag("monitoring", "true")
                mlflow.log_metrics({
                    'total_alerts': report['alert_summary']['total_alerts'],
                    'high_alerts': report['alert_summary']['high_severity']
                })
                mlflow.log_artifact(save_path)
        except Exception as e:
            logging.warning(f"Could not log to MLflow: {e}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on alerts"""
        recommendations = []
        
        alert_types = {alert['type'] for alert in self.alerts}
        
        if 'PERFORMANCE_DEGRADATION' in alert_types:
            recommendations.append("URGENT: Retrain model immediately due to performance degradation")
        
        if 'DATA_DRIFT' in alert_types:
            recommendations.append("Investigate data drift - consider retraining with recent data")
        
        if 'PREDICTION_SHIFT' in alert_types:
            recommendations.append("Monitor prediction patterns - may indicate changing data distribution")
        
        if 'MODEL_STALE' in alert_types:
            recommendations.append("Schedule model retraining - model is aging")
        
        if not recommendations:
            recommendations.append("No immediate actions required - system operating normally")
        
        return recommendations
    
    def get_alerts(self, severity: Optional[str] = None) -> List[Dict]:
        """
        Get current alerts, optionally filtered by severity
        
        Args:
            severity: Optional severity filter (HIGH, MEDIUM, LOW)
            
        Returns:
            List of alert dictionaries
        """
        if severity:
            return [a for a in self.alerts if a['severity'] == severity]
        return self.alerts


def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Model Monitoring')
    parser.add_argument('--model-path', required=True, help='Path to model file')
    parser.add_argument('--data-path', help='Path to current data for drift detection')
    parser.add_argument('--reference-data', help='Path to reference data for drift detection')
    parser.add_argument('--output', default='metrics/monitoring_report.json', 
                       help='Output path for report')
    
    args = parser.parse_args()
    
    monitor = ModelMonitor(args.model_path)
    
    # Generate basic report
    if monitor.model_artifacts:
        metadata = monitor.model_artifacts.get('metadata', {})
        staleness = monitor.monitor_model_staleness(metadata)
        
        print(f"\nModel Staleness Check:")
        print(f"  Age: {staleness.get('age_days', 'unknown')} days")
        print(f"  Status: {'⚠ STALE' if staleness.get('is_stale') else '✓ Fresh'}")
    
    # Check for drift if data provided
    if args.data_path and args.reference_data:
        current_data = pd.read_csv(args.data_path)
        reference_data = pd.read_csv(args.reference_data)
        
        drift_report = monitor.detect_data_drift(reference_data, current_data)
        
        print(f"\nData Drift Report:")
        print(f"  Features checked: {drift_report.features_checked}")
        print(f"  Drifted features: {len(drift_report.drifted_features)}")
        if drift_report.drifted_features:
            print(f"  Features: {', '.join(drift_report.drifted_features)}")
    
    # Print alerts
    alerts = monitor.get_alerts()
    if alerts:
        print(f"\n⚠ Alerts: {len(alerts)}")
        for alert in alerts:
            print(f"  [{alert['severity']}] {alert['type']}: {alert['message']}")
    else:
        print("\n✓ No alerts")


if __name__ == "__main__":
    main()
