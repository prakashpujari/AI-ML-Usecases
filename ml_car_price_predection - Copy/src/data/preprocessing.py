"""
Data preprocessing module
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from typing import Tuple, List

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DataPreprocessor:
    """Preprocess data for model training"""
    
    def __init__(self):
        self.preprocessor = None
        self.scaler = None
        self.numeric_features = []
        self.categorical_features = []
    
    def fit(self, X: pd.DataFrame) -> 'DataPreprocessor':
        """Fit preprocessor on training data"""
        # Identify feature types
        self.numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_features = X.select_dtypes(include=['object']).columns.tolist()
        
        logger.info(f"Numeric features: {self.numeric_features}")
        logger.info(f"Categorical features: {self.categorical_features}")
        
        # Create preprocessing pipeline
        self.preprocessor = ColumnTransformer(
            transformers=[
                ('num', 'passthrough', self.numeric_features),
                ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'),
                 self.categorical_features)
            ])
        
        # Fit preprocessor
        X_transformed = self.preprocessor.fit_transform(X)
        
        # Fit scaler
        self.scaler = StandardScaler()
        self.scaler.fit(X_transformed)
        
        logger.info("Preprocessor fitted successfully")
        return self
    
    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform data using fitted preprocessor"""
        if self.preprocessor is None or self.scaler is None:
            raise ValueError("Preprocessor not fitted. Call fit() first.")
        
        X_transformed = self.preprocessor.transform(X)
        X_scaled = self.scaler.transform(X_transformed)
        
        return X_scaled
    
    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """Fit and transform data"""
        self.fit(X)
        return self.transform(X)
    
    def get_feature_names(self) -> List[str]:
        """Get feature names after transformation"""
        if self.preprocessor is None:
            return []
        
        feature_names = []
        
        # Add numeric features
        feature_names.extend(self.numeric_features)
        
        # Add categorical features (one-hot encoded)
        if len(self.categorical_features) > 0:
            cat_encoder = self.preprocessor.named_transformers_['cat']
            cat_features = cat_encoder.get_feature_names_out(self.categorical_features)
            feature_names.extend(cat_features)
        
        return feature_names
