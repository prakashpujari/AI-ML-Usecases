"""
Feature engineering module
"""
import pandas as pd
import numpy as np
from typing import List

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class FeatureEngineer:
    """Build and engineer features for model training"""
    
    def __init__(self):
        self.feature_names = []
    
    def create_age_feature(self, df: pd.DataFrame, year_col: str = 'year',
                          current_year: int = 2026) -> pd.DataFrame:
        """Create car age feature"""
        df = df.copy()
        df['car_age'] = current_year - df[year_col]
        logger.info("Created car_age feature")
        return df
    
    def create_km_per_year(self, df: pd.DataFrame, km_col: str = 'km',
                          age_col: str = 'car_age') -> pd.DataFrame:
        """Create average kilometers per year feature"""
        df = df.copy()
        df['km_per_year'] = df[km_col] / (df[age_col] + 1)  # +1 to avoid division by zero
        logger.info("Created km_per_year feature")
        return df
    
    def create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features"""
        df = df.copy()
        
        # Example interactions
        if 'year' in df.columns and 'km' in df.columns:
            df['year_km_interaction'] = df['year'] * df['km'] / 1000000
        
        logger.info("Created interaction features")
        return df
    
    def create_categorical_combinations(self, df: pd.DataFrame,
                                       cols: List[str]) -> pd.DataFrame:
        """Create combined categorical features"""
        df = df.copy()
        
        if len(cols) >= 2:
            df[f"{'_'.join(cols)}_combined"] = df[cols[0]].astype(str)
            for col in cols[1:]:
                df[f"{'_'.join(cols)}_combined"] += '_' + df[col].astype(str)
        
        logger.info(f"Created combined categorical feature from {cols}")
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all feature engineering steps"""
        logger.info("Starting feature engineering...")
        
        df = self.create_age_feature(df)
        df = self.create_km_per_year(df)
        df = self.create_interaction_features(df)
        
        logger.info(f"Feature engineering complete. Total features: {len(df.columns)}")
        self.feature_names = df.columns.tolist()
        
        return df
