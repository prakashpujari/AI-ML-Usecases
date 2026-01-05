"""
Data ingestion module for car price prediction
"""
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
import os

from ..utils.logger import setup_logger
from ..utils.config import DATA_DIR

logger = setup_logger(__name__)


class DataIngestion:
    """Handle data loading and initial processing"""
    
    def __init__(self, data_path: Path = None):
        self.data_path = data_path or DATA_DIR
    
    def load_training_data(self) -> pd.DataFrame:
        """Load training dataset"""
        train_path = self.data_path / 'trainset' / 'train.csv'
        logger.info(f"Loading training data from {train_path}")
        
        if not train_path.exists():
            raise FileNotFoundError(f"Training data not found at {train_path}")
        
        df = pd.read_csv(train_path)
        logger.info(f"Loaded {len(df)} training samples with {len(df.columns)} features")
        return df
    
    def load_test_data(self) -> Optional[pd.DataFrame]:
        """Load test dataset if available"""
        test_path = self.data_path / 'testset' / 'test.csv'
        
        if not test_path.exists():
            logger.warning(f"Test data not found at {test_path}")
            return None
        
        df = pd.read_csv(test_path)
        logger.info(f"Loaded {len(df)} test samples")
        return df
    
    def split_data(self, df: pd.DataFrame, target_col: str = 'price',
                   test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """Split data into train and test sets"""
        from sklearn.model_selection import train_test_split
        
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        logger.info(f"Split data: train={len(X_train)}, test={len(X_test)}")
        return X_train, X_test, y_train, y_test
    
    def save_data(self, df: pd.DataFrame, filename: str, dataset_type: str = 'trainset'):
        """Save processed data"""
        output_path = self.data_path / dataset_type / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        logger.info(f"Saved data to {output_path}")
