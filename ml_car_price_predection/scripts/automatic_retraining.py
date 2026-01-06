"""
Automatic Model Retraining System
Monitors model performance and automatically retrains when drift/degradation is detected
"""

import logging
import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from db_utils import ModelEvaluationDB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "retraining.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DriftType(Enum):
    """Types of model drift"""
    DATA_DRIFT = "data_drift"           # Input feature distribution changed
    CONCEPT_DRIFT = "concept_drift"     # Relationship between features and target changed
    PERFORMANCE_DRIFT = "performance_drift"  # Model predictions becoming less accurate
    NONE = "none"                       # No drift detected


@dataclass
class RetrainingTrigger:
    """Trigger information for model retraining"""
    triggered: bool
    drift_type: DriftType
    reason: str
    severity: str
    confidence: float
    metrics: Dict
    recommended_action: str
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class DataDriftDetector:
    """Detect data drift using statistical methods"""
    
    def __init__(self, threshold: float = 0.05):
        """
        Initialize data drift detector
        
        Args:
            threshold: P-value threshold for statistical tests (default 0.05)
        """
        self.threshold = threshold
    
    def detect_distribution_shift(self, 
                                  reference_data: pd.DataFrame,
                                  current_data: pd.DataFrame,
                                  numeric_columns: List[str] = None) -> Tuple[bool, Dict]:
        """
        Detect if data distribution has shifted using Kolmogorov-Smirnov test
        
        Args:
            reference_data: Reference dataset (baseline)
            current_data: Current dataset to check
            numeric_columns: Numeric columns to check (default all numeric)
            
        Returns:
            Tuple of (drift_detected, metrics_dict)
        """
        from scipy.stats import ks_2samp
        
        if numeric_columns is None:
            numeric_columns = current_data.select_dtypes(include=[np.number]).columns.tolist()
        
        drift_scores = {}
        columns_with_drift = []
        
        for col in numeric_columns:
            if col not in reference_data.columns or col not in current_data.columns:
                continue
            
            try:
                # Handle missing values
                ref_values = reference_data[col].dropna()
                curr_values = current_data[col].dropna()
                
                if len(ref_values) == 0 or len(curr_values) == 0:
                    continue
                
                # Kolmogorov-Smirnov test
                statistic, p_value = ks_2samp(ref_values, curr_values)
                drift_scores[col] = {
                    'ks_statistic': float(statistic),
                    'p_value': float(p_value),
                    'drifted': p_value < self.threshold
                }
                
                if p_value < self.threshold:
                    columns_with_drift.append(col)
                    logger.warning(f"Data drift detected in column '{col}': p-value={p_value:.4f}")
            except Exception as e:
                logger.error(f"Error testing column {col}: {e}")
        
        drift_detected = len(columns_with_drift) > 0
        
        return drift_detected, {
            'drift_detected': drift_detected,
            'columns_affected': columns_with_drift,
            'column_scores': drift_scores,
            'pct_columns_drifted': len(columns_with_drift) / len(numeric_columns) * 100 if numeric_columns else 0
        }
    
    def detect_outliers(self, data: pd.DataFrame, 
                       threshold: float = 3.0) -> Tuple[int, Dict]:
        """
        Detect outliers using Z-score method
        
        Args:
            data: Data to check for outliers
            threshold: Z-score threshold (default 3.0 = 3 standard deviations)
            
        Returns:
            Tuple of (outlier_count, metrics_dict)
        """
        from scipy import stats
        
        numeric_data = data.select_dtypes(include=[np.number])
        
        outlier_counts = {}
        total_outliers = 0
        
        for col in numeric_data.columns:
            try:
                z_scores = np.abs(stats.zscore(numeric_data[col].dropna()))
                outliers = np.sum(z_scores > threshold)
                outlier_counts[col] = int(outliers)
                total_outliers += outliers
            except Exception as e:
                logger.error(f"Error detecting outliers in {col}: {e}")
        
        return total_outliers, {
            'total_outliers': total_outliers,
            'outliers_per_column': outlier_counts,
            'pct_outliers': total_outliers / len(data) * 100 if len(data) > 0 else 0
        }


class ConceptDriftDetector:
    """Detect concept drift - change in relationship between features and target"""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize concept drift detector
        
        Args:
            window_size: Size of sliding window for monitoring
        """
        self.window_size = window_size
    
    def detect_prediction_error_drift(self,
                                       predictions: List[float],
                                       actuals: List[float],
                                       error_threshold: float = 0.15) -> Tuple[bool, Dict]:
        """
        Detect if prediction errors have increased (concept drift indicator)
        
        Args:
            predictions: Model predictions
            actuals: Actual values
            error_threshold: Increase threshold (e.g., 0.15 = 15% increase)
            
        Returns:
            Tuple of (drift_detected, metrics_dict)
        """
        if len(predictions) < self.window_size * 2:
            logger.warning("Not enough predictions for concept drift detection")
            return False, {'warning': 'Insufficient data'}
        
        # Convert to numpy arrays
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        
        # Split into two windows
        split_idx = len(predictions) // 2
        
        # Calculate MAE for each window
        mae_first = np.mean(np.abs(predictions[:split_idx] - actuals[:split_idx]))
        mae_second = np.mean(np.abs(predictions[split_idx:] - actuals[split_idx:]))
        
        # Calculate percentage increase
        error_increase = (mae_second - mae_first) / (mae_first + 1e-10)
        
        drift_detected = error_increase > error_threshold
        
        if drift_detected:
            logger.warning(f"Concept drift detected: MAE increased by {error_increase*100:.2f}%")
        
        return drift_detected, {
            'mae_first_window': float(mae_first),
            'mae_second_window': float(mae_second),
            'error_increase_pct': float(error_increase * 100),
            'threshold': error_threshold * 100,
            'drifted': drift_detected
        }


class ModelPerformanceMonitor:
    """Monitor model performance against historical baseline"""
    
    def __init__(self, db: Optional[ModelEvaluationDB] = None,
                 r2_threshold: float = 0.05,
                 rmse_threshold: float = 0.10):
        """
        Initialize performance monitor
        
        Args:
            db: Database connection for retrieving history
            r2_threshold: R² degradation threshold (default 5%)
            rmse_threshold: RMSE increase threshold (default 10%)
        """
        self.db = db
        self.r2_threshold = r2_threshold
        self.rmse_threshold = rmse_threshold
    
    def check_performance_degradation(self, current_metrics: Dict) -> Tuple[bool, Dict]:
        """
        Check if current model performance has degraded
        
        Args:
            current_metrics: Current model metrics {r2, rmse, accuracy}
            
        Returns:
            Tuple of (degradation_detected, metrics_dict)
        """
        if not self.db:
            logger.warning("Database not available for performance monitoring")
            return False, {}
        
        # Get previous stable model metrics
        previous_metrics = self.db.get_model_history(limit=2)
        
        if not previous_metrics or len(previous_metrics) < 2:
            logger.info("No previous metrics for comparison")
            return False, {}
        
        prev_model = previous_metrics[1]  # Previous stable version
        
        # Compare metrics
        r2_current = current_metrics.get('r2', 0)
        r2_previous = prev_model.get('r2_score', 0)
        
        rmse_current = current_metrics.get('rmse', 0)
        rmse_previous = prev_model.get('rmse_score', 0)
        
        # Calculate percentage changes
        r2_change = ((r2_current - r2_previous) / (r2_previous + 1e-10)) * 100
        rmse_change = ((rmse_current - rmse_previous) / (rmse_previous + 1e-10)) * 100
        
        # Check thresholds
        degradation_detected = (r2_change < -self.r2_threshold or 
                              rmse_change > self.rmse_threshold)
        
        if degradation_detected:
            logger.warning(f"Performance degradation detected: R² change={r2_change:.2f}%, RMSE change={rmse_change:.2f}%")
        
        return degradation_detected, {
            'r2_current': float(r2_current),
            'r2_previous': float(r2_previous),
            'r2_change_pct': float(r2_change),
            'rmse_current': float(rmse_current),
            'rmse_previous': float(rmse_previous),
            'rmse_change_pct': float(rmse_change),
            'degraded': degradation_detected
        }


class AutomaticRetrainingOrchestrator:
    """
    Orchestrates automatic model retraining based on various triggers
    """
    
    def __init__(self, 
                 data_drift_threshold: float = 0.05,
                 performance_threshold: float = 0.05,
                 min_samples_for_retraining: int = 100):
        """
        Initialize retraining orchestrator
        
        Args:
            data_drift_threshold: P-value threshold for drift detection
            performance_threshold: Performance degradation threshold
            min_samples_for_retraining: Minimum samples before retraining
        """
        self.data_drift_detector = DataDriftDetector(threshold=data_drift_threshold)
        self.concept_drift_detector = ConceptDriftDetector()
        self.performance_monitor = ModelPerformanceMonitor(r2_threshold=performance_threshold)
        self.min_samples_for_retraining = min_samples_for_retraining
        self.db = None
        
        try:
            self.db = ModelEvaluationDB()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Could not connect to database: {e}")
    
    def should_retrain(self,
                       reference_data: pd.DataFrame,
                       recent_data: pd.DataFrame,
                       recent_predictions: List[float],
                       recent_actuals: List[float],
                       current_metrics: Dict) -> RetrainingTrigger:
        """
        Determine if model should be retrained
        
        Args:
            reference_data: Original training data (baseline)
            recent_data: Recent data to check for drift
            recent_predictions: Recent model predictions
            recent_actuals: Recent actual values
            current_metrics: Current model metrics
            
        Returns:
            RetrainingTrigger with decision and reasoning
        """
        logger.info("=" * 80)
        logger.info("🔍 CHECKING RETRAINING TRIGGERS")
        logger.info("=" * 80)
        
        # Check if we have enough recent data
        if len(recent_data) < self.min_samples_for_retraining:
            logger.info(f"Insufficient samples for retraining ({len(recent_data)}/{self.min_samples_for_retraining})")
            return RetrainingTrigger(
                triggered=False,
                drift_type=DriftType.NONE,
                reason="Insufficient data samples",
                severity="NONE",
                confidence=0.0,
                metrics={'samples_available': len(recent_data), 'min_required': self.min_samples_for_retraining},
                recommended_action="Continue monitoring"
            )
        
        triggers = []
        metrics = {}
        
        # 1. Check for data drift
        logger.info("📊 Checking for data drift...")
        data_drift, drift_metrics = self.data_drift_detector.detect_distribution_shift(
            reference_data, recent_data
        )
        metrics['data_drift'] = drift_metrics
        
        if data_drift:
            pct_drifted = drift_metrics.get('pct_columns_drifted', 0)
            logger.warning(f"⚠️  Data drift detected: {pct_drifted:.1f}% of columns affected")
            triggers.append({
                'type': DriftType.DATA_DRIFT,
                'confidence': min(100, pct_drifted * 1.5),  # Confidence based on % of columns
                'severity': 'HIGH' if pct_drifted > 30 else 'MEDIUM'
            })
        
        # 2. Check for outliers
        logger.info("🎯 Checking for outliers...")
        outlier_count, outlier_metrics = self.data_drift_detector.detect_outliers(recent_data)
        metrics['outliers'] = outlier_metrics
        
        pct_outliers = outlier_metrics.get('pct_outliers', 0)
        if pct_outliers > 5:  # More than 5% outliers
            logger.warning(f"⚠️  High outlier rate detected: {pct_outliers:.2f}%")
            triggers.append({
                'type': DriftType.DATA_DRIFT,
                'confidence': min(100, pct_outliers * 10),
                'severity': 'MEDIUM'
            })
        
        # 3. Check for concept drift
        logger.info("🔄 Checking for concept drift...")
        concept_drift, concept_metrics = self.concept_drift_detector.detect_prediction_error_drift(
            recent_predictions, recent_actuals
        )
        metrics['concept_drift'] = concept_metrics
        
        if concept_drift:
            error_increase = concept_metrics.get('error_increase_pct', 0)
            logger.warning(f"⚠️  Concept drift detected: {error_increase:.2f}% error increase")
            triggers.append({
                'type': DriftType.CONCEPT_DRIFT,
                'confidence': min(100, error_increase),
                'severity': 'HIGH' if error_increase > 20 else 'MEDIUM'
            })
        
        # 4. Check for performance degradation
        logger.info("📈 Checking for performance degradation...")
        perf_degraded, perf_metrics = self.performance_monitor.check_performance_degradation(current_metrics)
        metrics['performance'] = perf_metrics
        
        if perf_degraded:
            r2_change = perf_metrics.get('r2_change_pct', 0)
            logger.warning(f"⚠️  Performance degradation detected: R² change={r2_change:.2f}%")
            triggers.append({
                'type': DriftType.PERFORMANCE_DRIFT,
                'confidence': min(100, abs(r2_change) * 2),
                'severity': 'CRITICAL' if abs(r2_change) > 10 else 'HIGH'
            })
        
        logger.info("=" * 80)
        
        # Decide if retraining is needed
        if triggers:
            # Find the most severe trigger
            most_severe = max(triggers, key=lambda x: x['confidence'])
            
            severity_priority = {'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1}
            overall_severity = max([t['severity'] for t in triggers], 
                                  key=lambda x: severity_priority.get(x, 0))
            
            avg_confidence = np.mean([t['confidence'] for t in triggers])
            
            logger.warning(f"🔴 RETRAINING TRIGGERED")
            logger.warning(f"   Severity: {overall_severity}")
            logger.warning(f"   Triggers: {len(triggers)}")
            logger.warning(f"   Confidence: {avg_confidence:.2f}%")
            
            return RetrainingTrigger(
                triggered=True,
                drift_type=most_severe['type'],
                reason=f"Multiple triggers detected: {', '.join([t['type'].value for t in triggers])}",
                severity=overall_severity,
                confidence=avg_confidence,
                metrics=metrics,
                recommended_action="Retrain model with recent data"
            )
        else:
            logger.info("✅ No retraining triggers detected")
            return RetrainingTrigger(
                triggered=False,
                drift_type=DriftType.NONE,
                reason="Model performance is stable",
                severity="NONE",
                confidence=0.0,
                metrics=metrics,
                recommended_action="Continue monitoring"
            )
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()


def analyze_retraining_need(reference_data_path: str,
                           recent_data_path: str,
                           recent_predictions_path: str,
                           recent_actuals_path: str,
                           current_metrics: Dict) -> RetrainingTrigger:
    """
    Analyze if model retraining is needed
    
    Args:
        reference_data_path: Path to reference training data
        recent_data_path: Path to recent data
        recent_predictions_path: Path to recent predictions
        recent_actuals_path: Path to recent actuals
        current_metrics: Current model metrics
        
    Returns:
        RetrainingTrigger with decision
    """
    logger.info("Loading data...")
    
    try:
        reference_data = pd.read_csv(reference_data_path)
        recent_data = pd.read_csv(recent_data_path)
        recent_predictions = np.load(recent_predictions_path)
        recent_actuals = np.load(recent_actuals_path)
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return RetrainingTrigger(
            triggered=False,
            drift_type=DriftType.NONE,
            reason=f"Error loading data: {e}",
            severity="NONE",
            confidence=0.0,
            metrics={},
            recommended_action="Check data files"
        )
    
    # Analyze
    orchestrator = AutomaticRetrainingOrchestrator()
    result = orchestrator.should_retrain(
        reference_data, recent_data, recent_predictions, recent_actuals, current_metrics
    )
    orchestrator.close()
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Automatic Model Retraining Analysis")
    parser.add_argument("--reference-data", required=True, help="Path to reference training data")
    parser.add_argument("--recent-data", required=True, help="Path to recent data")
    parser.add_argument("--recent-predictions", required=True, help="Path to recent predictions")
    parser.add_argument("--recent-actuals", required=True, help="Path to recent actuals")
    parser.add_argument("--r2", type=float, default=0.85, help="Current R² score")
    parser.add_argument("--rmse", type=float, default=0.35, help="Current RMSE")
    parser.add_argument("--accuracy", type=float, default=0.80, help="Current accuracy")
    
    args = parser.parse_args()
    
    current_metrics = {
        'r2': args.r2,
        'rmse': args.rmse,
        'accuracy': args.accuracy
    }
    
    result = analyze_retraining_need(
        args.reference_data,
        args.recent_data,
        args.recent_predictions,
        args.recent_actuals,
        current_metrics
    )
    
    print(f"\n{'='*80}")
    print(f"RETRAINING DECISION: {'YES' if result.triggered else 'NO'}")
    print(f"{'='*80}")
    print(f"Reason: {result.reason}")
    print(f"Severity: {result.severity}")
    print(f"Confidence: {result.confidence:.2f}%")
    print(f"{'='*80}")
