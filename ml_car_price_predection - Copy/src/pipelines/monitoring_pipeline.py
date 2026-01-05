"""
Monitoring pipeline for model performance
Moved from scripts/monitor.py
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

from ..models.evaluate import ModelEvaluator
from ..utils.logger import setup_logger
from ..utils.db_utils import get_db_connection

logger = setup_logger(__name__)


class ModelMonitor:
    """Monitor model performance and detect drift"""
    
    def __init__(self):
        self.logger = logger
    
    def check_data_drift(self, reference_data: pd.DataFrame,
                        current_data: pd.DataFrame,
                        threshold: float = 0.1) -> Dict:
        """Detect data drift using statistical tests"""
        from scipy import stats
        
        drift_detected = {}
        
        for col in reference_data.columns:
            if col in current_data.columns:
                if pd.api.types.is_numeric_dtype(reference_data[col]):
                    # KS test for numerical features
                    statistic, p_value = stats.ks_2samp(
                        reference_data[col].dropna(),
                        current_data[col].dropna()
                    )
                    drift_detected[col] = {
                        'drift': p_value < threshold,
                        'p_value': float(p_value),
                        'test': 'ks_test'
                    }
        
        logger.info(f"Data drift check complete. Features with drift: {sum(v['drift'] for v in drift_detected.values())}")
        return drift_detected
    
    def check_performance_degradation(self, run_id: str,
                                     recent_window: int = 7) -> Dict:
        """Check if model performance has degraded"""
        with get_db_connection() as db:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get recent metrics
                cursor.execute("""
                    SELECT mr.run_id, mm.metric_name, mm.metric_value, mm.created_at
                    FROM model_runs mr
                    JOIN model_metrics mm ON mr.run_id = mm.run_id
                    WHERE mm.created_at >= %s
                    AND mm.metric_name = 'r2_score'
                    ORDER BY mm.created_at DESC
                """, (datetime.now() - timedelta(days=recent_window),))
                
                recent_metrics = cursor.fetchall()
                
                if len(recent_metrics) < 2:
                    return {'status': 'insufficient_data'}
                
                # Compare latest with previous
                latest_r2 = recent_metrics[0][2]
                previous_r2 = np.mean([m[2] for m in recent_metrics[1:]])
                
                degradation = previous_r2 - latest_r2
                degradation_pct = (degradation / previous_r2) * 100 if previous_r2 > 0 else 0
                
                is_degraded = degradation_pct > 10  # 10% threshold
                
                if is_degraded:
                    db.insert_alert(
                        run_id=run_id,
                        alert_type='PERFORMANCE_DEGRADATION',
                        severity='HIGH',
                        message=f'Model performance degraded by {degradation_pct:.2f}%'
                    )
                    logger.warning(f"Performance degradation detected: {degradation_pct:.2f}%")
                
                return {
                    'is_degraded': is_degraded,
                    'latest_r2': float(latest_r2),
                    'average_r2': float(previous_r2),
                    'degradation_pct': float(degradation_pct)
                }
    
    def generate_monitoring_report(self) -> Dict:
        """Generate comprehensive monitoring report"""
        with get_db_connection() as db:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get recent runs
                cursor.execute("""
                    SELECT run_id, model_name, trained_at
                    FROM model_runs
                    ORDER BY trained_at DESC
                    LIMIT 10
                """)
                recent_runs = cursor.fetchall()
                
                # Get recent alerts
                cursor.execute("""
                    SELECT alert_type, severity, COUNT(*)
                    FROM model_alerts
                    WHERE created_at >= %s
                    GROUP BY alert_type, severity
                """, (datetime.now() - timedelta(days=7),))
                alerts = cursor.fetchall()
                
                report = {
                    'generated_at': datetime.now().isoformat(),
                    'recent_runs_count': len(recent_runs),
                    'alerts': [{'type': a[0], 'severity': a[1], 'count': a[2]} for a in alerts]
                }
                
                logger.info(f"Monitoring report generated: {report}")
                return report


if __name__ == '__main__':
    monitor = ModelMonitor()
    report = monitor.generate_monitoring_report()
    print(f"Monitoring Report: {report}")
