# Final Training Script with Robust Preprocessing

from pyexpat import features
import mlflow
import logging
import os
import json
import numpy as np
import pandas as pd

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    mean_squared_error,
    r2_score,
)
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
import mlflow.sklearn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("training.log"), logging.StreamHandler()],
)


def preprocess_features(X: pd.DataFrame) -> np.ndarray:
    """Encode categorical features, impute missing values, and scale numeric ones."""
    categorical_cols = X.select_dtypes(include=["object"]).columns
    numeric_cols = X.select_dtypes(exclude=["object"]).columns

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="mean"), numeric_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
        ]
    )

    # Fit and transform
    X_processed = preprocessor.fit_transform(X)

    # Scale numeric + encoded features
    scaler = StandardScaler(with_mean=False)  # with_mean=False for sparse matrices
    X_scaled = scaler.fit_transform(X_processed)

    return X_scaled


def main():
    logging.info("Starting model training process....")

    csv_path = r"C:\pp\GitHub\AI-ML-Usecases\Datasets\Car_Price_Prediction.csv"
    if os.path.exists(csv_path):
        car_data = pd.read_csv(csv_path)
        logging.info("Car data loaded successfully. Head:\n%s", car_data.head().to_string())

        target_col = "price" if "price" in car_data.columns else car_data.columns[-1]
        X = car_data.drop(columns=[target_col])
        y = car_data[target_col]

        # 🔧 FIX: preprocess features (encode categoricals, impute, scale)
        X = preprocess_features(X)

    else:
        logging.warning("CSV dataset not found at %s — falling back to Iris dataset", csv_path)
        iris = load_iris()
        X = iris.data
        y = iris.target

    # Decide regression vs classification
    is_regression = np.issubdtype(getattr(y, "dtype", np.array(y).dtype), np.number) and (
        len(np.unique(y)) > 20
    )

    # Train/test split
    if is_regression:
        X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.2, random_state=60)
    else:
        X_train, X_test, Y_train, Y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

    logging.info("Dataset loaded and split into train and test sets.")

    with mlflow.start_run() as run:
        if is_regression:
            logging.info("Training RandomForestRegressor...")
            model = RandomForestRegressor(random_state=42)
            model.fit(X_train, Y_train)
            logging.info(f" X_test[0] ---> {X_test[0]}")
          #  car_info = X_test[0]
           # car_info = X_test[0]   # first row of the numpy array
            #print('first row : -->',car_info)
            # Create a single-row DataFrame
            import pandas as pd1
            csv_path = r"C:\pp\GitHub\AI-ML-Usecases\Datasets\Car_Price_Prediction.csv"
            car_data = pd1.read_csv(csv_path)
            print('car data',car_data.head())

# 7 features
            features = ['Brand', 'Model', 'Year', 'EngineSize', 'Mileage', 'FuelType', 'Transmission']

# 7 values
            car_info = pd.DataFrame([['Ford', 'Model C', 2014, 1.7, 94799, 'Electric', 'automatic']], columns=features)

            print(car_info)
            print("Prediction value:", model.predict(car_info))
            print(f"Prediction value: {model.predict([car_info])}")


            logging.info(f" Car info : {car_info} ")

            predictions = model.predict(X_test)
            mse = mean_squared_error(Y_test, predictions)
            r2 = r2_score(Y_test, predictions)
           


            mlflow.log_metric("mse", float(mse))
            mlflow.log_metric("r2", float(r2))
            logging.info(f"Regression MSE: {mse:.4f}, R2: {r2:.4f}")

            os.makedirs("metrics", exist_ok=True)
            with open("metrics/regression_metrics.json", "w", encoding="utf-8") as f:
                json.dump({"mse": mse, "r2": r2}, f, indent=2)
            mlflow.log_artifact("metrics/regression_metrics.json")

            print("MSE:", mse)
            print("R2:", r2)

        else:
            logging.info("Training RandomForestClassifier...")
            model = RandomForestClassifier(random_state=42)
            model.fit(X_train, Y_train)

            predictions = model.predict(X_test)
            accuracy = accuracy_score(Y_test, predictions)
            mlflow.log_metric("accuracy", float(accuracy))
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

            mlflow.log_artifact("metrics/classification_report.json")
            mlflow.log_artifact("metrics/classification_report.txt")
            mlflow.log_artifact("metrics/confusion_matrix.csv")

            print("Accuracy:", accuracy)
            print("Classification report:\n", report_txt)
            print("Confusion matrix:\n", cm)

        # Log model params and model itself
        mlflow.log_params({k: v for k, v in model.get_params().items()})
        mlflow.sklearn.log_model(model, name="model")


if __name__ == "__main__":
    main()