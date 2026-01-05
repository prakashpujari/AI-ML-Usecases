# Car Price Prediction - Production ML Pipeline

## 📁 Project Structure

```
ml_car_price_predection/
├── src/                          # Source code
│   ├── data/                     # Data processing
│   │   ├── ingestion.py         # Data loading
│   │   ├── validation.py        # Data quality checks
│   │   └── preprocessing.py     # Data preprocessing
│   ├── features/                # Feature engineering
│   │   └── build_features.py   # Feature creation
│   ├── models/                  # Model code
│   │   ├── model.py            # Model definitions
│   │   ├── train.py            # Training logic
│   │   ├── evaluate.py         # Evaluation metrics
│   │   └── predict.py          # Prediction logic
│   ├── pipelines/              # ML pipelines
│   │   ├── training_pipeline.py    # Training workflow
│   │   ├── inference_pipeline.py   # Batch inference
│   │   └── monitoring_pipeline.py  # Model monitoring
│   ├── utils/                  # Utilities
│   │   ├── config.py          # Configuration
│   │   ├── logger.py          # Logging setup
│   │   ├── helpers.py         # Helper functions
│   │   └── db_utils.py        # Database utilities
│   └── tests/                 # Tests
│       ├── unit/             # Unit tests
│       ├── integration/      # Integration tests
│       └── e2e/             # End-to-end tests
│
├── airflow/                   # Airflow orchestration
│   ├── dags/
│   │   └── training_pipeline.py
│   └── plugins/
│
├── mlflow/                    # MLflow setup
│   ├── tracking/             # MLflow artifacts
│   ├── docker/              # MLflow Docker config
│   └── mlflow_server.sh    # Startup script
│
├── configs/                  # Configuration files
│   ├── training_config.yaml
│   ├── inference_config.yaml
│   └── airflow_config.yaml
│
├── deployment/              # Deployment configs
│   ├── dev/
│   ├── sit/
│   ├── uat/
│   └── prod/
│
├── models/                  # Model artifacts
│   ├── production/
│   ├── staging/
│   └── trained/
│
├── data/                   # Data storage
│   ├── trainset/
│   └── testset/
│
├── experiments/           # Experimentation
│   ├── notebooks/        # Jupyter notebooks
│   └── reports/         # Analysis reports
│
├── ci_cd/                # CI/CD pipelines
│   └── github_actions/
│
├── scripts/             # Utility scripts
│   ├── run_training.sh
│   └── run_inference.sh
│
├── requirements.txt    # Python dependencies
├── setup.py           # Package setup
├── Makefile          # Build automation
└── README.md        # This file
```

## 🚀 Quick Start

### Installation

```bash
# Install package
pip install -e .

# Or just requirements
pip install -r requirements.txt
```

### Training

```bash
# Using Makefile
make train

# Or directly
python -m src.pipelines.training_pipeline --model-type random_forest --n-estimators 100

# Using script
./scripts/run_training.sh
```

### Inference

```bash
# Batch prediction
python -m src.pipelines.inference_pipeline \
    --input data/testset/test.csv \
    --output predictions.csv

# Using script
./scripts/run_inference.sh data/testset/test.csv predictions.csv
```

## 📊 MLflow Tracking

Start MLflow server:

```bash
# Using script
cd mlflow
./mlflow_server.sh

# Or directly
mlflow server --backend-store-uri sqlite:///mlflow/tracking/mlflow.db \
              --default-artifact-root ./mlflow/tracking/artifacts \
              --host 0.0.0.0 --port 5000
```

Access UI: http://localhost:5000

## 🔄 Airflow Orchestration

Start Airflow (Astronomer):

```bash
astro dev start
```

Access UI: http://localhost:8080

DAG: `car_price_training_pipeline_v2`

## 🐳 Docker Deployment

```bash
# Development
make docker-up

# Or specific environment
cd deployment/dev
docker-compose -f docker-compose.dev.yml up

# Production
cd deployment/prod
docker-compose -f docker-compose.prod.yml up -d
```

## 🧪 Testing

```bash
# All tests
make test

# Specific test suites
pytest src/tests/unit/ -v
pytest src/tests/integration/ -v
pytest src/tests/e2e/ -v
```

## 📝 Configuration

All configurations are in `configs/`:

- `training_config.yaml` - Training parameters
- `inference_config.yaml` - Inference settings
- `airflow_config.yaml` - DAG configuration

## 🔍 Monitoring

Monitor model performance:

```python
from src.pipelines.monitoring_pipeline import ModelMonitor

monitor = ModelMonitor()
report = monitor.generate_monitoring_report()
```

## 📈 Model Registry

Models are automatically registered to MLflow with versioning:

- **Production**: `models/production/model.pkl`
- **Staging**: `models/staging/`
- **Trained**: `models/trained/`

## 🗄️ Database

PostgreSQL stores evaluation metrics:

- Model runs and versions
- Performance metrics
- Data quality checks
- Alerts and monitoring

Connection: See `configs/` or environment variable `DATABASE_URL`

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
make format

# Lint code
make lint

# Clean artifacts
make clean
```

## 📦 CI/CD

GitHub Actions workflow: `.github/workflows/ml_pipeline.yml`

Triggers:
- Push to main/develop
- Pull requests
- Daily schedule (2 AM)
- Manual dispatch

## 🔐 Environment Variables

```bash
export MLFLOW_TRACKING_URI=http://localhost:5000
export DATABASE_URL=postgresql://user:pass@localhost:5433/ml_evaluation
export ENV=development
```

## 📚 API Usage

### Training API

```python
from src.models.train import ModelTrainer

trainer = ModelTrainer(model_type='random_forest')
results = trainer.train(n_estimators=100, max_depth=20)
```

### Prediction API

```python
from src.models.predict import ModelPredictor

predictor = ModelPredictor(stage='production')
prediction = predictor.predict({
    'year': 2020,
    'km': 50000,
    'fuel_type': 'Petrol',
    'seller_type': 'Dealer',
    'transmission': 'Manual'
})
```

## 🏗️ Architecture

### Data Flow

```
Data Ingestion → Validation → Feature Engineering → Preprocessing → Model Training → Evaluation → Registration → Deployment
```

### Components

1. **Data Layer**: Ingestion, validation, preprocessing
2. **Feature Layer**: Feature engineering and transformation
3. **Model Layer**: Training, evaluation, prediction
4. **Pipeline Layer**: Orchestration and workflow
5. **Infrastructure Layer**: MLflow, Airflow, Docker, Kubernetes

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Run tests: `make test`
4. Format code: `make format`
5. Submit PR

## 📄 License

MIT License

## 👥 Team

ML Team - mailtopprakash01@gmail.com

## 🔗 Links

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Airflow Documentation](https://airflow.apache.org/docs/)
- [Project Deployment Guide](deployment/README.md)
