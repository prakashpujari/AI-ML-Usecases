"""
Data Validation Module for Car Price Prediction
Provides comprehensive data quality checks and validation
"""

import pandas as pd
import numpy as np
import logging
import json
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


@dataclass
class DataValidationResult:
    """Result of data validation checks"""
    is_valid: bool
    total_rows: int
    total_columns: int
    missing_values: Dict[str, int]
    duplicate_rows: int
    data_types: Dict[str, str]
    numeric_ranges: Dict[str, Dict[str, float]]
    categorical_distributions: Dict[str, Dict[str, int]]
    validation_errors: List[str]
    validation_warnings: List[str]


class DataValidator:
    """Validates data quality for ML training"""
    
    def __init__(
        self,
        min_rows: int = 100,
        max_missing_percent: float = 30.0,
        target_column: str = 'price'
    ):
        self.min_rows = min_rows
        self.max_missing_percent = max_missing_percent
        self.target_column = target_column
        self.errors = []
        self.warnings = []
    
    def validate(self, df: pd.DataFrame) -> DataValidationResult:
        """
        Perform comprehensive data validation
        
        Args:
            df: DataFrame to validate
            
        Returns:
            DataValidationResult with validation outcome and details
        """
        logging.info("Starting data validation...")
        
        self.errors = []
        self.warnings = []
        
        # Basic checks
        self._check_minimum_rows(df)
        self._check_target_column(df)
        self._check_missing_values(df)
        self._check_duplicates(df)
        self._check_data_types(df)
        
        # Domain-specific checks
        self._check_numeric_ranges(df)
        self._check_categorical_values(df)
        
        # Compile results
        result = DataValidationResult(
            is_valid=len(self.errors) == 0,
            total_rows=len(df),
            total_columns=len(df.columns),
            missing_values=df.isnull().sum().to_dict(),
            duplicate_rows=int(df.duplicated().sum()),
            data_types=df.dtypes.astype(str).to_dict(),
            numeric_ranges=self._get_numeric_ranges(df),
            categorical_distributions=self._get_categorical_distributions(df),
            validation_errors=self.errors,
            validation_warnings=self.warnings
        )
        
        if result.is_valid:
            logging.info("✓ Data validation passed")
        else:
            logging.error(f"✗ Data validation failed with {len(self.errors)} errors")
        
        return result
    
    def _check_minimum_rows(self, df: pd.DataFrame):
        """Check if dataset has minimum required rows"""
        if len(df) < self.min_rows:
            self.errors.append(
                f"Insufficient data: {len(df)} rows (minimum {self.min_rows} required)"
            )
        else:
            logging.info(f"✓ Row count check passed: {len(df)} rows")
    
    def _check_target_column(self, df: pd.DataFrame):
        """Check if target column exists"""
        cols_lower = {c.lower(): c for c in df.columns}
        if self.target_column.lower() not in cols_lower:
            self.errors.append(f"Target column '{self.target_column}' not found in dataset")
        else:
            target_col = cols_lower[self.target_column.lower()]
            # Check target column values
            if df[target_col].isnull().all():
                self.errors.append(f"Target column '{target_col}' contains only null values")
            elif df[target_col].isnull().any():
                null_percent = (df[target_col].isnull().sum() / len(df)) * 100
                self.warnings.append(
                    f"Target column contains {null_percent:.2f}% missing values"
                )
            logging.info(f"✓ Target column '{target_col}' check passed")
    
    def _check_missing_values(self, df: pd.DataFrame):
        """Check for excessive missing values"""
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        missing_percent = (missing_cells / total_cells) * 100
        
        if missing_percent > self.max_missing_percent:
            self.errors.append(
                f"Excessive missing data: {missing_percent:.2f}% (max {self.max_missing_percent}%)"
            )
        elif missing_percent > self.max_missing_percent / 2:
            self.warnings.append(
                f"High missing data: {missing_percent:.2f}%"
            )
        else:
            logging.info(f"✓ Missing values check passed: {missing_percent:.2f}%")
    
    def _check_duplicates(self, df: pd.DataFrame):
        """Check for duplicate rows"""
        n_duplicates = df.duplicated().sum()
        duplicate_percent = (n_duplicates / len(df)) * 100
        
        if duplicate_percent > 10:
            self.warnings.append(
                f"High duplicate rate: {duplicate_percent:.2f}% ({n_duplicates} rows)"
            )
        elif n_duplicates > 0:
            logging.info(f"ℹ Found {n_duplicates} duplicate rows ({duplicate_percent:.2f}%)")
    
    def _check_data_types(self, df: pd.DataFrame):
        """Validate data types are appropriate"""
        for col in df.columns:
            dtype = df[col].dtype
            
            # Check for object columns that might be numeric
            if dtype == 'object':
                # Try to convert to numeric
                try:
                    pd.to_numeric(df[col].dropna(), errors='raise')
                    self.warnings.append(
                        f"Column '{col}' is object type but could be numeric"
                    )
                except (ValueError, TypeError):
                    pass
        
        logging.info("✓ Data types check completed")
    
    def _check_numeric_ranges(self, df: pd.DataFrame):
        """Check numeric columns for outliers and invalid ranges"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) == 0:
                continue
            
            # Check for negative values in columns that should be positive
            if col.lower() in ['price', 'mileage', 'year', 'engine_size']:
                if (data < 0).any():
                    self.errors.append(
                        f"Column '{col}' contains negative values (expected positive)"
                    )
            
            # Check for extreme outliers
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            
            outliers = ((data < lower_bound) | (data > upper_bound)).sum()
            outlier_percent = (outliers / len(data)) * 100
            
            if outlier_percent > 5:
                self.warnings.append(
                    f"Column '{col}' has {outlier_percent:.2f}% extreme outliers"
                )
        
        logging.info("✓ Numeric ranges check completed")
    
    def _check_categorical_values(self, df: pd.DataFrame):
        """Check categorical columns for unexpected values"""
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        
        # Expected values for known categorical columns
        expected_values = {
            'brand': ['Toyota', 'Honda', 'Ford', 'BMW', 'Audi', 'Hyundai'],
            'condition': ['Excellent', 'Good', 'Fair', 'Poor'],
            'transmission': ['Automatic', 'Manual']
        }
        
        for col in categorical_cols:
            if col.lower() in expected_values:
                actual_values = set(df[col].dropna().unique())
                expected = set(expected_values[col.lower()])
                
                unexpected = actual_values - expected
                if unexpected:
                    self.warnings.append(
                        f"Column '{col}' contains unexpected values: {unexpected}"
                    )
            
            # Check for excessive unique values
            n_unique = df[col].nunique()
            if n_unique > len(df) * 0.5:
                self.warnings.append(
                    f"Column '{col}' has {n_unique} unique values (possibly should be numeric)"
                )
        
        logging.info("✓ Categorical values check completed")
    
    def _get_numeric_ranges(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Get min, max, mean, std for numeric columns"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        ranges = {}
        
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) > 0:
                ranges[col] = {
                    'min': float(data.min()),
                    'max': float(data.max()),
                    'mean': float(data.mean()),
                    'std': float(data.std()),
                    'median': float(data.median())
                }
        
        return ranges
    
    def _get_categorical_distributions(self, df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
        """Get value distributions for categorical columns"""
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        distributions = {}
        
        for col in categorical_cols:
            value_counts = df[col].value_counts().to_dict()
            # Limit to top 20 values
            distributions[col] = dict(list(value_counts.items())[:20])
        
        return distributions


def validate_training_data(data_path: str, output_path: str = None) -> DataValidationResult:
    """
    Validate training data and optionally save results
    
    Args:
        data_path: Path to training data CSV
        output_path: Optional path to save validation results JSON
        
    Returns:
        DataValidationResult
    """
    logging.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    validator = DataValidator(
        min_rows=100,
        max_missing_percent=30.0,
        target_column='price'
    )
    
    result = validator.validate(df)
    
    # Save results if output path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(asdict(result), f, indent=2)
        logging.info(f"Validation results saved to {output_path}")
    
    # Print summary
    print("\n" + "="*80)
    print("DATA VALIDATION SUMMARY")
    print("="*80)
    print(f"Status: {'✓ PASSED' if result.is_valid else '✗ FAILED'}")
    print(f"Total Rows: {result.total_rows}")
    print(f"Total Columns: {result.total_columns}")
    print(f"Duplicate Rows: {result.duplicate_rows}")
    print(f"\nErrors: {len(result.validation_errors)}")
    for error in result.validation_errors:
        print(f"  ✗ {error}")
    print(f"\nWarnings: {len(result.validation_warnings)}")
    for warning in result.validation_warnings:
        print(f"  ⚠ {warning}")
    print("="*80 + "\n")
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_validation.py <data_path> [output_path]")
        sys.exit(1)
    
    data_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "metrics/data_validation.json"
    
    result = validate_training_data(data_path, output_path)
    sys.exit(0 if result.is_valid else 1)
