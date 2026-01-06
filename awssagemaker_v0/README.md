# Mobile Price Classification — SageMaker + scikit-learn

This repository demonstrates how to prepare data, train a scikit-learn
RandomForest model, and run predictions for mobile price-range classification.
The repository supports both direct local training and SageMaker (local or
AWS) workflows. Use `research.ipynb` as a guided notebook, or follow the
instructions below for command-line / script-based usage.

Overview — what this guide covers
- Setup development environment
- Prepare data (create `train-V-1.csv` and `test-V-1.csv`)
- Train locally (using `script.py`) or via SageMaker
- Evaluate model and save `model.joblib`
- Run inference locally (load `model.joblib` and predict)
- (Optional) Deploy to SageMaker endpoint and invoke
- Cleanup and troubleshooting

## Prerequisites

- Python 3.8+ (examples use 3.11)
- Conda or virtualenv
- Docker Desktop (required for SageMaker local mode)
- AWS CLI configured (for AWS runs): `aws configure`

## Setup environment (PowerShell)

Create and activate a Conda env (or use venv):

```powershell
conda create -n mlops python=3.11 -y
conda activate mlops
# or with venv:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install Python dependencies:

```powershell
pip install -r requirements.txt
```

## Prepare data

1. Open `research.ipynb` and run the data-prep cells to load
   `mob_price_classification_train.csv`, split into train/test and write
   `train-V-1.csv` and `test-V-1.csv`.

2. Or run the same steps in a Python script: split the dataframe and
   save CSVs with the label column as the last column.

The notebook already includes the code to create `train-V-1.csv` and
`test-V-1.csv` in the project root.

## Train the model locally (fast)

You can train the RandomForest model directly using `script.py`. This is
useful for quick iterations without Docker/SageMaker.

```powershell
python script.py --train . --test . --train-file train-V-1.csv --test-file test-V-1.csv --model-dir ./Model/Train
```

What this does:
- Loads the CSVs from `--train`/`--test` paths
- Uses the last column as the label and all preceding columns as features
- Trains `RandomForestClassifier` with hyperparameters you can pass
- Saves the trained model to `./Model/Train/model.joblib`
- Prints test-set metrics (accuracy and classification report)

If you prefer the notebook SageMaker flow (local mode using Docker), set:

```powershell
$env:SAGEMAKER_INSTANCE_TYPE = 'local'
```

Then open `research.ipynb` and run the notebook cells. The notebook will
write `script.py` into the container and launch a local training container.

## Evaluate and inspect model

After training, `model.joblib` contains the fitted `RandomForestClassifier`.
You can load and inspect it in Python:

```python
import joblib
model = joblib.load('Model/Train/model.joblib')
print(model)

# example predict
import pandas as pd
sample = pd.read_csv('test-V-1.csv')
X_sample = sample.drop(columns=[sample.columns[-1]])
print(model.predict(X_sample.head(2)))
```

## Run inference locally without an endpoint

If you only need to make predictions locally, load `model.joblib` and call
`predict()` as shown above. For programmatic inference create a small script
`predict.py` (example):

```python
import joblib
import pandas as pd
model = joblib.load('Model/Train/model.joblib')
data = pd.read_csv('input.json')  # if JSON lines, adapt accordingly
preds = model.predict(data)
print(preds)
```

If `input.json` contains JSON array of rows, convert to DataFrame with the
same feature order used for training (column order is critical).

## Deploy to SageMaker (optional — incurs charges)

The notebook shows how to create an `SKLearnModel` and call
`model.deploy(...)`. High-level steps:

1. Ensure AWS credentials and region are configured.
2. Upload training CSVs to S3 (the notebook does this when `instance_type` is not local).
3. Run the estimator to create a training job; the job produces an S3 artifact.
4. Create an `SKLearnModel` pointing to the artifact S3 URI and call
   `deploy()` to create an endpoint.

Example (in the notebook):

```python
from sagemaker.sklearn.model import SKLearnModel
model = SKLearnModel(name=model_name, model_data=artifact, role=role_arn, entry_point='script.py', framework_version=FRAMEWORK_VERSION)
predictor = model.deploy(initial_instance_count=1, instance_type='ml.m4.xlarge', endpoint_name=endpoint_name)
```

Invoke the endpoint using the SageMaker `predictor` in the notebook:

```python
predictions = predictor.predict(testX[features][:2].values.tolist())
print(predictions)
```

Or invoke via AWS CLI (replace region and endpoint name):

```powershell
aws sagemaker-runtime invoke-endpoint --endpoint-name <endpoint_name> --region <region> --body fileb://input.json --content-type application/json output.json
```

Input format and feature order
- The inference payload must match the feature order used during training.
- If using JSON, send an array of arrays or array of objects matching the
  model's expected fields. The notebook shows how to extract `features` and
  uses the same ordering when preparing `input.json`.

## Cleanup (important)

- Delete the endpoint to avoid charges:

```powershell
aws sagemaker delete-endpoint --endpoint-name <endpoint_name>
aws sagemaker delete-endpoint-config --endpoint-config-name <endpoint_config_name>
aws sagemaker delete-model --model-name <model_name>
```

- Remove local generated files if desired:

```powershell
del model.tar.gz
del Model\Train\model.joblib
del train-V-1.csv
del test-V-1.csv
```

## Troubleshooting

- Docker local mode: ensure Docker Desktop is running and that the SageMaker
  SDK version you installed supports local mode.
- Endpoint 500 errors: check CloudWatch logs for the container; ensure
  `script.py` implements `model_fn` (it does) and that dependencies used
  in the container are available.
- Prediction mismatch: verify the JSON payload feature order exactly matches
  the training feature ordering printed by the notebook.

## Images
The `images/` folder contains illustrative GIFs showing training and
deployment flows. Embedded below for convenience (open full-size by
clicking the image):

### Model training & deploy
![Model training and deployment](images/ModelTrainAndDeployToAws.gif)

### Deploy endpoint demo
![Deploy endpoint demo](images/DeployEndpoint-aws.gif)

If the GIFs do not render in your viewer, open them directly from the
file system at `images/ModelTrainAndDeployToAws.gif` and
`images/DeployEndpoint-aws.gif`.

If you'd like, I can add a small `predict_local.py` script to the repo that
loads `model.joblib` and accepts JSON input from stdin or a file — want me
to add that?
