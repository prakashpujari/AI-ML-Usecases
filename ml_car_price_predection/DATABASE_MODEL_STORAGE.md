# 🗄️ Database Model Storage Guide

Store trained ML models directly in PostgreSQL for production deployment, versioning, and monitoring.

## Overview

The model storage system provides:

- **Centralized Storage**: Store serialized models in PostgreSQL database
- **Version Control**: Track multiple model versions with automatic versioning
- **Production Flagging**: Mark specific versions as production models
- **Performance Metrics**: Store accuracy, RMSE, R² scores with each model
- **Prediction History**: Track all predictions for monitoring and validation
- **Easy Retrieval**: Load models from database with automatic fallback to filesystem

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  train.py          predict_api.py      streamlit_app.py        │
│  (Stores)          (Loads)             (Loads)                 │
└──────┬──────────────────┬──────────────────┬────────────────────┘
       │                  │                  │
       └──────────────────┴──────────────────┘
                    ↓
       ┌──────────────────────────────┐
       │   model_loader.py            │
       │   (Smart Loading Logic)      │
       │   - Try Database             │
       │   - Fallback to Filesystem   │
       │   - Cache Models             │
       └──────────────────────────────┘
                    ↓
       ┌──────────────────────────────┐
       │   db_utils.py                │
       │   (Database Operations)      │
       │   - store_model()            │
       │   - get_model()              │
       │   - list_models()            │
       │   - store_prediction()       │
       └──────────────────────────────┘
                    ↓
       ┌──────────────────────────────┐
       │    PostgreSQL Database       │
       │  ┌──────────────────────┐    │
       │  │ model_artifacts      │    │
       │  │ model_predictions    │    │
       │  │ model_runs           │    │
       │  │ model_metrics        │    │
       │  └──────────────────────┘    │
       └──────────────────────────────┘
```

## Database Tables

### model_artifacts
Stores serialized trained models

```sql
CREATE TABLE model_artifacts (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(255) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(100) NOT NULL,       -- e.g., RandomForest
    model_binary BYTEA NOT NULL,             -- Serialized model (joblib)
    model_size_bytes INTEGER,
    accuracy_score FLOAT,
    rmse_score FLOAT,
    r2_score FLOAT,
    is_production BOOLEAN DEFAULT FALSE,
    deployment_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(run_id, model_version)
);
```

**Key Fields**:
- `model_binary`: Pickle-serialized model bytes
- `model_version`: Auto-generated version string (YYYYMMDD_HHMMSS)
- `is_production`: Boolean flag for production model
- `accuracy_score`, `rmse_score`, `r2_score`: Performance metrics

### model_predictions
Tracks all predictions for monitoring

```sql
CREATE TABLE model_predictions (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) NOT NULL,
    input_features JSONB NOT NULL,
    predicted_value FLOAT NOT NULL,
    actual_value FLOAT,
    confidence_score FLOAT,
    prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Usage Examples

### Training & Storing Models

**In train.py** (automatic):
```python
with ModelEvaluationDB() as db:
    # Serialize model to bytes
    model_bytes = io.BytesIO()
    joblib.dump(model_artifact, model_bytes)
    model_binary = model_bytes.getvalue()
    
    # Store in database
    db.store_model(
        run_id="mlflow-run-id",
        model_version="20260105_143022",
        model_type="RandomForest",
        model_binary=model_binary,
        accuracy=0.85,
        rmse=3500.25,
        r2=0.92,
        is_production=True  # Mark as production
    )
```

### Loading Models for Prediction

**Option 1: Using ModelLoader class**
```python
from models.model_loader import ModelLoader

loader = ModelLoader()

# Load production model
prod_model = loader.load_production_model()

# Load specific version
v1_model = loader.load_model_by_version("20260105_143022")

# Load latest model
latest_model = loader.load_latest_model()

# List available models
models = loader.list_available_models(limit=10)

loader.close()
```

**Option 2: Using convenience functions**
```python
from models.model_loader import (
    load_production_model,
    load_model_by_version,
    list_models
)

# These use global loader instance
model_artifact = load_production_model()
models_list = list_models(limit=5)
```

**Option 3: In FastAPI** (predict_api.py)
```python
from models.model_loader import load_production_model

model_artifact = load_production_model()
if model_artifact:
    model = model_artifact['model']
    preprocessor = model_artifact['preprocessor']
    scaler = model_artifact['scaler']
```

### Storing Predictions

```python
from scripts.db_utils import ModelEvaluationDB

with ModelEvaluationDB() as db:
    db.store_prediction(
        model_version="20260105_143022",
        input_features={
            "year": 2020,
            "mileage": 50000,
            "brand": "Toyota",
            "condition": "Good",
            "engine_size": 2.5,
            "transmission": "Automatic"
        },
        predicted_value=22500.50,
        actual_value=23000.00,  # Optional
        confidence_score=0.95    # Optional
    )
```

### List Available Models

```python
from scripts.db_utils import ModelEvaluationDB

with ModelEvaluationDB() as db:
    models = db.list_models(limit=10)
    
    for model in models:
        print(f"Version: {model['model_version']}")
        print(f"Type: {model['model_type']}")
        print(f"R² Score: {model['r2_score']}")
        print(f"Production: {model['is_production']}")
        print(f"Created: {model['created_at']}")
        print("---")
```

### Promote Model to Production

```python
from scripts.db_utils import ModelEvaluationDB

with ModelEvaluationDB() as db:
    # Promote specific version to production
    db.set_production_model("20260105_143022")
    print("✓ Model promoted to production")
```

## Model Loading Workflow

The `ModelLoader` class implements intelligent fallback:

```
1. Load Production Model
   ↓
   ├─→ Try Database (is_production = TRUE)
   │   ├─→ Success: Return model ✓
   │   └─→ Failed: Continue to step 2
   │
   ├─→ Try Filesystem
   │   ├─→ models/production/model.pkl exists: Load ✓
   │   └─→ models/model.pkl exists: Load ✓
   │
   └─→ Failed: Return None, log warning
```

**Benefits**:
- **Graceful Degradation**: Works even if database is unavailable
- **Performance**: In-memory caching reduces database queries
- **Version Control**: Easy rollback to previous versions
- **Production-Ready**: Automatic fallback ensures reliability

## Configuration

### Database Connection

Set environment variables:
```bash
# PostgreSQL connection string
export DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres

# Or use defaults (localhost:5433)
```

### Model Versioning

Models are auto-versioned using timestamp:
```
Format: YYYYMMDD_HHMMSS
Example: 20260105_143022 (2026-01-05 at 14:30:22)
```

## Integration Examples

### Complete Training Pipeline

```python
import train
from scripts.db_utils import ModelEvaluationDB
import joblib
import io

# Train model
model_artifact = train.train_model()

# Serialize to bytes
model_bytes = io.BytesIO()
joblib.dump(model_artifact, model_bytes)
model_binary = model_bytes.getvalue()

# Store in database
with ModelEvaluationDB() as db:
    model_version = "20260105_143022"
    
    db.store_model(
        run_id="mlflow-run-123",
        model_version=model_version,
        model_type="RandomForest",
        model_binary=model_binary,
        accuracy=0.85,
        rmse=3500.0,
        r2=0.92,
        is_production=True
    )
    print(f"✓ Model v{model_version} stored")

# Later: Load and use
from models.model_loader import load_production_model

model_artifact = load_production_model()
model = model_artifact['model']
prediction = model.predict([[...features...]])
```

### Prediction with Logging

```python
from models.model_loader import ModelLoader
from scripts.db_utils import ModelEvaluationDB

loader = ModelLoader()
model_artifact = loader.load_production_model()
model = model_artifact['model']

# Make prediction
input_features = {"year": 2020, "mileage": 50000, ...}
prediction = model.predict([[...features...]])[0]

# Log prediction
with ModelEvaluationDB() as db:
    db.store_prediction(
        model_version="20260105_143022",
        input_features=input_features,
        predicted_value=prediction
    )

loader.close()
```

## Monitoring & Maintenance

### Check Model Status

```python
from scripts.db_utils import ModelEvaluationDB

with ModelEvaluationDB() as db:
    models = db.list_models(limit=20)
    
    print("Production Model:")
    prod = [m for m in models if m['is_production']]
    if prod:
        print(f"  v{prod[0]['model_version']}")
        print(f"  R² = {prod[0]['r2_score']}")
    
    print("\nAll Models:")
    for m in models:
        print(f"  v{m['model_version']}: "
              f"R²={m['r2_score']}, "
              f"Size={m['model_size_bytes']/1024:.1f}KB")
```

### Model Size Tracking

```sql
-- Total size of all model versions
SELECT 
    SUM(model_size_bytes) / 1024.0 / 1024.0 as total_size_mb,
    COUNT(*) as total_models
FROM model_artifacts;

-- Size by model type
SELECT 
    model_type,
    COUNT(*) as count,
    AVG(model_size_bytes) / 1024.0 as avg_size_kb
FROM model_artifacts
GROUP BY model_type;
```

### Prediction Monitoring

```sql
-- Recent predictions
SELECT 
    model_version,
    COUNT(*) as prediction_count,
    AVG(predicted_value) as avg_prediction
FROM model_predictions
WHERE prediction_time > NOW() - INTERVAL '1 day'
GROUP BY model_version;

-- Prediction accuracy (when actual_value available)
SELECT 
    model_version,
    COUNT(*) as predictions_with_actual,
    AVG(ABS(predicted_value - actual_value)) as mean_absolute_error
FROM model_predictions
WHERE actual_value IS NOT NULL
GROUP BY model_version;
```

## Troubleshooting

### Issue: "Failed to store model in database"

**Solution**: Check database connection
```python
from scripts.db_utils import ModelEvaluationDB

try:
    with ModelEvaluationDB() as db:
        print("✓ Database connection OK")
except Exception as e:
    print(f"✗ Database error: {e}")
    print("  Check PostgreSQL is running on port 5433")
    print("  Check DATABASE_URL environment variable")
```

### Issue: "Model artifact not found"

**Solution**: Check both database and filesystem
```bash
# Check filesystem
ls -la models/production/model.pkl
ls -la models/model.pkl

# Check database
python -c "from models.model_loader import list_models; print(list_models(10))"
```

### Issue: "Database unavailable, using filesystem"

**Normal behavior** - system will fall back to filesystem if database is unavailable.

To verify database:
```bash
# Test database connection
python -c "from scripts.db_utils import ModelEvaluationDB; ModelEvaluationDB()"

# Check PostgreSQL service
docker-compose -f deployment/dev/docker-compose.dev.yml ps postgres
```

## Best Practices

✅ **DO**:
- Store models after every successful training
- Mark production models with `is_production=True`
- Store predictions for monitoring
- Use ModelLoader for all model loading
- Clean up old model versions periodically

❌ **DON'T**:
- Manually delete models from database (use migrations)
- Store unversioned models
- Ignore database connection errors
- Use filesystem as only backup

## Performance Considerations

### Storage
- **Typical Model Size**: 5-50 MB (pickle serialized)
- **Storage**: 20 models × 25 MB = 500 MB
- **Recommendation**: Archive old models to keep database lean

### Loading
- **First Load**: ~500ms (database query + deserialization)
- **Cached Load**: ~1ms (in-memory)
- **Recommendation**: Use ModelLoader for automatic caching

### Queries
- Model artifacts indexed by `run_id` and `is_production`
- Predictions indexed by `model_version`
- Optimize for reads (most operations are predictions)

## Next Steps

1. **Train a model**: `python train.py` (automatically stores in database)
2. **List models**: `python src/models/model_loader.py`
3. **Load model**: Use `ModelLoader` in your code
4. **Monitor**: Check `model_predictions` table
5. **Maintain**: Archive old versions monthly

---

**Questions?** Check [README.md](README.md) or [GETTING_STARTED.md](GETTING_STARTED.md)
