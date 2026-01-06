"""
Model Performance Monitoring & Automatic Rollback
Continuously monitors model performance and automatically rolls back if degradation is detected
"""

import logging
import sys
import os
import argparse
from datetime import datetime
from typing import Dict, Optional

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from db_utils import ModelEvaluationDB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "monitoring.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModelMonitor:
    """
    Monitor model performance and manage automatic rollbacks
    """
    
    def __init__(self, degradation_threshold: float = 5.0, auto_rollback: bool = True):
        """
        Initialize model monitor
        
        Args:
            degradation_threshold: Percentage threshold for performance degradation (default 5%)
            auto_rollback: Whether to automatically rollback on degradation (default True)
        """
        self.degradation_threshold = degradation_threshold
        self.auto_rollback = auto_rollback
        self.db = None
        self._connect()
    
    def _connect(self):
        """Initialize database connection"""
        try:
            self.db = ModelEvaluationDB()
            logger.info("✓ Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def check_and_respond(self) -> Dict:
        """
        Check for performance degradation and automatically rollback if needed
        
        Returns:
            Dictionary with monitoring results
        """
        logger.info("=" * 80)
        logger.info("🔍 STARTING MODEL PERFORMANCE CHECK")
        logger.info("=" * 80)
        
        # Check for degradation
        degradation_result = self.db.check_performance_degradation(
            threshold_percent=self.degradation_threshold
        )
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'degradation_check': degradation_result,
            'rollback_performed': False,
            'status': 'OK'
        }
        
        if degradation_result.get('degraded'):
            logger.warning("⚠️  PERFORMANCE DEGRADATION DETECTED!")
            logger.warning(f"   R² Change: {degradation_result['r2_change_percent']}%")
            logger.warning(f"   RMSE Change: {degradation_result['rmse_change_percent']}%")
            logger.warning(f"   Current Version: {degradation_result['current_version']}")
            logger.warning(f"   Previous Version: {degradation_result['previous_version']}")
            
            result['status'] = 'DEGRADATION_DETECTED'
            
            # Determine severity based on degradation percentages
            abs_r2_change = abs(degradation_result['r2_change_percent'])
            abs_rmse_change = abs(degradation_result['rmse_change_percent'])
            max_degradation = max(abs_r2_change, abs_rmse_change)
            
            if max_degradation >= 20:
                severity = 'CRITICAL'
            elif max_degradation >= 15:
                severity = 'HIGH'
            elif max_degradation >= 10:
                severity = 'MEDIUM'
            else:
                severity = 'LOW'
            
            # Determine degradation type
            degradation_types = []
            if degradation_result['r2_change_percent'] < -self.degradation_threshold:
                degradation_types.append('R2_DEGRADATION')
            if degradation_result['rmse_change_percent'] > self.degradation_threshold:
                degradation_types.append('RMSE_INCREASE')
            degradation_type = ','.join(degradation_types) if degradation_types else 'PERFORMANCE_DEGRADATION'
            
            # Store detailed degradation analysis
            explanation = (
                f"Model v{degradation_result['current_version']} showed performance degradation compared to "
                f"v{degradation_result['previous_version']}. "
                f"R² dropped from {degradation_result['previous_r2']:.4f} to {degradation_result['current_r2']:.4f} "
                f"({degradation_result['r2_change_percent']:.2f}%). "
                f"RMSE increased from {degradation_result['previous_rmse']:.4f} to {degradation_result['current_rmse']:.4f} "
                f"({degradation_result['rmse_change_percent']:.2f}%)."
            )
            
            try:
                degradation_id = self.db.store_degradation_analysis(
                    degraded_model_version=degradation_result['current_version'],
                    previous_stable_version=degradation_result['previous_version'],
                    degradation_type=degradation_type,
                    severity=severity,
                    r2_degraded=degradation_result['current_r2'],
                    r2_stable=degradation_result['previous_r2'],
                    r2_change_percent=degradation_result['r2_change_percent'],
                    rmse_degraded=degradation_result['current_rmse'],
                    rmse_stable=degradation_result['previous_rmse'],
                    rmse_change_percent=degradation_result['rmse_change_percent'],
                    threshold_percent=self.degradation_threshold,
                    explanation=explanation,
                    root_cause_hypothesis="Possible causes: Data distribution change, training data quality degradation, model overfitting, or external factors affecting model performance",
                    recommended_action="Review training data quality, validate model predictions, check for data drift, consider retraining with latest data"
                )
                logger.info(f"✓ Degradation analysis stored with ID: {degradation_id}")
                result['degradation_id'] = degradation_id
            except Exception as e:
                logger.error(f"Failed to store degradation analysis: {e}")
            
            if self.auto_rollback:
                logger.info("🔄 AUTOMATIC ROLLBACK ENABLED - Reverting to previous model...")
                rollback_success = self.db.rollback_production_model()
                
                result['rollback_performed'] = rollback_success
                
                if rollback_success:
                    logger.warning(f"✓ ROLLBACK SUCCESSFUL to v{degradation_result['previous_version']}")
                    result['status'] = 'ROLLED_BACK'
                    
                    # Update degradation record with rollback info
                    try:
                        self.db.update_degradation_with_rollback(degradation_id, rollback_executed=True)
                        logger.info(f"✓ Degradation record updated with rollback status")
                    except Exception as e:
                        logger.error(f"Failed to update degradation record: {e}")
                else:
                    logger.error("✗ ROLLBACK FAILED")
                    result['status'] = 'DEGRADATION_DETECTED_ROLLBACK_FAILED'
            else:
                logger.warning("🚨 AUTOMATIC ROLLBACK DISABLED - Manual intervention required")
                result['status'] = 'DEGRADATION_DETECTED_AUTO_ROLLBACK_DISABLED'
        else:
            logger.info("✓ No performance degradation detected")
            logger.info(f"   R² Change: {degradation_result['r2_change_percent']}%")
            logger.info(f"   RMSE Change: {degradation_result['rmse_change_percent']}%")
            logger.info(f"   Current R²: {degradation_result['current_r2']}")
            logger.info(f"   Previous R²: {degradation_result['previous_r2']}")
        
        logger.info("=" * 80)
        return result
    
    def get_model_history(self, limit: int = 10) -> list:
        """
        Get model version history
        
        Args:
            limit: Maximum number of versions to show
            
        Returns:
            List of model versions with metrics
        """
        return self.db.get_model_history(limit=limit)
    
    def compare_versions(self, version1: str, version2: str) -> Dict:
        """
        Compare two specific model versions
        
        Args:
            version1: First model version
            version2: Second model version
            
        Returns:
            Comparison results
        """
        return self.db.compare_models(version1, version2)
    
    def manual_rollback(self, target_version: Optional[str] = None) -> bool:
        """
        Manually rollback to a previous version
        
        Args:
            target_version: Specific version to rollback to.
                          If None, rolls back to previous version.
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"🔄 MANUAL ROLLBACK INITIATED")
        if target_version:
            logger.info(f"   Target Version: {target_version}")
        else:
            logger.info(f"   Target: Previous version")
        
        success = self.db.rollback_production_model(target_version=target_version)
        
        if success:
            logger.warning(f"✓ Manual rollback successful")
        else:
            logger.error(f"✗ Manual rollback failed")
        
        return success
    
    def print_status(self):
        """Print current model status"""
        logger.info("=" * 80)
        logger.info("📊 MODEL STATUS")
        logger.info("=" * 80)
        
        history = self.get_model_history(limit=5)
        
        if not history:
            logger.info("No models found in database")
            return
        
        for i, model in enumerate(history):
            prod_indicator = "🚀 PROD" if model['is_production'] else "  TEST"
            logger.info(
                f"\n{prod_indicator} | v{model['model_version']}\n"
                f"       Type: {model['model_type']}\n"
                f"       R²: {model['r2_score']}\n"
                f"       RMSE: {model['rmse_score']}\n"
                f"       Size: {model['size_mb']} MB\n"
                f"       Created: {model['created_at']}"
            )
        
        logger.info("=" * 80)
    
    def print_degradation_history(self, limit: int = 10, severity: Optional[str] = None):
        """
        Print degradation analysis history
        
        Args:
            limit: Maximum number of records to show
            severity: Filter by severity (HIGH, MEDIUM, LOW, CRITICAL)
        """
        logger.info("=" * 80)
        logger.info("📋 DEGRADATION ANALYSIS HISTORY")
        logger.info("=" * 80)
        
        history = self.db.get_degradation_history(limit=limit, severity=severity)
        
        if not history:
            logger.info("No degradation events found")
            return
        
        for event in history:
            severity_emoji = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }.get(event['severity'], '⚪')
            
            logger.info(f"\n{severity_emoji} {event['severity']} | {event['detected_at']}")
            logger.info(f"   Degraded: v{event['degraded_model_version']} → Stable: v{event['previous_stable_version']}")
            logger.info(f"   Type: {event['degradation_type']}")
            logger.info(f"   R² Change: {event['r2_change_percent']:+.2f}% ({event['r2_degraded']:.4f} → {event['r2_stable']:.4f})")
            logger.info(f"   RMSE Change: {event['rmse_change_percent']:+.2f}% ({event['rmse_degraded']:.4f} → {event['rmse_stable']:.4f})")
            
            if event['explanation']:
                logger.info(f"   Explanation: {event['explanation']}")
            
            if event['root_cause_hypothesis']:
                logger.info(f"   Root Cause: {event['root_cause_hypothesis']}")
            
            if event['recommended_action']:
                logger.info(f"   Action: {event['recommended_action']}")
            
            rollback_status = "✓ EXECUTED" if event['rollback_executed'] else "✗ NOT EXECUTED"
            logger.info(f"   Rollback: {rollback_status}")
        
        logger.info("=" * 80)
        
        # Print summary
        summary = self.db.get_degradation_summary()
        if summary:
            logger.info("\n📊 DEGRADATION SUMMARY STATISTICS")
            logger.info(f"   Total Events: {summary['total_events']}")
            logger.info(f"   Rollbacks Executed: {summary['rollbacks_executed']}")
            logger.info(f"   Critical: {summary['critical_count']} | High: {summary['high_count']} | Medium: {summary['medium_count']} | Low: {summary['low_count']}")
            logger.info(f"   Avg R² Change: {summary['avg_r2_change']:.2f}%")
            logger.info(f"   Avg RMSE Change: {summary['avg_rmse_change']:.2f}%")
            logger.info("=" * 80)
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Monitor model performance and manage rollbacks"
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=5.0,
        help='Performance degradation threshold in percentage (default 5%)'
    )
    parser.add_argument(
        '--auto-rollback',
        action='store_true',
        default=True,
        help='Enable automatic rollback on degradation (default True)'
    )
    parser.add_argument(
        '--no-auto-rollback',
        action='store_false',
        dest='auto_rollback',
        help='Disable automatic rollback (manual only)'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check performance and apply rollback if needed'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current model status'
    )
    parser.add_argument(
        '--rollback',
        metavar='VERSION',
        help='Manually rollback to specific version (e.g., 20260105_143022)'
    )
    parser.add_argument(
        '--rollback-previous',
        action='store_true',
        help='Manually rollback to previous version'
    )
    parser.add_argument(
        '--history',
        type=int,
        metavar='LIMIT',
        nargs='?',
        const=10,
        help='Show model version history (default 10 versions)'
    )
    parser.add_argument(
        '--degradation-history',
        type=int,
        metavar='LIMIT',
        nargs='?',
        const=10,
        help='Show degradation analysis history (default 10 records)'
    )
    parser.add_argument(
        '--severity',
        choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        help='Filter degradation history by severity'
    )
    parser.add_argument(
        '--compare',
        nargs=2,
        metavar=('VERSION1', 'VERSION2'),
        help='Compare two model versions'
    )
    
    args = parser.parse_args()
    
    try:
        monitor = ModelMonitor(
            degradation_threshold=args.threshold,
            auto_rollback=args.auto_rollback
        )
        
        # Default action: check performance
        if not any([args.status, args.rollback, args.rollback_previous, 
                   args.history is not None, args.compare, args.degradation_history is not None]):
            args.check = True
        
        if args.check:
            result = monitor.check_and_respond()
            logger.info(f"\nMonitoring Result: {result['status']}")
        
        if args.status:
            monitor.print_status()
        
        if args.history is not None:
            logger.info("\n📜 MODEL HISTORY")
            logger.info("=" * 80)
            history = monitor.get_model_history(limit=args.history)
            for model in history:
                prod = "🚀 PROD" if model['is_production'] else "    "
                logger.info(
                    f"{prod} | v{model['model_version']} | "
                    f"R²={model['r2_score']:.4f} | "
                    f"Size={model['size_mb']}MB | "
                    f"{model['created_at']}"
                )
            logger.info("=" * 80)
        
        if args.degradation_history is not None:
            monitor.print_degradation_history(
                limit=args.degradation_history,
                severity=args.severity
            )
        
        if args.compare:
            logger.info(f"\n🔄 COMPARING VERSIONS")
            logger.info("=" * 80)
            comparison = monitor.compare_versions(args.compare[0], args.compare[1])
            if comparison:
                logger.info(f"Current (newer): v{comparison['current_version']}")
                logger.info(f"  R²: {comparison['r2_current']:.4f}")
                logger.info(f"  RMSE: {comparison['rmse_current']:.2f}")
                logger.info(f"\nPrevious (older): v{comparison['previous_version']}")
                logger.info(f"  R²: {comparison['r2_previous']:.4f}")
                logger.info(f"  RMSE: {comparison['rmse_previous']:.2f}")
                logger.info(f"\nChange:")
                logger.info(f"  R² Change: {comparison['r2_change']:.4f}")
                logger.info(f"  RMSE Change: {comparison['rmse_change']:.2f}")
                logger.info(f"  Degraded: {'Yes' if comparison['degraded'] else 'No'}")
            logger.info("=" * 80)
        
        if args.rollback:
            monitor.manual_rollback(target_version=args.rollback)
        
        if args.rollback_previous:
            monitor.manual_rollback()
        
        monitor.close()
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
