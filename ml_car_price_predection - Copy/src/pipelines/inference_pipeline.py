"""
Inference pipeline for batch predictions
"""
import pandas as pd
from pathlib import Path
from typing import Union

from ..models.predict import ModelPredictor
from ..utils.logger import setup_logger
from ..utils.config import DATA_DIR

logger = setup_logger(__name__)


class InferencePipeline:
    """Handle batch inference"""
    
    def __init__(self, model_stage: str = 'production'):
        self.predictor = ModelPredictor(stage=model_stage)
        logger.info(f"Inference pipeline initialized with {model_stage} model")
    
    def predict_batch(self, input_file: Path) -> pd.DataFrame:
        """Make predictions for batch of data"""
        logger.info(f"Loading data from {input_file}")
        
        # Load data
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} records for prediction")
        
        # Make predictions
        predictions = self.predictor.predict(df)
        
        # Add predictions to dataframe
        df['predicted_price'] = predictions
        
        logger.info("Batch predictions complete")
        return df
    
    def save_predictions(self, df: pd.DataFrame, output_file: Path):
        """Save predictions to file"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        logger.info(f"Predictions saved to {output_file}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run batch inference')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file')
    parser.add_argument('--model-stage', type=str, default='production',
                       choices=['production', 'staging', 'trained'])
    
    args = parser.parse_args()
    
    pipeline = InferencePipeline(model_stage=args.model_stage)
    results = pipeline.predict_batch(Path(args.input))
    pipeline.save_predictions(results, Path(args.output))
