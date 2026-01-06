"""
Model Retraining Executor
Handles automatic model retraining pipeline execution
"""

import logging
import os
import sys
import subprocess
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, Tuple
from pathlib import Path

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from db_utils import ModelEvaluationDB
from automatic_retraining import AutomaticRetrainingOrchestrator, RetrainingTrigger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "retraining_executor.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RetrainingExecutor:
    """
    Executes automatic model retraining
    """
    
    def __init__(self, 
                 project_root: str = ".",
                 training_script: str = "train.py",
                 data_path: str = "data/trainset/train.csv"):
        """
        Initialize retraining executor
        
        Args:
            project_root: Root directory of project
            training_script: Path to training script
            data_path: Path to training data
        """
        self.project_root = project_root
        self.training_script = os.path.join(project_root, training_script)
        self.data_path = os.path.join(project_root, data_path)
        self.db = None
        
        try:
            self.db = ModelEvaluationDB()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Could not connect to database: {e}")
    
    def prepare_training_data(self, recent_data: Optional[pd.DataFrame] = None) -> str:
        """
        Prepare data for retraining
        
        Args:
            recent_data: Optional recent data to include in training
            
        Returns:
            Path to prepared training data
        """
        logger.info("📦 Preparing training data...")
        
        try:
            # Load original training data
            original_data = pd.read_csv(self.data_path)
            logger.info(f"Loaded original data: {len(original_data)} rows")
            
            # If recent data provided, combine with original
            if recent_data is not None:
                combined_data = pd.concat([original_data, recent_data], ignore_index=True)
                combined_data = combined_data.drop_duplicates()
                logger.info(f"Combined with recent data: {len(combined_data)} total rows")
            else:
                combined_data = original_data
            
            # Save prepared data
            prepared_path = os.path.join(
                os.path.dirname(self.data_path),
                f"retrain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            combined_data.to_csv(prepared_path, index=False)
            logger.info(f"✓ Training data prepared: {prepared_path}")
            
            return prepared_path
        
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return self.data_path
    
    def execute_retraining(self,
                          training_data_path: str,
                          retrain_trigger: RetrainingTrigger) -> Tuple[bool, Dict]:
        """
        Execute the retraining process
        
        Args:
            training_data_path: Path to training data
            retrain_trigger: Original trigger for retraining
            
        Returns:
            Tuple of (success, metrics_dict)
        """
        logger.info("=" * 80)
        logger.info("🚀 STARTING MODEL RETRAINING")
        logger.info("=" * 80)
        logger.info(f"Trigger: {retrain_trigger.drift_type.value}")
        logger.info(f"Severity: {retrain_trigger.severity}")
        logger.info(f"Training data: {training_data_path}")
        
        try:
            # Check if training script exists
            if not os.path.exists(self.training_script):
                logger.error(f"Training script not found: {self.training_script}")
                return False, {'error': 'Training script not found'}
            
            # Run training script
            logger.info("Starting training subprocess...")
            
            cmd = [
                sys.executable,
                self.training_script,
                "--data-path", training_data_path,
                "--auto-retrain", "true",
                "--retrain-reason", retrain_trigger.drift_type.value,
                "--retrain-severity", retrain_trigger.severity
            ]
            
            # Execute
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                logger.info("✓ Training completed successfully")
                logger.info(result.stdout)
                
                # Parse output for metrics
                try:
                    # Try to extract metrics from output
                    metrics = {
                        'success': True,
                        'training_completed': True,
                        'timestamp': datetime.now().isoformat(),
                        'trigger_type': retrain_trigger.drift_type.value,
                        'trigger_severity': retrain_trigger.severity
                    }
                    return True, metrics
                except Exception as e:
                    logger.error(f"Error parsing training output: {e}")
                    return True, {'success': True, 'timestamp': datetime.now().isoformat()}
            else:
                logger.error(f"Training failed with return code {result.returncode}")
                logger.error(result.stderr)
                return False, {'error': result.stderr}
        
        except subprocess.TimeoutExpired:
            logger.error("Training timeout (exceeded 1 hour)")
            return False, {'error': 'Training timeout'}
        except Exception as e:
            logger.error(f"Error executing retraining: {e}")
            return False, {'error': str(e)}
    
    def log_retraining_event(self, 
                            trigger: RetrainingTrigger,
                            execution_success: bool,
                            execution_metrics: Dict) -> int:
        """
        Log retraining event to database
        
        Args:
            trigger: Retraining trigger
            execution_success: Whether execution was successful
            execution_metrics: Execution metrics
            
        Returns:
            ID of logged event
        """
        if not self.db:
            logger.warning("Database not available, cannot log retraining event")
            return -1
        
        try:
            sql = """
            INSERT INTO model_retraining_events (
                trigger_type, severity, drift_type, trigger_reason,
                trigger_metrics, execution_attempted, execution_successful,
                execution_metrics, triggered_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
            """
            
            with self.db.conn.cursor() as cur:
                cur.execute(sql, (
                    trigger.drift_type.value,
                    trigger.severity,
                    trigger.drift_type.value,
                    trigger.reason,
                    json.dumps(trigger.metrics),
                    True,
                    execution_success,
                    json.dumps(execution_metrics)
                ))
                event_id = cur.fetchone()[0]
                self.db.conn.commit()
                
                logger.info(f"✓ Retraining event logged with ID: {event_id}")
                return event_id
        
        except Exception as e:
            logger.error(f"Error logging retraining event: {e}")
            return -1
    
    def should_execute_retraining(self,
                                  reference_data: pd.DataFrame,
                                  recent_data: pd.DataFrame,
                                  recent_predictions: np.ndarray,
                                  recent_actuals: np.ndarray,
                                  current_metrics: Dict) -> Tuple[bool, RetrainingTrigger]:
        """
        Determine if retraining should be executed
        
        Args:
            reference_data: Original training data
            recent_data: Recent data
            recent_predictions: Recent predictions
            recent_actuals: Recent actual values
            current_metrics: Current model metrics
            
        Returns:
            Tuple of (should_retrain, trigger)
        """
        orchestrator = AutomaticRetrainingOrchestrator()
        trigger = orchestrator.should_retrain(
            reference_data, recent_data, recent_predictions, recent_actuals, current_metrics
        )
        orchestrator.close()
        
        return trigger.triggered, trigger
    
    def execute_full_retraining_pipeline(self,
                                        reference_data: pd.DataFrame,
                                        recent_data: Optional[pd.DataFrame] = None,
                                        recent_predictions: Optional[np.ndarray] = None,
                                        recent_actuals: Optional[np.ndarray] = None,
                                        current_metrics: Optional[Dict] = None) -> Dict:
        """
        Execute complete retraining pipeline from trigger detection to execution
        
        Args:
            reference_data: Reference/original training data
            recent_data: Optional recent data
            recent_predictions: Optional recent predictions
            recent_actuals: Optional recent actuals
            current_metrics: Optional current metrics
            
        Returns:
            Dictionary with pipeline results
        """
        logger.info("\n" + "=" * 80)
        logger.info("🔄 EXECUTING FULL RETRAINING PIPELINE")
        logger.info("=" * 80 + "\n")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'trigger_detected': False,
            'retraining_executed': False,
            'success': False,
            'trigger': None,
            'execution_metrics': None,
            'error': None
        }
        
        try:
            # Step 1: Check if retraining is needed
            logger.info("STEP 1: Checking if retraining is needed...")
            
            if current_metrics is None:
                current_metrics = {'r2': 0.85, 'rmse': 0.35, 'accuracy': 0.80}
            
            should_retrain, trigger = self.should_execute_retraining(
                reference_data, recent_data, recent_predictions, recent_actuals, current_metrics
            )
            
            result['trigger_detected'] = trigger.triggered
            result['trigger'] = {
                'triggered': trigger.triggered,
                'drift_type': trigger.drift_type.value,
                'severity': trigger.severity,
                'confidence': trigger.confidence,
                'reason': trigger.reason
            }
            
            if not should_retrain:
                logger.info("✅ No retraining needed at this time")
                result['success'] = True
                return result
            
            logger.warning(f"⚠️  Retraining triggered: {trigger.reason}")
            
            # Step 2: Prepare training data
            logger.info("\nSTEP 2: Preparing training data...")
            training_data_path = self.prepare_training_data(recent_data)
            
            # Step 3: Execute retraining
            logger.info("\nSTEP 3: Executing retraining...")
            exec_success, exec_metrics = self.execute_retraining(training_data_path, trigger)
            
            result['retraining_executed'] = True
            result['execution_metrics'] = exec_metrics
            
            if not exec_success:
                logger.error("❌ Retraining execution failed")
                result['error'] = exec_metrics.get('error', 'Unknown error')
                self.log_retraining_event(trigger, False, exec_metrics)
                return result
            
            # Step 4: Log event
            logger.info("\nSTEP 4: Logging retraining event...")
            event_id = self.log_retraining_event(trigger, exec_success, exec_metrics)
            result['event_id'] = event_id
            
            logger.info("=" * 80)
            logger.info("✅ RETRAINING PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            result['success'] = True
            return result
        
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            result['error'] = str(e)
            return result
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Model Retraining Executor")
    parser.add_argument("--reference-data", required=True, help="Reference training data path")
    parser.add_argument("--recent-data", help="Recent data path")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--training-script", default="train.py", help="Training script path")
    
    args = parser.parse_args()
    
    # Load data
    reference_data = pd.read_csv(args.reference_data)
    recent_data = pd.read_csv(args.recent_data) if args.recent_data else None
    
    # Create executor and run pipeline
    executor = RetrainingExecutor(
        project_root=args.project_root,
        training_script=args.training_script
    )
    
    result = executor.execute_full_retraining_pipeline(
        reference_data=reference_data,
        recent_data=recent_data
    )
    
    executor.close()
    
    # Print results
    print("\n" + "=" * 80)
    print("RETRAINING PIPELINE RESULTS")
    print("=" * 80)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
