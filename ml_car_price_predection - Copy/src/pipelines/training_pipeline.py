"""
Training pipeline orchestration
"""
import argparse
from datetime import datetime

from ..models.train import ModelTrainer
from ..utils.logger import setup_logger
from ..utils.db_utils import get_db_connection

logger = setup_logger(__name__, f'training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')


def run_training_pipeline(
    model_type: str = 'random_forest',
    n_estimators: int = 100,
    max_depth: int = None,
    cv_folds: int = 5
):
    """Execute complete training pipeline"""
    logger.info("="*80)
    logger.info("STARTING TRAINING PIPELINE")
    logger.info("="*80)
    
    try:
        # Initialize trainer
        trainer = ModelTrainer(model_type=model_type)
        
        # Train model
        results = trainer.train(
            n_estimators=n_estimators,
            max_depth=max_depth,
            cv_folds=cv_folds,
            save_production=True
        )
        
        # Store results in database
        try:
            with get_db_connection() as db:
                run_id = results['run_id']
                metrics = results['metrics']
                
                db.insert_model_run(
                    run_id=run_id,
                    model_name='car_price_predictor',
                    trained_at=datetime.now(),
                    metadata={'model_type': model_type}
                )
                
                db.insert_metrics(run_id, metrics, metric_type='test')
                
                logger.info("Results stored in database successfully")
        except Exception as e:
            logger.error(f"Failed to store results in database: {e}")
        
        logger.info("="*80)
        logger.info("TRAINING PIPELINE COMPLETE")
        logger.info(f"Run ID: {results['run_id']}")
        logger.info(f"R² Score: {results['metrics']['r2_score']:.4f}")
        logger.info("="*80)
        
        return results
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train car price prediction model')
    parser.add_argument('--model-type', type=str, default='random_forest',
                       choices=['random_forest', 'ridge', 'lasso', 'decision_tree'])
    parser.add_argument('--n-estimators', type=int, default=100)
    parser.add_argument('--max-depth', type=int, default=None)
    parser.add_argument('--cv-folds', type=int, default=5)
    
    args = parser.parse_args()
    
    run_training_pipeline(
        model_type=args.model_type,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        cv_folds=args.cv_folds
    )
