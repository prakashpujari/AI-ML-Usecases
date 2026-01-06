# Training source code

import mlflow
import logging
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import json
import numpy as np
import os
import mlflow.sklearn


# Configure logging for both console and file output. This helps with debugging and
# keeps a persistent log of training runs in `training.log`.
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("training.log"),
                        logging.StreamHandler()
                    ]
                    )


def main():
    """Main entrypoint for training.

    Steps:
    1. Load dataset
    2. Split into train/test (stratified to preserve class balance)
    3. Train a RandomForestClassifier
    4. Evaluate and log metrics/artifacts to MLflow
    5. Save the trained model as an MLflow artifact
    """

    logging.info("Starting model training process....")
    logging.info("Loading the iris dataset...")

    # Load Iris dataset from scikit-learn (small example dataset with 3 classes)
    iris = load_iris()

    # Split data into train/test. Use `stratify` so each class keeps its proportional
    # representation in train and test sets. `random_state` ensures reproducibility.
    X_train, X_test, Y_train, Y_test = train_test_split(
        iris.data, iris.target, test_size=0.2, random_state=42, stratify=iris.target
    )

    logging.info("Dataset loaded and split into train and test sets.")

    # Start an MLflow run. All metrics, params and artifacts logged inside this
    # context will be grouped under a single run in the MLflow tracking server.
    with mlflow.start_run() as run:
        logging.info("Training the RandomForestClassifier model...")

        # Instantiate and train the model. Set `random_state` for reproducibility.
        model = RandomForestClassifier(random_state=42)
        model.fit(X_train, Y_train)
        logging.info("Model training completed.")

        # Make predictions on the test set and compute accuracy
        predictions = model.predict(X_test)
        accuracy = accuracy_score(Y_test, predictions)

        # Log a numeric metric to MLflow so you can compare runs later.
        # Convert to float to ensure JSON-serializable types.
        mlflow.log_metric("accuracy", float(accuracy))
        logging.info(f"Model accuracy: {accuracy:4f}")

        # Log model hyperparameters (all estimator params) so runs are reproducible
        # and comparable. `get_params()` returns a dict of parameter names -> values.
        mlflow.log_params({k: v for k, v in model.get_params().items()})

        # Create human- and machine-readable classification reports. The JSON
        # (`output_dict=True`) is useful for programmatic checks; the text form
        # is convenient for quick human inspection.
        report = classification_report(Y_test, predictions, output_dict=True)
        report_txt = classification_report(Y_test, predictions)
        cm = confusion_matrix(Y_test, predictions)

        # Ensure the `metrics` directory exists locally, write artifacts there,
        # and then upload them to MLflow as run artifacts. This keeps run-related
        # files organized on disk and in MLflow's artifact store.
        os.makedirs("metrics", exist_ok=True)
        report_path = os.path.join("metrics", "classification_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        report_txt_path = os.path.join("metrics", "classification_report.txt")
        with open(report_txt_path, "w", encoding="utf-8") as f:
            f.write(report_txt)

        cm_path = os.path.join("metrics", "confusion_matrix.csv")
        # Save confusion matrix as CSV of integers for easy loading in spreadsheets
        # or other tools.
        np.savetxt(cm_path, cm, fmt="%d", delimiter=",")

        # Upload the generated metric files to MLflow so they are attached to the run
        # and persist beyond the local workspace.
        mlflow.log_artifact(report_path)
        mlflow.log_artifact(report_txt_path)
        mlflow.log_artifact(cm_path)

        # Save and log the trained model as an MLflow artifact. This makes it easy
        # to load the model later using `mlflow.sklearn.load_model` and to deploy it.
        mlflow.sklearn.log_model(model, "model")

        # Also print a concise summary to the console so users see immediate
        # feedback without opening MLflow UI.
        print("Accuracy:", accuracy)
        print("Classification report:\n", report_txt)
        print("Confusion matrix:\n", cm)


if __name__ == "__main__":
    # When run as a script, execute the main training flow. Importing this file
    # as a module won't trigger training automatically (good for tests).
    main()

