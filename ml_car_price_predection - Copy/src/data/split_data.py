"""Split raw CSV into train/test and save under data/trainset and data/testset.

Usage:
    python scripts/split_data.py --source path/to/raw.csv --test-size 0.2 --random-state 42

If no --source is provided, the script will look for the default dataset used by the repo.
"""
import argparse
import os
import pandas as pd
from sklearn.model_selection import train_test_split

DEFAULT_PATH = r"C:\pp\GitHub\AI-ML-Usecases\Datasets\Car_Price_Prediction.csv"
ROOT = os.path.dirname(os.path.dirname(__file__))
TRAIN_OUT = os.path.join(ROOT, "data", "trainset", "train.csv")
TEST_OUT = os.path.join(ROOT, "data", "testset", "test.csv")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=str, default=None)
    p.add_argument("--test-size", type=float, default=0.2)
    p.add_argument("--random-state", type=int, default=42)
    args = p.parse_args()

    src = args.source or os.path.join(ROOT, "data", "raw.csv")
    if not os.path.exists(src):
        if os.path.exists(DEFAULT_PATH):
            src = DEFAULT_PATH
        else:
            raise FileNotFoundError(f"No source CSV found at {src} and default {DEFAULT_PATH} is missing.")

    df = pd.read_csv(src)
    os.makedirs(os.path.dirname(TRAIN_OUT), exist_ok=True)
    os.makedirs(os.path.dirname(TEST_OUT), exist_ok=True)

    train, test = train_test_split(df, test_size=args.test_size, random_state=args.random_state)
    train.to_csv(TRAIN_OUT, index=False)
    test.to_csv(TEST_OUT, index=False)
    print(f"Wrote train->{TRAIN_OUT} ({len(train)} rows) and test->{TEST_OUT} ({len(test)} rows)")


if __name__ == "__main__":
    main()
