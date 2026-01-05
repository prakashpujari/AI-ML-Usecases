"""
MLflow Model Registry Management
Handles model versioning, promotion, and deployment lifecycle
"""

import mlflow
from mlflow.tracking import MlflowClient
from mlflow.entities.model_registry import ModelVersion
import logging
import os
from datetime import datetime
from typing import Optional, Dict, List
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
MODEL_NAME = 'car_price_predictor'


class ModelRegistry:
    """Manages ML model lifecycle in MLflow registry"""
    
    def __init__(self, tracking_uri: str = MLFLOW_TRACKING_URI):
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient()
        logging.info(f"Connected to MLflow at {tracking_uri}")
    
    def get_latest_model_version(self, model_name: str, stage: Optional[str] = None) -> Optional[ModelVersion]:
        """
        Get the latest version of a model, optionally filtered by stage
        
        Args:
            model_name: Name of the registered model
            stage: Optional stage filter (None, Staging, Production, Archived)
            
        Returns:
            ModelVersion or None if not found
        """
        try:
            if stage:
                versions = self.client.get_latest_versions(model_name, stages=[stage])
            else:
                versions = self.client.search_model_versions(f"name='{model_name}'")
            
            if versions:
                latest = max(versions, key=lambda v: int(v.version))
                logging.info(f"Found model {model_name} version {latest.version} (stage: {latest.current_stage})")
                return latest
            return None
        except Exception as e:
            logging.error(f"Error getting model version: {e}")
            return None
    
    def promote_model(
        self, 
        model_name: str, 
        version: str, 
        stage: str,
        archive_existing: bool = True
    ) -> bool:
        """
        Promote a model version to a specific stage
        
        Args:
            model_name: Name of the registered model
            version: Version number to promote
            stage: Target stage (Staging, Production, Archived)
            archive_existing: Whether to archive existing models in target stage
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logging.info(f"Promoting {model_name} version {version} to {stage}")
            
            # Archive existing models in the target stage if requested
            if archive_existing and stage in ['Staging', 'Production']:
                existing = self.client.get_latest_versions(model_name, stages=[stage])
                for model in existing:
                    self.client.transition_model_version_stage(
                        name=model_name,
                        version=model.version,
                        stage="Archived"
                    )
                    logging.info(f"Archived existing version {model.version}")
            
            # Promote new version
            self.client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage
            )
            
            logging.info(f"✓ Successfully promoted version {version} to {stage}")
            return True
            
        except Exception as e:
            logging.error(f"Error promoting model: {e}")
            return False
    
    def compare_models(
        self, 
        model_name: str,
        version1: str,
        version2: str,
        metric: str = 'test_r2'
    ) -> Dict:
        """
        Compare two model versions based on metrics
        
        Args:
            model_name: Name of the registered model
            version1: First version to compare
            version2: Second version to compare
            metric: Metric to compare (default: test_r2)
            
        Returns:
            Dictionary with comparison results
        """
        try:
            v1_details = self.client.get_model_version(model_name, version1)
            v2_details = self.client.get_model_version(model_name, version2)
            
            # Get metrics from runs
            v1_run = self.client.get_run(v1_details.run_id)
            v2_run = self.client.get_run(v2_details.run_id)
            
            v1_metric = v1_run.data.metrics.get(metric, 0)
            v2_metric = v2_run.data.metrics.get(metric, 0)
            
            comparison = {
                'model_name': model_name,
                'version1': {
                    'version': version1,
                    'stage': v1_details.current_stage,
                    'metric': v1_metric,
                    'run_id': v1_details.run_id
                },
                'version2': {
                    'version': version2,
                    'stage': v2_details.current_stage,
                    'metric': v2_metric,
                    'run_id': v2_details.run_id
                },
                'metric_name': metric,
                'improvement': v2_metric - v1_metric,
                'improvement_percent': ((v2_metric - v1_metric) / v1_metric * 100) if v1_metric != 0 else 0,
                'better_version': version2 if v2_metric > v1_metric else version1
            }
            
            logging.info(f"Comparison: v{version1}={v1_metric:.4f} vs v{version2}={v2_metric:.4f}")
            return comparison
            
        except Exception as e:
            logging.error(f"Error comparing models: {e}")
            return {}
    
    def evaluate_promotion_criteria(
        self,
        model_name: str,
        version: str,
        min_r2: float = 0.7,
        max_overfit: float = 0.15,
        compare_to_production: bool = True
    ) -> Dict:
        """
        Evaluate if a model version meets promotion criteria
        
        Args:
            model_name: Name of the registered model
            version: Version to evaluate
            min_r2: Minimum R2 score required
            max_overfit: Maximum acceptable overfitting score
            compare_to_production: Whether to compare with production model
            
        Returns:
            Dictionary with evaluation results and recommendation
        """
        try:
            model_version = self.client.get_model_version(model_name, version)
            run = self.client.get_run(model_version.run_id)
            metrics = run.data.metrics
            
            # Get key metrics
            test_r2 = metrics.get('test_r2', 0)
            overfit_score = metrics.get('overfit_score', 0)
            cv_r2_mean = metrics.get('cv_r2_mean', 0)
            
            # Evaluate criteria
            passes_r2 = test_r2 >= min_r2
            passes_overfit = overfit_score <= max_overfit
            passes_cv = cv_r2_mean >= min_r2 - 0.05
            
            evaluation = {
                'model_name': model_name,
                'version': version,
                'metrics': {
                    'test_r2': test_r2,
                    'overfit_score': overfit_score,
                    'cv_r2_mean': cv_r2_mean
                },
                'criteria': {
                    'min_r2': min_r2,
                    'max_overfit': max_overfit
                },
                'checks': {
                    'r2_check': passes_r2,
                    'overfit_check': passes_overfit,
                    'cv_check': passes_cv
                },
                'passes_all': passes_r2 and passes_overfit and passes_cv,
                'recommendation': None,
                'comparison_to_production': None
            }
            
            # Compare with production if requested
            if compare_to_production:
                prod_model = self.get_latest_model_version(model_name, stage='Production')
                if prod_model:
                    comparison = self.compare_models(
                        model_name,
                        prod_model.version,
                        version,
                        metric='test_r2'
                    )
                    evaluation['comparison_to_production'] = comparison
                    
                    # Only promote if new model is better
                    if comparison.get('improvement', 0) > 0:
                        evaluation['recommendation'] = 'Promote to Production'
                    else:
                        evaluation['recommendation'] = 'Keep current Production model'
                        evaluation['passes_all'] = False
                else:
                    evaluation['recommendation'] = 'Promote to Production (no existing model)'
            else:
                if evaluation['passes_all']:
                    evaluation['recommendation'] = 'Promote to Staging'
                else:
                    evaluation['recommendation'] = 'Do not promote'
            
            logging.info(f"Evaluation: {evaluation['recommendation']}")
            return evaluation
            
        except Exception as e:
            logging.error(f"Error evaluating promotion criteria: {e}")
            return {}
    
    def get_model_lineage(self, model_name: str) -> List[Dict]:
        """
        Get the full lineage of a model including all versions
        
        Args:
            model_name: Name of the registered model
            
        Returns:
            List of dictionaries with version details
        """
        try:
            versions = self.client.search_model_versions(f"name='{model_name}'")
            
            lineage = []
            for version in sorted(versions, key=lambda v: int(v.version), reverse=True):
                run = self.client.get_run(version.run_id)
                
                lineage.append({
                    'version': version.version,
                    'stage': version.current_stage,
                    'created_at': version.creation_timestamp,
                    'run_id': version.run_id,
                    'metrics': run.data.metrics,
                    'tags': dict(run.data.tags)
                })
            
            return lineage
            
        except Exception as e:
            logging.error(f"Error getting model lineage: {e}")
            return []
    
    def auto_promote_best_model(
        self,
        model_name: str,
        min_r2: float = 0.7,
        max_overfit: float = 0.15
    ) -> bool:
        """
        Automatically evaluate and promote the best model version
        
        Args:
            model_name: Name of the registered model
            min_r2: Minimum R2 score required
            max_overfit: Maximum acceptable overfitting score
            
        Returns:
            True if promotion occurred, False otherwise
        """
        try:
            # Get the latest None stage model (newly registered)
            versions = self.client.search_model_versions(f"name='{model_name}'")
            none_versions = [v for v in versions if v.current_stage == 'None']
            
            if not none_versions:
                logging.info("No new models to evaluate")
                return False
            
            latest_new = max(none_versions, key=lambda v: int(v.version))
            
            # Evaluate promotion criteria
            evaluation = self.evaluate_promotion_criteria(
                model_name,
                latest_new.version,
                min_r2=min_r2,
                max_overfit=max_overfit,
                compare_to_production=True
            )
            
            # Save evaluation report
            os.makedirs("metrics", exist_ok=True)
            eval_path = f"metrics/promotion_evaluation_v{latest_new.version}.json"
            with open(eval_path, 'w') as f:
                json.dump(evaluation, f, indent=2)
            logging.info(f"Evaluation report saved to {eval_path}")
            
            # Promote if criteria met
            if evaluation.get('passes_all'):
                recommendation = evaluation.get('recommendation', '')
                
                if 'Production' in recommendation:
                    self.promote_model(model_name, latest_new.version, 'Production')
                    return True
                elif 'Staging' in recommendation:
                    self.promote_model(model_name, latest_new.version, 'Staging')
                    return True
            
            logging.info("Model did not meet promotion criteria")
            return False
            
        except Exception as e:
            logging.error(f"Error in auto-promotion: {e}")
            return False


def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MLflow Model Registry Management')
    parser.add_argument('--action', required=True, 
                       choices=['promote', 'compare', 'evaluate', 'lineage', 'auto-promote'],
                       help='Action to perform')
    parser.add_argument('--model-name', default=MODEL_NAME, help='Model name')
    parser.add_argument('--version', help='Model version')
    parser.add_argument('--version2', help='Second model version (for compare)')
    parser.add_argument('--stage', choices=['Staging', 'Production', 'Archived'], 
                       help='Target stage (for promote)')
    parser.add_argument('--min-r2', type=float, default=0.7, help='Minimum R2 for promotion')
    parser.add_argument('--max-overfit', type=float, default=0.15, 
                       help='Maximum overfit score for promotion')
    
    args = parser.parse_args()
    
    registry = ModelRegistry()
    
    if args.action == 'promote':
        if not args.version or not args.stage:
            print("Error: --version and --stage required for promote action")
            return
        registry.promote_model(args.model_name, args.version, args.stage)
    
    elif args.action == 'compare':
        if not args.version or not args.version2:
            print("Error: --version and --version2 required for compare action")
            return
        result = registry.compare_models(args.model_name, args.version, args.version2)
        print(json.dumps(result, indent=2))
    
    elif args.action == 'evaluate':
        if not args.version:
            print("Error: --version required for evaluate action")
            return
        result = registry.evaluate_promotion_criteria(
            args.model_name, args.version, 
            min_r2=args.min_r2, max_overfit=args.max_overfit
        )
        print(json.dumps(result, indent=2))
    
    elif args.action == 'lineage':
        lineage = registry.get_model_lineage(args.model_name)
        print(json.dumps(lineage, indent=2))
    
    elif args.action == 'auto-promote':
        success = registry.auto_promote_best_model(
            args.model_name,
            min_r2=args.min_r2,
            max_overfit=args.max_overfit
        )
        print(f"Auto-promotion: {'Success' if success else 'No promotion'}")


if __name__ == "__main__":
    main()
