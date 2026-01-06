
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,classification_report,confusion_matrix,precision_score
import sklearn
import joblib
import boto3
"""
Training script for a RandomForest classifier used with SageMaker/local runs.

This module trains a RandomForest model using CSV train/test files, saves
the trained model to `model.joblib` under the provided model directory, and
prints basic evaluation metrics on the test set.

The script expects the following (can be provided via SageMaker env vars):
- `SM_MODEL_DIR` -> model output directory
- `SM_CHANNEL_TRAIN` -> path to training data channel
- `SM_CHANNEL_TEST` -> path to testing data channel

Run as a script for local testing, or used by SageMaker during training.
"""

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_score
import sklearn
import joblib
import argparse
import os
import numpy as np
import pandas as pd


def model_fn(model_dir):
    """Load and return the trained model from `model_dir`.

    This function follows the SageMaker inference convention where the
    serving/container runtime calls `model_fn` to deserialize the model.

    Args:
        model_dir (str): Directory where `model.joblib` is stored.

    Returns:
        sklearn estimator: The deserialized model object.
    """
    clf = joblib.load(os.path.join(model_dir, "model.joblib"))
    return clf


if __name__ == "__main__":
    # Parse input arguments (hyperparameters and channel locations)
    print("[Info] Extracting arguments")
    parser = argparse.ArgumentParser()

    # Hyperparameters for the RandomForest model
    parser.add_argument("--n_estimators", type=int, default=100, help="Number of trees in the forest")
    parser.add_argument("--random_state", type=int, default=0, help="Random seed for reproducibility")

    # Directories: model output and data channels (SageMaker style env vars)
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR"), help="Model output directory")
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN"), help="Training data channel path")
    parser.add_argument("--test", type=str, default=os.environ.get("SM_CHANNEL_TEST"), help="Testing data channel path")
    parser.add_argument("--train-file", type=str, default="train-V-1.csv", help="Training CSV file name")
    parser.add_argument("--test-file", type=str, default="test-V-1.csv", help="Testing CSV file name")

    args, _ = parser.parse_known_args()

    # Report versions for reproducibility/debugging
    print("SKLearn Version: ", sklearn.__version__)
    print("Joblib Version: ", joblib.__version__)

    # Read CSV data from provided channels
    print("[INFO] Reading data")
    train_df = pd.read_csv(os.path.join(args.train, args.train_file))
    test_df = pd.read_csv(os.path.join(args.test, args.test_file))

    # Last column is assumed to be the label; all preceding columns are features
    features = list(train_df.columns)
    label = features.pop(-1)

    print("Building training and testing datasets")
    X_train = train_df[features]
    X_test = test_df[features]
    y_train = train_df[label]
    y_test = test_df[label]

    # Print dataset summary information
    print('Column order: ')
    print(features)
    print()
    print("Label column is: ", label)
    print()

    print("Data Shape: ")
    print("---- SHAPE OF TRAINING DATA (rows, cols) ----")
    print(X_train.shape)
    print(y_train.shape)
    print("---- SHAPE OF TESTING DATA (rows, cols) ----")
    print(X_test.shape)
    print(y_test.shape)

    # Initialize and train the RandomForest model
    print("Training RandomForest Model ....")
    model = RandomForestClassifier(n_estimators=args.n_estimators, random_state=args.random_state,
                                   verbose=2, n_jobs=1)

    model.fit(X_train, y_train)

    # Save the trained model for later inference
    model_path = os.path.join(args.model_dir, "model.joblib")
    joblib.dump(model, model_path)
    print("Model saved at " + model_path)

    # Evaluate on the test set and print metrics
    y_pred_test = model.predict(X_test)
    test_acc = accuracy_score(y_test, y_pred_test)
    test_rep = classification_report(y_test, y_pred_test)

    print()
    print("---- METRICS RESULTS FOR TESTING DATA ----")
    print("Total Rows are: ", X_test.shape[0])
    print('[TESTING] Model Accuracy is: ', test_acc)
    print('[TESTING] Testing Report: ')
    print(test_rep)


