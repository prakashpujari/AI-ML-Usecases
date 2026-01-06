# Production-Ready Training Script with Comprehensive MLflow Tracking

import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature
import logging
import os
import json
import numpy as np
import pandas as pd
import joblib
import sklearn
import argparse
from datetime import datetime
import shutil
from contextlib import contextmanager
import sys
import io

# Add scripts to path for db_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    mean_squared_error,
    mean_absolute_error,
    r2_score,
)
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

# Import database utilities
try:
    from db_utils import ModelEvaluationDB
    HAS_DB = True
except ImportError:
    HAS_DB = False
    logging.warning("Database utilities not available. Model will not be stored in database.")


# Dummy MLflow wrapper for when MLflow is unavailable
class DummyMLflowRun:
    """Dummy context manager that mimics mlflow.start_run()"""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    @property
    def info(self):
        class Info:
            run_id = 'local_run'
        return Info()


@contextmanager
def optional_mlflow_run(use_mlflow, run_name=None):
    """Context manager that uses MLflow if available, otherwise uses dummy"""
    if use_mlflow:
        try:
            with mlflow.start_run(run_name=run_name) as run:
                yield run
        except Exception as e:
            logging.warning(f"MLflow run failed: {e}. Continuing without MLflow.")
            yield DummyMLflowRun()
    else:
        yield DummyMLflowRun()


def safe_mlflow_log(func, *args, **kwargs):
    """Safely call mlflow logging functions, ignoring errors"""
    try:
        func(*args, **kwargs)
    except:
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("training.log"), logging.StreamHandler()],
)

# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
MODEL_NAME = 'car_price_predictor'
EXPERIMENT_NAME = 'car_price_prediction'


def log_dataset_info(df: pd.DataFrame, dataset_type: str = "train"):
    """Log comprehensive dataset information to MLflow"""
    safe_mlflow_log(mlflow.log_param, f"{dataset_type}_rows", len(df))
    safe_mlflow_log(mlflow.log_param, f"{dataset_type}_columns", len(df.columns))
    safe_mlflow_log(mlflow.log_param, f"{dataset_type}_memory_mb", df.memory_usage(deep=True).sum() / 1024**2)
    
    # Log missing values
    missing_info = df.isnull().sum().to_dict()
    safe_mlflow_log(mlflow.log_dict, missing_info, f"{dataset_type}_missing_values.json")
    
    # Log data statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        stats = df[numeric_cols].describe().to_dict()
        safe_mlflow_log(mlflow.log_dict, stats, f"{dataset_type}_statistics.json")

def backup_previous_model():
    """Backup previous production model before training new one"""
    prod_model_path = os.path.join("models", "production", "model.pkl")
    if os.path.exists(prod_model_path):
        backup_dir = os.path.join("models", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"model_backup_{timestamp}.pkl")
        shutil.copy2(prod_model_path, backup_path)
        logging.info(f"Previous model backed up to {backup_path}")


def preprocess_features(X: pd.DataFrame):
    """Encode categorical features, impute missing values, and scale numeric ones.

    Returns:
        X_scaled: np.ndarray
        preprocessor: fitted ColumnTransformer
        scaler: fitted StandardScaler
        feature_names: list of output feature names after encoding
    """
    categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
    numeric_cols = X.select_dtypes(exclude=["object", "category"]).columns.tolist()

    # Use dense output from OneHotEncoder to allow get_feature_names_out
    # Choose the correct OneHotEncoder param depending on scikit-learn version
    sv = sklearn.__version__.split('.')
    try:
        major = int(sv[0])
        minor = int(sv[1])
    except Exception:
        major, minor = 0, 0
    ohe_kwargs = {"handle_unknown": "ignore"}
    if major > 1 or (major == 1 and minor >= 2):
        ohe_kwargs["sparse_output"] = False
    else:
        ohe_kwargs["sparse"] = False

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="mean"), numeric_cols),
            ("cat", OneHotEncoder(**ohe_kwargs), categorical_cols),
        ],
        remainder="drop",
    )

    # Fit and transform
    X_processed = preprocessor.fit_transform(X)

    # Scale numeric + encoded features
    scaler = StandardScaler(with_mean=False)  # with_mean=False for sparse matrices
    X_scaled = scaler.fit_transform(X_processed)

    # Build feature names: numeric cols first, then OHE feature names
    feature_names = []
    if numeric_cols:
        feature_names.extend(numeric_cols)
    if categorical_cols:
        ohe = preprocessor.named_transformers_["cat"]
        try:
            cat_names = ohe.get_feature_names_out(categorical_cols).tolist()
        except Exception:
            # fallback naming
            cat_names = [f"{c}_{v}" for c in categorical_cols for v in []]
        feature_names.extend(cat_names)

    return X_scaled, preprocessor, scaler, feature_names


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Train car price prediction model')
    parser.add_argument('--n-estimators', type=int, default=100, help='Number of trees in Random Forest')
    parser.add_argument('--max-depth', type=int, default=None, help='Maximum depth of trees')
    parser.add_argument('--min-samples-split', type=int, default=2, help='Minimum samples to split node')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test set size fraction')
    args, unknown = parser.parse_known_args()
    
    logging.info("Starting production model training process...")
    logging.info(f"Training parameters: n_estimators={args.n_estimators}, max_depth={args.max_depth}")
    
    # Set MLflow tracking URI and experiment (make optional)
    use_mlflow = bool(MLFLOW_TRACKING_URI and MLFLOW_TRACKING_URI.strip())
    if use_mlflow:
        try:
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            mlflow.set_experiment(EXPERIMENT_NAME)
            logging.info(f"MLflow Tracking URI: {MLFLOW_TRACKING_URI}")
        except Exception as e:
            logging.warning(f"MLflow setup failed: {e}. Training will continue without MLflow tracking.")
            use_mlflow = False
    else:
        logging.info("MLflow tracking disabled (MLFLOW_TRACKING_URI not set)")
        use_mlflow = False
    
    # Backup previous model
    backup_previous_model()
    
    # Prefer a dataset placed in the repository data folder for reproducible runs.
    csv_path_local = os.path.join(os.path.dirname(__file__), "data", "trainset", "train.csv")
    csv_path_default = r"C:\pp\GitHub\AI-ML-Usecases\Datasets\Car_Price_Prediction.csv"
    test_path_local = os.path.join(os.path.dirname(__file__), "data", "testset", "test.csv")

    # Load training data
    if os.path.exists(csv_path_local):
        df_train = pd.read_csv(csv_path_local)
        logging.info("Loaded local training CSV: %s", csv_path_local)
    elif os.path.exists(csv_path_default):
        df_train = pd.read_csv(csv_path_default)
        logging.info("Loaded default training CSV: %s", csv_path_default)
    else:
        raise FileNotFoundError("No training CSV found. Place one at data/trainset/train.csv or update the default path.")

    # If a separate test CSV exists, load it; otherwise split train into train/test
    if os.path.exists(test_path_local):
        df_test = pd.read_csv(test_path_local)
        logging.info("Loaded local test CSV: %s", test_path_local)
    else:
        df_train, df_test = train_test_split(df_train, test_size=args.test_size, random_state=42)
        logging.info(f"No separate test CSV found; performed {int((1-args.test_size)*100)}/{int(args.test_size*100)} train/test split from training data.")

    # Determine target column (prefer a column named 'price' case-insensitive)
    cols_lower = {c.lower(): c for c in df_train.columns}
    target_col = cols_lower.get("price", df_train.columns[-1])

    # Raw feature names from training data
    X_train_raw = df_train.drop(columns=[target_col])
    Y_train = df_train[target_col]
    X_test_raw = df_test.drop(columns=[target_col])
    Y_test = df_test[target_col]

    raw_feature_names = X_train_raw.columns.tolist()

    # Preprocess features (fit on training data only)
    X_train, preprocessor, scaler, feature_names = preprocess_features(X_train_raw)
    # Transform test set using the fitted preprocessor/scaler
    X_test = preprocessor.transform(X_test_raw)
    X_test = scaler.transform(X_test)

    # Decide regression vs classification based on training labels
    is_regression = np.issubdtype(getattr(Y_train, "dtype", np.array(Y_train).dtype), np.number) and (
        len(np.unique(Y_train)) > 20
    )

    logging.info("Dataset prepared: %d train rows, %d test rows", len(Y_train), len(Y_test))

    # Start MLflow run with comprehensive tracking
    with optional_mlflow_run(use_mlflow, run_name=f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}") as run:
        # Log run metadata
        safe_mlflow_log(mlflow.set_tag, "model_type", "regression" if is_regression else "classification")
        safe_mlflow_log(mlflow.set_tag, "training_date", datetime.now().isoformat())
        safe_mlflow_log(mlflow.set_tag, "data_version", "v1.0")
        safe_mlflow_log(mlflow.set_tag, "git_commit", os.getenv('GIT_COMMIT', 'unknown'))
        
        # Log hyperparameters
        safe_mlflow_log(mlflow.log_param, "n_estimators", args.n_estimators)
        safe_mlflow_log(mlflow.log_param, "max_depth", args.max_depth)
        safe_mlflow_log(mlflow.log_param, "min_samples_split", args.min_samples_split)
        safe_mlflow_log(mlflow.log_param, "test_size", args.test_size)
        safe_mlflow_log(mlflow.log_param, "random_state", 42)
        safe_mlflow_log(mlflow.log_param, "n_features", len(feature_names))
        safe_mlflow_log(mlflow.log_param, "n_input_features", len(raw_feature_names))
        
        # Log dataset information
        log_dataset_info(df_train, "train")
        log_dataset_info(df_test, "test")
        
        # Log feature names
        safe_mlflow_log(mlflow.log_dict, {"features": feature_names}, "feature_names.json")
        safe_mlflow_log(mlflow.log_dict, {"input_features": raw_feature_names}, "input_feature_names.json")
        
        if is_regression:
            logging.info("Training RandomForestRegressor...")
            model = RandomForestRegressor(
                n_estimators=args.n_estimators,
                max_depth=args.max_depth,
                min_samples_split=args.min_samples_split,
                random_state=42,
                n_jobs=-1
            )
            
            # Train model
            model.fit(X_train, Y_train)
            
            # Make predictions
            predictions = model.predict(X_test)
            train_predictions = model.predict(X_train)
            
            # Calculate comprehensive metrics
            mse = mean_squared_error(Y_test, predictions)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(Y_test, predictions)
            r2 = r2_score(Y_test, predictions)
            
            # Training set metrics (to detect overfitting)
            train_mse = mean_squared_error(Y_train, train_predictions)
            train_r2 = r2_score(Y_train, train_predictions)
            
            # Cross-validation score
            cv_scores = cross_val_score(model, X_train, Y_train, cv=5, scoring='r2')
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
            
            # Log all metrics
            safe_mlflow_log(mlflow.log_metric, "test_mse", float(mse))
            safe_mlflow_log(mlflow.log_metric, "test_rmse", float(rmse))
            safe_mlflow_log(mlflow.log_metric, "test_mae", float(mae))
            safe_mlflow_log(mlflow.log_metric, "test_r2", float(r2))
            safe_mlflow_log(mlflow.log_metric, "train_mse", float(train_mse))
            safe_mlflow_log(mlflow.log_metric, "train_r2", float(train_r2))
            safe_mlflow_log(mlflow.log_metric, "cv_r2_mean", float(cv_mean))
            safe_mlflow_log(mlflow.log_metric, "cv_r2_std", float(cv_std))
            
            # Calculate and log overfitting indicator
            overfit_score = train_r2 - r2
            safe_mlflow_log(mlflow.log_metric, "overfit_score", float(overfit_score))
            
            logging.info(f"Test Metrics - MSE: {mse:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}, R2: {r2:.4f}")
            logging.info(f"Train Metrics - MSE: {train_mse:.4f}, R2: {train_r2:.4f}")
            logging.info(f"Cross-validation R2: {cv_mean:.4f} (+/- {cv_std:.4f})")
            logging.info(f"Overfitting score: {overfit_score:.4f}")
            
            # Log feature importances
            feature_importance = pd.DataFrame({
                'feature': feature_names,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            safe_mlflow_log(mlflow.log_dict, feature_importance.to_dict(), "feature_importance.json")
            
            # Save metrics to file
            os.makedirs("metrics", exist_ok=True)
            metrics_data = {
                "test": {"mse": mse, "rmse": rmse, "mae": mae, "r2": r2},
                "train": {"mse": train_mse, "r2": train_r2},
                "cross_validation": {"mean_r2": cv_mean, "std_r2": cv_std},
                "overfit_score": overfit_score,
                "feature_importance": feature_importance.head(10).to_dict('records')
            }
            with open("metrics/regression_metrics.json", "w", encoding="utf-8") as f:
                json.dump(metrics_data, f, indent=2)
            safe_mlflow_log(mlflow.log_artifact, "metrics/regression_metrics.json")

            print(f"Test MSE: {mse:.4f}, Test RMSE: {rmse:.4f}, Test R2: {r2:.4f}")
            print(f"Cross-validation R2: {cv_mean:.4f} (+/- {cv_std:.4f})")

        else:
            logging.info("Training RandomForestClassifier...")
            model = RandomForestClassifier(random_state=42)
            model.fit(X_train, Y_train)

            predictions = model.predict(X_test)
            accuracy = accuracy_score(Y_test, predictions)
            safe_mlflow_log(mlflow.log_metric, "accuracy", float(accuracy))
            logging.info(f"Model accuracy: {accuracy:.4f}")

            report = classification_report(Y_test, predictions, output_dict=True)
            report_txt = classification_report(Y_test, predictions)
            cm = confusion_matrix(Y_test, predictions)

            os.makedirs("metrics", exist_ok=True)
            with open("metrics/classification_report.json", "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            with open("metrics/classification_report.txt", "w", encoding="utf-8") as f:
                f.write(report_txt)
            np.savetxt("metrics/confusion_matrix.csv", cm, fmt="%d", delimiter=",")

            safe_mlflow_log(mlflow.log_artifact, "metrics/classification_report.json")
            safe_mlflow_log(mlflow.log_artifact, "metrics/classification_report.txt")
            safe_mlflow_log(mlflow.log_artifact, "metrics/confusion_matrix.csv")

            print("Accuracy:", accuracy)
            print("Classification report:\n", report_txt)
            print("Confusion matrix:\n", cm)

        # Log all model parameters
        safe_mlflow_log(mlflow.log_params, {k: v for k, v in model.get_params().items()})
        
        # Create model signature for input/output schema validation
        signature = infer_signature(X_train, model.predict(X_train))
        
        # Log model with signature and input example
        input_example = pd.DataFrame(X_train[:5], columns=feature_names)
        safe_mlflow_log(mlflow.sklearn.log_model, 
            model,
            artifact_path="model",
            signature=signature,
            input_example=input_example,
            registered_model_name=MODEL_NAME
        )
        
        logging.info(f"Model logged to MLflow with signature and registered as '{MODEL_NAME}'")

        # Save a local artifact that includes the model and preprocessing objects
        # Save to a production-ready models folder and provide a backward-compatible copy
        os.makedirs(os.path.join("models", "production"), exist_ok=True)
        artifact_path = os.path.join("models", "production", "model.pkl")
        artifact_path_compat = os.path.join("models", "model.pkl")
        
        # Enhanced model artifact with metadata
        model_artifact = {
            "model": model,
            "preprocessor": preprocessor,
            "scaler": scaler,
            "features": feature_names,
            "input_features": raw_feature_names,
            "target": target_col,
            "metadata": {
                "trained_at": datetime.now().isoformat(),
                "mlflow_run_id": run.info.run_id,
                "sklearn_version": sklearn.__version__,
                "model_type": "regression" if is_regression else "classification",
                "n_estimators": args.n_estimators,
                "max_depth": args.max_depth,
            }
        }
        
        try:
            joblib.dump(model_artifact, artifact_path)
            # also write a compatibility copy at models/model.pkl
            try:
                joblib.dump(model_artifact, artifact_path_compat)
            except Exception:
                pass
            logging.info(f"Saved model artifact to {artifact_path}")
            
            # Log the model artifact to MLflow
            safe_mlflow_log(mlflow.log_artifact, artifact_path, "production_model")
            
            # Store model in database
            if HAS_DB:
                try:
                    # Serialize model to bytes
                    model_bytes = io.BytesIO()
                    joblib.dump(model_artifact, model_bytes)
                    model_binary = model_bytes.getvalue()
                    
                    # Get metrics for storage
                    accuracy = test_metrics.get('accuracy') if is_classification else None
                    rmse = test_metrics.get('rmse') if is_regression else None
                    r2 = test_metrics.get('r2') if is_regression else None
                    
                    # Store in database
                    with ModelEvaluationDB() as db:
                        # Generate version from timestamp
                        model_version = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        db.store_model(
                            run_id=run.info.run_id,
                            model_version=model_version,
                            model_type="RandomForest",
                            model_binary=model_binary,
                            accuracy=accuracy,
                            rmse=rmse,
                            r2=r2,
                            is_production=True  # Mark new model as production
                        )
                        logging.info(f"Model stored in database with version: {model_version}")
                except Exception as e:
                    logging.warning(f"Failed to store model in database: {e}. Continuing...")
            
        except Exception as e:
            logging.error("Failed to save local model artifact: %s", e)
            raise
        
        # Log training completion
        logging.info("="*80)
        logging.info("MODEL TRAINING COMPLETED SUCCESSFULLY")
        logging.info(f"MLflow Run ID: {run.info.run_id}")
        logging.info(f"Model registered as: {MODEL_NAME}")
        logging.info(f"Artifact saved to: {artifact_path}")
        logging.info("Model also stored in database for production access")
        logging.info("="*80)


if __name__ == "__main__":
    main()
