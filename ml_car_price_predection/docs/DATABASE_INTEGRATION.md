# PostgreSQL Database Integration for Model Evaluation

## Overview

Model evaluation results are automatically stored in PostgreSQL database for:
- Historical tracking and trend analysis
- Performance monitoring across versions
- Alert management
- Feature importance tracking
- Data quality metrics

## Database Schema

### Tables

**model_runs** - Training run metadata
- `run_id` - MLflow run identifier (unique)
- `model_name` - Model name
- `model_version` - Version number
- `model_stage` - Deployment stage (None/Staging/Production)
- `trained_at` - Training timestamp
- `metadata` - Additional metadata (JSONB)

**model_metrics** - Performance metrics
- `run_id` - Reference to model_runs
- `metric_name` - Metric name (mse, rmse, mae, r2_score, etc.)
- `metric_value` - Metric value
- `metric_type` - train/test/cv

**model_hyperparameters** - Model configuration
- `run_id` - Reference to model_runs
- `param_name` - Parameter name
- `param_value` - Parameter value

**data_quality** - Data quality metrics
- `run_id` - Reference to model_runs
- `dataset_type` - train/test
- `total_rows`, `total_columns`
- `missing_values` - Column-wise missing values (JSONB)
- `duplicate_rows` - Count of duplicate rows

**model_alerts** - Alerts and warnings
- `run_id` - Reference to model_runs (optional)
- `alert_type` - Type of alert
- `severity` - HIGH/MEDIUM/LOW
- `message` - Alert message
- `resolved` - Resolution status

**feature_importance** - Feature importance scores
- `run_id` - Reference to model_runs
- `feature_name` - Feature name
- `importance_score` - Importance value
- `rank` - Feature rank

## Configuration

The DAG automatically uses Airflow's PostgreSQL database:

```python
# Default connection (using port 5433 to avoid conflict with local PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres
```

## Usage

### 1. Automatic Storage (via Airflow DAG)

Results are automatically stored when the training pipeline runs:
- After model training completes
- During model evaluation
- When registering models
- On promotion to staging/production

### 2. Query Results

**View latest runs:**
```bash
python query_results.py --action runs --limit 10
```

**View detailed metrics for a run:**
```bash
python query_results.py --action metrics --run-id <run_id>
```

**View performance trend:**
```bash
python query_results.py --action trend --model-name car_price_predictor --metric r2_score --days 30
```

**View alerts:**
```bash
# All alerts
python query_results.py --action alerts --limit 20

# High severity only
python query_results.py --action alerts --severity HIGH
```

**Compare two runs:**
```bash
python query_results.py --action compare --run-id <run_id_1> --run-id2 <run_id_2>
```

**Export to CSV:**
```bash
python query_results.py --action export --output model_results.csv
```

### 3. Direct Database Access

**Connect via psql:**
```bash
psql -h localhost -p 5433 -U postgres -d postgres
```

**Example queries:**

```sql
-- Latest model performance
SELECT 
    mr.trained_at,
    mr.model_version,
    mm.metric_name,
    mm.metric_value
FROM model_runs mr
JOIN model_metrics mm ON mr.run_id = mm.run_id
WHERE mr.model_name = 'car_price_predictor'
AND mm.metric_type = 'test'
ORDER BY mr.trained_at DESC
LIMIT 5;

-- Model performance trend
SELECT 
    DATE(mr.trained_at) as date,
    AVG(mm.metric_value) as avg_r2
FROM model_runs mr
JOIN model_metrics mm ON mr.run_id = mm.run_id
WHERE mm.metric_name = 'r2_score'
GROUP BY DATE(mr.trained_at)
ORDER BY date DESC;

-- Unresolved alerts
SELECT severity, COUNT(*) 
FROM model_alerts 
WHERE resolved = FALSE 
GROUP BY severity;

-- Top features across all runs
SELECT 
    feature_name,
    AVG(importance_score) as avg_importance
FROM feature_importance
GROUP BY feature_name
ORDER BY avg_importance DESC
LIMIT 10;
```

## Python API

Use the database utilities in your own scripts:

```python
from scripts.db_utils import get_db_connection

# Store evaluation results
with get_db_connection() as db:
    # Insert model run
    db.insert_model_run(
        run_id='run_123',
        model_name='car_price_predictor',
        model_version='1',
        trained_at=datetime.now(),
        metadata={'notes': 'Production run'}
    )
    
    # Insert metrics
    metrics = {
        'mse': 1234.56,
        'rmse': 35.12,
        'r2_score': 0.87
    }
    db.insert_metrics('run_123', metrics, metric_type='test')
    
    # Insert alert
    db.insert_alert(
        run_id='run_123',
        alert_type='PERFORMANCE_WARNING',
        severity='MEDIUM',
        message='R2 score below threshold'
    )
    
    # Query results
    trend = db.get_model_performance_trend('car_price_predictor', 'r2_score')
    alerts = db.get_unresolved_alerts(severity='HIGH')
```

## Benefits

✅ **Historical tracking** - All training runs preserved with metrics  
✅ **Performance monitoring** - Track model degradation over time  
✅ **Easy querying** - SQL queries for analysis and reporting  
✅ **Alert management** - Centralized alert tracking and resolution  
✅ **Audit trail** - Complete history of model changes  
✅ **Integration** - Works with existing MLflow and Airflow setup  

## Maintenance

### Backup Database

```bash
pg_dump -h localhost -p 5433 -U postgres postgres > model_eval_backup.sql
```

### Restore Database

```bash
psql -h localhost -p 5433 -U postgres postgres < model_eval_backup.sql
```

### Clean Old Records

```sql
-- Delete runs older than 90 days
DELETE FROM model_runs 
WHERE trained_at < NOW() - INTERVAL '90 days';

-- Archive resolved alerts older than 30 days
DELETE FROM model_alerts 
WHERE resolved = TRUE 
AND created_at < NOW() - INTERVAL '30 days';
```

## Troubleshooting

**Connection refused:**
- Check PostgreSQL is running: `docker ps | grep postgres`
- Verify port 5433 is accessible: `netstat -an | findstr 5433`

**Permission denied:**
- Check database credentials in connection string
- Ensure user has CREATE/INSERT permissions

**Table not found:**
- Run `python scripts/db_utils.py` to create tables
- Or trigger Airflow DAG which creates tables automatically
